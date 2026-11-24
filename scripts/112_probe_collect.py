"""Collect Qwen3 reasoning traces with residual-stream activations (docs/OPEN_WEIGHTS_PROBE_PROTOCOL.md).

Runs the deference design locally through `transformers`, records the final answer, the reasoning segment and the
residual stream at the last position of every generation step at four layers (fractions of depth 0.25, 0.5, 0.75
and L-4). Row 0 of `acts` is the prefill: the state at the last prompt token, before any reasoning token. Row j
(j >= 1) is the state at generated token j-1, i.e. the forward pass that produced generated token j; so the row for
generated token i is i+1. A run that stops by EOS has n_gen+1 rows (the last row is the state at the final answer
token, whose forward produced EOS); a run cut by the cap has n_gen rows (no forward follows the last token).

    python scripts/112_probe_collect.py --model Qwen/Qwen3-32B --label qwen3_32b
    python scripts/112_probe_collect.py --model Qwen/Qwen3-4B --label smoke_qwen3_4b --smoke   # laptop smoke test

Resumable: runs whose activation file exists are skipped. Outputs under results/open_weights_probe/<label>/:
runs.csv, traces.jsonl, acts/<sample_id>.npz (acts float16 [n_steps, n_layers, d]; token_ids; n_think; n_gen).
No API calls.
"""
import argparse, json, pathlib, re, sys, time
import numpy as np, pandas as pd, torch, yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "scripts"))
from outcomes import parse_answer
cfg = yaml.safe_load(open(ROOT / "config.yaml"))
REFUSAL = re.compile(cfg["outcomes"]["refusal_regex"])
SEED = int(cfg["study"]["seed"])
LAYER_FRACS = (0.25, 0.5, 0.75)


def pick_layers(n_layers):
    return sorted({max(1, round(f * n_layers)) for f in LAYER_FRACS} | {n_layers - 4})


def safe_id(sample_id):
    return sample_id.replace("|", "__")


def load_model(name, device):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(name); tok.padding_side = "left"
    if tok.pad_token_id is None: tok.pad_token = tok.eos_token
    kw = dict(dtype=torch.bfloat16)
    if device == "cuda": kw["device_map"] = "auto"
    model = AutoModelForCausalLM.from_pretrained(name, **kw)
    if device != "cuda": model = model.to(device)
    model.eval()
    return tok, model


def decoder_layers(model):
    for attr in ("model.layers", "transformer.h", "layers"):
        obj = model
        try:
            for a in attr.split("."): obj = getattr(obj, a)
            return obj
        except AttributeError:
            continue
    raise RuntimeError("cannot find decoder layers")


class Capture:
    """Forward hooks on the chosen layers; at each forward call store hidden[:, -1, :] (float16, CPU)."""
    def __init__(self, layers, idx):
        self.steps = []          # list over steps of [n_layers, B, d]
        self._cur = {}
        self.idx = idx
        self.handles = [layers[i].register_forward_hook(self._hook(i)) for i in idx]

    def _hook(self, i):
        def f(module, inp, out):
            h = out[0] if isinstance(out, (tuple, list)) else out
            self._cur[i] = h[:, -1, :].detach().to("cpu", torch.float16)
            if len(self._cur) == len(self.idx):
                self.steps.append(torch.stack([self._cur[j] for j in self.idx]))
                self._cur = {}
        return f

    def reset(self): self.steps, self._cur = [], {}

    def close(self):
        for h in self.handles: h.remove()

    def stacked(self):   # [n_steps, n_layers, B, d]
        return torch.stack(self.steps)


def build_prompts(tok, prompts):
    return [tok.apply_chat_template([{"role": "user", "content": p}], tokenize=False, add_generation_prompt=True, enable_thinking=True) for p in prompts]


def split_generation(tok, gen_ids, think_id, end_think_id, eos_ids):
    """Returns (n_gen, n_think, reasoning_text, completion_text, stop_reason). n_think = reasoning tokens between
    <think> and </think>; positions in the activation array are 1-based for generated tokens (0 = prefill)."""
    ids = gen_ids.tolist()
    n_gen = len(ids)
    for j, t in enumerate(ids):
        if t in eos_ids: n_gen = j; break          # eos excluded from the generated count
    ids = ids[:n_gen]
    stop = "stop" if n_gen < len(gen_ids) else "max_tokens"
    start = 1 if ids and ids[0] == think_id else 0
    if end_think_id in ids:
        e = ids.index(end_think_id)
        reasoning = tok.decode(ids[start:e], skip_special_tokens=True)
        completion = tok.decode(ids[e + 1:], skip_special_tokens=True)
        n_think = e - start
    else:
        reasoning = tok.decode(ids[start:], skip_special_tokens=True); completion = ""; n_think = n_gen - start
    return n_gen, n_think, reasoning, completion, stop, (start, (ids.index(end_think_id) if end_think_id in ids else None))


def classify(completion, stop, has_end_think):
    chosen = parse_answer(completion)
    if not has_end_think and stop == "max_tokens": return "censored", None
    if REFUSAL.search(completion or ""): return "refusal", None
    if chosen is None: return ("censored" if stop == "max_tokens" else "unparseable"), None
    return "answered", chosen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen3-32B"); ap.add_argument("--label", required=True)
    ap.add_argument("--design", default=str(ROOT / "data/processed/deference_model2_design.csv"))
    ap.add_argument("--max-new-tokens", type=int, default=int(cfg["model"]["max_tokens"]))
    ap.add_argument("--batch-size", type=int, default=8); ap.add_argument("--device", default=None)
    ap.add_argument("--temperature", type=float, default=float(cfg["model"]["temperature"]))
    ap.add_argument("--top-p", type=float, default=0.95); ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--smoke", action="store_true", help="10 questions x (control rep 0 + p95 rep 0), cap 2048")
    ap.add_argument("--limit", type=int, default=None, help="first N design rows (debug)")
    a = ap.parse_args()
    device = a.device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    out = ROOT / "results/open_weights_probe" / a.label; (out / "acts").mkdir(parents=True, exist_ok=True)

    d = pd.read_csv(a.design)
    d["sample_id"] = d.qid + "|" + d.cell + "|" + d.rep.astype(str)
    if a.smoke:
        qs = sorted(d.qid.unique())[:10]
        d = d[d.qid.isin(qs) & (d.rep == 0) & d.cell.isin(["control", "p95"])]
        a.max_new_tokens = min(a.max_new_tokens, 2048)
    if a.limit: d = d.head(a.limit)
    done = {p.stem for p in (out / "acts").glob("*.npz")}
    todo = d[~d.sample_id.map(safe_id).isin(done)].copy()
    print(f"{len(todo)} runs to make ({len(done)} already on disk); device {device}; model {a.model}; cap {a.max_new_tokens}", flush=True)
    json.dump(dict(model=a.model, device=device, max_new_tokens=a.max_new_tokens, temperature=a.temperature, top_p=a.top_p, top_k=a.top_k,
                   batch_size=a.batch_size, seed=SEED, design=a.design, smoke=a.smoke, started=time.strftime("%Y-%m-%dT%H:%M:%S")),
              open(out / "collect_config.json", "w"), indent=1)
    if todo.empty: return

    tok, model = load_model(a.model, device)
    layers = decoder_layers(model); idx = pick_layers(len(layers))
    print(f"{len(layers)} layers; capturing {idx}", flush=True)
    think_id, end_think_id = tok.convert_tokens_to_ids("<think>"), tok.convert_tokens_to_ids("</think>")
    eos_ids = {tok.eos_token_id, tok.convert_tokens_to_ids("<|im_end|>"), tok.convert_tokens_to_ids("<|endoftext|>")} - {None}
    cap = Capture(layers, idx)
    # longest prompts first so padding waste is small and the first batch is the worst case for memory
    todo["plen"] = [len(tok(p).input_ids) for p in build_prompts(tok, todo.prompt.tolist())]
    todo = todo.sort_values("plen", ascending=False)
    runs_path, traces_path = out / "runs.csv", out / "traces.jsonl"
    rows = []
    for b0 in range(0, len(todo), a.batch_size):
        batch = todo.iloc[b0:b0 + a.batch_size]
        enc = tok(build_prompts(tok, batch.prompt.tolist()), return_tensors="pt", padding=True).to(model.device)
        torch.manual_seed(SEED + int(batch.order.iloc[0]))
        cap.reset(); t0 = time.time()
        with torch.no_grad():
            gen = model.generate(**enc, do_sample=True, temperature=a.temperature, top_p=a.top_p, top_k=a.top_k,
                                 max_new_tokens=a.max_new_tokens, pad_token_id=tok.pad_token_id)
        plen = enc.input_ids.shape[1]; acts = cap.stacked()     # [steps, L, B, d]; steps = 1 + generated
        for i, x in enumerate(batch.itertuples()):
            g = gen[i, plen:]
            n_gen, n_think, reasoning, completion, stop, (start, e_idx) = split_generation(tok, g, think_id, end_think_id, eos_ids)
            outcome, chosen = classify(completion, stop, e_idx is not None)
            followed = (chosen == x.hint_letter) if chosen else None; correct = (chosen == x.target) if chosen else None
            A = acts[: n_gen + 1, :, i, :].numpy()               # prefill + each generated token (see module docstring)
            assert A.shape[0] == n_gen + (1 if stop == "stop" else 0), (x.sample_id, A.shape, n_gen, stop)
            np.savez_compressed(out / "acts" / f"{safe_id(x.sample_id)}.npz", acts=A, layers=np.array(idx), token_ids=g[:n_gen].cpu().numpy(),
                                n_gen=n_gen, n_think=n_think, think_start=start, end_think_idx=-1 if e_idx is None else e_idx)
            row = dict(sample_id=x.sample_id, qid=x.qid, cell=x.cell, rep=int(x.rep), rate=x.rate, cue=x.cue, hint_letter=x.hint_letter, target=x.target,
                       correct_is_A=bool(x.correct_is_A), cue_present=int(x.cell != "control"), outcome=outcome, chosen=chosen, correct=correct, followed=followed,
                       reasoning_tokens=n_think, output_tokens=n_gen, stop_reason=stop, prompt_tokens=int(x.plen), model=a.model, label=a.label)
            rows.append(row)
            pd.DataFrame([row]).to_csv(runs_path, mode="a", header=not runs_path.exists(), index=False)
            with open(traces_path, "a") as f:
                f.write(json.dumps(dict(sample_id=x.sample_id, qid=x.qid, cell=x.cell, rep=int(x.rep), hint_letter=x.hint_letter, target=x.target,
                                        chosen=chosen, reasoning=reasoning, completion=completion)) + "\n")
        dt = time.time() - t0; ntok = int(sum(r["output_tokens"] for r in rows[-len(batch):]))
        print(f"batch {b0 // a.batch_size + 1}/{(len(todo) + a.batch_size - 1) // a.batch_size}: {len(batch)} runs, {ntok} tokens, {dt:.0f}s ({ntok / dt:.1f} tok/s); "
              f"outcomes {[r['outcome'] for r in rows[-len(batch):]]}", flush=True)
    cap.close()
    r = pd.read_csv(runs_path).drop_duplicates("sample_id", keep="last")
    print(r.groupby("cell").agg(n=("qid", "size"), answered=("outcome", lambda s: (s == "answered").mean()), followed=("followed", "mean"),
                                correct=("correct", "mean"), tokens=("reasoning_tokens", "mean")).round(3))


if __name__ == "__main__":
    main()

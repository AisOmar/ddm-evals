"""Parse Inspect logs into one row per run (plan 2.3 deliverable: pilot.csv).

usage: python scripts/03_parse_logs.py [--log-dir logs/pilot] [--out results/pilot.csv]
"""
import argparse, glob, csv, re, yaml
from inspect_ai.log import read_eval_log
from outcomes import classify, parse_answer, _lines

cfg = yaml.safe_load(open("config.yaml"))
REFUSAL_RE = re.compile(cfg["outcomes"]["refusal_regex"])

# Plan 0.3: when the API reports no reasoning_tokens but the log holds the reasoning text, count it with the
# study model's own tokenizer (config model.tokenizer). Falls back to output_tokens - answer_line_tokens otherwise.
_TOK = None
if cfg["model"].get("tokenizer"):
    try:
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer
        _TOK = Tokenizer.from_file(hf_hub_download(cfg["model"]["tokenizer"], "tokenizer.json"))
    except Exception as e:  # offline or missing dep: counting degrades to the output_tokens rule, and we say so
        print(f"tokenizer {cfg['model']['tokenizer']} unavailable ({type(e).__name__}); using output_tokens fallback")


def reasoning_text(sample):
    """Concatenated reasoning blocks Inspect stored for the final assistant message ('' if none)."""
    try:
        content = sample.output.message.content
        if isinstance(content, list):
            return "".join(getattr(c, "reasoning", "") for c in content if getattr(c, "type", "") == "reasoning")
    except Exception:
        pass
    return ""
ap = argparse.ArgumentParser()
ap.add_argument("--log-dir", default=cfg["pilot"]["log_dir"])
ap.add_argument("--out", default="results/pilot.csv")
ap.add_argument("--max-tokens", type=int, default=None, help="cap C used in this log dir when it differs from config model.max_tokens (deadline of censored rows)")
a = ap.parse_args()

rows = []
for path in sorted(glob.glob(f"{a.log_dir}/*.eval")):
    log = read_eval_log(path)
    if log.status != "success":
        print(f"skipping {path.split('/')[-1]}: status={log.status}")
    for s in log.samples or []:
        if not s.scores:          # interrupted/errored sample, never scored
            continue
        sc = next(iter(s.scores.values()))
        md = dict(sc.metadata or {})
        # Re-classify from the stored completion so pilot.csv always reflects the current rule in outcomes.py.
        usage = s.output.usage
        api_rt = getattr(usage, "reasoning_tokens", None) if usage else None   # provider's own count, kept for cross-check
        rtext = reasoning_text(s)
        completion = s.output.completion or ""
        # plan 0.3: the reasoning segment is everything generated before the final answer line = the hidden reasoning
        # channel + any visible text above the answer line, counted with the study model's own tokenizer. That path
        # is taken only for the frozen study model (config model.name), whose tokenizer this is; other models keep the
        # fallback output_tokens - answer_line_tokens (plus the API count when the provider gives one).
        # Note (R1 rerun 2026-10-08): OpenRouter's reasoning_tokens undercounts truncated runs by ~35%, so the API
        # count is a cross-check only.
        study_model = (log.eval.model == cfg["model"]["name"])
        recorded_cap = None
        for event in s.events or []:
            if getattr(event, "event", None) == "model":
                recorded_cap = getattr(getattr(event, "config", None), "max_tokens", None) or recorded_cap
        token_cap = a.max_tokens or recorded_cap or cfg["model"]["max_tokens"]
        vis_lines = _lines(completion)
        vis_pre = "\n".join(vis_lines[:-1]) if (vis_lines and parse_answer(completion) is not None) else completion
        if _TOK is not None and study_model:
            tok_r = len(_TOK.encode(rtext, add_special_tokens=False).ids) if rtext else 0
            tok_v = len(_TOK.encode(vis_pre, add_special_tokens=False).ids) if vis_pre.strip() else 0
            tok_rt = tok_r + tok_v
        else:
            tok_r = tok_v = tok_rt = None
        measured = tok_rt if tok_rt is not None else api_rt
        cat, chosen, rt, rt_source = classify(
            s.output.completion, getattr(s.output, "stop_reason", None),
            measured,
            getattr(usage, "output_tokens", None) if usage else None,
            REFUSAL_RE, cfg["measurement"]["answer_line_tokens"])
        if rt_source == "api" and tok_rt is not None:
            rt_source = "hf_tokenizer"
        # deadline on the DDM time scale: our cap for censored runs, the run's own length for incomplete ones
        if cat == "censored":
            deadline = token_cap / cfg["measurement"]["rt_unit_tokens"]
        elif cat == "incomplete" and rt:
            deadline = rt / cfg["measurement"]["rt_unit_tokens"]
        else:
            deadline = None
        target = s.target if isinstance(s.target, str) else s.target[0]
        correct = (chosen == target) if chosen else None
        rows.append({"log": path.split("/")[-1], "model": log.eval.model, "sample_id": s.id,
                     **{k: md.get(k) for k in ["qid", "condition", "scaffold", "instruction", "rep",
                                                "correct_is_A", "has_code"]},
                     "outcome": cat, "scorer_outcome": md.get("outcome"), "chosen": chosen, "correct": correct,
                     "reasoning_tokens": rt, "rt_source": rt_source, "api_reasoning_tokens": api_rt, "reasoning_chars": len(rtext),
                     "hidden_reasoning_tokens": tok_r, "visible_pre_answer_tokens": tok_v, "deadline": deadline,
                     "token_cap": token_cap, "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
                     "stop_reason": getattr(s.output, "stop_reason", None),
                     "rt": (rt / cfg["measurement"]["rt_unit_tokens"]) if rt else None,
                     "response": (1 if correct else -1) if correct is not None else None})

if not rows:
    raise SystemExit(f"no scored samples found in {a.log_dir}/*.eval — nothing written to {a.out}")
with open(a.out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
from collections import Counter
print(f"{len(rows)} runs -> {a.out}")
print("outcomes:", dict(Counter(r["outcome"] for r in rows)))
changed = sum(r["outcome"] != r["scorer_outcome"] for r in rows)
print(f"re-classified vs. scorer-at-run-time: {changed} rows changed category")
for c in cfg["conditions"]:
    sub = [r for r in rows if r["condition"] == c and r["outcome"] == "answered"]
    if sub:
        acc = sum(r["correct"] for r in sub) / len(sub)
        toks = sorted(r["reasoning_tokens"] or 0 for r in sub)
        print(f"  {c:15s} n={len(sub):4d} acc={acc:.2f} median_reasoning_tokens={toks[len(toks)//2]}")

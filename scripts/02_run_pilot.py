"""Run the 2x2 pilot with Inspect AI (plan v2, phase 2).

Each (question, condition, repeat) is its own Inspect sample so that option order can be balanced
WITHIN each question and condition, independently of repeat parity across conditions. Run with epochs=1 in Inspect;
the "epochs" here is our own repeat index.

usage: python scripts/02_run_pilot.py --model openrouter/<model> --limit 50 --epochs 10
       python scripts/02_run_pilot.py --model mockllm/model --limit 20 --epochs 2   # smoke test, no key
"""
import argparse, json, random, re, yaml
from outcomes import classify
from design import correct_is_a
from inspect_ai import Task, eval, task
from inspect_ai.dataset import Sample
from inspect_ai.model import GenerateConfig
from inspect_ai.scorer import Score, Target, accuracy, scorer
from inspect_ai.solver import TaskState, generate, solver

cfg = yaml.safe_load(open("config.yaml"))
REFUSAL_RE = re.compile(cfg["outcomes"]["refusal_regex"])


def build_samples(limit: int, epochs: int, seed: int, cells=None, rep_start: int = 0):
    items = [json.loads(l) for l in open(cfg["data"]["two_choice_path"])]
    rng = random.Random(seed)
    rng.shuffle(items)
    items = items[:limit]
    samples = []
    for it in items:
        for cond_name, cond in cfg["conditions"].items():
            if cells is not None and (it["qid"], cond_name) not in cells:   # follow-up runs restricted to listed cells
                continue
            for rep in range(rep_start, rep_start + epochs):
                correct_is_A = correct_is_a(it["qid"], cond_name, rep, cfg["conditions"], seed)
                A, B = (it["correct"], it["distractor"]) if correct_is_A else (it["distractor"], it["correct"])
                prompt = f"{cond['prompt']}\n\n{it['question']}\n\nA) {A}\nB) {B}"
                samples.append(Sample(
                    id=f"{it['qid']}|{cond_name}|{rep}", input=prompt, target="A" if correct_is_A else "B",
                    metadata={"qid": it["qid"], "condition": cond_name, "scaffold": cond["scaffold"],
                              "instruction": cond["instruction"], "rep": rep,
                              "correct_is_A": correct_is_A, "has_code": it["has_code"]}))
    return samples


@scorer(metrics=[accuracy()])
def two_choice_scorer():
    """Records chosen option, correctness, reasoning tokens and the outcome category (plan 2.3)."""
    async def score(state: TaskState, target: Target) -> Score:
        out = state.output
        text = out.completion or ""
        usage = out.usage
        reasoning_tokens = getattr(usage, "reasoning_tokens", None) if usage else None
        # fallback: length of any reasoning content blocks, if provider exposes them (count later with tokenizer)
        reasoning_text = ""
        try:
            for part in out.message.content if isinstance(out.message.content, list) else []:
                if getattr(part, "type", "") == "reasoning":
                    reasoning_text += getattr(part, "reasoning", "")
        except Exception:
            pass
        stop = getattr(out, "stop_reason", None)
        cat, chosen, reasoning_tokens, rt_source = classify(
            text, stop, reasoning_tokens, getattr(usage, "output_tokens", None) if usage else None,
            REFUSAL_RE, cfg["measurement"]["answer_line_tokens"])
        correct = (chosen == target.text) if chosen else None
        return Score(value=1.0 if correct else 0.0, answer=chosen,
                     metadata={"outcome": cat, "correct": correct, "chosen": chosen,
                               "reasoning_tokens": reasoning_tokens, "rt_source": rt_source, "reasoning_chars": len(reasoning_text),
                               "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
                               "stop_reason": stop, **state.metadata})
    return score


@task
def ddm_pilot(limit: int = 50, epochs: int = 10, cells=None, rep_start: int = 0, max_tokens: int | None = None):
    return Task(dataset=build_samples(limit, epochs, cfg["study"]["seed"], cells, rep_start),
                solver=[generate()], scorer=two_choice_scorer(),
                config=GenerateConfig(temperature=cfg["model"]["temperature"], max_tokens=max_tokens or cfg["model"]["max_tokens"]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=cfg["model"]["name"])
    ap.add_argument("--limit", type=int, default=cfg["pilot"]["n_questions"])
    ap.add_argument("--epochs", type=int, default=cfg["pilot"]["epochs"])
    ap.add_argument("--log-dir", default=cfg["pilot"]["log_dir"])
    ap.add_argument("--max-connections", type=int, default=None,
                    help="concurrent requests to the provider (OpenRouter caps in-flight spend by credit balance; use 1-4 on a small balance)")
    ap.add_argument("--cells", default=None, help="CSV with qid,condition columns: run only these cells (follow-up experiments)")
    ap.add_argument("--rep-start", type=int, default=0, help="first repeat index; position is counterbalanced across conditions and reverses each repeat")
    ap.add_argument("--max-tokens", type=int, default=None, help="override config model.max_tokens (the cap C) for this run; note it in CHANGELOG")
    ap.add_argument("--provider", default=None, help="OpenRouter upstream to pin, no fallbacks (e.g. DeepInfra)")
    ap.add_argument("--offline", action="store_true",
                    help="smoke test with no network: replace Inspect's tiktoken-based token estimate with len/4")
    a = ap.parse_args()
    if a.offline:
        import inspect_ai.model._model as _m
        _m.count_text_tokens = lambda text: max(1, len(text) // 4)
    cells = None
    if a.cells:
        import csv
        cells = {(r["qid"], r["condition"]) for r in csv.DictReader(open(a.cells))}
    model_args = {"provider": {"order": [a.provider], "allow_fallbacks": False}} if a.provider else {}
    eval(ddm_pilot(limit=a.limit, epochs=a.epochs, cells=cells, rep_start=a.rep_start, max_tokens=a.max_tokens),
         model=a.model, model_args=model_args, log_dir=a.log_dir, epochs=1,
         max_connections=a.max_connections, fail_on_error=0.05)   # tolerate up to 5% sample errors (transient 402/429) instead of aborting

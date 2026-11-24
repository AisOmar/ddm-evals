"""Frozen trust-study endpoints; inference is blocked until every response exists."""
import argparse
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from outcomes import parse_answer

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trust_collect_analysis", ROOT / "scripts/31_trust_collect.py")
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)
OUT = collect.OUT
MODELS = ["R1", "Qwen3", "gpt-oss"]
WORDS = ["frequency", "probability"]
SEED = 20261017
GROUPS = list(itertools.product(MODELS, WORDS, [False, True], [.55, .95]))


def read_completed():
    collect.require_no_batch()
    m = collect.manifest()
    attempts = collect.index_attempts()
    valid = [(t, *collect.delivered(t, attempts[t["sample_id"]])) for t in m["trials"]]
    if any(x is None for _, _, x in valid):
        raise ValueError("Incomplete collection: treatment-effect analysis is blocked")
    rows, traces = [], []
    for trial, path, response in valid:
        choice = response["choices"][0]
        message = choice["message"]
        text = message.get("content") or ""
        if not isinstance(text, str):
            raise ValueError("Invalid completion type")
        chosen = parse_answer(text)
        if collect.REFUSAL.search(text.replace("’", "'")):
            outcome, chosen = "refusal", None
        elif chosen is not None:
            outcome = "answered"
        elif choice.get("finish_reason") == "length":
            outcome = "censored"
        else:
            outcome = "unparseable" if text.strip() else "incomplete"
        usage = response["usage"]
        rows.append(dict(sample_id=trial["sample_id"], qid=trial["qid"], model=trial["model"],
                         wording=trial["wording"], key_correct=trial["key_correct"], rate=trial["rate"],
                         rep=trial["rep"], target=trial["target"], key_letter=trial["key_letter"],
                         outcome=outcome, chosen=chosen, correct=float(chosen == trial["target"]) if chosen else np.nan,
                         followed=float(chosen == trial["key_letter"]) if chosen and trial["key_letter"] else np.nan,
                         provider=response["provider"], api_in=usage.get("prompt_tokens"),
                         api_out=usage.get("completion_tokens"), cost=usage.get("cost"), log=path.name))
        reasoning = message.get("reasoning") or "\n".join(x.get("text", "") for x in message.get("reasoning_details", []) if x.get("type") == "reasoning.text")
        traces.append(dict(sample_id=trial["sample_id"], completion=text, reasoning=reasoning))
    d = pd.DataFrame(rows)
    if len(d) != len(m["trials"]) or d.sample_id.duplicated().any():
        raise ValueError("Coverage mismatch")
    d.to_csv(OUT / "runs.csv", index=False)
    (OUT / "traces.jsonl").write_text("".join(json.dumps(x) + "\n" for x in traces))
    return d, m


def arrays(d, qids):
    hinted = d[d.wording.isin(WORDS)]
    if hinted.duplicated(["qid", "model", "wording", "key_correct", "rate"]).any():
        raise ValueError("Duplicate factorial cells")
    p = hinted.pivot(index="qid", columns=["model", "wording", "key_correct", "rate"], values="correct")
    p = p.reindex(index=qids, columns=pd.MultiIndex.from_tuples(GROUPS))
    x = p.to_numpy(float).reshape(len(qids), 3, 2, 2, 2)
    control = d[d.wording == "control"]
    if control.duplicated(["qid", "model", "rep"]).any():
        raise ValueError("Duplicate control cells")
    c = control.pivot(index="qid", columns=["model", "rep"], values="correct")
    c = c.reindex(index=qids, columns=pd.MultiIndex.from_product([MODELS, [0, 1]]))
    return x, c.to_numpy(float).reshape(len(qids), 3, 2)


def primary_scores(x):
    # Average over fixed wording and key-correctness levels, not trials of varying size.
    return (x[..., 1] - x[..., 0]).mean(axis=(2, 3))


def family_intervals(scores, names, draws, rng):
    scores = np.asarray(scores)
    if scores.ndim != 2 or scores.shape[1] != len(names) or not len(scores) or not np.isfinite(scores).all():
        raise ValueError("Intervals require complete question-level scores")
    boots = np.empty((draws, len(names)))
    for start in range(0, draws, 500):
        size = min(500, draws - start)
        weights = rng.multinomial(len(scores), np.full(len(scores), 1 / len(scores)), size=size)
        boots[start:start+size] = weights @ scores / len(scores)
    tail = .05 / (2 * len(names))
    bounds = np.quantile(boots, [tail, 1-tail], axis=0)
    return [dict(name=name, estimate=float(estimate), lo=float(bounds[0, i]), hi=float(bounds[1, i]),
                 n_questions=len(scores), family_size=len(names), supported=bool(bounds[0, i] > 0 or bounds[1, i] < 0))
            for i, (name, estimate) in enumerate(zip(names, scores.mean(axis=0)))]


def available_intervals(x, draws, rng):
    flat = x.reshape(len(x), -1)
    values = np.nan_to_num(flat)
    counts = np.isfinite(flat).astype(float)
    means = np.divide(values.sum(axis=0), counts.sum(axis=0), out=np.full(flat.shape[1], np.nan), where=counts.sum(axis=0) > 0)
    point = primary_scores(means.reshape(1, 3, 2, 2, 2))[0]
    boots = np.empty((draws, 3))
    for start in range(0, draws, 500):
        size = min(500, draws-start)
        weights = rng.multinomial(len(x), np.full(len(x), 1 / len(x)), size=size)
        denom = weights @ counts
        numer = weights @ values
        means = np.divide(numer, denom, out=np.full_like(numer, np.nan), where=denom > 0)
        boots[start:start+size] = primary_scores(means.reshape(size, 3, 2, 2, 2))
    bounds = np.nanquantile(boots, [.05/6, 1-.05/6], axis=0)
    return [dict(name=model, estimate=float(point[i]), lo=float(bounds[0, i]), hi=float(bounds[1, i])) for i, model in enumerate(MODELS)]


def missing_bounds(x):
    coefficients = np.broadcast_to(np.array([-.25, .25]), (2, 2, 2))
    values = np.nan_to_num(x)
    missing = np.isnan(x)
    lower = ((values + missing * (coefficients < 0)) * coefficients).sum(axis=(2, 3, 4)).mean(axis=0)
    upper = ((values + missing * (coefficients > 0)) * coefficients).sum(axis=(2, 3, 4)).mean(axis=0)
    return [dict(name=model, lo=float(lower[i]), hi=float(upper[i])) for i, model in enumerate(MODELS)]


def estimate(d, qids, draws=20000):
    x, controls = arrays(d, qids)
    complete = np.isfinite(x).all(axis=(1, 2, 3, 4))
    selected = x[complete]
    rng = np.random.default_rng(SEED)
    minimum = max(80, int(np.ceil(.8 * len(qids))))
    result = dict(n_planned_questions=len(qids), n_primary_questions=int(complete.sum()),
                  primary_minimum_questions=minimum, confirmatory_cohort_passed=bool(complete.sum() >= minimum),
                  excluded_primary_questions=[q for q, keep in zip(qids, complete) if not keep],
                  primary=[], pairs=[], wordings=[], helpful_harmful=[])
    if len(selected):
        scores = primary_scores(selected)
        result["primary"] = family_intervals(scores, MODELS, draws, rng)
        pairs = scores[:, [0, 0, 1]] - scores[:, [1, 2, 2]]
        result["pairs"] = family_intervals(pairs, ["R1 minus Qwen3", "R1 minus gpt-oss", "Qwen3 minus gpt-oss"], draws, rng)
        words = (selected[..., 1] - selected[..., 0]).mean(axis=3).reshape(len(selected), 6)
        result["wordings"] = family_intervals(words, [f"{m} {w}" for m in MODELS for w in WORDS], draws, rng)
    secondary = complete & np.isfinite(controls).all(axis=(1, 2))
    result["n_helpful_harmful_questions"] = int(secondary.sum())
    result["excluded_helpful_harmful_questions"] = [q for q, keep in zip(qids, secondary) if not keep]
    if secondary.any():
        # question × model × reliability; control mean is kept paired with every cell.
        a = x[secondary].mean(axis=2)
        b = controls[secondary].mean(axis=2)[..., None]
        helpful = a[:, :, 1, :] - b
        harmful = b - a[:, :, 0, :]
        combined = np.stack([helpful, harmful], axis=-1).reshape(secondary.sum(), 12)
        names = [f"{m} {rate} {kind}" for m in MODELS for rate in ["55%", "95%"] for kind in ["helpful", "harmful"]]
        result["helpful_harmful"] = family_intervals(combined, names, draws, rng)
    result["available_answers"] = available_intervals(x, draws, rng)
    result["unconditional_correct_yield"] = family_intervals(primary_scores(np.nan_to_num(x)), MODELS, draws, rng)
    result["worst_case_missing_bounds"] = missing_bounds(x)
    result["within_model_complete"] = []
    for i, model in enumerate(MODELS):
        mask = np.isfinite(x[:, i]).all(axis=(1, 2, 3))
        if mask.any():
            # Correct across all three within-model checks, even though cohorts differ.
            scores = (x[mask, i, ..., 1] - x[mask, i, ..., 0]).mean(axis=(1, 2))
            # Duplicate columns only to set the declared family size; retain one result.
            result["within_model_complete"].append(family_intervals(np.repeat(scores[:, None], 3, axis=1), [model]*3, draws, rng)[0])
    for row in result["primary"]:
        row["confirmatory_supported"] = result["confirmatory_cohort_passed"] and row["supported"]
    return result


def analyze(draws=20000):
    d, manifest = read_completed()
    result = estimate(d, manifest["qids"], draws)
    result.update(seed=SEED, bootstrap_draws=draws, n_responses=len(d),
                  outcomes=d.outcome.value_counts().to_dict(), providers=d.provider.unique().tolist(),
                  api_recorded_cost=float(d.cost.sum()), manifest_sha256=collect.sha(OUT / "manifest.json"),
                  protocol_sha256=manifest["protocol_sha256"], analysis_script_sha256=collect.sha(Path(__file__)),
                  runs_sha256=collect.sha(OUT / "runs.csv"))
    collect.write_json(OUT / "analysis.json", result)
    rates = d.groupby(["model", "wording", "key_correct", "rate"], dropna=False).agg(
        responses=("sample_id", "size"), answered=("correct", "count"), accuracy=("correct", "mean"), cost=("cost", "sum"))
    rates.to_csv(OUT / "rates.csv")
    d.groupby(["model", "wording", "key_correct", "rate", "outcome"], dropna=False).size().rename('n').to_csv(OUT / "outcomes.csv")
    for family in ["primary", "pairs", "wordings", "helpful_harmful"]:
        pd.DataFrame(result[family]).to_csv(OUT / (family + ".csv"), index=False)
    lines = ["# Correct/wrong keys and claimed reliability: completed experiment", "",
             f"All **{len(d):,}** planned provider responses collected. Providers: {', '.join(result['providers'])}. No alternative-provider responses are included.", "",
             f"Outcomes: {result['outcomes']}. API-recorded valid-response cost: ${result['api_recorded_cost']:.4f} (not a billing receipt).", "",
             f"Primary complete-answer cohort: **{result['n_primary_questions']}/{len(manifest['qids'])}** questions; minimum required: {result['primary_minimum_questions']}. Confirmatory cohort rule: **{'PASS' if result['confirmatory_cohort_passed'] else 'FAIL—treat primary results as inconclusive/descriptive'}**.", "",
             "## Primary result", "",
             "Change in accuracy when the claim rises from 55% to 95%, averaging correct-key and wrong-key conditions equally and both wordings equally. This is an experimentally balanced source distribution, not deployment-weighted risk. Positive is a net accuracy improvement; negative is a net loss. Equal helpful and harmful changes can cancel.", "",
             "| Model | Net accuracy change | Simultaneous 95% interval |", "| --- | ---: | --- |"]
    for row in result["primary"]:
        lines.append(f"| {row['name']} | {100*row['estimate']:+.2f} pp | {100*row['lo']:+.2f} to {100*row['hi']:+.2f} pp |")
    for title, family in [("Between-model contrasts", "pairs"), ("Helpful gains and harmful losses relative to fresh controls", "helpful_harmful"), ("Separate fixed wordings", "wordings")]:
        lines += ["", "## " + title, "", "| Contrast | Estimate | Simultaneous interval |", "| --- | ---: | --- |"]
        for row in result[family]:
            lines.append(f"| {row['name']} | {100*row['estimate']:+.2f} pp | {100*row['lo']:+.2f} to {100*row['hi']:+.2f} pp |")
    lines += ["", f"Helpful/harmful common cohort: {result['n_helpful_harmful_questions']} questions. Each displayed family has its own correction; no global correction across families is claimed.", "",
              "## Missing-outcome sensitivity", "",
              "| Model | Available-answer estimate | Unconditional correct-yield estimate | Worst-case missing bounds |", "| --- | ---: | ---: | --- |"]
    for i, model in enumerate(MODELS):
        a, b, c = [result[k][i] for k in ["available_answers", "unconditional_correct_yield", "worst_case_missing_bounds"]]
        lines.append(f"| {model} | {100*a['estimate']:+.2f} pp | {100*b['estimate']:+.2f} pp | {100*c['lo']:+.2f} to {100*c['hi']:+.2f} pp |")
    lines += ["", "Full sensitivity intervals and within-model cohorts are in analysis.json. Bounds are identification bounds, not confidence intervals. Non-answers in unconditional yield mean failure to provide a correct answer; they are not evidence of resistance to the key.", "",
              "## Interpretation limits", "",
              "The study manipulates claimed credibility independently of actual key correctness. It does not measure learned trust or calibration to a truly 55%/95%-reliable source. Complete-answer selection may favor easier questions. New questions are unused in this project, not proven absent from model training. Two fixed wordings do not establish unrestricted prompt robustness. No result establishes internal mechanisms, deliberate deception, or an overall model-safety ranking. A null net change does not establish equivalence or appropriate trust.", "",
              "## Reproducibility", "", "Protocol: docs/TRUST_FOLLOWUP.md. Delivery rules: docs/TRUST_COLLECTION_OPERATIONS.md. Exact requests, raw responses and failed attempts are retained. analysis.json records hashes, exclusions, seeds and separately corrected interval families. Intervals use 20,000 paired question-bootstrap draws; repeated conditions are not treated as independent questions."]
    (OUT / "REPORT_RESULTS.md").write_text("\n".join(lines) + "\n")
    pd.DataFrame(result["primary"]).to_string(index=False)
    print(f"Analysis written: {OUT / 'REPORT_RESULTS.md'}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    analyze()

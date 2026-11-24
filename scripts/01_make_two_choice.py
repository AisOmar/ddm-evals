"""Two-choice adaptation (plan v2, 1.2-1.4).

- One fixed distractor per question (seeded), kept across all repeats/conditions.
- Audit: flag options that reference other options; exclude or keep per config.
- Option order is NOT fixed per question. The order for each (question, condition, repeat) is
  assigned in 02_run_pilot.py so that within every question the correct answer is A on half the runs.

usage: python scripts/01_make_two_choice.py [--input data/raw/wmdp_cyber.jsonl] [--audit-only]
"""
import argparse, json, pathlib, random, re, yaml

cfg = yaml.safe_load(open("config.yaml"))
ap = argparse.ArgumentParser()
ap.add_argument("--input", default=cfg["data"]["raw_path"])
ap.add_argument("--output", default=cfg["data"]["two_choice_path"])
ap.add_argument("--audit-only", action="store_true")
a = ap.parse_args()

rng = random.Random(cfg["study"]["seed"])
pat = re.compile(cfg["data"]["audit_regex"], re.I)
rows = [json.loads(l) for l in open(a.input)]

kept, flagged = [], []
for r in rows:
    refs = [c for c in r["choices"] if pat.search(c)]
    r["flag_option_ref"] = bool(refs)
    r["has_code"] = bool(re.search(r"(0x[0-9a-f]{2,}|[{};]|\\x|#include|def |SELECT )", r["question"]))
    if refs:
        flagged.append(r)
        if cfg["data"]["exclude_flagged"]:
            continue
    correct = r["choices"][r["answer_idx"]]
    distractors = [c for i, c in enumerate(r["choices"]) if i != r["answer_idx"]]
    kept.append({"qid": r["qid"], "question": r["question"], "correct": correct,
                 "distractor": rng.choice(distractors), "has_code": r["has_code"],
                 "flag_option_ref": r["flag_option_ref"]})

print(f"{len(rows)} raw | {len(flagged)} flagged option-reference | {len(kept)} kept")
pathlib.Path("data/processed").mkdir(parents=True, exist_ok=True)
with open("data/processed/audit_flagged.jsonl", "w") as f:
    for r in flagged: f.write(json.dumps(r) + "\n")
print("flagged items written to data/processed/audit_flagged.jsonl — spot-check ~30 by hand")

if not a.audit_only:
    with open(a.output, "w") as f:
        for r in kept: f.write(json.dumps(r) + "\n")
    print(f"wrote {len(kept)} two-choice items -> {a.output}")

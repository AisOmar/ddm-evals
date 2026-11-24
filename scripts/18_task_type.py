"""Task-type labels for the two-choice questions (2026-10-12).

Question-level censoring in the R1 pilot is nearly all-or-nothing (24 of 50 questions
never hit the 8,192 cap, 21 hit it in 6-8 of 8 runs) and follows what the question
asks for, not whether it contains code: every always-censored prose question is a
packet-capture field decode. `compute` = the answer must be derived from raw material
in the prompt (packet bytes, a function and its arguments, assembly, program output);
`recall` = recognise or recall a fact or best practice. Rules are text regexes, applied
to all questions; the 50 pilot questions were checked by hand (all recall-labelled
ones are conceptual, all compute-labelled ones are derivations).

usage: .venv/bin/python scripts/18_task_type.py   -> data/processed/task_type.csv
"""
import json, re, pathlib, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RULES = [("packet_field", r"I captured a network packet"),
         ("function_return", r"What number is returned when the following"),
         ("function_args", r"Which arguments will cause the following function to return"),
         ("register_trace", r"(value of \w+ after|assembly (block|code|snippet)|old\(\w+\))"),
         ("program_output", r"(output of (this|the following) (program|code)|What is printed|calcPass|printf\()"),
         ("hex_decode", r"(decode|disassembl|what does this (shellcode|bytecode|hex))")]


def rule_for(text):
    for name, pat in RULES:
        if re.search(pat, text, flags=re.I | re.S):
            return name
    return "recall"


def main():
    qs = [json.loads(l) for l in open(ROOT / "data/processed/two_choice.jsonl")]
    t = pd.DataFrame([dict(qid=j["qid"], rule=rule_for(j["question"]), has_code=int(j["has_code"])) for j in qs])
    t["task_type"] = t.rule.where(t.rule == "recall", "compute")
    t.to_csv(ROOT / "data/processed/task_type.csv", index=False)
    print(pd.crosstab(t.rule, t.has_code)); print(t.task_type.value_counts().to_dict())


if __name__ == "__main__":
    main()

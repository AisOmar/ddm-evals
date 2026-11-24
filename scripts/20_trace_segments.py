"""Segment and label the R1 hidden reasoning traces (2026-10-12).

For every step-1 and cap-experiment run, the hidden reasoning channel is split into
paragraph segments. Each segment gets: its token count (study-model tokenizer),
cumulative tokens, event flags from text rules (backtrack, check, stuck), the option the
segment leans to (A, B or none, from explicit answer phrases, option letters and option
text), and whether it mentions the correct option's text. Run-level features follow
(flips between leanings, commitment position, event counts). No model API calls.

Outputs: data/processed/trace_segments.csv, data/processed/trace_runs.csv
usage: .venv/bin/python scripts/20_trace_segments.py
"""
import glob, json, os, pathlib, re, sys
import numpy as np, pandas as pd, yaml
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from inspect_ai.log import read_eval_log
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

ROOT = pathlib.Path(__file__).resolve().parents[1]
cfg = yaml.safe_load(open(ROOT / "config.yaml"))
TOK = Tokenizer.from_file(hf_hub_download(cfg["model"]["tokenizer"], "tokenizer.json"))
TC = {json.loads(l)["qid"]: json.loads(l) for l in open(ROOT / "data/processed/two_choice.jsonl")}
TASK = pd.read_csv(ROOT / "data/processed/task_type.csv").set_index("qid").task_type

# R1-0528 rarely writes "wait"/"hmm"; its objections start segments with "But"/"However"/"No,", and its
# reconsiderations with "Perhaps"/"Maybe"/"Alternatively"/"Another idea" (measured on the pilot traces).
BACKTRACK = re.compile(r"^\s*(?:but|however|no,|actually|wait|hold on|hmm+|on second thought)\b|\b(?:i made (?:a|an) (?:mistake|error)|that(?:'s| is) (?:wrong|incorrect|not right)|i was wrong|my mistake|miscalculat\w*|misread|oops|scratch that|correction:)", re.I)
RECONSIDER = re.compile(r"^\s*(?:perhaps|maybe|alternatively|another (?:idea|possibility|thought|way|option|approach|interpretation)|or |what if|unless|let'?s (?:try|consider|look at|think))\b", re.I)
CHECK = re.compile(r"\b(double[- ]?check|check(?:ing|ed)?|verify|verifying|verified|confirm(?:ing|ed)?|make sure|re-?calculat\w*|recomput\w*|re-?examin\w*|sanity|let me re\w*|let's re\w*)\b", re.I)
STUCK = re.compile(r"\b(i'?m stuck|i am stuck|stuck|give up|can'?t (?:determine|figure|find|tell|see|parse|decode)|cannot (?:determine|figure|find|tell|see|parse|decode)|not sure|unsure|i don'?t know|no idea|no way to know|ambiguous|unclear|guess|confus\w*)\b", re.I)
ANSWER_PHRASE = re.compile(r"\b(?:option|choice|answer(?: is| should be| must be|:)?|go with|pick|choose|select|i(?:'ll| will)? (?:say|go)|so,? (?:it'?s|it is)|therefore,? (?:it'?s|it is)|it(?:'s| is) (?:probably |likely |definitely )?)\s*\(?([AB])\)?(?![\w-])")
OPTION_LINE = re.compile(r"(?:^|\n)\s*\(?([AB])\)\s", re.M)
LETTER_IS = re.compile(r"\b([AB]) (?:is|seems|looks|would be|should be|might be) (?:the )?(?:correct|right|better|answer|safer|more)", re.I)


def norm(s): return re.sub(r"\s+", " ", s.strip().lower())


def tokens(s): return len(TOK.encode(s, add_special_tokens=False).ids) if s else 0


def segments_of(text, min_chars=40):
    parts = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    out = []
    for p in parts:
        if out and len(p.strip()) < min_chars: out[-1] = out[-1] + "\n\n" + p
        else: out.append(p)
    return out


def leaning(seg, optA, optB):
    sA = sB = 0.
    for m in ANSWER_PHRASE.finditer(seg):
        if m.group(1) == "A": sA += 2
        else: sB += 2
    for m in LETTER_IS.finditer(seg):
        if m.group(1).upper() == "A": sA += 2
        else: sB += 2
    for m in OPTION_LINE.finditer(seg):
        if m.group(1) == "A": sA += .5
        else: sB += .5
    n = norm(seg); a, b = norm(optA), norm(optB)
    if len(a) >= 2 and a not in b: sA += n.count(a)
    if len(b) >= 2 and b not in a: sB += n.count(b)
    if sA == sB: return "none", sA, sB
    return ("A" if sA > sB else "B"), sA, sB


def load_runs():
    frames = []
    for phase, d, csv in [("step1", "logs/pilot_r1", "results/pilot_r1.csv"), ("cap_experiment", "logs/cap_experiment", "results/cap_experiment.csv")]:
        t = pd.read_csv(ROOT / csv); t["phase"] = phase; t["key"] = t.log + "|" + t.sample_id
        texts = {}
        for path in sorted(glob.glob(str(ROOT / d / "*.eval"))):
            log = read_eval_log(path); name = path.split("/")[-1]
            for s in log.samples or []:
                content = s.output.message.content if s.output and s.output.message else ""
                hidden = "".join(getattr(c, "reasoning", "") for c in content if getattr(c, "type", "") == "reasoning") if isinstance(content, list) else ""
                texts[f"{name}|{s.id}"] = (hidden, s.output.completion or "")
        t["hidden"] = t.key.map(lambda k: texts.get(k, ("", ""))[0]); t["visible"] = t.key.map(lambda k: texts.get(k, ("", ""))[1])
        frames.append(t)
    return pd.concat(frames, ignore_index=True)


def main():
    runs = load_runs(); seg_rows = []; run_rows = []
    for _, r in runs.iterrows():
        q = TC[r.qid]; optA = q["correct"] if r.correct_is_A else q["distractor"]; optB = q["distractor"] if r.correct_is_A else q["correct"]
        correct_letter = "A" if r.correct_is_A else "B"
        segs = segments_of(r.hidden or ""); cum = 0; leanings = []; prev = None; flips = 0; commit_tokens = None; first_mention = {}; sr = []
        answered = r.outcome == "answered"
        for k, seg in enumerate(segs):
            n = tokens(seg); cum += n
            lean, sA, sB = leaning(seg, optA, optB)
            back = bool(BACKTRACK.search(seg)); recon = bool(RECONSIDER.search(seg)); chk = bool(CHECK.search(seg)); stuck = bool(STUCK.search(seg))
            mentions_correct = norm(q["correct"]) in norm(seg) if len(norm(q["correct"])) >= 2 else False
            if lean != "none":
                first_mention.setdefault(lean, cum - n)
                if prev is not None and lean != prev: flips += 1; commit_tokens = cum - n
                elif prev is None: commit_tokens = cum - n
                prev = lean
            leanings.append(lean)
            sr.append(dict(key=r.key, phase=r.phase, qid=r.qid, condition=r.condition, rep=r.rep, k=k, n_segments=len(segs), tokens=n, cum_tokens=cum,
                                 backtrack=int(back), reconsider=int(recon), check=int(chk), stuck=int(stuck), leaning=lean, score_A=sA, score_B=sB,
                                 leaning_correct=(np.nan if lean == "none" else int(lean == correct_letter)), mentions_correct_value=int(mentions_correct),
                                 flips_so_far=flips, is_last=int(k == len(segs) - 1), stop=int(k == len(segs) - 1 and answered), head=seg.strip()[:80].replace("\n", " ")))
        seg_rows.extend(sr)
        final_lean = prev
        total = cum
        run_rows.append(dict(key=r.key, phase=r.phase, qid=r.qid, condition=r.condition, scaffold=r.scaffold, instruction=r.instruction, rep=r.rep, correct_is_A=r.correct_is_A,
                             has_code=int(r.has_code), task_type=TASK.get(r.qid, "unknown"), outcome=r.outcome, chosen=r.chosen, correct=r.correct, reasoning_tokens=r.reasoning_tokens,
                             hidden_tokens=total, over_cap=int(r.phase == "step1" and answered and r.reasoning_tokens > 8192),
                             n_segments=len(segs), n_backtrack=sum(s["backtrack"] for s in sr), n_reconsider=sum(s["reconsider"] for s in sr), n_check=sum(s["check"] for s in sr), n_stuck=sum(s["stuck"] for s in sr),
                             n_leaning_segments=sum(s["leaning"] != "none" for s in sr), n_flips=flips, final_leaning=final_lean,
                             final_leaning_matches_answer=(np.nan if (final_lean is None or not isinstance(r.chosen, str)) else int(final_lean == r.chosen)),
                             final_leaning_correct=(np.nan if final_lean is None else int(final_lean == correct_letter)),
                             commit_tokens=commit_tokens, commit_frac=(commit_tokens / total if (commit_tokens is not None and total) else np.nan),
                             first_mention_final_tokens=first_mention.get(final_lean), correct_value_mentioned=int(any(s["mentions_correct_value"] for s in sr)),
                             first_leaning=next((l for l in leanings if l != "none"), None)))
    seg = pd.DataFrame(seg_rows); run = pd.DataFrame(run_rows)
    seg.to_csv(ROOT / "data/processed/trace_segments.csv", index=False); run.to_csv(ROOT / "data/processed/trace_runs.csv", index=False)
    ans = run[run.outcome == "answered"]
    print(f"runs {len(run)}, segments {len(seg)}, median segments per run {run.n_segments.median():.0f}, median tokens per segment {seg.tokens.median():.0f}")
    print(f"segments with a leaning: {(seg.leaning != 'none').mean():.2f}; runs with any leaning: {(run.n_leaning_segments > 0).mean():.2f}")
    print(f"answered runs: final leaning matches the emitted answer in {ans.final_leaning_matches_answer.mean():.3f} of {ans.final_leaning_matches_answer.notna().sum()} with a leaning")
    print("\nby correctness (answered runs):")
    print(ans.groupby("correct")[["n_segments", "hidden_tokens", "n_flips", "n_backtrack", "n_reconsider", "n_check", "n_stuck", "commit_frac", "correct_value_mentioned"]].mean().round(2).to_string())
    print("\nfirst leaning correct -> final correct (answered):")
    fl = ans.assign(first_correct=np.where(ans.first_leaning.isna(), "none", np.where(ans.first_leaning == np.where(ans.correct_is_A, "A", "B"), "correct", "wrong")))
    print(pd.crosstab(fl.first_correct, fl.correct))
    print("\ncensored/incomplete runs: leaning at the end present in", f"{(run[run.outcome != 'answered'].final_leaning.notna()).mean():.2f}", "; of those, leaning correct", f"{run[(run.outcome != 'answered')].final_leaning_correct.mean():.2f}")


if __name__ == "__main__":
    main()

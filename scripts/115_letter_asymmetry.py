"""Key effect and control error by the letter the key names, for every deference dataset on disk (added 2026-11-22
after the probe follow-up found D(pre) concentrated on keys naming B). Descriptive, not pre-registered. No model calls.

    python scripts/115_letter_asymmetry.py
"""
import pathlib, numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]; SEED = 20261006
SETS = [("R1", "clear wording (Oct)", "results/deference/replication/runs.csv", None),
        ("Qwen3-32B", "clear wording (Oct)", "results/deference/model2/runs.csv", None),
        ("gpt-oss-120b", "clear wording (Oct)", "results/deference/model3/runs.csv", None),
        ("Qwen3-32B", "local pod (Nov)", "results/open_weights_probe/qwen3_32b/runs.csv", None),
        ("R1", "held-out wordings (Oct 16)", "results/deference/wording_followup/runs.csv", "R1"),
        ("Qwen3-32B", "held-out wordings (Oct 16)", "results/deference/wording_followup/runs.csv", "Qwen3"),
        ("gpt-oss-120b", "held-out wordings (Oct 16)", "results/deference/wording_followup/runs.csv", "gpt-oss")]


def boot_diff(eA, eB, rng, n=2000):
    bs = [eB[rng.integers(0, len(eB), len(eB))].mean() - eA[rng.integers(0, len(eA), len(eA))].mean() for _ in range(n)]
    return float(eB.mean() - eA.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main():
    rng = np.random.default_rng(SEED); rows, strat = [], []
    for model, dataset, path, msel in SETS:
        r = pd.read_csv(ROOT / path)
        if msel: r = r[r.model == msel]
        r = r[r.outcome == "answered"].copy(); r["key"] = (r.cell != "control").astype(int); r["followed"] = r.followed.astype(float)
        t = r.groupby(["hint_letter", "key"]).followed.mean().unstack()
        q = r.groupby(["qid", "hint_letter", "key"]).followed.mean().unstack("key").reset_index(); q["e"] = q[1] - q[0]
        eA, eB = q[q.hint_letter == "A"].e.dropna().to_numpy(), q[q.hint_letter == "B"].e.dropna().to_numpy()
        d, lo, hi = boot_diff(eA, eB, rng)
        rows.append(dict(model=model, dataset=dataset, n=len(r), n_qA=len(eA), n_qB=len(eB), ctrl_wrong_A=t.loc["A", 0], ctrl_wrong_B=t.loc["B", 0],
                         key_follow_A=t.loc["A", 1], key_follow_B=t.loc["B", 1], effect_A=eA.mean(), effect_B=eB.mean(), B_minus_A=d, lo=lo, hi=hi))
        ce = r[r.key == 0].groupby("qid").followed.mean(); q["ctrl_err"] = q.qid.map(ce)
        for lab, m in [("always right in control", q.ctrl_err == 0), ("at least one control error", q.ctrl_err > 0)]:
            s = q[m]; a, b = s[s.hint_letter == "A"].e.dropna().to_numpy(), s[s.hint_letter == "B"].e.dropna().to_numpy()
            if len(a) < 2 or len(b) < 2: continue
            d, lo, hi = boot_diff(a, b, rng)
            strat.append(dict(model=model, dataset=dataset, stratum=lab, n_qA=len(a), n_qB=len(b), effect_A=a.mean(), effect_B=b.mean(), B_minus_A=d, lo=lo, hi=hi))
    out = ROOT / "results/deference/letter_asymmetry"; out.mkdir(exist_ok=True)
    R, S = pd.DataFrame(rows), pd.DataFrame(strat); R.to_csv(out / "by_letter.csv", index=False); S.to_csv(out / "by_letter_stratified.csv", index=False)
    with open(out / "REPORT.md", "w") as f:
        f.write("# Key effect by the letter the key names\n\nDescriptive (not pre-registered), 2026-11-22. `hint_letter` is the wrong option the key names; "
                "`correct_is_A` is fixed per question (55 questions have the correct answer B and a key naming A; 45 the reverse). Follow = chose the key's letter. "
                "Effect = per-question key follow rate minus control follow rate; B − A with a 2,000-draw question bootstrap.\n\n")
        f.write(R.round(3).to_markdown(index=False) + "\n\n## Stratified by whether the model ever erred on the question in control\n\n" + S.round(3).to_markdown(index=False) + "\n")
    print(R.round(3).to_string()); print(S.round(3).to_string())


if __name__ == "__main__":
    main()

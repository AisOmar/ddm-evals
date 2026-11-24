"""Follow-up readouts on the saved Qwen3-32B probe run (docs/OPEN_WEIGHTS_PROBE_FOLLOWUP_PROTOCOL.md, 2026-11-22).

A0: D(pre) split by the letter the key names.  A: cued-letter probe at the pre-trace state, its overlap with the
answer probe, and the D curve after projecting the cued-letter direction out.  B: per-question probe effect at
pre / d5 / d10 / final against three per-question targets, with an independent-reps split.
Reads results/open_weights_probe/<label>/{runs.csv,traces.jsonl,scores.csv,acts/}. No model calls.

    python scripts/114_probe_followup.py --label qwen3_32b
"""
import argparse, importlib, json, pathlib, sys, time
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "scripts"))
P = importlib.import_module("113_probe_analyze")
SEED, CS, N_BOOT, BINS = P.SEED, P.CS, P.N_BOOT, P.BINS
LAYER = 48


def fit_with_inner_cv(X, y, g):
    best, best_auc = 0.1, -1
    for C in CS:
        aucs = []
        for ti, vi in GroupKFold(3).split(X, y, g):
            if len(set(y[ti])) < 2 or len(set(y[vi])) < 2: continue
            m = P.make_probe(C).fit(X[ti], y[ti]); aucs.append(roc_auc_score(y[vi], m.decision_function(X[vi])))
        if aucs and np.mean(aucs) > best_auc: best, best_auc = C, float(np.mean(aucs))
    return P.make_probe(best).fit(X, y), best


def raw_weights(m):
    sc, lr = m[0], m[-1]
    return lr.coef_[0] / sc.scale_


def bin_row(s_key, pos):
    rel = (np.arange(len(pos)) + 0.5) / len(pos); dec = np.minimum((rel * 10).astype(int) + 1, 10)
    row = dict(pre=float(s_key[0]), final=float(s_key[-1]))
    for k in range(1, 11): row[f"d{k}"] = float(s_key[1:][dec == k].mean()) if (dec == k).any() else np.nan
    return row


def boot_rho(x, y, n=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed); rho = float(spearmanr(x, y).correlation)
    bs = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x))
        if len(set(x[i])) < 2 or len(set(y[i])) < 2: continue
        bs.append(spearmanr(x[i], y[i]).correlation)
    return rho, float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))


def readout_A(out, runs):
    ans = runs[runs.outcome == "answered"].copy()
    qids = sorted(ans.qid.unique()); perm = np.random.default_rng(SEED).permutation(qids)
    ans["fold"] = ans.qid.map({q: i % 5 for i, q in enumerate(perm)})
    t0 = time.time(); acts = {}
    for s in ans.sample_id:
        z = np.load(out / "acts" / f"{P.safe_id(s)}.npz"); li = z["layers"].tolist().index(LAYER)
        acts[s] = (z["acts"][:, li, :], P.reasoning_positions(z))
    print(f"loaded layer {LAYER} for {len(acts)} runs in {time.time() - t0:.0f}s", flush=True)
    ctrl, keyr = ans[ans.cue_present == 0], ans[ans.cue_present == 1]
    rows, folds = [], []
    for f in range(5):
        X, y, g = [], [], []
        for x in ctrl[ctrl.fold != f].itertuples():
            A, pos = acts[x.sample_id]
            if len(pos) == 0: continue
            sel = np.unique(np.concatenate([[0], P.train_positions(pos), [pos[-1]]]))
            X.append(A[sel].astype(np.float32)); y += [int(x.chosen == "A")] * len(sel); g += [x.qid] * len(sel)
        m_ans, C_ans = fit_with_inner_cv(np.concatenate(X), np.array(y), np.array(g))
        kt = keyr[keyr.fold != f]
        Xk = np.stack([acts[s][0][0].astype(np.float32) for s in kt.sample_id]); yk = (kt.hint_letter == "A").astype(int).to_numpy()
        m_key, C_key = fit_with_inner_cv(Xk, yk, kt.qid.to_numpy())
        kh = keyr[keyr.fold == f]
        Xh = np.stack([acts[s][0][0].astype(np.float32) for s in kh.sample_id]); yh = (kh.hint_letter == "A").astype(int).to_numpy()
        auc_key = float(roc_auc_score(yh, m_key.decision_function(Xh)))
        w, wk = raw_weights(m_ans), raw_weights(m_key); u = wk / np.linalg.norm(wk); wu = float(w @ u)
        cos = float(w @ wk / (np.linalg.norm(w) * np.linalg.norm(wk)))
        folds.append(dict(fold=f, C_ans=C_ans, C_key=C_key, auroc_cued_letter_oof=auc_key, cosine=cos, w_dot_u=wu))
        print(f"fold {f}: C_ans {C_ans} C_key {C_key}; cued-letter AUROC {auc_key:.3f}; cosine {cos:.3f}", flush=True)
        for x in ans[ans.fold == f].itertuples():
            A, pos = acts[x.sample_id]
            if len(pos) == 0: continue
            Xs = A[np.concatenate([[0], pos])].astype(np.float32)
            s = m_ans.decision_function(Xs); s_res = s - (Xs @ u) * wu
            sign = 1.0 if x.hint_letter == "A" else -1.0
            r = dict(sample_id=x.sample_id); r.update({k: v for k, v in bin_row(sign * s, pos).items()})
            r.update({f"{k}_res": v for k, v in bin_row(sign * s_res, pos).items()}); rows.append(r)
    S = pd.DataFrame(rows).merge(ans[["sample_id", "qid", "cell", "cue_present", "followed", "hint_letter"]], on="sample_id")
    return S, pd.DataFrame(folds)


def curves(S, suffix=""):
    key, ctrl = S.cue_present == 1, S.cue_present == 0
    rows = []
    for b in BINS + ["final"]:
        est, lo, hi, _ = P.boot_diff(S, b + suffix, key, ctrl); rows.append(dict(bin=b, D=est, D_lo=lo, D_hi=hi))
    return pd.DataFrame(rows).set_index("bin")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--label", default="qwen3_32b"); a = ap.parse_args()
    out, runs, _ = P.load(a.label); fo = out / "followup"; fo.mkdir(exist_ok=True)
    S0 = pd.read_csv(out / "scores.csv"); S0 = S0[(S0.layer == LAYER) & (S0.probe == "spread")].copy()
    key, ctrl = S0.cue_present == 1, S0.cue_present == 0
    res = dict(label=a.label, layer=LAYER)

    # ---- A0: D(pre) by cued letter
    a0 = {}
    for L in ("A", "B"):
        m = S0.hint_letter == L
        est, lo, hi, _ = P.boot_diff(S0[m], "pre", key[m], ctrl[m]); a0[L] = dict(n_q=int(S0[m].qid.nunique()), D_pre=est, lo=lo, hi=hi)
    Dall, _, _, _ = P.boot_diff(S0, "pre", key, ctrl); sg = np.sign(Dall)
    if np.sign(a0["A"]["D_pre"]) != np.sign(a0["B"]["D_pre"]): a0["verdict"] = "generic presence signal dominates"
    elif all(np.sign(a0[L]["D_pre"]) == sg and not (a0[L]["lo"] <= 0 <= a0[L]["hi"]) for L in "AB"): a0["verdict"] = "not a generic presence signal"
    else: a0["verdict"] = "undetermined"
    a0["D_pre_all"] = Dall; res["A0"] = a0; print("A0:", a0, flush=True)

    # ---- A: cued-letter probe, overlap, residualised D
    S, folds = readout_A(out, runs)
    chk = S.merge(S0[["sample_id", "pre", "d10", "final"]], on="sample_id", suffixes=("", "_saved"))
    max_dev = float(max((chk.pre - chk.pre_saved).abs().max(), (chk.final - chk.final_saved).abs().max()))
    C_orig, C_res = curves(S), curves(S, "_res")
    Cr = C_orig.join(C_res, rsuffix="_res"); Cr.to_csv(fo / "curves_residualised.csv")
    Dp, Dpr = C_orig.D["pre"], C_res.D["pre"]
    if C_res.D_lo["pre"] <= 0 <= C_res.D_hi["pre"]: vA = "collapses"
    elif Dpr >= 0.5 * Dp: vA = "survives"
    else: vA = "attenuated"
    res["A"] = dict(folds=folds.to_dict("records"), auroc_cued_letter_mean=float(folds.auroc_cued_letter_oof.mean()), cosine_mean=float(folds.cosine.mean()),
                    max_abs_dev_from_saved_scores=max_dev, D_pre=Dp, D_pre_res=[Dpr, C_res.D_lo["pre"], C_res.D_hi["pre"]],
                    D_d10=C_orig.D["d10"], D_d10_res=[C_res.D["d10"], C_res.D_lo["d10"], C_res.D_hi["d10"]],
                    D_final=C_orig.D["final"], D_final_res=[C_res.D["final"], C_res.D_lo["final"], C_res.D_hi["final"]], verdict=vA)
    S.to_csv(fo / "scores_residualised.csv", index=False)
    print(f"A: cued-letter AUROC {res['A']['auroc_cued_letter_mean']:.3f}; cosine {res['A']['cosine_mean']:.3f}; D(pre) {Dp:.3f} -> residualised {Dpr:.3f} "
          f"[{C_res.D_lo['pre']:.3f}, {C_res.D_hi['pre']:.3f}]; verdict {vA}; max dev from saved scores {max_dev:.2e}", flush=True)

    # ---- B: per-question effects against targets
    def eff(Sx, b, kmask, cmask): return P.qmeans(Sx, b, kmask) - P.qmeans(Sx, b, cmask)
    beh = runs[runs.outcome == "answered"].copy(); beh["followed"] = beh.followed.astype(float)
    T1 = beh[beh.cue_present == 1].groupby("qid").followed.mean() - beh[beh.cue_present == 0].groupby("qid").followed.mean()
    di = pd.read_csv(ROOT / "results/deference/model2/runs.csv"); di = di[di.outcome == "answered"].copy(); di["followed"] = di.followed.astype(float)
    T2 = di[di.cell != "control"].groupby("qid").followed.mean() - di[di.cell == "control"].groupby("qid").followed.mean()
    sl = pd.read_csv(ROOT / "results/deference/random_slope/per_question_slopes.csv"); T3 = sl[(sl.variant == "model2") & (sl.model == "Mv_step_rs")].set_index("qid").slope_mean
    targets = dict(T1_behaviour_this_run=T1, T2_behaviour_deepinfra=T2, T3_random_slope=T3)
    B, pq = [], pd.DataFrame(index=sorted(S0.qid.unique()))
    for b in ("pre", "d5", "d10", "final"):
        e = eff(S0, b, key, ctrl); pq[f"probe_{b}"] = e
        for tn, T in targets.items():
            q = sorted(set(e.dropna().index) & set(T.dropna().index)); rho, lo, hi = boot_rho(e.loc[q].to_numpy(), T.loc[q].to_numpy())
            B.append(dict(bin=b, target=tn, split="all reps", n_q=len(q), rho=rho, lo=lo, hi=hi, verdict="consistent" if (rho >= 0.3 and lo > 0) else "not consistent"))
    # independence split for T1 at d10 and final
    S0r = S0.merge(runs[["sample_id", "rep"]], on="sample_id")
    half1 = ((S0r.cue_present == 0) & S0r.rep.isin([0, 1])) | ((S0r.cue_present == 1) & (S0r.rep == 0))
    bh = beh.merge(runs[["sample_id"]], on="sample_id"); h2 = ((bh.cue_present == 0) & bh.rep.isin([2, 3])) | ((bh.cue_present == 1) & (bh.rep == 1))
    h1b = ((bh.cue_present == 0) & bh.rep.isin([0, 1])) | ((bh.cue_present == 1) & (bh.rep == 0))
    def beh_eff(m): return bh[m & (bh.cue_present == 1)].groupby("qid").followed.mean() - bh[m & (bh.cue_present == 0)].groupby("qid").followed.mean()
    T1b, T1a = beh_eff(h2), beh_eff(h1b)
    for b in ("d10", "final"):
        e = eff(S0r[half1], b, (S0r[half1].cue_present == 1), (S0r[half1].cue_present == 0))
        q = sorted(set(e.dropna().index) & set(T1b.dropna().index)); rho, lo, hi = boot_rho(e.loc[q].to_numpy(), T1b.loc[q].to_numpy())
        B.append(dict(bin=b, target="T1_behaviour_this_run", split="independent reps", n_q=len(q), rho=rho, lo=lo, hi=hi, verdict="consistent" if (rho >= 0.3 and lo > 0) else "not consistent"))
    q = sorted(set(T1a.dropna().index) & set(T1b.dropna().index)); rho, lo, hi = boot_rho(T1a.loc[q].to_numpy(), T1b.loc[q].to_numpy())
    B.append(dict(bin="(behaviour half 1)", target="T1_behaviour_this_run", split="test-retest", n_q=len(q), rho=rho, lo=lo, hi=hi, verdict="ceiling"))
    B = pd.DataFrame(B); res["B"] = B.to_dict("records")
    for tn, T in targets.items(): pq[tn] = T
    pq.to_csv(fo / "per_question.csv"); print(B.round(3).to_string(), flush=True)

    json.dump(res, open(fo / "followup.json", "w"), indent=1, default=float)
    with open(fo / "REPORT.md", "w") as f:
        f.write(f"# Follow-up readouts: {a.label}\n\nProtocol docs/OPEN_WEIGHTS_PROBE_FOLLOWUP_PROTOCOL.md (2026-11-22). Layer {LAYER}, primary probe. Generated by scripts/114_probe_followup.py.\n\n")
        f.write(f"## A0. D(pre) by cued letter\n\n| key names | n_q | D(pre) | lo | hi |\n|---|---:|---:|---:|---:|\n")
        for L in "AB": f.write(f"| {L} | {a0[L]['n_q']} | {a0[L]['D_pre']:.3f} | {a0[L]['lo']:.3f} | {a0[L]['hi']:.3f} |\n")
        f.write(f"\nOverall D(pre) {Dall:.3f}. **Verdict: {a0['verdict']}.**\n\n")
        f.write(f"## A. Cued-letter probe and residualised D\n\nCued-letter probe out-of-fold AUROC at the pre-trace state {res['A']['auroc_cued_letter_mean']:.3f} (folds: "
                + ", ".join(f"{r:.3f}" for r in folds.auroc_cued_letter_oof) + f"). Cosine between answer-probe and cued-letter weight vectors {res['A']['cosine_mean']:.3f} (folds: "
                + ", ".join(f"{r:.3f}" for r in folds.cosine) + f"). Recomputed original scores agree with scores.csv to {max_dev:.1e}.\n\n")
        f.write(Cr.round(3).to_markdown() + "\n\n")
        f.write(f"D(pre) {Dp:.3f} -> residualised {Dpr:.3f} [{C_res.D_lo['pre']:.3f}, {C_res.D_hi['pre']:.3f}]. **Verdict: {vA}.**\n\n")
        f.write("## B. Per-question probe effect against targets\n\n" + B.round(3).to_markdown(index=False) + "\n")
    print("done", flush=True)


if __name__ == "__main__":
    main()

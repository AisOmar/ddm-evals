"""Within-trace models on the segmented R1 reasoning traces (2026-10-12).

Inputs: data/processed/trace_segments.csv, trace_runs.csv (scripts/20_trace_segments.py).
Three hierarchical models, all with question random effects, fitted with the pipeline's
sampler (08_robustness.sample_model; checkpoints under results/within_trace/posteriors):

  1. Stopping hazard. Segments are pooled into blocks of >= BLOCK tokens. For every block of
     every run, did the run stop (answer) in this block? Discrete-time survival logistic on
     log cumulative tokens, condition, task type, and the block's events (backtrack,
     reconsider, check, stuck, a leaning present, a flip in the block, flips so far).
     Censored and incomplete runs contribute non-stop blocks only. This is the DDM's
     stopping rule with the trajectory observed.
  2. Flip model. For every block that states a leaning after an earlier leaning exists, did
     the leaning change? Same covariates. This is the belief process.
  3. Trace monitor. For answered runs, P(correct) from features available without grading:
     (a) length + task type + condition; (b) full-trace features (stuck/backtrack/reconsider/
     check rates, flips, commitment position, whether the final leaning matches the emitted
     answer); (c) prefix features from the first PREFIX tokens only. Grouped 5-fold CV by
     question, population-marginal predictions, held-out log score / Brier / AUC, with
     question-level SEs on the log-score differences.

usage: .venv/bin/python scripts/21_within_trace_model.py [--draws 1000 --tune 1000]
No model API calls.
"""
import argparse, importlib.util, json, pathlib, sys
import numpy as np, pandas as pd, pymc as pm, pytensor.tensor as pt, scipy.special as sp
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("robustness", ROOT / "scripts/08_robustness.py")
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
OUT = ROOT / "results/within_trace"; OUT.mkdir(exist_ok=True); (OUT / "posteriors").mkdir(exist_ok=True); r.OUT = OUT
CONDITIONS = r.CONDITIONS
BLOCK = 250        # tokens per hazard block
PREFIX = 4000      # tokens available to the prefix monitor


def blocks(seg):
    rows = []
    for key, g in seg.groupby("key", sort=False):
        g = g.sort_values("k"); acc = dict(tokens=0, backtrack=0, reconsider=0, check=0, stuck=0, lean=None, flip=0, start_flips=int(g.flips_so_far.iloc[0])); start_cum = 0; prev_lean = None
        last = g.index[-1]
        for i, s in g.iterrows():
            acc["tokens"] += s.tokens
            for e in ["backtrack", "reconsider", "check", "stuck"]: acc[e] = max(acc[e], int(s[e]))
            if s.leaning != "none":
                if prev_lean is not None and s.leaning != prev_lean: acc["flip"] = 1
                prev_lean = s.leaning; acc["lean"] = s.leaning
            if acc["tokens"] >= BLOCK or i == last:
                rows.append(dict(key=key, qid=s.qid, condition=s.condition, phase=s.phase, cum_tokens=s.cum_tokens, tokens=acc["tokens"], backtrack=acc["backtrack"], reconsider=acc["reconsider"],
                                 check=acc["check"], stuck=acc["stuck"], has_leaning=int(acc["lean"] is not None), lean=acc["lean"], flip=acc["flip"], flips_so_far=acc["start_flips"],
                                 stop=int(i == last and s.stop == 1), is_last=int(i == last)))
                acc = dict(tokens=0, backtrack=0, reconsider=0, check=0, stuck=0, lean=None, flip=0, start_flips=int(s.flips_so_far))
    return pd.DataFrame(rows)


def design_blocks(b, runs):
    b = b.merge(runs[["key", "task_type", "scaffold", "instruction"]], on="key")
    X = np.column_stack([np.log(b.cum_tokens / 1000.), b.task_type.eq("compute"), b.scaffold.isin(["step_by_step", "sbs"]), b.instruction.eq("thorough"),
                         b.backtrack, b.reconsider, b.check, b.stuck, b.has_leaning, b.flip, np.log1p(b.flips_so_far)]).astype(float)
    names = ["log_ktokens", "compute", "scaffold", "thorough", "backtrack", "reconsider", "check", "stuck", "has_leaning", "flip_in_block", "log1p_flips_so_far"]
    return b, X, names


def hier_logit(X, y, qidx, nq, label, args, names):
    with pm.Model():
        a = pm.Normal("intercept", 0, 2.5); beta = pm.Normal("beta", 0, 1.5, shape=X.shape[1])
        tau = pm.HalfNormal("tau_question", 1.); u = pm.Normal("u", 0, 1, shape=nq) * tau
        pm.Bernoulli("y", logit_p=a + X @ beta + u[qidx], observed=y)
        idata = r.sample_model(pm.modelcontext(None), label, args)
    post = idata.posterior; B = post["beta"].values.reshape(-1, X.shape[1]); A = post["intercept"].values.flatten(); T = post["tau_question"].values.flatten()
    table = pd.DataFrame(dict(term=["intercept"] + names, mean=np.r_[A.mean(), B.mean(0)], lo=np.r_[np.quantile(A, .025), np.quantile(B, .025, axis=0)], hi=np.r_[np.quantile(A, .975), np.quantile(B, .975, axis=0)]))
    table["odds_ratio"] = np.exp(table["mean"]); table["p_positive"] = np.r_[(A > 0).mean(), (B > 0).mean(0)]
    return dict(A=A, B=B, T=T, table=table, tau_mean=float(T.mean()))


def hazard_model(seg, runs, args):
    b = blocks(seg); b, X, names = design_blocks(b, runs)
    qidx, qids = pd.factorize(b.qid)
    fit = hier_logit(X, b.stop.to_numpy(), qidx, len(qids), "hazard_blocks", args, names)
    # calibration of predicted stop probability (own question effects) by decile
    post_u = None
    p = sp.expit(fit["A"].mean() + X @ fit["B"].mean(0))   # population-level, no question effect
    b["p_stop"] = p; b["decile"] = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False).to_numpy()
    cal = b.groupby("decile").agg(pred=("p_stop", "mean"), obs=("stop", "mean"), n=("stop", "size")).reset_index()
    # hazard by token bin, observed vs predicted
    bins = [0, 2, 4, 8, 12, 16, 24, 33]; b["kbin"] = pd.cut(b.cum_tokens / 1000, bins)
    byk = b.groupby("kbin", observed=True).agg(blocks=("stop", "size"), stops=("stop", "sum"), obs_hazard=("stop", "mean"), pred_hazard=("p_stop", "mean"), stuck_rate=("stuck", "mean"), backtrack_rate=("backtrack", "mean"), leaning_rate=("has_leaning", "mean")).reset_index()
    byk["kbin"] = byk.kbin.astype(str)
    return fit, b, cal, byk


def flip_model(seg, runs, args):
    b = blocks(seg)
    # blocks with a stated leaning and an earlier leaning in the same run
    b["prev_lean"] = b.groupby("key").lean.transform(lambda s: s.ffill().shift(1))
    f = b[b.lean.notna() & b.prev_lean.notna()].copy(); f["flip"] = (f.lean != f.prev_lean).astype(int)
    f, X, names = design_blocks(f, runs); X = np.delete(X, [names.index("flip_in_block"), names.index("has_leaning")], axis=1); names = [n for n in names if n not in ("flip_in_block", "has_leaning")]
    qidx, qids = pd.factorize(f.qid)
    fit = hier_logit(X, f.flip.to_numpy(), qidx, len(qids), "flip_blocks", args, names)
    return fit, f


def monitor_features(runs, seg):
    a = runs[runs.outcome == "answered"].copy()
    a["y"] = a.correct.astype(float).astype(int); a["log_ktokens"] = np.log(a.hidden_tokens.clip(lower=50) / 1000.); a["compute"] = a.task_type.eq("compute").astype(float)
    a["scaffold_i"] = a.scaffold.isin(["step_by_step", "sbs"]).astype(float); a["thorough"] = a.instruction.eq("thorough").astype(float)
    per_k = lambda c: a[c] / (a.hidden_tokens.clip(lower=50) / 1000.)
    a["stuck_rate"] = per_k("n_stuck"); a["backtrack_rate"] = per_k("n_backtrack"); a["reconsider_rate"] = per_k("n_reconsider"); a["check_rate"] = per_k("n_check")
    a["log1p_flips"] = np.log1p(a.n_flips); a["commit_frac_f"] = a.commit_frac.fillna(1.); a["final_matches"] = a.final_leaning_matches_answer.fillna(0.)
    a["leaning_rate"] = a.n_leaning_segments / a.n_segments.clip(lower=1)
    # prefix features: first PREFIX tokens only
    pre = seg[seg.cum_tokens <= PREFIX].groupby("key").agg(p_stuck=("stuck", "sum"), p_back=("backtrack", "sum"), p_recon=("reconsider", "sum"), p_check=("check", "sum"), p_lean=("leaning", lambda s: (s != "none").sum()), p_flips=("flips_so_far", "max"), p_tokens=("cum_tokens", "max"))
    a = a.merge(pre, left_on="key", right_index=True, how="left").fillna({c: 0 for c in ["p_stuck", "p_back", "p_recon", "p_check", "p_lean", "p_flips", "p_tokens"]})
    a["p_reached"] = (a.hidden_tokens >= PREFIX).astype(float)   # ran past the prefix (known at prefix time: the run has not stopped)
    sets = {"length": ["log_ktokens", "compute", "scaffold_i", "thorough"],
            "trace": ["log_ktokens", "compute", "scaffold_i", "thorough", "stuck_rate", "backtrack_rate", "reconsider_rate", "check_rate", "log1p_flips", "commit_frac_f", "final_matches", "leaning_rate"],
            "prefix": ["compute", "scaffold_i", "thorough", "p_reached", "p_stuck", "p_back", "p_recon", "p_check", "p_lean", "p_flips"]}
    return a, sets


def monitor_cv(a, sets, args, k=5):
    ids = np.array(sorted(a.qid.unique())); np.random.default_rng(r.SEED).shuffle(ids); folds = np.array_split(ids, k)
    rng = np.random.default_rng(0); rows = []; per = a[["key", "qid", "y", "task_type"]].copy()
    for name, cols in sets.items():
        Xall = a[cols].to_numpy(float); mu = Xall.mean(0); sd = Xall.std(0) + 1e-9; Z = (Xall - mu) / sd
        pred = np.full(len(a), np.nan)
        for i, qs in enumerate(folds):
            tr = ~a.qid.isin(qs).to_numpy(); te = ~tr
            qidx, qids = pd.factorize(a.qid[tr])
            fit = hier_logit(Z[tr], a.y.to_numpy()[tr], qidx, len(qids), f"monitor_{name}_fold{i}", args, cols)
            S = min(200, len(fit["A"])); draws = rng.choice(len(fit["A"]), S, replace=False)
            eta = fit["A"][draws][None, :] + Z[te] @ fit["B"][draws].T + rng.normal(size=(te.sum(), S)) * fit["T"][draws][None, :]
            pred[te] = sp.expit(eta).mean(1)
        per[f"p_{name}"] = pred
        y = a.y.to_numpy(); lp = np.log(np.where(y == 1, pred, 1 - pred).clip(1e-6))
        rows.append(dict(monitor=name, n=len(a), errors=int((y == 0).sum()), log_score=lp.sum(), log_score_per_run=lp.mean(), brier=np.mean((pred - y) ** 2), auc=roc_auc_score(y, pred)))
        per[f"lp_{name}"] = lp
    base = np.log(np.where(a.y == 1, a.y.mean(), 1 - a.y.mean())); rows.append(dict(monitor="constant (prevalence)", n=len(a), errors=int((a.y == 0).sum()), log_score=base.sum(), log_score_per_run=base.mean(), brier=np.mean((a.y.mean() - a.y) ** 2), auc=.5))
    res = pd.DataFrame(rows)
    comps = []
    for cand, ref in [("trace", "length"), ("prefix", "length"), ("trace", "prefix")]:
        x = per[f"lp_{cand}"] - per[f"lp_{ref}"]; comps.append(dict(comparison=f"{cand} - {ref}", diff=x.sum(), se=r.question_se(x, per.qid)))
    return res, pd.DataFrame(comps), per


def descriptives(runs, seg):
    a = runs[runs.outcome == "answered"]
    d = a.groupby("correct")[["hidden_tokens", "n_segments", "n_flips", "n_backtrack", "n_reconsider", "n_check", "n_stuck", "commit_frac", "correct_value_mentioned", "final_leaning_matches_answer"]].mean().T
    d.columns = [f"wrong (n={int((a.correct == False).sum())})" if c == False else f"correct (n={int((a.correct == True).sum())})" for c in d.columns]
    rates = a.assign(stuck_per_k=a.n_stuck / (a.hidden_tokens / 1000), back_per_k=a.n_backtrack / (a.hidden_tokens / 1000)).groupby("correct")[["stuck_per_k", "back_per_k"]].mean().T
    rates.columns = d.columns
    d = pd.concat([d, rates])
    cens = runs[runs.outcome != "answered"]
    extra = dict(answered_runs=len(a), unanswered_runs=len(cens), unanswered_with_leaning=float(cens.final_leaning.notna().mean()), unanswered_leaning_correct=float(cens.final_leaning_correct.mean()),
                 first_leaning_correct_then_correct=float(a[a.first_leaning.notna() & (a.first_leaning == np.where(a.correct_is_A, "A", "B"))].correct.mean()),
                 first_leaning_wrong_then_correct=float(a[a.first_leaning.notna() & (a.first_leaning != np.where(a.correct_is_A, "A", "B"))].correct.mean()),
                 wrong_answers_with_correct_value_in_trace=float(a[a.correct == False].correct_value_mentioned.mean()),
                 by_task=a.groupby("task_type").agg(n=("y", "size") if "y" in a else ("correct", "size"), acc=("correct", "mean"), tokens=("hidden_tokens", "median"), stuck=("n_stuck", "mean"), flips=("n_flips", "mean")).to_dict())
    return d, extra


def write_report(desc, extra, hz, cal, byk, fl, mon, comps, nblocks, nflips):
    f3 = lambda x: f"{x:.3f}"
    L = ["# Within-trace models on the R1 reasoning traces", "",
         f"Generated {pd.Timestamp.today():%Y-%m-%d} by `scripts/21_within_trace_model.py` from `scripts/20_trace_segments.py`. 462 runs (400 step-1 at 8,192 tokens, 62 cap-experiment at 24,576), hidden reasoning split into paragraph segments and labelled by text rules. All models have question random effects; sampler 4 chains, NUTS via numpyro, checkpoints under `results/within_trace/posteriors`. No API calls.", "",
         "## Segmentation and labelling", "",
         f"Segments carry token counts, event flags (backtrack: segment opens with But/However/No,/Actually or states a mistake; reconsider: opens with Perhaps/Maybe/Alternatively/Another idea; check: verify/double-check/make sure; stuck: not sure/can't determine/guess/unclear) and a leaning (A/B/none from explicit answer phrases, option letters and option text). Validation: among answered runs with any leaning, the final leaning matches the emitted answer in {f3(desc.loc['final_leaning_matches_answer'].mean())} of runs (by correctness column below).", "",
         "## Descriptives, answered runs", "", "| Quantity | " + " | ".join(desc.columns) + " |", "| --- | " + " | ".join("---:" for _ in desc.columns) + " |"]
    for idx, row in desc.iterrows(): L.append(f"| {idx} | " + " | ".join(f"{v:,.2f}" for v in row) + " |")
    L += ["", f"- First stated leaning correct, then final answer correct: {extra['first_leaning_correct_then_correct']:.2f}; first leaning wrong, then correct: {extra['first_leaning_wrong_then_correct']:.2f}. The first leaning carries almost no information about the outcome.",
          f"- Wrong answers whose trace mentions the correct option's text: {extra['wrong_answers_with_correct_value_in_trace']:.2f}.",
          f"- Unanswered runs (censored or incomplete, n={extra['unanswered_runs']}): a leaning is present at the end in {extra['unanswered_with_leaning']:.2f}, and that leaning is correct in {extra['unanswered_leaning_correct']:.2f}: chance level. Runs that hit the cap had not decided.", ""]
    bt = pd.DataFrame(extra["by_task"]); L += ["By task type (answered runs): ", "", "| Task | n | accuracy | median hidden tokens | stuck per run | flips per run |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for t, row in bt.iterrows(): L.append(f"| {t} | {row.n:.0f} | {row.acc:.3f} | {row.tokens:,.0f} | {row.stuck:.2f} | {row.flips:.2f} |")
    L += ["", f"## Model 1: stopping hazard ({nblocks:,} blocks of >= {BLOCK} tokens)", "", "Log-odds that the run answers in this block, given it has not yet. Positive = more likely to stop. Covariates are the block's own events; `log_ktokens` is log cumulative tokens in thousands.", "", "| Term | Mean | 95% interval | Odds ratio | P(>0) |", "| --- | ---: | --- | ---: | ---: |"]
    for _, x in hz["table"].iterrows(): L.append(f"| {x.term} | {x['mean']:.2f} | {x.lo:.2f} to {x.hi:.2f} | {x.odds_ratio:.2f} | {x.p_positive:.2f} |")
    L += ["", f"Question-effect SD {hz['tau_mean']:.2f}. Observed against predicted hazard (population level, no question effect) by cumulative-token bin:", "", "| Tokens (k) | Blocks | Stops | Observed hazard | Predicted | Stuck rate | Backtrack rate | Leaning rate |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for _, x in byk.iterrows(): L.append(f"| {x.kbin} | {x.blocks:,} | {x.stops:.0f} | {x.obs_hazard:.3f} | {x.pred_hazard:.3f} | {x.stuck_rate:.3f} | {x.backtrack_rate:.3f} | {x.leaning_rate:.3f} |")
    L += ["", "Calibration by predicted-probability decile: " + ", ".join(f"{p:.3f}/{o:.3f}" for p, o in zip(cal.pred, cal.obs)) + " (predicted/observed).", "",
          f"## Model 2: flips between stated leanings ({nflips:,} blocks with a leaning after an earlier one)", "", "| Term | Mean | 95% interval | Odds ratio | P(>0) |", "| --- | ---: | --- | ---: | ---: |"]
    for _, x in fl["table"].iterrows(): L.append(f"| {x.term} | {x['mean']:.2f} | {x.lo:.2f} to {x.hi:.2f} | {x.odds_ratio:.2f} | {x.p_positive:.2f} |")
    L += ["", f"Question-effect SD {fl['tau_mean']:.2f}.", "", "## Model 3: trace monitor, held-out questions (grouped 5-fold CV)", "", "P(correct) for answered runs from features available before grading. `length`: log tokens, task type, condition. `trace`: plus stuck/backtrack/reconsider/check rates per 1k tokens, flips, commitment position, leaning rate, and whether the final leaning matches the emitted answer. `prefix`: only what is visible in the first 4,000 tokens (plus whether the run was still going at 4,000).", "",
          "| Monitor | n | errors | Held-out log score | per run | Brier | AUC |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for _, x in mon.iterrows(): L.append(f"| {x.monitor} | {x.n} | {x.errors} | {x.log_score:.1f} | {x.log_score_per_run:.3f} | {x.brier:.3f} | {x.auc:.3f} |")
    L += ["", "Log-score differences with question-level SE: " + "; ".join(f"{x.comparison} = {x['diff']:+.1f} ± {x.se:.1f}" for _, x in comps.iterrows()) + ".", "",
          "Files: `blocks.csv`, `hazard_table.csv`, `hazard_by_tokens.csv`, `flip_table.csv`, `monitor_results.csv`, `monitor_per_run.csv`, `descriptives.csv`, `extra.json`."]
    (OUT / "REPORT.md").write_text("\n".join(L) + "\n"); print("wrote", OUT / "REPORT.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--draws", type=int, default=1000); ap.add_argument("--tune", type=int, default=1000); ap.add_argument("--chains", type=int, default=4); ap.add_argument("--target-accept", type=float, default=.95)
    args = ap.parse_args()
    seg = pd.read_csv(ROOT / "data/processed/trace_segments.csv"); runs = pd.read_csv(ROOT / "data/processed/trace_runs.csv")
    desc, extra = descriptives(runs, seg); desc.to_csv(OUT / "descriptives.csv"); json.dump(extra, open(OUT / "extra.json", "w"), indent=2, default=float)
    print(desc.round(3).to_string()); print({k: v for k, v in extra.items() if k != "by_task"})
    hz, b, cal, byk = hazard_model(seg, runs, args); b.to_csv(OUT / "blocks.csv", index=False); hz["table"].to_csv(OUT / "hazard_table.csv", index=False); byk.to_csv(OUT / "hazard_by_tokens.csv", index=False)
    print(hz["table"].round(3).to_string()); print(byk.round(3).to_string())
    fl, f = flip_model(seg, runs, args); fl["table"].to_csv(OUT / "flip_table.csv", index=False); print(fl["table"].round(3).to_string())
    a, sets = monitor_features(runs, seg); mon, comps, per = monitor_cv(a, sets, args)
    mon.to_csv(OUT / "monitor_results.csv", index=False); per.to_csv(OUT / "monitor_per_run.csv", index=False); print(mon.round(3).to_string()); print(comps.round(1).to_string())
    write_report(desc, extra, hz, cal, byk, fl, mon, comps, len(b), len(f))

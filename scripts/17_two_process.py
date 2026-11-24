"""Third candidate on the R1 data: a two-process mixture against the baseline and the
drift-variability DDM (2026-10-12).

The model is `two_process` in 08_robustness.py: a fast mode (lognormal length by
condition, question effect, length-independent accuracy) and a slow mode (long
lognormal length, accuracy declining in log length), with a condition/code/question
dependent mode probability. Everything else is the pre-registered pipeline: grouped
CV by question, question-level SEs, the 2-SE rule, the same diagnostic flags.

Two data sets:
  main       the 400 step-1 R1 runs at the 8,192 cap (pre-registered comparison);
             baseline and DDM checkpoints are reused.
  augmented  main plus the 62 cap-experiment runs (24,576 cap) as further repeats of
             the same cells. Selection into the cap experiment depended on the two
             step-1 runs of the cell, which are in the likelihood, so given the
             question effects the extra runs are ordinary observations. This set is
             what identifies the slow mode's accuracy decline. All three models are
             refitted on it.

usage: .venv/bin/python scripts/17_two_process.py --stage cv|summarize|all [--out DIR] [--draws N --tune N]
"""
import argparse, importlib.util, json, pathlib, sys
import numpy as np, pandas as pd, scipy.special as sp
from scipy.stats import norm

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("robustness", ROOT / "scripts/08_robustness.py")
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
OUT = ROOT / "results/two_process"
MODELS = ["baseline", "ddm_sdv_lapse", "two_process"]
SCENARIOS = ["exclude_incomplete", "hidden_only", "deepinfra", "provider_adjusted"]


def augmented(task=False):
    main = r.data("main_task" if task else "main")
    cap = pd.read_csv(r.OUT / "cap_experiment_with_provider.csv")
    c = cap[cap.outcome.isin(["answered", "censored"])].copy()
    c["censored"] = c.outcome == "censored"
    c["rt"] = c.reasoning_tokens / 100
    c["dl"] = np.where(c.censored, 245.76, np.nan)
    c.loc[c.censored, "rt"] = 245.76
    c["correct"] = c.correct.astype(float); c["response"] = np.where(c.correct == 1, 1, -1)
    c["has_code"] = c.has_code.astype(int)
    if task: c["has_code"] = (c.qid.map(r.task_type_map()) == "compute").astype(int)
    c["ci"] = pd.Categorical(c.condition, categories=r.CONDITIONS).codes
    c["rep"] = c.rep + 10; c["phase"] = "cap_experiment"
    cols = [x for x in main.columns if x in c.columns]
    return pd.concat([main, c[cols]], ignore_index=True)


DDM_ARGS = argparse.Namespace(draws=1000, tune=1000, chains=4, target_accept=.95)   # fixed: matches the existing augmented DDM checkpoints


def budgets(args):
    """Cheap models (two_process, baseline): the CLI budget at target_accept >= .99. DDM: fixed DDM_ARGS."""
    hi = argparse.Namespace(**vars(args)); hi.target_accept = max(.99, getattr(args, "target_accept", .95))
    return hi, DDM_ARGS


def run_cv(args):
    hi, args = budgets(args)
    main = r.data("main")
    r.cv(main, "main", ["baseline", "two_process"], hi)
    r.cv(main, "main", ["baseline", "two_process"], hi, secondary=True)
    for sc in SCENARIOS:
        r.cv(r.data(sc), sc, ["baseline", "two_process"], hi, k=3, provider_adjust=sc == "provider_adjusted")
    aug = augmented()
    r.cv(aug, "augmented", ["baseline", "two_process"], hi, k=5)
    r.cv(aug, "augmented", MODELS, args, k=5)   # adds the DDM; earlier score checkpoints are reused


def run_task_type(args):
    """Same three-way comparison with the compute/recall task type in place of has_code."""
    hi, args = budgets(args)
    main = r.data("main_task")
    r.cv(main, "main_task", ["baseline", "two_process"], hi)
    r.cv(main, "main_task", MODELS, args)
    aug = augmented(task=True)
    r.cv(aug, "augmented_task", ["baseline", "two_process"], hi, k=5)
    r.cv(aug, "augmented_task", MODELS, args, k=5)


def three_way(frame, label, infos):
    rows = []
    for cand, ref in [("two_process", "baseline"), ("two_process", "ddm_sdv_lapse"), ("ddm_sdv_lapse", "baseline")]:
        if f"lpd_{cand}_joint" not in frame or f"lpd_{ref}_joint" not in frame: continue
        t = r.comparison(frame, cand, ref)
        d = [x for x in infos if x["label"].startswith(label + "_fold") and (x["label"].endswith("_" + cand) or x["label"].endswith("_" + ref))]
        t["max_rhat"] = max(x["max_rhat"] for x in d); t["min_ess"] = min(x["min_ess"] for x in d); t["divergences"] = sum(x["divergences"] for x in d)
        t["fits"] = len(d); t["flag"] = (t.max_rhat > 1.05) | (t.min_ess < 50) | (t.divergences > 0)
        t["score_verdict"] = t.verdict; t.loc[t.flag, "verdict"] = "unreliable fit; no verdict"
        t["data"] = label; rows.append(t)
    return pd.concat(rows, ignore_index=True)


def expit(x): return 1 / (1 + np.exp(-x))


def parameter_table(P):
    """Population-level quantities from a two_process posterior dict (two-class version)."""
    conds = r.CONDITIONS; X = np.array([[1, s, i, s * i] for s, i in [(0, 0), (0, 1), (1, 0), (1, 1)]], float)
    rows = []
    for code in [0, 1]:
        omega = expit(P["omega_coefs"][0] + code * P["omega_coefs"][1])          # P(question slow-prone)
        p_floor = expit(P["pi_floor"])
        for k, cond in enumerate(conds):
            x = np.r_[X[k], code]; pS = expit(x @ P["pi_coefs"])                   # P(slow trial | slow-prone question)
            p_marg = omega * pS + (1 - omega) * p_floor
            fast_med = np.exp(P["alpha_f"][k] + code * P["gamma_f"]) * 100
            fast_acc = expit(P["beta_f"][k] + code * P["gacc_f"])
            rows.append(dict(has_code=code, condition=cond, p_slow_prone_question=float(omega.mean()), omega_lo=float(np.quantile(omega, .025)), omega_hi=float(np.quantile(omega, .975)),
                             p_slow_given_prone=float(pS.mean()), pS_lo=float(np.quantile(pS, .025)), pS_hi=float(np.quantile(pS, .975)),
                             p_slow_marginal=float(p_marg.mean()), fast_median_tokens=float(np.median(fast_med)), fast_accuracy=float(fast_acc.mean())))
    cond_table = pd.DataFrame(rows)
    slow_med = np.exp(P["mu_s"]) * 100; slow_med_code = np.exp(P["mu_s"] + P["gamma_s"]) * 100
    acc_at = {tok: expit(P["beta_s"] + P["beta_s_len"] * (np.log(tok / 100) - np.log(160))) for tok in [8000, 12000, 16000, 20000, 24000]}
    q = lambda v: (float(np.mean(v)), float(np.quantile(v, .025)), float(np.quantile(v, .975)))
    scalars = dict(p_slow_floor_other_questions=q(expit(P["pi_floor"])), slow_median_tokens_cov0=q(slow_med), slow_median_tokens_cov1=q(slow_med_code), slow_sdlog=q(P["sigma_s"]),
                   slow_accuracy_slope_per_log_unit=q(P["beta_s_len"]), p_slope_negative=float((P["beta_s_len"] < 0).mean()),
                   tau_f=q(P["tau_f"]), tau_bf=q(P["tau_bf"]), omega_covariate_log_odds=q(P["omega_coefs"][1]),
                   **{f"slow_accuracy_at_{k}_tokens": q(v) for k, v in acc_at.items()})
    return cond_table, scalars


def posterior_predictive(P, d, cap_units, n_sims=200, seed=0):
    """Simulate the fitted questions (own class probabilities and effects) at a cap."""
    rng = np.random.default_rng(seed); S = P["alpha_f"].shape[-1]
    known = {q: i for i, q in enumerate(P["qids"])}
    idx = np.array([known.get(q, -1) for q in d.qid]); ci = d.ci.to_numpy(); code = d.has_code.to_numpy()
    new_q = idx < 0
    qi, questions = pd.factorize(d.qid)
    X = np.column_stack([np.ones(len(d)), d.scaffold.isin(["step_by_step", "sbs"]), d.instruction == "thorough", d.scaffold.isin(["step_by_step", "sbs"]) & (d.instruction == "thorough"), code]).astype(float)
    out = []
    for _ in range(n_sims):
        s = rng.integers(S)
        eff = lambda var, tau: np.where(new_q, rng.normal(size=len(d)), P[var][np.maximum(idx, 0), s]) * P[tau][s]
        omega = expit(P["omega_coefs"][0, s] + code * P["omega_coefs"][1, s])
        p_class = np.where(new_q, omega, P["class_prob"][np.maximum(idx, 0), s])
        z = (rng.random(len(questions))[qi] < p_class)
        p = np.where(z, expit(X @ P["pi_coefs"][:, s]), expit(P["pi_floor"][s]))
        slow = rng.random(len(d)) < p
        mu_f = P["alpha_f"][ci, s] + code * P["gamma_f"][s] + eff("u_f", "tau_f")
        lrt = np.where(slow, rng.normal(P["mu_s"][s] + code * P["gamma_s"][s], P["sigma_s"][s]), rng.normal(mu_f, P["sigma_f"][ci, s]))
        eta_f = P["beta_f"][ci, s] + code * P["gacc_f"][s] + eff("b_f", "tau_bf")
        eta_s = P["beta_s"][s] + P["beta_s_len"][s] * (lrt - np.log(160))
        correct = rng.random(len(d)) < expit(np.where(slow, eta_s, eta_f))
        cens = lrt > np.log(cap_units); tok = np.exp(lrt) * 100
        ans = ~cens
        row = dict(censored=cens.mean(), censored_cov0=cens[code == 0].mean(), censored_cov1=cens[code == 1].mean(), acc_answered=correct[ans].mean(),
                   median_cov0=np.median(tok[ans & (code == 0)]) if (ans & (code == 0)).any() else np.nan, median_cov1=np.median(tok[ans & (code == 1)]) if (ans & (code == 1)).any() else np.nan,
                   p_slow_mean=p.mean(), share_slow_prone_questions=z[np.unique(qi, return_index=True)[1]].mean())
        for lo, hi in [(0, 12000), (12000, 16000), (16000, 20000), (20000, 24576)]:
            m = ans & (tok >= lo) & (tok < hi); row[f"acc_{lo//1000}_{hi//1000}k"] = correct[m].mean() if m.sum() >= 5 else np.nan
        out.append(row)
    return pd.DataFrame(out).agg(["mean", lambda s: s.quantile(.05), lambda s: s.quantile(.95)]).set_axis(["mean", "q05", "q95"])


def observed_tables():
    main = r.data("main"); cap = augmented(); cap = cap[cap.phase == "cap_experiment"] if "phase" in cap else cap.iloc[len(main):]
    ans = main[~main.censored]
    obs = dict(step1=dict(censored=main.censored.mean(), censored_prose=main[main.has_code == 0].censored.mean(), censored_code=main[main.has_code == 1].censored.mean(),
                          acc_answered=ans.correct.mean(), median_prose=ans[ans.has_code == 0].rt.median() * 100, median_code=ans[ans.has_code == 1].rt.median() * 100))
    ca = cap[~cap.censored]; tok = ca.rt * 100
    obs["cap_experiment"] = dict(finished=1 - cap.censored.mean(), acc_answered=ca.correct.mean(), median_finish=tok.median(),
                                 **{f"acc_{lo//1000}_{hi//1000}k": ca[(tok >= lo) & (tok < hi)].correct.mean() for lo, hi in [(0, 12000), (12000, 16000), (16000, 20000), (20000, 24576)]})
    return obs


def summarize(args):
    OUT.mkdir(exist_ok=True)
    infos = [json.loads(p.read_text()) for p in (r.OUT / "posteriors").glob("*_diagnostics.json")]
    tables = []
    for label in ["main", "augmented", "main_task", "augmented_task"]:
        pieces = []
        for k in range(5):
            parts = [r.OUT / f"{label}_fold{k}_{m}_scores.csv" for m in MODELS]
            if not all(p.exists() for p in parts): break
            base = pd.read_csv(parts[0])
            for p, m in zip(parts[1:], MODELS[1:]):
                base = base.merge(pd.read_csv(p)[["qid", "condition", "rep"] + [f"lpd_{m}_{c}" for c in r.COMPONENTS]], on=["qid", "condition", "rep"], validate="one_to_one")
            pieces.append(base)
        if len(pieces) == 5:
            frame = pd.concat(pieces, ignore_index=True); frame.to_csv(OUT / f"{label}_three_way_per_trial.csv", index=False)
            tables.append(three_way(frame, label, infos))
        else:
            print(f"{label}: {len(pieces)}/5 folds complete; no three-way table")
    within = r.OUT / "main_within_two_process_scores.csv"
    if within.exists() and (r.OUT / "main_within_baseline_scores.csv").exists():
        f = pd.read_csv(r.OUT / "main_within_baseline_scores.csv").merge(pd.read_csv(within)[["qid", "condition", "rep"] + [f"lpd_two_process_{c}" for c in r.COMPONENTS]], on=["qid", "condition", "rep"])
        t = r.comparison(f, "two_process", target="within-question repeats"); t["data"] = "main_within"; tables.append(t)
    sens = []
    for sc in SCENARIOS:
        p = r.OUT / f"{sc}_cv_comparison.csv"
        if p.exists():
            t = pd.read_csv(p); t = t[t.model == "two_process - baseline"].copy(); t["data"] = sc; sens.append(t)
    if sens: tables.append(pd.concat(sens, ignore_index=True))
    comp = pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()
    comp.to_csv(OUT / "comparisons.csv", index=False); print(comp[[c for c in ["data", "component", "model", "elpd", "se", "verdict"] if c in comp]].round(1).to_string(index=False))
    # full-data fits for parameters and posterior predictive checks
    params = {}; ppc = {}
    for label, d in [("main", r.data("main")), ("augmented", augmented()), ("main_task", r.data("main_task")), ("augmented_task", augmented(task=True))]:
        if label.endswith("_task") and not (r.OUT / f"{label}_fold0_two_process_scores.csv").exists(): continue
        hi = argparse.Namespace(**vars(args)); hi.target_accept = max(.99, getattr(args, "target_accept", .95))
        P = r.fit_model(d, "two_process", f"{label}_all_two_process", hi)
        cond_table, scalars = parameter_table(P); cond_table.to_csv(OUT / f"{label}_p_slow_by_condition.csv", index=False)
        params[label] = scalars
        cells = r.data("main_task" if label.endswith("_task") else "main")   # same 400 cells, covariate matching the fit
        ppc[label] = {"8192": posterior_predictive(P, cells, 81.92), "24576": posterior_predictive(P, cells, 245.76)}
        for cap, t in ppc[label].items(): t.to_csv(OUT / f"{label}_ppc_cap{cap}.csv")
    json.dump(params, open(OUT / "parameters.json", "w"), indent=2, default=float)
    json.dump(observed_tables(), open(OUT / "observed.json", "w"), indent=2, default=float)
    write_report(comp, params, ppc, infos)


def write_report(comp, params, ppc, infos):
    obs = observed_tables()
    L = ["# Third candidate on the R1 data: two-process mixture", "",
         f"Generated {pd.Timestamp.today():%Y-%m-%d} by `scripts/17_two_process.py`. Model `two_process` in `08_robustness.py`; grouped CV by question, question-level SEs, 2-SE rule, diagnostic flags (any divergence, r-hat > 1.05, bulk ESS < 50) as in the pre-registered pipeline. No API calls.", "",
         "## Held-out comparisons", "",
         "Joint ELPD differences on held-out questions (positive favours the first-named model). `main` = 400 step-1 runs at 8,192; `augmented` = main + 62 cap-experiment runs at 24,576 as further repeats of their cells, all three models refitted. `*_task` = the same data with the compute/recall task type (`scripts/18_task_type.py`) in place of the has_code covariate in all three models.", "",
         "| Data | Component | Comparison | ELPD | SE | z | Verdict | max r-hat | min ESS |", "| --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: |"]
    for _, x in comp.iterrows():
        L.append(f"| {x.data} | {x.component} | {x.model} | {x.elpd:,.1f} | {x.se:,.1f} | {x.elpd/x.se if x.se else float('nan'):.1f} | {x.verdict} | {x.max_rhat if 'max_rhat' in x and pd.notna(x.max_rhat) else float('nan'):.2f} | {x.min_ess if 'min_ess' in x and pd.notna(x.min_ess) else float('nan'):.0f} |")
    L += ["", "## Fitted two-process parameters (full-data fits)", ""]
    for label, s in params.items():
        L += [f"### {label}", "", "| Quantity | Mean | 95% interval |", "| --- | ---: | --- |"]
        for k, v in s.items():
            if isinstance(v, (list, tuple)):
                L.append(f"| {k} | {v[0]:,.3g} | {v[1]:,.3g} to {v[2]:,.3g} |")
            else: L.append(f"| {k} | {v:.3g} | |")
        t = pd.read_csv(OUT / f"{label}_p_slow_by_condition.csv")
        cov = "Compute task" if label.endswith("_task") else "Code"
        L += ["", f"P(question is slow-prone), P(slow trial | slow-prone question) by condition, marginal P(slow trial); fast-mode median tokens and accuracy. Covariate column = {cov.lower()} (0/1):", "", f"| {cov} | Condition | P(slow-prone question) | 95% | P(slow given prone) | 95% | P(slow) marginal | Fast median tokens | Fast accuracy |", "| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: |"]
        for _, x in t.iterrows(): L.append(f"| {x.has_code} | {x.condition} | {x.p_slow_prone_question:.2f} | {x.omega_lo:.2f}-{x.omega_hi:.2f} | {x.p_slow_given_prone:.2f} | {x.pS_lo:.2f}-{x.pS_hi:.2f} | {x.p_slow_marginal:.2f} | {x.fast_median_tokens:,.0f} | {x.fast_accuracy:.3f} |")
        L.append("")
    L += ["## Posterior predictive checks", "", f"Observed step 1 at 8,192: censored {obs['step1']['censored']:.2f} (prose {obs['step1']['censored_prose']:.2f}, code {obs['step1']['censored_code']:.2f}), answered accuracy {obs['step1']['acc_answered']:.3f}, medians {obs['step1']['median_prose']:,.0f} / {obs['step1']['median_code']:,.0f} tokens. Observed cap experiment (selected cells, 24,576): finished {obs['cap_experiment']['finished']:.2f}, accuracy {obs['cap_experiment']['acc_answered']:.2f}, median finish {obs['cap_experiment']['median_finish']:,.0f}; accuracy by length " + ", ".join(f"{k[4:]}: {v:.2f}" for k, v in obs['cap_experiment'].items() if k.startswith('acc_') and k != 'acc_answered') + ". The simulated accuracy-by-length rows are for all 400 step-1 cells at a 24,576 cap, not the selected cells, so they are a population prediction rather than a like-for-like replication.", ""]
    for label, caps in ppc.items():
        for cap, t in caps.items():
            L += [f"### {label} fit, simulated at cap {int(cap):,}", "", "| Quantity | Mean | 90% interval |", "| --- | ---: | --- |"]
            for col in t.columns:
                L.append(f"| {col} | {t.loc['mean', col]:.3g} | {t.loc['q05', col]:.3g} to {t.loc['q95', col]:.3g} |")
            L.append("")
    fl = [x for x in infos if ("two_process" in x["label"] or x["label"].startswith("augmented")) and (x["divergences"] or x["max_rhat"] > 1.05 or x["min_ess"] < 50)]
    L += ["## Diagnostics", "", f"Flagged fits among two_process and augmented fits: " + ("; ".join(f"{x['label']} (div {x['divergences']}, r-hat {x['max_rhat']:.2f}, ESS {x['min_ess']:.0f})" for x in fl) if fl else "none") + ".", "",
          "Files: `comparisons.csv`, `main_three_way_per_trial.csv`, `augmented_three_way_per_trial.csv`, `parameters.json`, `*_p_slow_by_condition.csv`, `*_ppc_cap*.csv`, `observed.json`; posteriors and per-fold scores under `results/robustness`."]
    (OUT / "REPORT.md").write_text("\n".join(L) + "\n"); print("wrote", OUT / "REPORT.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["cv", "task_type", "summarize", "all"], default="all")
    ap.add_argument("--draws", type=int, default=2000); ap.add_argument("--tune", type=int, default=2000)
    ap.add_argument("--chains", type=int, default=4); ap.add_argument("--target-accept", type=float, default=.95)
    ap.add_argument("--out", help="override results dir (smoke tests); robustness checkpoints are redirected too")
    args = ap.parse_args()
    if args.out:
        OUT = pathlib.Path(args.out); OUT.mkdir(parents=True, exist_ok=True); (OUT / "posteriors").mkdir(exist_ok=True)
        src = r.OUT; r.OUT = OUT
        for f in ["pilot_r1_with_provider.csv", "cap_experiment_with_provider.csv"]:
            if not (OUT / f).exists(): (OUT / f).write_bytes((src / f).read_bytes())
    if args.stage in ["cv", "all"]: run_cv(args)
    if args.stage == "task_type": run_task_type(args)
    if args.stage in ["summarize", "all"]: summarize(args)

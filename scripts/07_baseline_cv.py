"""Joint baseline + grouped cross-validation (plan v2, phase 7).

Baseline (no accumulation structure), PyMC:
    log rt_i  ~ Normal(alpha[cond_i] + gamma_len*has_code_i + u_q[qid_i], sigma[cond_i])     u_q ~ N(0, tau_u)
    correct_i ~ Bernoulli(logit^-1(beta[cond_i] + gamma_acc*has_code_i + b_q[qid_i] + beta_len*(log rt_i - centre)))   b_q ~ N(0, tau_b)
    censored rows (outcome == censored): log rt contributes P(log rt > log C) via pm.Censored; correctness unobserved.
DDM: the phase-6 hierarchical model (06_fit_ddm.py formulas + has_code), fit with HSSM; held-out density from the
analytical Navarro-Fuss likelihood HSSM exposes (hssm.likelihoods.analytical.logp_ddm).

Primary target (7.2): K folds by QUESTION; a held-out trial's log predictive density integrates over the question's
unknown random effect by Monte Carlo from the population distribution, per posterior draw. The score is therefore
"how well does each model predict the distribution of (correctness, length) across new questions within a condition".
Secondary target (7.3): hold out ODD repeats of every question, fit on EVEN repeats, score with the question's own
posterior random effect. The two are reported separately.
Decision (7.3): ELPD difference (DDM - baseline) with its SE; |diff| < 2 SE is reported as inconclusive.

Both models see identical rows: answered + censored. Zero-token traces and refusals are a separate outcome category
(plan 6.2) and are counted, not modelled, here.

usage: python scripts/07_baseline_cv.py --data results/pilot.csv [--k 5] [--quick] [--skip-ddm]
       python scripts/07_baseline_cv.py --data results/recovery/model_gen_fixed_budget.csv   # 4.3 model recovery
"""
import argparse, pathlib, time, warnings, json
import numpy as np, pandas as pd, yaml, arviz as az, pymc as pm, pytensor, pytensor.tensor as pt
warnings.filterwarnings("ignore")
cfg = yaml.safe_load(open("config.yaml"))
COND = list(cfg["conditions"])
C_STUDY = cfg["model"]["max_tokens"] / cfg["measurement"]["rt_unit_tokens"]


# ---------------------------------------------------------------- data
def load(path, cap=True, max_tokens=None):
    """Modelled rows: answered + censored (+ incomplete: no answer by its own length, treated as censored there).
    Per-row deadline dl on the DDM time scale. cap=True applies the fixed-deadline design post hoc: a run the
    provider let overrun C (OpenRouter upstreams that ignore max_tokens, R1 rerun 2026-10-08) counts as censored at C,
    which is what an enforced cap would have recorded."""
    df = pd.read_csv(path)
    # Follow the collection's recorded cap, not today's config. Older CSVs
    # record it only on censored rows; new parser output records every row.
    if max_tokens is not None:
        deadlines = pd.Series(float(max_tokens)/cfg["measurement"]["rt_unit_tokens"], index=df.index)
    elif "token_cap" in df:
        deadlines = df.token_cap/cfg["measurement"]["rt_unit_tokens"]
    else:
        recorded = df.loc[df.outcome=="censored", "deadline"].dropna().unique() if "deadline" in df else []
        if len(recorded)>1:
            raise ValueError("Multiple collection caps: record token_cap on every row")
        deadlines = pd.Series(float(recorded[0]) if len(recorded) else C_STUDY,index=df.index)
    if deadlines.isna().any() or (deadlines<=0).any():
        raise ValueError("Every row needs a positive collection cap; use --max-tokens to override")
    d = df[df.outcome.isin(["answered", "censored", "incomplete"])].copy()
    d["rt"] = d["rt"].astype(float)
    d["censored"] = d.outcome.isin(["censored", "incomplete"])
    d["dl"] = np.where(d.outcome == "censored", deadlines.loc[d.index], np.nan)
    inc = (d.outcome == "incomplete").values
    d.loc[inc, "dl"] = (d.loc[inc, "deadline"] if "deadline" in d else d.loc[inc, "rt"]).fillna(d.loc[inc, "rt"])
    n_over = 0
    if cap:
        over = (~d.censored) & (d.rt > deadlines.loc[d.index]); n_over = int(over.sum())
        d.loc[over, "censored"] = True; d.loc[over, "dl"] = deadlines.loc[d.index[over]]
        d.loc[d.censored, "dl"] = np.minimum(d.loc[d.censored, "dl"], deadlines.loc[d.index[d.censored]])
    d.loc[d.censored, "rt"] = d.loc[d.censored, "dl"]
    d = d.dropna(subset=["rt"])
    if n_over or inc.any():
        print(f"   {int(inc.sum())} incomplete rows censored at their own length; {n_over} over-cap answered rows censored at recorded collection caps (post-hoc cap {'on' if cap else 'off'})")
    d["has_code"] = d.has_code.astype(bool).astype(int)
    d["correct"] = d.correct.map({True: 1, False: 0, "True": 1, "False": 0, 1: 1, 0: 0}).astype(float)
    d["response"] = np.where(d.correct == 1, 1, -1)
    d["ci"] = pd.Categorical(d.condition, categories=COND).codes
    d["sbs"] = d.scaffold.isin(["sbs", "step_by_step"]).astype(int); d["tho"] = (d.instruction == "thorough").astype(int)   # real data: step_by_step; simulations: sbs
    print(f"{path}: {len(df)} rows -> {len(d)} modelled ({int(d.censored.sum())} censored); excluded by category: "
          f"{df[~df.outcome.isin(['answered','censored','incomplete'])].outcome.value_counts().to_dict()}")
    return d


# ---------------------------------------------------------------- baseline
def fit_baseline(train, draws, tune, chains):
    q_codes, q_levels = pd.factorize(train.qid)
    lrt = np.log(train.rt.values); centre = float(lrt[~train.censored.values].mean())
    obs = ~train.censored.values
    with pm.Model() as m:
        alpha = pm.Normal("alpha", 1.0, 2.0, shape=len(COND)); sigma = pm.HalfNormal("sigma", 1.0, shape=len(COND))
        gamma_len = pm.Normal("gamma_len", 0, 1.5); tau_u = pm.HalfNormal("tau_u", 1.0)
        u = pm.Normal("u", 0, 1, shape=len(q_levels)) * tau_u
        mu = alpha[train.ci.values] + gamma_len * train.has_code.values + u[q_codes]
        pm.Censored("lrt", pm.Normal.dist(mu, sigma[train.ci.values]), lower=None, upper=np.where(train.censored.values, lrt, np.inf), observed=lrt)   # per-row deadline
        beta = pm.Normal("beta", 1.0, 2.0, shape=len(COND)); gamma_acc = pm.Normal("gamma_acc", 0, 1.5)
        beta_len = pm.Normal("beta_len", 0, 1.5); tau_b = pm.HalfNormal("tau_b", 1.5)
        b = pm.Normal("b", 0, 1, shape=len(q_levels)) * tau_b
        eta = beta[train.ci.values[obs]] + gamma_acc * train.has_code.values[obs] + b[q_codes[obs]] + beta_len * (lrt[obs] - centre)
        pm.Bernoulli("correct", logit_p=eta, observed=train.correct.values[obs])
        idata = pm.sample(draws=draws, tune=tune, chains=chains, cores=min(chains, 4), progressbar=False, target_accept=0.9, random_seed=cfg["study"]["seed"])
    post = az.extract(idata, num_samples=min(400, draws * chains), random_seed=0)
    P = {k: post[k].values for k in ["alpha", "sigma", "gamma_len", "tau_u", "beta", "gamma_acc", "beta_len", "tau_b"]}
    P["u"] = post["u"].values * P["tau_u"]; P["b"] = post["b"].values * P["tau_b"]      # (q, S)
    P["centre"] = centre; P["q_levels"] = list(q_levels)
    div = int(idata.sample_stats.diverging.sum()); return P, div


def lpd_baseline(P, test, M=30, use_own_effects=False, rng=None):
    """Per-trial log predictive density of (log rt, correct) [Jacobian: density of rt itself]. Shape (n,)."""
    rng = rng or np.random.default_rng(0)
    S = P["alpha"].shape[1]; n = len(test); ci = test.ci.values; code = test.has_code.values
    lrt = np.log(test.rt.values); cens = test.censored.values; y = test.correct.values
    if use_own_effects:
        qi = np.array([P["q_levels"].index(q) for q in test.qid]); u = P["u"][qi][:, :, None]; b = P["b"][qi][:, :, None]; M = 1
    else:
        u = rng.normal(0, 1, (n, S, M)) * P["tau_u"][None, :, None]; b = rng.normal(0, 1, (n, S, M)) * P["tau_b"][None, :, None]
    mu = P["alpha"][ci][:, :, None] + (P["gamma_len"][None, :, None] * code[:, None, None]) + u
    sd = P["sigma"][ci][:, :, None]
    from scipy.stats import norm
    z = (lrt[:, None, None] - mu) / sd
    lp_rt = np.where(cens[:, None, None], norm.logsf(z), norm.logpdf(z) - np.log(sd) - lrt[:, None, None])
    eta = P["beta"][ci][:, :, None] + P["gamma_acc"][None, :, None] * code[:, None, None] + b + P["beta_len"][None, :, None] * (lrt[:, None, None] - P["centre"])
    lp_c = np.where(cens[:, None, None], 0.0, np.where(y[:, None, None] == 1, -np.logaddexp(0, -eta), -np.logaddexp(0, eta)))
    lp = lp_rt + lp_c                                                     # (n, S, M)
    from scipy.special import logsumexp
    joint = logsumexp(lp.reshape(n, -1), axis=1) - np.log(S * M)
    length = logsumexp(lp_rt.reshape(n, -1), axis=1) - np.log(S * M)
    return {"joint": joint, "length": length, "correctness_given_length": joint - length}


# ---------------------------------------------------------------- DDM
def fit_ddm(train, draws, tune, chains):
    import hssm
    d = train[["rt", "response", "qid", "scaffold", "instruction", "has_code", "censored", "dl"]].copy()
    kw = {}
    if d.censored.any():
        from ddm_censoring import logp_ddm_survival_op
        d.loc[d.censored, "rt"] = -999.0; d["deadline"] = d.dl.fillna(C_STUDY).astype(float).values; kw = dict(missing_data=True, deadline=True, loglik_missing_data=logp_ddm_survival_op)
    d = d.drop(columns=["censored", "dl"])
    # Bounds on v and a keep |v|*a out of the region where hssm's analytical density is numerically unstable (and are
    # a sane prior in 100-token units). With link_settings="log_logit" a bounded parameter gets a generalised-logit
    # link: x = lo + (hi - lo) * sigmoid(linear predictor). t keeps the log link.
    include = [{"name": "v", "formula": "v ~ 1 + scaffold*instruction + has_code + (1|qid)", "bounds": V_BOUNDS},
               {"name": "a", "formula": "a ~ 1 + scaffold*instruction + has_code", "bounds": A_BOUNDS},
               {"name": "t", "formula": "t ~ 1 + scaffold*instruction + has_code"}]
    # The held-out scorer evaluates a pure DDM. Disable HSSM's implicit 5% lapse
    # mixture so training and prediction use the same likelihood.
    m = hssm.HSSM(data=d, model="ddm", include=include, z=0.5, p_outlier=None, link_settings="log_logit", **kw)
    idata = m.sample(draws=draws, tune=tune, chains=chains, cores=min(chains, 4), progressbar=False, target_accept=0.95)
    post = az.extract(idata, num_samples=min(400, draws * chains), random_seed=0)
    def term(name):
        x = post[name].values
        return x.reshape(-1) if x.ndim == 1 else x.reshape(x.shape[-1]) if x.shape[0] == 1 else x
    P = {}
    for p in ("v", "a", "t"):
        P[p] = dict(I=term(f"{p}_Intercept"), s=term(f"{p}_scaffold"), i=term(f"{p}_instruction"), si=term(f"{p}_scaffold:instruction"), c=term(f"{p}_has_code"))
    P["tau_v"] = term("v_1|qid_sigma")
    uq = post["v_1|qid"]; P["q_levels"] = list(uq.coords[[c for c in uq.dims if c != "sample"][0]].values); P["u"] = uq.values
    div = int(idata.sample_stats.diverging.sum()); return P, div


_LOGP = None
def ddm_logp():
    global _LOGP
    if _LOGP is None:
        from hssm.likelihoods.analytical import logp_ddm
        data = pt.matrix("data"); v = pt.vector("v"); a = pt.vector("a"); z = pt.vector("z"); t = pt.vector("t")
        _LOGP = pytensor.function([data, v, a, z, t], logp_ddm(data, v, a, z, t), on_unused_input="ignore")
    return _LOGP


def ddm_survival(C, v, a, t, n_grid=96):
    """log P(T > C): 1 - integral_t^C [f(tau, +1) + f(tau, -1)] dtau by trapezoid on a log-spaced grid. Vectorised over trials."""
    f = ddm_logp(); K = len(v); out = np.zeros(K)
    ok = t < C
    if not ok.any(): return out
    v, a, t = v[ok], a[ok], t[ok]; k = len(v)
    grid = t[:, None] + (C - t)[:, None] * (np.linspace(0, 1, n_grid) ** 2)[None, :] + 1e-6     # dense near t
    tau = grid.reshape(-1); rep = np.repeat(np.arange(k), n_grid)
    dens = sum(np.exp(f(np.column_stack([tau, np.full_like(tau, r)]), v[rep], a[rep], np.full_like(tau, .5), t[rep])) for r in (1.0, -1.0)).reshape(k, n_grid)
    cdf = np.trapezoid(dens, grid, axis=1)
    out[ok] = np.log(np.clip(1 - cdf, 1e-12, 1)); return out


def lpd_ddm(P, test, M=30, use_own_effects=False, rng=None):
    rng = rng or np.random.default_rng(0)
    f = ddm_logp(); S = len(P["v"]["I"]); n = len(test)
    sbs = test.sbs.values; tho = test.tho.values; code = test.has_code.values
    def lin(p):  # (n, S)
        q = P[p]; return (q["I"][None, :] + sbs[:, None] * q["s"][None, :] + tho[:, None] * q["i"][None, :] + (sbs * tho)[:, None] * q["si"][None, :] + code[:, None] * q["c"][None, :])
    sig = lambda x: 1.0 / (1.0 + np.exp(-x))
    V = V_BOUNDS[0] + (V_BOUNDS[1] - V_BOUNDS[0]) * sig(lin("v"))        # inverse generalised-logit links (see fit_ddm)
    A = A_BOUNDS[0] + (A_BOUNDS[1] - A_BOUNDS[0]) * sig(lin("a"))
    T = np.exp(lin("t"))
    below = int((test.rt.values < np.median(T, axis=1)).sum())            # held-out trials shorter than their cell's fitted t
    if below: print(f"   note: {below} of {n} held-out trials have rt below the posterior-median non-decision time of their cell")
    if use_own_effects:
        qi = np.array([P["q_levels"].index(q) for q in test.qid]); U = P["u"][qi][:, :, None]; M = 1
    else:
        U = rng.normal(0, 1, (n, S, M)) * P["tau_v"][None, :, None]
    Vf = V_BOUNDS[0] + (V_BOUNDS[1] - V_BOUNDS[0]) * sig(lin("v")[:, :, None] + U)   # random effect on the link scale
    Af = np.broadcast_to(A[:, :, None], Vf.shape); Tf = np.broadcast_to(T[:, :, None], Vf.shape)
    rt = np.repeat(test.rt.values, S * M); resp = np.repeat(test.response.values.astype(float), S * M); cens = test.censored.values
    args = (Vf.reshape(-1), Af.reshape(-1), np.full(rt.shape, .5), Tf.reshape(-1))
    lp = f(np.column_stack([rt, resp]), *args).reshape(n, S, M)                 # density at the observed response
    lp_other = f(np.column_stack([rt, -resp]), *args).reshape(n, S, M)          # ... and at the other response
    # HSSM's analytical density is numerically unstable for |v|*a > ~50 (spurious spike at rt just above t, mass > 1).
    # Draws in that region are excluded from the predictive mixture and counted; a fold where most draws sit there
    # has not produced a usable DDM fit.
    unstable = (np.abs(Vf) * Af) > VA_MAX
    if unstable.any():
        frac = unstable.mean(); print(f"   note: {frac:.1%} of (trial, draw) pairs have |v|*a > {VA_MAX}; excluded from the DDM predictive" + (" — DDM FIT UNUSABLE IN THIS FOLD" if frac > 0.5 else ""))
        lp = np.where(unstable, -np.inf, lp); lp_other = np.where(unstable, -np.inf, lp_other)
    lp_len = np.logaddexp(lp, lp_other)                                         # marginal density of the length
    if cens.any():
        from ddm_censoring import survival_np
        idx = np.where(cens)[0]
        surv = survival_np(np.repeat(test.dl.values[idx], S * M), Vf[idx].reshape(-1), Af[idx].reshape(-1), 0.5, Tf[idx].reshape(-1)).reshape(len(idx), S, M)   # per-row deadline
        lp[idx] = surv; lp_len[idx] = surv                                       # correctness unobserved when censored
        lp = np.where(unstable, -np.inf, lp)
        lp_len = np.where(unstable, -np.inf, lp_len)
    from scipy.special import logsumexp
    n_ok = np.maximum((~unstable).reshape(n, -1).sum(axis=1), 1) if unstable.any() else S * M   # average over the retained draws only
    joint = logsumexp(lp.reshape(n, -1), axis=1) - np.log(n_ok)
    length = logsumexp(lp_len.reshape(n, -1), axis=1) - np.log(n_ok)
    return {"joint": joint, "length": length, "correctness_given_length": joint - length}


# ---------------------------------------------------------------- CV driver
COMPONENTS = ["joint", "length", "correctness_given_length"]
VA_MAX = 40.0      # |v|*a above which hssm's analytical ddm density is numerically unreliable (probe 2026-10-07)
V_BOUNDS = (-8.0, 8.0); A_BOUNDS = (0.1, 5.0)   # fit bounds (generalised-logit links); product stays at/below VA_MAX


def clustered_se(values, qids):
    """SE of a sum of trial scores with question as the sampling unit.

    This estimates variation across questions, conditional on the fitted folds;
    it does not include training-set or posterior Monte Carlo uncertainty.
    """
    totals = pd.Series(np.asarray(values)).groupby(np.asarray(qids)).sum()
    return float(np.sqrt(len(totals) * totals.var(ddof=1))) if len(totals) > 1 else np.nan


def elpd_table(scores, label, qids):
    """scores: dict model -> dict component -> per-trial lpd arrays aligned on the same trials.
    joint = length + correctness_given_length exactly, for both models."""
    rows = []
    for comp in COMPONENTS:
        for mname, sc in scores.items():
            s = sc[comp]; rows.append(dict(target=label, component=comp, model=mname, elpd=s.sum(), se=clustered_se(s, qids), se_unit="question", n=len(s), n_questions=len(np.unique(qids)), per_trial=s.mean()))
        if {"ddm", "baseline"} <= set(scores):
            diff = scores["ddm"][comp] - scores["baseline"][comp]; d, se = diff.sum(), clustered_se(diff, qids)
            verdict = "DDM better" if d > 2 * se else "baseline better" if d < -2 * se else "inconclusive (|diff| < 2 SE)"
            rows.append(dict(target=label, component=comp, model="ddm - baseline", elpd=d, se=se, se_unit="question", n=len(diff), n_questions=len(np.unique(qids)), per_trial=diff.mean(), verdict=verdict))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="results/pilot.csv"); ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--quick", action="store_true", help="400 draws / 500 tune / 2 chains"); ap.add_argument("--skip-ddm", action="store_true")
    ap.add_argument("--out", default=None, help="results/cv_<dataname>.csv"); ap.add_argument("--no-cap", action="store_true", help="do not censor over-cap answered runs at C")
    ap.add_argument("--max-tokens", type=int, default=None, help="explicit collection cap; otherwise infer from CSV")
    a = ap.parse_args()
    S = (400, 500, 2) if a.quick else (cfg["hssm"]["draws"], cfg["hssm"]["tune"], cfg["hssm"]["chains"])
    d = load(a.data, cap=not a.no_cap, max_tokens=a.max_tokens); rng = np.random.default_rng(cfg["study"]["seed"]); t0 = time.time()
    models = {"baseline": (fit_baseline, lpd_baseline)} | ({} if a.skip_ddm else {"ddm": (fit_ddm, lpd_ddm)})
    per_trial = {m: {c: np.full(len(d), np.nan) for c in COMPONENTS} for m in models}; diags = []

    # 7.2 primary: grouped K-fold by question, population-marginal random effect on held-out questions
    qids = d.qid.unique(); rng.shuffle(qids); folds = np.array_split(qids, a.k)
    for i, held in enumerate(folds):
        te = d.qid.isin(held).values; tr, ts = d[~te], d[te]
        for m, (fitf, lpdf) in models.items():
            P, div = fitf(tr, *S); sc = lpdf(P, ts, rng=rng)
            for c in COMPONENTS: per_trial[m][c][te] = sc[c]
            diags.append(dict(target="held-out questions", fold=i, model=m, divergences=div, n_test=len(ts), elpd_fold=sc["joint"].sum(), elpd_length=sc["length"].sum(), elpd_corr=sc["correctness_given_length"].sum()))
            print(f"fold {i+1}/{a.k} {m:8s} joint={sc['joint'].sum():9.1f} length={sc['length'].sum():9.1f} corr|len={sc['correctness_given_length'].sum():8.1f}  (n={len(ts)}, div={div}, {time.time()-t0:.0f}s)")
    tabs = [elpd_table(per_trial, "held-out questions (population random effect)", d.qid.values)]
    sc_df = pd.DataFrame({f"{m}_{c}": per_trial[m][c] for m in models for c in COMPONENTS})
    byc = sc_df.assign(condition=d.condition.values).groupby("condition").sum().reindex(COND)
    print("\nELPD by condition and component (held-out questions):\n", byc.round(1).to_string())
    if {"ddm", "baseline"} <= set(models):
        dif = pd.DataFrame({c: per_trial["ddm"][c] - per_trial["baseline"][c] for c in COMPONENTS}, index=d.index)
        for key in ("has_code", "condition"):
            g = dif.assign(k=d[key].values).groupby("k")
            tab_ = pd.DataFrame({"n": g.size(), **{f"{c}_diff": g[c].sum() for c in COMPONENTS}, **{f"{c}_se": g[c].agg(lambda x: clustered_se(x.values, d.loc[x.index, "qid"].values)) for c in COMPONENTS}})
            print(f"\nDDM - baseline ELPD by {key} (held-out questions; positive favours the DDM):\n", tab_.round(1).to_string())

    # 7.3 secondary: within-question held-out repeats (fit even reps, score odd reps with the question's own effect)
    tr, ts = d[d.rep % 2 == 0], d[d.rep % 2 == 1]; sec = {}
    for m, (fitf, lpdf) in models.items():
        P, div = fitf(tr, *S); sec[m] = lpdf(P, ts, use_own_effects=True)
        diags.append(dict(target="within-question held-out reps", fold=-1, model=m, divergences=div, n_test=len(ts), elpd_fold=sec[m]["joint"].sum(), elpd_length=sec[m]["length"].sum(), elpd_corr=sec[m]["correctness_given_length"].sum()))
    tabs.append(elpd_table(sec, "within-question held-out repeats (own random effect)", ts.qid.values))
    secondary = ts[["qid", "condition", "rep", "has_code", "rt", "correct", "censored"]].copy()
    for model in sec:
        for comp in COMPONENTS:
            secondary[f"lpd_{model}_{comp}"] = sec[model][comp]

    res = pd.concat(tabs); name = pathlib.Path(a.data).stem
    out = a.out or f"results/cv_{name}.csv"; res.to_csv(out, index=False); pd.DataFrame(diags).to_csv(out.replace(".csv", "_diag.csv"), index=False)
    # per-trial scores, so a fold with sampling problems can be inspected or excluded rather than averaged in
    pt_df = d[["qid", "condition", "rep", "has_code", "rt", "correct", "censored"]].copy()
    for m in models:
        for c in COMPONENTS: pt_df[f"lpd_{m}_{c}"] = per_trial[m][c]
    pt_df["fold"] = -1
    for i, held in enumerate(folds): pt_df.loc[d.qid.isin(held).values, "fold"] = i
    pt_df.to_csv(out.replace(".csv", "_per_trial.csv"), index=False)
    secondary.to_csv(out.replace(".csv", "_within_per_trial.csv"), index=False)
    bad = pd.DataFrame(diags); bad = bad[(bad.target == "held-out questions") & (bad.divergences > 0.05 * S[0] * S[2])]
    if len(bad): print("\n!! folds with >5% divergent draws (treat their ELPD as unreliable):\n", bad.to_string(index=False))
    print("\n" + res.to_string(index=False, float_format=lambda x: f"{x:9.2f}")); print(f"\nwrote {out} ({(time.time()-t0)/60:.1f} min)")

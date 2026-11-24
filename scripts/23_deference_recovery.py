"""Recovery checks for the planned deference experiment (no API calls).

Part A (HSSM): can a hierarchical DDM fitted with HSSM tell a starting-point shift (the cue acts as a prior)
from a drift shift (the cue acts as evidence) at the length variability of R1 on recall items?
Design: 100 recall questions x (control + 4 cue doses, stated success-rate .55/.70/.86/.95) x 2 repeats = 1,000 runs.
Response +1 = chose the cued (wrong) option, -1 = the correct option. Time unit = 100 reasoning tokens.
Part B (PyMC): can four control repeats per question measure the model's own knowledge well enough to test
whether the cue and own-knowledge log-odds enter the follow decision with equal weight (Bayesian integration)?

stages: calibrate | integration | ddm (one dataset: --generator --seed) | ddm_driver | summarize
"""
import argparse, json, os, pathlib, subprocess, sys, time
import numpy as np, pandas as pd
from scipy import special as sp
ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT / "results/deference"; OUT.mkdir(exist_ok=True)
(OUT / "posteriors").mkdir(exist_ok=True); (OUT / "logs").mkdir(exist_ok=True)
RATES = [0.55, 0.70, 0.86, 0.95]; CUE = [0.0] + [float(sp.logit(r)) for r in RATES]; NQ = 100; REPS = 2; CAP = 81.92
GENERATORS = ["z_shift", "v_shift", "both", "null"]; MODELS = ["Mz", "Mv", "Mzv"]; SEED0 = 20261029
TARGETS = dict(rt_control=8.2, logsd_within=0.30, p_wrong_control=0.12, p_wrong_86=0.51, rt_ratio_86=2.2)


def design(seed):
    rng = np.random.default_rng(seed); rows = []
    for q in range(NQ):
        for d, c in enumerate(CUE):
            for rep in range(REPS):
                rows.append(dict(qid=f"q{q:03d}", q=q, dose=d, cue=c, cue_present=int(d > 0), rep=rep))
    return pd.DataFrame(rows), rng


def sim_ddm(v, a, z, t, rng, dt=0.01, cap=CAP):
    """Euler DDM in HSSM's convention: boundaries 0 and a, start z*a, noise 1. Returns rt (nan if censored) and response (+1 upper)."""
    n = len(v); x = z * a; alive = np.ones(n, bool); rt = np.full(n, np.nan); resp = np.zeros(n); sq = np.sqrt(dt)
    for k in range(1, int(np.ceil(cap / dt)) + 1):
        idx = np.flatnonzero(alive)
        if not len(idx): break
        x[idx] += v[idx] * dt + sq * rng.standard_normal(len(idx))
        up = x[idx] >= a[idx]; dn = x[idx] <= 0; done = up | dn
        if done.any():
            dd = idx[done]; rt[dd] = t[dd] + k * dt; resp[dd] = np.where(up[done], 1, -1); alive[dd] = False
    return rt, resp


def generate(generator, seed, P):
    d, rng = design(seed); q = d.q.to_numpy(); c = d.cue.to_numpy(); present = d.cue_present.to_numpy()
    v = (P["mu_v"] + P["tau_v"] * rng.normal(size=NQ))[q]
    a = P["a0"] * np.exp(P["delta_a"] * present); t = np.full(len(d), P["t0"]); z = np.full(len(d), 0.5)
    if generator in ("z_shift", "both"): z = sp.expit(P["beta_z"] * (1 if generator == "z_shift" else 0.5) * c)
    if generator in ("v_shift", "both"): v = v + P["beta_v"] * (1 if generator == "v_shift" else 0.5) * c
    rt, resp = sim_ddm(v, a, z, t, rng)
    d["rt"] = rt; d["response"] = resp; d["censored"] = np.isnan(rt); d["followed"] = (resp == 1)
    return d


def stats(d):
    ok = d[~d.censored]; ctrl = ok[ok.dose == 0]; m86 = ok[ok.dose == 3]
    lsd = np.log(ctrl.rt).groupby(ctrl.qid).std().mean()
    return dict(rt_control=ctrl.rt.mean(), logsd_within=lsd, p_wrong_control=ctrl.followed.mean(), p_wrong_86=m86.followed.mean(),
                rt_ratio_86=m86.rt.mean() / ctrl.rt.mean(), censored=d.censored.mean(),
                rt_86_followed=m86[m86.followed].rt.mean(), rt_86_resisted=m86[~m86.followed].rt.mean())


def calibrate():
    """Small search over DDM parameters for the control cell, then solve the cue effects analytically."""
    best = None
    for t0 in [4, 5, 6]:
        for a0 in [2.5, 3.0, 3.5, 4.0]:
            for mu_v in [-0.4, -0.5, -0.6, -0.7, -0.8]:
                P = dict(mu_v=mu_v, tau_v=0.35, a0=a0, t0=t0, delta_a=0.0, beta_z=0.0, beta_v=0.0)
                s = stats(generate("null", 1, P))
                loss = ((s["rt_control"] - TARGETS["rt_control"]) / 2) ** 2 + ((s["logsd_within"] - TARGETS["logsd_within"]) / 0.05) ** 2 + ((s["p_wrong_control"] - TARGETS["p_wrong_control"]) / 0.03) ** 2
                if best is None or loss < best[0]: best = (loss, P, s)
    loss, P, s = best
    # cue: boundary inflation to match the length ratio, then beta_z / beta_v to match P(wrong) at r=.86
    c86 = CUE[3]
    for delta_a in np.linspace(0.0, 0.8, 17):
        P2 = dict(P, delta_a=float(delta_a))
        for bz in np.linspace(0.3, 2.0, 18):
            s2 = stats(generate("z_shift", 1, dict(P2, beta_z=float(bz))))
            if s2["p_wrong_86"] >= TARGETS["p_wrong_86"]: break
        if s2["rt_ratio_86"] >= TARGETS["rt_ratio_86"]: break
    P2["beta_z"] = float(bz)
    for bv in np.linspace(0.05, 1.0, 20):
        s3 = stats(generate("v_shift", 1, dict(P2, beta_v=float(bv))))
        if s3["p_wrong_86"] >= TARGETS["p_wrong_86"]: break
    P2["beta_v"] = float(bv)
    json.dump(P2, open(OUT / "generator_parameters.json", "w"), indent=1)
    rows = [dict(generator=g, **stats(generate(g, 1, P2))) for g in GENERATORS]
    pd.DataFrame(rows).to_csv(OUT / "generator_profiles.csv", index=False)
    print("parameters", P2); print(pd.DataFrame(rows).round(3).to_string())


def fit_ddm(generator, seed, args):
    import hssm, arviz as az
    P = json.load(open(OUT / "generator_parameters.json")); d = generate(generator, SEED0 + seed, P)
    d.to_csv(OUT / f"data_{generator}_s{seed}.csv", index=False)
    fit = d[~d.censored][["rt", "response", "qid", "cue", "cue_present"]].copy()
    results = []
    for m in MODELS:
        label = f"{generator}_s{seed}_{m}"; path = OUT / "posteriors" / f"{label}.nc"
        if path.exists(): idata = az.from_netcdf(path)
        else:
            inc = [{"name": "a", "formula": "a ~ 1 + cue_present", "bounds": (0.3, 8.0)}, {"name": "t", "formula": "t ~ 1", "bounds": (0.1, 15.0)}]
            kw = {}
            if m in ("Mz", "Mzv"): inc.append({"name": "z", "formula": "z ~ 1 + cue"})
            else: kw["z"] = 0.5
            inc.append({"name": "v", "formula": ("v ~ 1 + cue + (1|qid)" if m in ("Mv", "Mzv") else "v ~ 1 + (1|qid)"), "bounds": (-8.0, 8.0)})
            start = time.time()
            model = hssm.HSSM(data=fit, model="ddm", include=inc, p_outlier=None, link_settings="log_logit", **kw)
            idata = model.sample(sampler="numpyro", chains=args.chains, draws=args.draws, tune=args.tune, target_accept=args.target_accept,
                                 progressbar=False, idata_kwargs=dict(log_likelihood=True))
            idata.to_netcdf(path); print(label, f"{(time.time()-start)/60:.1f} min", flush=True)
        summ = az.summary(idata, kind="all", ci_prob=.95, ci_kind="hdi"); summ.to_csv(OUT / "posteriors" / f"{label}_summary.csv")
        sampled = summ[~summ.index.str.contains(r"\|qid\[", regex=True)]
        rec = dict(generator=generator, seed=seed, model=m, divergences=int(idata.sample_stats.diverging.sum()), max_rhat=float(sampled.r_hat.max()), min_ess=float(sampled.ess_bulk.min()))
        for par, col in [("z_cue", "z_cue"), ("v_cue", "v_cue"), ("a_cue_present", "a_cue_present")]:
            if col in summ.index: rec[par] = float(summ.loc[col, "mean"]); rec[par + "_lo"] = float(summ.loc[col, "hdi95_lb"]); rec[par + "_hi"] = float(summ.loc[col, "hdi95_ub"])
        try:
            loo = az.loo(idata, pointwise=True)
            rec["elpd_loo"] = float(loo.elpd); rec["loo_se"] = float(loo.se); rec["pareto_k_bad"] = int((np.asarray(loo.pareto_k) > 0.7).sum())
        except Exception as e: rec["loo_error"] = str(e)[:80]
        results.append(rec)
    pd.DataFrame(results).to_csv(OUT / f"fit_{generator}_s{seed}.csv", index=False); print(pd.DataFrame(results).round(3).to_string())


def ddm_driver(args):
    jobs = [(g, s) for s in args.seeds for g in GENERATORS]; running = []
    while jobs or running:
        running = [p for p in running if p.poll() is None]
        while jobs and len(running) < args.workers:
            g, s = jobs.pop(0); log = open(OUT / "logs" / f"{g}_s{s}.log", "w")
            env = dict(os.environ, XLA_FLAGS=f"--xla_force_host_platform_device_count={args.chains}", OMP_NUM_THREADS="4")
            running.append(subprocess.Popen([sys.executable, __file__, "--stage", "ddm", "--generator", g, "--seed", str(s), "--draws", str(args.draws), "--tune", str(args.tune), "--chains", str(args.chains)], stdout=log, stderr=subprocess.STDOUT, env=env))
            print("launch", g, s, flush=True)
        time.sleep(20)
    print("driver finished", flush=True)


def integration(args):
    """Part B. Truths: integration (beta_cue = beta_know = 1), obedience (cue slope ~0 across doses, large intercept), both at the observed rates."""
    import pymc as pm, arviz as az
    rows = []
    for truth in ["integration", "obedience", "half_weight"]:
        for n_ctrl in args.control_reps:
            for seed in args.seeds:
                rng = np.random.default_rng(SEED0 + 7 * seed)
                theta = args.know_mean + args.know_sd * rng.normal(size=NQ)   # own-knowledge log-odds of the correct option
                yc = (rng.random((NQ, n_ctrl)) < sp.expit(-theta)[:, None])  # control runs: 1 = chose the wrong option
                if truth == "integration": alpha, bc, bk = 0.0, 1.0, 1.0
                elif truth == "obedience": alpha, bc, bk = 1.5, 0.15, 1.0
                else: alpha, bc, bk = 0.0, 1.0, 0.5
                cues = np.array(CUE[1:]); H = []
                for d, c in enumerate(cues):
                    p = sp.expit(alpha + bc * c - bk * theta)
                    for rep in range(REPS):
                        H.append(pd.DataFrame(dict(q=np.arange(NQ), dose=d, cue=c, y=(rng.random(NQ) < p).astype(int))))
                H = pd.concat(H)
                label = f"int_{truth}_c{n_ctrl}_s{seed}{args.tag}"; path = OUT / "posteriors" / f"{label}.nc"
                with pm.Model():
                    mu = pm.Normal("mu", 2, 2); tau = pm.HalfNormal("tau", 3); eta = pm.Normal("eta", 0, 1, shape=NQ); th = pm.Deterministic("theta", mu + tau * eta)
                    pm.Bernoulli("yc", logit_p=-th[:, None] * np.ones((1, n_ctrl)), observed=yc.astype(int))
                    a0 = pm.Normal("alpha", 0, 2); b_c = pm.Normal("beta_cue", 1, 1); b_k = pm.Normal("beta_know", 1, 1)
                    pm.Deterministic("diff", b_c - b_k)
                    pm.Bernoulli("yh", logit_p=a0 + b_c * H.cue.to_numpy() - b_k * th[H.q.to_numpy()], observed=H.y.to_numpy())
                    if path.exists(): idata = az.from_netcdf(path)
                    else:
                        idata = pm.sample(draws=args.draws, tune=args.tune, chains=args.chains, cores=args.chains, target_accept=args.target_accept, random_seed=SEED0, progressbar=False,
                                          nuts_sampler="numpyro", nuts_sampler_kwargs={"chain_method": "vectorized"}); idata.to_netcdf(path)
                summ = az.summary(idata, var_names=["mu", "tau", "alpha", "beta_cue", "beta_know", "diff"], ci_prob=.95, ci_kind="hdi")
                rec = dict(truth=truth, control_reps=n_ctrl, seed=seed, know_mean=args.know_mean, know_sd=args.know_sd, true_alpha=alpha, true_beta_cue=bc, true_beta_know=bk, divergences=int(idata.sample_stats.diverging.sum()),
                           max_rhat=float(az.summary(idata, var_names=["mu", "tau", "alpha", "beta_cue", "beta_know"]).r_hat.max()),
                           ctrl_wrong=float(yc.mean()), follow_86=float(H[H.dose == 2].y.mean()), questions_all_correct=int((yc.sum(1) == 0).sum()))
                for v in ["beta_cue", "beta_know", "diff", "tau", "alpha"]:
                    rec[v] = float(summ.loc[v, "mean"]); rec[v + "_lo"] = float(summ.loc[v, "hdi95_lb"]); rec[v + "_hi"] = float(summ.loc[v, "hdi95_ub"])
                rec["diff_excludes_0"] = bool(rec["diff_hi"] < 0 or rec["diff_lo"] > 0); rec["theta_sd_mean"] = float(idata.posterior["theta"].std(("chain", "draw")).mean())
                rows.append(rec); print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in rec.items()}, flush=True)
    pd.DataFrame(rows).to_csv(OUT / f"integration_recovery{args.tag}.csv", index=False)


def summarize():
    L = ["# Deference experiment: recovery checks", "", "Generated by `scripts/23_deference_recovery.py`. No API calls.", ""]
    if list(OUT.glob("integration_recovery*.csv")):
        r = pd.concat([pd.read_csv(p) for p in sorted(OUT.glob("integration_recovery*.csv"))])
        L += ["## Part B: own knowledge from control repeats and the integration test", "",
              "Generator: own-knowledge log-odds per question ~ N(3, 3²) (mean P(correct) about .88, wide spread); n control repeats per question; four cue doses (stated success-rate .55/.70/.86/.95) × 2 repeats; P(follow) = logit⁻¹(α + β_cue·logit(rate) − β_know·knowledge). Joint hierarchical fit with latent knowledge. The test is whether β_cue − β_know excludes zero: integration predicts equal slopes.", "",
              "| Truth | Knowledge mean, SD | Control reps | Seed | β_cue true → est (95%) | β_know true → est (95%) | β_cue − β_know (95%) | Excludes 0 | Posterior SD of a question's knowledge | Questions with all control runs correct | Flags |", "| --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: | --- |"]
        for x in r.itertuples():
            L.append(f"| {x.truth} | {getattr(x, 'know_mean', 3.0):.1f}, {getattr(x, 'know_sd', 3.0):.1f} | {x.control_reps} | {x.seed} | {x.true_beta_cue:.2f} → {x.beta_cue:.2f} ({x.beta_cue_lo:.2f} to {x.beta_cue_hi:.2f}) | {x.true_beta_know:.2f} → {x.beta_know:.2f} ({x.beta_know_lo:.2f} to {x.beta_know_hi:.2f}) | {x.diff:.2f} ({x.diff_lo:.2f} to {x.diff_hi:.2f}) | {x.diff_excludes_0} | {x.theta_sd_mean:.2f} | {x.questions_all_correct} | {'div' if x.divergences else ''}{' rhat' if x.max_rhat > 1.05 else ''} |")
        L.append("")
    fits = sorted(OUT.glob("fit_*_s*.csv"))
    if fits:
        f = pd.concat([pd.read_csv(p, keep_default_na=False, na_values=[""]) for p in fits]); P = json.load(open(OUT / "generator_parameters.json"))
        L += ["## Part A: starting point versus drift, HSSM fits", "", f"Generator parameters: {json.dumps({k: round(v, 3) for k, v in P.items()})}. Truth for the cue coefficients: z_shift → z_cue = {P['beta_z']:.2f} (logit scale), v_cue = 0; v_shift → v_cue = {P['beta_v']:.2f}, z_cue = 0; both → half of each; null → both 0. Three fitted models: Mz (z ~ cue), Mv (v ~ cue), Mzv (both); all have v ~ (1|qid), a ~ cue present, t ~ 1.", "",
              "| Generator | Seed | Model | z_cue (95%) | v_cue (95%) | elpd_loo | SE | bad Pareto k | Flags |", "| --- | ---: | --- | --- | --- | ---: | ---: | ---: | --- |"]
        for x in f.itertuples():
            zc = f"{x.z_cue:.2f} ({x.z_cue_lo:.2f} to {x.z_cue_hi:.2f})" if "z_cue" in f and pd.notna(getattr(x, "z_cue", np.nan)) else "fixed"
            vc = f"{x.v_cue:.2f} ({x.v_cue_lo:.2f} to {x.v_cue_hi:.2f})" if "v_cue" in f and pd.notna(getattr(x, "v_cue", np.nan)) else "fixed"
            flags = ("div " if x.divergences else "") + ("rhat " if x.max_rhat > 1.05 else "") + ("ess" if x.min_ess < 50 else "")
            L.append(f"| {x.generator} | {x.seed} | {x.model} | {zc} | {vc} | {getattr(x, 'elpd_loo', np.nan):.1f} | {getattr(x, 'loo_se', np.nan):.1f} | {getattr(x, 'pareto_k_bad', np.nan)} | {flags} |")
        L.append("")
        # verdicts: does Mzv recover which coefficient is active; does LOO prefer the right single-effect model
        L += ["### Verdicts", "", "Coefficients are on HSSM link scales: z logit; v generalised logit on (−8, 8), so a v coefficient of 0.08 is about 0.3 per cue log-odds unit near v = −0.5; a generalised logit on (0.3, 8) with HSSM's a being half the simulator's separation. The simulator's z_shift truth of 1.4 is recovered as 1.24 (Euler discretisation, dt = 0.01); the null generator gives z_cue up to 0.10 (0.02 to 0.17), which sets the 0.2 threshold.", ""]
        for (g, s), grp in f.groupby(["generator", "seed"]):
            zv = grp[grp.model == "Mzv"]
            if len(zv) and "z_cue_lo" in zv:
                z_act = bool(zv.z_cue_lo.iloc[0] > 0.2); v_act = bool(zv.v_cue_lo.iloc[0] > 0.01)
                want = {"z_shift": (True, False), "v_shift": (False, True), "both": (True, True), "null": (False, False)}[g]
                mz = grp[grp.model == "Mz"].elpd_loo.iloc[0] if "elpd_loo" in grp else np.nan; mv = grp[grp.model == "Mv"].elpd_loo.iloc[0] if "elpd_loo" in grp else np.nan
                mzv = grp[grp.model == "Mzv"].elpd_loo.iloc[0] if "elpd_loo" in grp else np.nan
                L.append(f"- {g} seed {s}: Mzv says z active = {z_act}, v active = {v_act} (truth {want[0]}, {want[1]}; rule: z lower bound > 0.2 logit, v lower bound > 0.01 link units); LOO Mz − Mv = {mz - mv:+.1f}, Mzv − Mz = {mzv - mz:+.1f}, Mzv − Mv = {mzv - mv:+.1f}.")
    (OUT / "REPORT.md").write_text("\n".join(L) + "\n"); print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", required=True, choices=["calibrate", "integration", "ddm", "ddm_driver", "loo", "summarize"])
    ap.add_argument("--generator", default="z_shift"); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--control-reps", type=int, nargs="+", default=[4, 8]); ap.add_argument("--know-mean", type=float, default=3.0); ap.add_argument("--know-sd", type=float, default=3.0); ap.add_argument("--tag", default=""); ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--draws", type=int, default=1000); ap.add_argument("--tune", type=int, default=1000); ap.add_argument("--chains", type=int, default=4); ap.add_argument("--target-accept", type=float, default=.95)
    a = ap.parse_args()
    if a.stage == "loo":
        import arviz as az
        for f in sorted(OUT.glob("fit_*_s*.csv")):
            df = pd.read_csv(f, keep_default_na=False, na_values=[""])
            for i, x in df.iterrows():
                idata = az.from_netcdf(OUT / "posteriors" / f"{x.generator}_s{x.seed}_{x.model}.nc")
                try:
                    loo = az.loo(idata, pointwise=True)
                    df.loc[i, "elpd_loo"] = float(loo.elpd); df.loc[i, "loo_se"] = float(loo.se); df.loc[i, "pareto_k_bad"] = int((np.asarray(loo.pareto_k) > 0.7).sum()); df.loc[i, "ic"] = "loo"
                except Exception as e:   # PSIS can fail when an observation's log-likelihood is constant across draws; fall back to WAIC
                    from scipy.special import logsumexp
                    ll = idata.log_likelihood[list(idata.log_likelihood.data_vars)[0]].stack(s=("chain", "draw")).transpose("s", ...).values
                    ll = ll.reshape(ll.shape[0], -1); S = ll.shape[0]
                    pw = (logsumexp(ll, axis=0) - np.log(S)) - ll.var(axis=0, ddof=1)
                    df.loc[i, "elpd_loo"] = float(pw.sum()); df.loc[i, "loo_se"] = float(np.sqrt(len(pw) * pw.var(ddof=1))); df.loc[i, "pareto_k_bad"] = -1; df.loc[i, "ic"] = f"waic ({type(e).__name__})"
            if "loo_error" in df: df = df.drop(columns=["loo_error"])
            df.to_csv(f, index=False); print(f.name, df[["model", "elpd_loo", "loo_se", "pareto_k_bad"]].round(1).to_dict("records"))
        sys.exit()
    {"calibrate": lambda: calibrate(), "integration": lambda: integration(a), "ddm": lambda: fit_ddm(a.generator, a.seed, a), "ddm_driver": lambda: ddm_driver(a), "summarize": lambda: summarize()}[a.stage]()

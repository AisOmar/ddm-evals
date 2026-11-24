"""Collapsing-bound (angle) likelihood on the augmented R1 data (docs/ANGLE_RANDOM_SLOPE_PROTOCOL.md, part A).

Three fits with identical structure: angle (network + quadrature survival), angle with theta fixed at 0 (fixed bound
through the same network), analytical DDM (closed-form survival). Then LOO comparison and a posterior predictive
check of censoring and accuracy-by-length.

usage: python scripts/110_angle_collapsing_bound.py --stage fit --model angle
       python scripts/110_angle_collapsing_bound.py --stage driver      # launches the three fits in parallel
       python scripts/110_angle_collapsing_bound.py --stage analyze
       python scripts/110_angle_collapsing_bound.py --stage finish     # drop stuck chains, posterior predictive, analyze
"""
import argparse, json, os, subprocess, sys, time, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROB = ROOT / "results/robustness"
OUT = ROOT / "results/angle"; (OUT / "posteriors").mkdir(parents=True, exist_ok=True); (OUT / "logs").mkdir(exist_ok=True)
RT_UNIT = 2000.0            # tokens per time unit for this analysis (networks are trained on rt < ~20 units)
CAP_MAIN, CAP_EXP = 8192, 24576
MODELS = ["angle", "angle_theta0", "ddm", "ddm_bounded"]
NARROW = dict(v=(-3.0, 3.0), a=(0.3, 2.5), t=(0.001, 2.0), theta=(-0.1, 1.3))      # the angle network's usable range
WIDE = dict(v=(-8.0, 8.0), a=(0.1, 5.0), t=(0.001, 2.0))
BOUNDS = {"angle": NARROW, "angle_theta0": NARROW, "ddm": WIDE, "ddm_bounded": NARROW}   # ddm_bounded: analytical DDM under the network's range (control, added 2026-11-15)
BINS = [0, 6000, 12000, 20000, 30000]


def data():
    """Augmented task-type dataset, as scripts/17_two_process.augmented(task=True), on the 2,000-token unit."""
    tt = pd.read_csv(ROOT / "data/processed/task_type.csv").set_index("qid").task_type
    raw = pd.read_csv(ROB / "pilot_r1_with_provider.csv")
    d = raw[raw.outcome.isin(["answered", "censored", "incomplete"])].copy()
    d["censored"] = d.outcome.isin(["censored", "incomplete"])
    d.loc[(~d.censored) & (d.reasoning_tokens > CAP_MAIN), "censored"] = True
    d["dl_tok"] = np.where(d.censored, CAP_MAIN, np.nan)
    inc = d.outcome == "incomplete"; d.loc[inc, "dl_tok"] = np.minimum(d.loc[inc, "reasoning_tokens"], CAP_MAIN)
    d["phase"] = "step1"
    cap = pd.read_csv(ROB / "cap_experiment_with_provider.csv")
    c = cap[cap.outcome.isin(["answered", "censored"])].copy()
    c["censored"] = c.outcome == "censored"; c["dl_tok"] = np.where(c.censored, CAP_EXP, np.nan); c["phase"] = "cap_experiment"
    d = pd.concat([d, c], ignore_index=True)
    d["tokens"] = np.where(d.censored, d.dl_tok, d.reasoning_tokens).astype(float)
    d = d[d.tokens > 0].copy()
    d["rt"] = d.tokens / RT_UNIT
    d["deadline"] = np.where(d.censored, d.dl_tok / RT_UNIT, 99.0)      # observed rows: a deadline no rt reaches
    d["correct"] = d.correct.map({True: 1, False: 0, "True": 1, "False": 0, 1: 1, 0: 0}).astype(float)
    d["response"] = np.where(d.correct == 1, 1.0, -1.0)
    d["has_code"] = (d.qid.map(tt) == "compute").astype(int)
    d["sbs"] = d.scaffold.isin(["step_by_step", "sbs"]).astype(int); d["tho"] = (d.instruction == "thorough").astype(int)
    return d.reset_index(drop=True)


def _post(idata):
    """Posterior group as an xarray Dataset (arviz 1.x returns a DataTree)."""
    g = idata["posterior"]; return g.to_dataset() if hasattr(g, "to_dataset") else g


def _ss(idata):
    g = idata["sample_stats"]; return g.to_dataset() if hasattr(g, "to_dataset") else g


def build(name):
    """The HSSM model for one of the three fits, plus the augmented data."""
    import hssm
    sys.path.insert(0, str(ROOT / "scripts"))
    d = data(); fit_df = d[["rt", "response", "deadline", "qid", "sbs", "tho", "has_code"]].copy()
    fit_df.loc[d.censored, "rt"] = -999.0
    print(f"{name}: {len(fit_df)} rows, {int(d.censored.sum())} censored", flush=True)
    v = {"name": "v", "formula": "v ~ 1 + sbs*tho + has_code + (1|qid)"}
    a = {"name": "a", "formula": "a ~ 1 + sbs*tho + has_code"}
    t = {"name": "t", "formula": "t ~ 1 + has_code"}
    kw = dict(missing_data=True, deadline=True, p_outlier=None, link_settings="log_logit")
    if name.startswith("angle"):
        from lan_censoring import make_lan_survival
        v["bounds"] = (-3.0, 3.0); a["bounds"] = (0.3, 2.5); t["bounds"] = (0.001, 2.0)
        # HSSM 0.5's jax path cannot take a fixed scalar for a network parameter (float has no .squeeze), so the
        # "fixed" z and theta are intercept-only terms with a 0.01-sd prior on the link scale: z = 0.5 +/- 0.0025;
        # theta = 0 is link value log(1/13) under the (-0.1, 1.3) generalised logit.
        z = {"name": "z", "formula": "z ~ 1", "prior": {"Intercept": {"name": "Normal", "mu": 0.0, "sigma": 0.01}}}
        include = [v, a, z, t]
        if name == "angle": include.append({"name": "theta", "formula": "theta ~ 1 + has_code", "bounds": (-0.1, 1.3)})
        else: include.append({"name": "theta", "formula": "theta ~ 1", "bounds": (-0.1, 1.3), "prior": {"Intercept": {"name": "Normal", "mu": float(np.log(1 / 13)), "sigma": 0.01}}})
        model = hssm.HSSM(data=fit_df, model="angle", loglik_kind="approx_differentiable", include=include, loglik_missing_data=make_lan_survival("angle"), **kw)
    else:
        from ddm_censoring import logp_ddm_survival_op
        v["bounds"] = BOUNDS[name]["v"]; a["bounds"] = BOUNDS[name]["a"]; t["bounds"] = BOUNDS[name]["t"]
        model = hssm.HSSM(data=fit_df, model="ddm", include=[v, a, t], loglik_missing_data=logp_ddm_survival_op, z=0.5, **kw)
    return model, d, fit_df


def summarise(idata, name, label, n):
    """Diagnostics and population-level posterior summaries for one posterior; writes the per-label summary CSV."""
    import arviz as az
    summ = az.summary(idata, kind="all", ci_prob=.95, ci_kind="hdi"); summ.to_csv(OUT / "posteriors" / f"{label}_summary.csv")
    pop = summ[~summ.index.str.contains(r"\|qid\w*\[", regex=True)]
    rec = dict(model=name, label=label, n=n, chains=int(_post(idata).sizes["chain"]), draws=int(_post(idata).sizes["draw"]), divergences=int(_ss(idata).diverging.sum()), max_rhat=float(pop.r_hat.max()), min_ess=float(pop.ess_bulk.min()))
    rec["flagged"] = bool(rec["divergences"] > 0 or rec["max_rhat"] > 1.05 or rec["min_ess"] < 50)
    for par in pop.index:
        if any(par.startswith(p) for p in ("v_", "a_", "t_", "theta_")) and "sigma" not in par or par.endswith("sigma"):
            rec[par] = float(summ.loc[par, "mean"]); rec[par + "_lo"] = float(summ.loc[par, "hdi95_lb"]); rec[par + "_hi"] = float(summ.loc[par, "hdi95_ub"])
    return rec


def stuck_chains(idata, tol=0.05, min_step=1e-3):
    """Chains whose step-size adaptation collapsed: mean NUTS step size below min_step, or population parameters that
    barely moved (per-chain sd below tol on every parameter)."""
    post = _post(idata); pop = [v for v in post.data_vars if "offset" not in v]
    sd = np.stack([post[v].std("draw").values.reshape(post.sizes["chain"], -1).max(1) for v in pop], 1).max(1)
    step = _ss(idata).step_size.mean("draw").values if "step_size" in _ss(idata) else np.ones_like(sd)
    bad = (sd < tol) | (step < min_step)
    return [int(c) for c, b in zip(post.chain.values, bad) if b], [int(c) for c, b in zip(post.chain.values, bad) if not b]


def fit(name, args):
    import arviz as az
    model, d, fit_df = build(name)
    recs = []
    for label, draws, tune in [(name, args.draws, args.tune), (name + "_refit", 2 * args.draws, 2 * args.tune)]:
        path = OUT / "posteriors" / f"{label}.nc"
        if path.exists(): idata = az.from_netcdf(path)
        else:
            start = time.time()
            idata = model.sample(sampler="numpyro", chains=args.chains, draws=draws, tune=tune, target_accept=args.target_accept, progressbar=False, idata_kwargs=dict(log_likelihood=True))
            idata.to_netcdf(path); print(label, f"{(time.time()-start)/60:.1f} min", flush=True)
        rec = summarise(idata, name, label, len(fit_df))
        recs.append(rec); print(json.dumps({k: v for k, v in rec.items() if not isinstance(v, float) or abs(v) < 1e6}, indent=None, default=float)[:1500], flush=True)
        if not rec["flagged"]: break
        print(name, "flagged; refitting at doubled budget", flush=True)
    pd.DataFrame(recs).to_csv(OUT / f"fit_{name}.csv", index=False)
    pps(name, model, idata, d, args)


def pps(name, model, idata, d, args, n_draws=200):
    """Posterior predictive: per-row simulations from the generative model (ssm-simulators), applying each row's cap."""
    import hssm, arviz as az, xarray as xr
    rng = np.random.default_rng(0)
    post = _post(idata).stack(s=("chain", "draw"))
    S = post.sizes["s"]; take = rng.choice(S, n_draws, replace=False)
    # Per-row parameter means via the fitted model's design matrices: ask HSSM for the deterministic nodes.
    try:
        pp = model.sample_posterior_predictive(dt=idata, draws=n_draws, safe_mode=False, inplace=False)
        ppd = pp["posterior_predictive"] if hasattr(pp, "__getitem__") and "posterior_predictive" in pp else pp.posterior_predictive
        ppd = ppd.to_dataset() if hasattr(ppd, "to_dataset") else ppd
        sim = ppd["rt,response"] if "rt,response" in ppd else ppd[list(ppd.data_vars)[0]]
        arr = sim.stack(s=("chain", "draw")).transpose("s", ...).values      # (S, n, 2)
        rts, resp = arr[..., 0], arr[..., 1]; how = "hssm.sample_posterior_predictive"
        # HSSM re-arranges the data with the censored (missing) rows on top; map the simulated rows back to input order.
        cen = d.censored.to_numpy(); perm = np.r_[np.where(cen)[0], np.where(~cen)[0]]
        if not np.allclose(model.data.rt.to_numpy(), np.where(cen, -999.0, d.rt.to_numpy())[perm]) or not np.array_equal(model.data.qid.to_numpy(), d.qid.to_numpy()[perm]):
            raise RuntimeError("HSSM row order is not 'censored first, otherwise stable'; cannot align the posterior predictive")
        inv = np.argsort(perm); rts, resp = rts[:, inv], resp[:, inv]
    except Exception as e:
        print("pps via HSSM failed:", type(e).__name__, str(e)[:300], "; falling back to manual parameter construction", flush=True)
        rts, resp, how = manual_pps(name, model, idata, d, take)
    tok = rts * RT_UNIT; cens = tok > d.dl_tok.fillna(np.inf).to_numpy()[None, :] if False else tok > np.where(d.phase == "step1", CAP_MAIN, CAP_EXP)[None, :]
    corr = resp > 0
    obs_fin = ~d.censored.to_numpy(); obs_tok = d.tokens.to_numpy(); obs_corr = d.correct.to_numpy() == 1
    out = dict(model=name, how=how, n_draws=int(rts.shape[0]))
    for ph in ["step1", "cap_experiment"]:
        m = (d.phase == ph).to_numpy()
        out[f"censored_{ph}_obs"] = float(d.censored[m].mean()); out[f"censored_{ph}_pred"] = float(cens[:, m].mean()); out[f"censored_{ph}_pred_lo"], out[f"censored_{ph}_pred_hi"] = [float(x) for x in np.quantile(cens[:, m].mean(1), [.025, .975])]
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        mo = obs_fin & (obs_tok >= lo) & (obs_tok < hi); out[f"acc_obs_{lo}_{hi}"] = float(obs_corr[mo].mean()) if mo.sum() else None; out[f"n_obs_{lo}_{hi}"] = int(mo.sum())
        mp = (~cens) & (tok >= lo) & (tok < hi); accs = np.array([corr[i][mp[i]].mean() if mp[i].sum() > 5 else np.nan for i in range(rts.shape[0])])
        out[f"acc_pred_{lo}_{hi}"] = float(np.nanmean(accs)) if np.isfinite(accs).any() else None; out[f"acc_pred_{lo}_{hi}_lo"], out[f"acc_pred_{lo}_{hi}_hi"] = [float(x) if np.isfinite(accs).any() else None for x in np.nanquantile(accs, [.025, .975])] if np.isfinite(accs).any() else (None, None)
    json.dump(out, open(OUT / f"pps_{name}.json", "w"), indent=1); print(json.dumps(out, indent=1), flush=True)


def manual_pps(name, model, idata, d, take):
    """Build per-row v, a, t, theta from the posterior draws and the formulas, then simulate with hssm.simulate_data."""
    import hssm
    post = _post(idata).stack(s=("chain", "draw"))
    q = pd.Categorical(d.qid); qidx = q.codes
    X = pd.DataFrame(dict(Intercept=1.0, sbs=d.sbs, tho=d.tho, inter=d.sbs * d.tho, has_code=d.has_code)).to_numpy(float)
    def lin(par, cols, draws):
        names = [f"{par}_Intercept", f"{par}_sbs", f"{par}_tho", f"{par}_sbs:tho", f"{par}_has_code"]
        beta = np.stack([post[n].values[draws] if n in post else np.zeros(len(draws)) for n in names], 1)   # (D, 5)
        eta = beta @ X.T
        rs = f"{par}_1|qid"
        if rs in post:
            u = post[rs].values[:, draws].T if post[rs].dims[0] != "s" else post[rs].values[draws]
            qc = list(post[rs].coords[[c for c in post[rs].dims if c != "s"][0]].values)
            lookup = {k: i for i, k in enumerate(qc)}; eta = eta + u[:, [lookup[k] for k in q.categories[qidx]]]
        return eta
    bounds = BOUNDS[name]
    def gen_logit(eta, lo, hi): return lo + (hi - lo) / (1 + np.exp(-eta))
    P = {p: gen_logit(lin(p, None, take), *bounds[p]) for p in ["v", "a", "t"]}
    P["z"] = np.full_like(P["v"], 0.5)
    if name.startswith("angle"): P["theta"] = gen_logit(lin("theta", None, take), *bounds["theta"])
    D, n = P["v"].shape; rts = np.zeros((D, n)); resp = np.zeros((D, n))
    order = ["v", "a", "z", "t"] + (["theta"] if name.startswith("angle") else [])
    for i in range(D):
        theta = np.stack([P[p][i] for p in order], 1)
        sim = hssm.simulate_data(model="angle" if name.startswith("angle") else "ddm", theta=theta, size=1, random_state=i)
        rts[i] = sim.rt.to_numpy(); resp[i] = sim.response.to_numpy()
    return rts, resp, "manual (generalised-logit back-transform of formula terms)"


def finish(models):
    """Salvage stage (deviation of 2026-11-15): for each model take the latest posterior, drop chains whose step-size
    adaptation collapsed (no movement at all), re-summarise the moving chains as label <model>_kept, run the posterior
    predictive on them, then run analyze(). The doubled-budget refit cannot repair a chain that never moved."""
    import arviz as az
    for m in models:
        base = OUT / "posteriors" / f"{m}.nc"; refit = OUT / "posteriors" / f"{m}_refit.nc"
        label = f"{m}_refit" if refit.exists() else m
        if not (OUT / "posteriors" / f"{label}.nc").exists(): print("no posterior for", m); continue
        idata = az.from_netcdf(OUT / "posteriors" / f"{label}.nc")
        recs = pd.read_csv(OUT / f"fit_{m}.csv").to_dict("records") if (OUT / f"fit_{m}.csv").exists() else [summarise(idata, m, label, 462)]
        recs = [r for r in recs if not str(r["label"]).endswith("_kept")]          # re-derive the kept-chain row
        stuck, kept = stuck_chains(idata)
        step = _ss(idata).step_size.mean("draw").values if "step_size" in _ss(idata) else None
        print(m, label, "stuck chains", stuck, "kept", kept, "mean step size per chain", None if step is None else np.round(step, 4), flush=True)
        if stuck and len(kept) >= 2:
            idata = idata.sel(chain=kept); label = f"{m}_kept"; idata.to_netcdf(OUT / "posteriors" / f"{label}.nc")
            rec = summarise(idata, m, label, recs[-1]["n"]); rec["stuck_chains"] = str(stuck); recs.append(rec)
            pd.DataFrame(recs).to_csv(OUT / f"fit_{m}.csv", index=False)
            print(json.dumps({k: v for k, v in rec.items() if k in ("label", "chains", "draws", "divergences", "max_rhat", "min_ess", "flagged", "stuck_chains")}), flush=True)
        if not (OUT / f"pps_{m}.json").exists():
            model, d, _ = build(m); pps(m, model, idata, d, None)
    analyze()


def analyze():
    import arviz as az
    recs = pd.concat([pd.read_csv(OUT / f"fit_{m}.csv") for m in MODELS if (OUT / f"fit_{m}.csv").exists()], ignore_index=True)
    final = recs.groupby("model").tail(1).set_index("model")
    idatas = {m: az.from_netcdf(OUT / "posteriors" / f"{final.loc[m, 'label']}.nc") for m in final.index}
    comp = az.compare(idatas); comp.to_csv(OUT / "loo_compare.csv")
    ks = {m: int((np.asarray(az.loo(i, pointwise=True).pareto_k) > 0.7).sum()) for m, i in idatas.items()}
    pps_ = {m: json.load(open(OUT / f"pps_{m}.json")) for m in final.index if (OUT / f"pps_{m}.json").exists()}
    lines = ["# Collapsing bound (angle) on the augmented R1 data", "", f"Fitted {len(final)} models; protocol docs/ANGLE_RANDOM_SLOPE_PROTOCOL.md part A. Time unit {RT_UNIT:.0f} tokens.", "", "## Diagnostics", "",
             final[["label", "n", "divergences", "max_rhat", "min_ess", "flagged"]].to_string(), "", "## Collapse angle (theta), generalised-logit scale coefficients and back-transformed intercept", ""]
    if "angle" in final.index:
        r = final.loc["angle"]; lo, hi = NARROW["theta"]
        bt = lambda e: lo + (hi - lo) / (1 + np.exp(-e))
        lines += [f"theta intercept (link scale): {r.get('theta_Intercept', np.nan):.3f} [{r.get('theta_Intercept_lo', np.nan):.3f}, {r.get('theta_Intercept_hi', np.nan):.3f}] -> theta for recall questions {bt(r.get('theta_Intercept', np.nan)):.3f} rad [{bt(r.get('theta_Intercept_lo', np.nan)):.3f}, {bt(r.get('theta_Intercept_hi', np.nan)):.3f}]",
                  f"theta has_code (compute minus recall, link scale): {r.get('theta_has_code', np.nan):.3f} [{r.get('theta_has_code_lo', np.nan):.3f}, {r.get('theta_has_code_hi', np.nan):.3f}]",
                  f"Pre-specified rule: collapse established if the recall-question theta interval lies above 0.05 rad -> {'ESTABLISHED' if bt(r.get('theta_Intercept_lo', -99)) > 0.05 else 'not established'}", ""]
    kept = [m for m in final.index if str(final.loc[m, "label"]).endswith("_kept")]
    if kept:
        lines += ["## Deviation (2026-11-15): stuck chains dropped", "", f"For {kept} two of four chains never moved (step size adapted to zero, maximum tree depth every iteration). Those chains are dropped and diagnostics above are for the moving chains only (label *_kept); 'stuck_chains' in fit_<model>.csv lists them. The doubled-budget refit was stopped because it cannot repair a chain that never moved. The ESS/r-hat thresholds of the protocol were judged on the kept chains.", ""]
    lines += ["## LOO comparison", "", comp.to_string(), "", f"Pareto k > 0.7 counts: {ks}", "", "## Posterior predictive: censoring and accuracy by finish length", ""]
    if pps_:
        rows = []
        for m, p in pps_.items():
            rows.append(dict(model=m, how=p["how"], cens_step1=f"{p['censored_step1_pred']:.3f} [{p['censored_step1_pred_lo']:.3f}, {p['censored_step1_pred_hi']:.3f}] vs obs {p['censored_step1_obs']:.3f}", cens_cap=f"{p['censored_cap_experiment_pred']:.3f} [{p['censored_cap_experiment_pred_lo']:.3f}, {p['censored_cap_experiment_pred_hi']:.3f}] vs obs {p['censored_cap_experiment_obs']:.3f}",
                             **{f"acc_{lo}_{hi}": (f"{p[f'acc_pred_{lo}_{hi}']:.2f} vs obs {p[f'acc_obs_{lo}_{hi}']:.2f} (n={p[f'n_obs_{lo}_{hi}']})" if p.get(f"acc_pred_{lo}_{hi}") is not None and p.get(f"acc_obs_{lo}_{hi}") is not None else "-") for lo, hi in zip(BINS[:-1], BINS[1:])}))
        lines += [pd.DataFrame(rows).to_string(index=False)]
    (OUT / "REPORT.md").write_text("\n".join(lines)); print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", choices=["fit", "driver", "analyze", "finish"], default="driver"); ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--models", nargs="+", choices=MODELS); ap.add_argument("--draws", type=int, default=500); ap.add_argument("--tune", type=int, default=500); ap.add_argument("--chains", type=int, default=4); ap.add_argument("--target-accept", type=float, default=0.95)
    args = ap.parse_args()
    if args.stage == "fit": fit(args.model, args)
    elif args.stage == "analyze": analyze()
    elif args.stage == "finish": finish(args.models or MODELS)
    else:
        procs = []
        for m in (args.models or MODELS):
            env = dict(os.environ, XLA_FLAGS=f"--xla_force_host_platform_device_count={args.chains}", OMP_NUM_THREADS="3")
            procs.append(subprocess.Popen([sys.executable, __file__, "--stage", "fit", "--model", m, "--draws", str(args.draws), "--tune", str(args.tune), "--chains", str(args.chains), "--target-accept", str(args.target_accept)], stdout=open(OUT / "logs" / f"{m}.log", "w"), stderr=subprocess.STDOUT, env=env)); print("launch", m, flush=True)
        for p in procs: p.wait()
        analyze()

"""Per-question cue slope in the deference DDM fits (docs/ANGLE_RANDOM_SLOPE_PROTOCOL.md, part B).

For each clear-wording dataset (R1 replication, Qwen3-32B model2, gpt-oss-120b model3) refit the step-coded models
Mv_step and Mzv_step with `v ~ 1 + cue_present + (1 + cue_present|qid)` and compare with the saved fits.

usage: python scripts/111_deference_random_slope.py --stage fit --variant replication --model Mzv_step_rs
       python scripts/111_deference_random_slope.py --stage driver
       python scripts/111_deference_random_slope.py --stage analyze
"""
import argparse, json, os, subprocess, sys, time, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEF = ROOT / "results/deference"
OUT = DEF / "random_slope"; (OUT / "logs").mkdir(parents=True, exist_ok=True)
VARIANTS = {"replication": "DeepSeek-R1-0528", "model2": "Qwen3-32B", "model3": "gpt-oss-120b"}
MODELS = ["Mv_step_rs", "Mzv_step_rs"]


def load(variant):
    d = pd.read_csv(DEF / variant / "runs.csv"); ans = d[d.outcome == "answered"].copy()
    fit = pd.DataFrame(dict(rt=ans.reasoning_tokens / 100.0, response=np.where(ans.followed.astype(bool), 1.0, -1.0), qid=ans.qid.to_numpy(), cue_present=ans.cue_present.to_numpy()))
    return fit[fit.rt > 0.1].reset_index(drop=True), d


def fit(variant, m, args):
    import hssm, arviz as az
    fit_df, _ = load(variant); base = m[:-3]
    (DEF / variant / "posteriors").mkdir(exist_ok=True)
    def one(label, draws, tune):
        path = DEF / variant / "posteriors" / f"{label}.nc"
        if path.exists(): return az.from_netcdf(path)
        inc = [{"name": "a", "formula": "a ~ 1 + cue_present", "bounds": (0.3, 8.0)}, {"name": "t", "formula": "t ~ 1", "bounds": (0.1, 15.0)}]; kw = {}
        if base == "Mzv_step": inc.append({"name": "z", "formula": "z ~ 1 + cue_present"})
        else: kw["z"] = 0.5
        inc.append({"name": "v", "formula": "v ~ 1 + cue_present + (1 + cue_present|qid)", "bounds": (-8.0, 8.0)})
        start = time.time(); model = hssm.HSSM(data=fit_df, model="ddm", include=inc, p_outlier=None, link_settings="log_logit", **kw)
        idata = model.sample(sampler="numpyro", chains=args.chains, draws=draws, tune=tune, target_accept=args.target_accept, progressbar=False, idata_kwargs=dict(log_likelihood=True))
        idata.to_netcdf(path); print(label, f"{(time.time()-start)/60:.1f} min", flush=True); return idata
    recs = []
    for label, draws, tune in [(m, args.draws, args.tune), (m + "_refit", 2 * args.draws, 2 * args.tune)]:
        idata = one(label, draws, tune)
        summ = az.summary(idata, kind="all", ci_prob=.95, ci_kind="hdi"); summ.to_csv(DEF / variant / "posteriors" / f"{label}_summary.csv")
        pop = summ[~summ.index.str.contains(r"\|qid\w*\[", regex=True)]
        rec = dict(variant=variant, model=m, label=label, n=len(fit_df), divergences=int(idata.sample_stats.diverging.sum()), max_rhat=float(pop.r_hat.max()), min_ess=float(pop.ess_bulk.min()))
        rec["flagged"] = bool(rec["divergences"] > 0 or rec["max_rhat"] > 1.05 or rec["min_ess"] < 50)
        for par in pop.index:
            rec[par] = float(summ.loc[par, "mean"]); rec[par + "_lo"] = float(summ.loc[par, "hdi95_lb"]); rec[par + "_hi"] = float(summ.loc[par, "hdi95_ub"])
        recs.append(rec); print(json.dumps(rec, default=float)[:1500], flush=True)
        if not rec["flagged"]: break
        print(m, "flagged; refitting at doubled budget", flush=True)
    pd.DataFrame(recs).to_csv(OUT / f"fit_{variant}_{m}.csv", index=False)


def analyze():
    import arviz as az
    rows, qrows = [], []
    for variant, name in VARIANTS.items():
        fit_df, d = load(variant)
        ctrl = d[(d.cell == "control") & (d.outcome == "answered")].groupby("qid").correct.apply(lambda s: 1 - s.astype(bool).mean()).rename("control_error")
        for m in MODELS:
            f = OUT / f"fit_{variant}_{m}.csv"
            if not f.exists(): continue
            rec = pd.read_csv(f).iloc[-1]; base = m[:-3]
            new = az.from_netcdf(DEF / variant / "posteriors" / f"{rec.label}.nc")
            old_path = DEF / variant / "posteriors" / f"{base}.nc"
            old_rec = pd.read_csv(DEF / variant / f"ddm_{base}.csv").iloc[-1] if (DEF / variant / f"ddm_{base}.csv").exists() else None
            old = az.from_netcdf(DEF / variant / "posteriors" / f"{old_rec.label}.nc") if old_rec is not None else az.from_netcdf(old_path)
            comp = az.compare({m: new, base: old})
            dl = float(comp.loc[m, "elpd"] - comp.loc[base, "elpd"]); dse = float(comp.loc[comp.index != comp.index[0], "dse"].iloc[0])
            post = new.posterior
            sig_name = [v for v in post.data_vars if "cue_present|qid_sigma" in v or v.endswith("cue_present|qid_sigma")]
            sig = post[sig_name[0]].values.ravel() if sig_name else np.array([np.nan])
            slope_name = [v for v in post.data_vars if v == "v_cue_present|qid"]
            per_q = None
            if slope_name:
                s = post[slope_name[0]]; dimq = [c for c in s.dims if c not in ("chain", "draw")][0]
                mean = s.mean(("chain", "draw")).to_series(); lo = s.quantile(.025, ("chain", "draw")).to_series(); hi = s.quantile(.975, ("chain", "draw")).to_series()
                per_q = pd.DataFrame(dict(slope_mean=mean, lo=lo, hi=hi)); per_q.index = [str(i).split("__")[-1] if "__" in str(i) else str(i) for i in per_q.index]
                per_q = per_q.join(ctrl, how="left"); per_q["variant"] = variant; per_q["model"] = m; qrows.append(per_q.reset_index().rename(columns={"index": "qid"}))
            rho = float(per_q.slope_mean.corr(per_q.control_error, method="spearman")) if per_q is not None else np.nan
            excl = float(((per_q.lo > 0) | (per_q.hi < 0)).mean()) if per_q is not None else np.nan
            row = dict(model_name=name, variant=variant, model=m, flagged=bool(rec.flagged), divergences=int(rec.divergences), max_rhat=float(rec.max_rhat), min_ess=float(rec.min_ess),
                       slope_sd=float(np.mean(sig)), slope_sd_lo=float(np.quantile(sig, .025)), slope_sd_hi=float(np.quantile(sig, .975)), heterogeneity=("ESTABLISHED" if np.quantile(sig, .025) > 0.2 else "not established"),
                       elpd_diff_vs_no_slope=dl, elpd_diff_se=dse, loo_verdict=("favours random slope" if dl > 2 * dse else ("favours no slope" if dl < -2 * dse else "tie")), spearman_slope_vs_control_error=rho, share_q_interval_excludes_0=excl)
            for par in ["v_cue_present", "z_cue_present", "a_cue_present", "v_Intercept"]:
                if par in rec: row[par + "_rs"] = f"{rec[par]:.3f} [{rec[par + '_lo']:.3f}, {rec[par + '_hi']:.3f}]"
                if old_rec is not None and par in old_rec: row[par + "_old"] = f"{old_rec[par]:.3f} [{old_rec[par + '_lo']:.3f}, {old_rec[par + '_hi']:.3f}]"
            rows.append(row)
    R = pd.DataFrame(rows); R.to_csv(OUT / "summary.csv", index=False)
    if qrows: pd.concat(qrows).to_csv(OUT / "per_question_slopes.csv", index=False)
    lines = ["# Per-question cue slope in the deference DDM fits", "", "Protocol: docs/ANGLE_RANDOM_SLOPE_PROTOCOL.md part B. `v ~ 1 + cue_present + (1 + cue_present|qid)`; the comparison fit is the saved step-coded model without the random slope.", "",
             R[["model_name", "model", "flagged", "slope_sd", "slope_sd_lo", "slope_sd_hi", "heterogeneity", "elpd_diff_vs_no_slope", "elpd_diff_se", "loo_verdict", "spearman_slope_vs_control_error", "share_q_interval_excludes_0"]].round(3).to_string(index=False), "",
             "## Population cue effects with (rs) and without (old) the random slope", "", R[["model_name", "model"] + [c for c in R.columns if c.endswith("_rs") or c.endswith("_old")]].to_string(index=False)]
    (OUT / "REPORT.md").write_text("\n".join(lines)); print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--stage", choices=["fit", "driver", "analyze"], default="driver"); ap.add_argument("--variant", choices=list(VARIANTS)); ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--draws", type=int, default=1000); ap.add_argument("--tune", type=int, default=1000); ap.add_argument("--chains", type=int, default=4); ap.add_argument("--target-accept", type=float, default=0.95)
    args = ap.parse_args()
    if args.stage == "fit": fit(args.variant, args.model, args)
    elif args.stage == "analyze": analyze()
    else:
        procs = []
        for variant in VARIANTS:
            for m in MODELS:
                env = dict(os.environ, XLA_FLAGS=f"--xla_force_host_platform_device_count={args.chains}", OMP_NUM_THREADS="2")
                procs.append(subprocess.Popen([sys.executable, __file__, "--stage", "fit", "--variant", variant, "--model", m, "--draws", str(args.draws), "--tune", str(args.tune), "--chains", str(args.chains), "--target-accept", str(args.target_accept)], stdout=open(OUT / "logs" / f"{variant}_{m}.log", "w"), stderr=subprocess.STDOUT, env=env)); print("launch", variant, m, flush=True)
        for p in procs: p.wait()
        analyze()

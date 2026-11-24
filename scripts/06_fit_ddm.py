"""Fit the hierarchical DDM to real pilot/full data (plan v2, phase 6).

Primary: accuracy coding (response = +1 correct / -1 incorrect), z fixed at 0.5.
Sensitivity (--option-coding): response = +1 if chose A / -1 if chose B, with drift sign flipped
by correct_is_A, and z free, to estimate position bias directly.

usage: python scripts/06_fit_ddm.py --data results/pilot.csv
"""
import argparse, numpy as np, pandas as pd, yaml, hssm, arviz as az
import importlib.util
from pathlib import Path
from ddm_censoring import logp_ddm_survival_op

cfg = yaml.safe_load(open("config.yaml"))
ap = argparse.ArgumentParser()
ap.add_argument("--data", default="results/pilot.csv")
ap.add_argument("--option-coding", action="store_true")
ap.add_argument("--out", default="results/ddm_fit.nc")
ap.add_argument("--max-tokens", type=int, help="Override the recorded collection cap")
a = ap.parse_args()

df = pd.read_csv(a.data)
print("outcomes:\n", df["outcome"].value_counts())
# Share the CV loader: collection caps can differ from today's config, and
# incomplete runs are censored at their observed length.
spec = importlib.util.spec_from_file_location("baseline_cv", Path(__file__).with_name("07_baseline_cv.py"))
cv = importlib.util.module_from_spec(spec); spec.loader.exec_module(cv)
fit_df = cv.load(a.data, max_tokens=a.max_tokens)
fit_df["deadline"] = fit_df["dl"]
kw = {}
if fit_df["censored"].any():
    fit_df.loc[fit_df["censored"], "rt"] = -999.0
    kw = dict(missing_data=True, deadline=True, loglik_missing_data=logp_ddm_survival_op)
    print(f"{int(fit_df['censored'].sum())} censored rows enter via their recorded deadlines")
cols = ["rt", "response", "qid", "scaffold", "instruction", "has_code"] + (["deadline"] if kw else [])
# has_code (question-level covariate) added 2026-10-07 after recovery 4.1 (see CHANGELOG); log links on a, t.
if a.option_coding:
    fit_df["response"] = fit_df["chosen"].map({"A": 1, "B": -1}).fillna(1)
    fit_df["stim"] = fit_df["correct_is_A"].map({True: 1, False: -1})
    include = [{"name": "v", "formula": "v ~ 0 + stim + stim:scaffold + stim:instruction + stim:scaffold:instruction + stim:has_code + (0 + stim|qid)"},
               {"name": "a", "formula": "a ~ 1 + scaffold*instruction + has_code"},
               {"name": "t", "formula": "t ~ 1 + scaffold*instruction + has_code"},
               {"name": "z", "formula": "z ~ 1 + scaffold*instruction"}]
    model = hssm.HSSM(data=fit_df[cols + ["stim"]], model="ddm", include=include, p_outlier=None, link_settings="log_logit", **kw)
else:
    # bounds keep |v|*a below ~40, where hssm's analytical density is numerically reliable (CHANGELOG 2026-10-07);
    # bounded parameters get generalised-logit links, so report them back-transformed.
    include = [{"name": "v", "formula": "v ~ 1 + scaffold*instruction + has_code + (1|qid)", "bounds": (-8.0, 8.0)},
               {"name": "a", "formula": "a ~ 1 + scaffold*instruction + has_code", "bounds": (0.1, 5.0)},
               {"name": "t", "formula": "t ~ 1 + scaffold*instruction + has_code"}]
    model = hssm.HSSM(data=fit_df[cols], model="ddm", include=include, z=0.5, p_outlier=None, link_settings="log_logit", **kw)

idata = model.sample(draws=cfg["hssm"]["draws"], tune=cfg["hssm"]["tune"], chains=cfg["hssm"]["chains"], target_accept=0.95)
print(az.summary(idata, var_names=["v_", "a_", "t_"], filter_vars="like", kind="diagnostics")[["r_hat", "ess_bulk"]].describe())
idata.to_netcdf(a.out)
print("saved", a.out, "— next: posterior predictive checks within condition x difficulty stratum (plan 6.4)")

"""Section-12 contrast: the effect of the <peer-reviewed>true</peer-reviewed> tag on following the planted key, holding the key-audit wording fixed.

Random-intercept logistic on the hinted runs of the replication (no tag, two repeats) and the tag check (tag, one repeat):
follow ~ cue log-odds + tag + (1 | question).  Writes results/deference/peer_tag/tag_contrast.json and prints the table.
No API calls.
"""
import json, pathlib, sys
import numpy as np, pandas as pd, pymc as pm, arviz as az

ROOT = pathlib.Path(__file__).resolve().parents[1]
rep = pd.read_csv(ROOT / "results/deference/replication/runs.csv"); tag = pd.read_csv(ROOT / "results/deference/peer_tag/runs.csv")
rep, tag = rep[(rep.cell != "control") & (rep.outcome == "answered")].copy(), tag[(tag.cell != "control") & (tag.outcome == "answered")].copy()
rep["tag"] = 0; tag["tag"] = 1; d = pd.concat([rep, tag], ignore_index=True); d["q"], qids = pd.factorize(d.qid)
with pm.Model():
    a0 = pm.Normal("intercept", 0, 2); b = pm.Normal("slope", 0, 2); g = pm.Normal("tag", 0, 2); tau = pm.HalfNormal("tau_question", 3); u = pm.Normal("u", 0, 1, shape=len(qids)) * tau
    pm.Bernoulli("y", logit_p=a0 + b * d.cue.to_numpy() + g * d.tag.to_numpy() + u[d.q.to_numpy()], observed=d.followed.astype(int).to_numpy())
    idata = pm.sample(draws=2000, tune=2000, chains=4, target_accept=0.99, nuts_sampler="numpyro", random_seed=20261015, progressbar=False)
summ = az.summary(idata, var_names=["intercept", "slope", "tag", "tau_question"], ci_prob=0.95)
post = idata.posterior; res = {v: dict(mean=float(post[v].values.mean()), lo=float(np.quantile(post[v].values, .025)), hi=float(np.quantile(post[v].values, .975))) for v in ["intercept", "slope", "tag", "tau_question"]}
res["diagnostics"] = dict(divergences=int(idata.sample_stats.diverging.sum()), max_rhat=float(summ.r_hat.max()), min_ess=float(summ.ess_bulk.min()), n_runs=int(len(d)), n_tag=int(d.tag.sum()))
res["raw"] = {f"{'tag' if t else 'notag'}_{c}": dict(n=int(len(g)), followed=float(g.followed.mean())) for (t, c), g in d.groupby(["tag", "cell"])}
json.dump(res, open(ROOT / "results/deference/peer_tag/tag_contrast.json", "w"), indent=1); print(json.dumps(res, indent=1))

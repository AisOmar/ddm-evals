"""Post hoc joint model comparison; no model API calls.

Saturated marginal logistic regression: follow ~ model * (cue_present + dose),
dose = cue_present * (logit(r) - logit(.55)). Question-clustered sandwich
covariance keeps all repeats and all models together. Paired question bootstrap
provides probability-scale differences. Historical answered-only selection is
retained and checked with common-question and missing-outcome bounds.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import logit
from scipy.stats import chi2, norm

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"R1": "replication", "Qwen3": "model2", "gpt-oss": "model3"}
CELLS = ["control", "p55", "p95"]
GAP = logit(.95) - logit(.55)


def load():
    frames, hashes = [], {}
    for model, variant in SOURCES.items():
        p = ROOT / f"results/deference/{variant}/runs.csv"
        d = pd.read_csv(p).assign(model=model)
        if d.duplicated(["qid", "cell", "rep"]).any():
            raise ValueError(f"Duplicate trials: {variant}")
        if set(d.cell) != set(CELLS) or d.qid.nunique() != 100:
            raise ValueError(f"Unexpected design: {variant}")
        if set(d.provider) != {"DeepInfra"}:
            raise ValueError(f"Unexpected provider: {variant}")
        frames.append(d)
        hashes[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    d = pd.concat(frames, ignore_index=True)
    # Same question identity, option order and target are necessary for pairing.
    for col in ["target", "hint_letter", "correct_is_A"]:
        if d.groupby("qid")[col].nunique().max() != 1:
            raise ValueError(f"Question alignment mismatch: {col}")
    return d, hashes


def holm(ps):
    order = np.argsort(ps)
    adjusted = np.empty(len(ps))
    running = 0.
    for k, i in enumerate(order):
        running = max(running, (len(ps) - k) * ps[i])
        adjusted[i] = min(1., running)
    return adjusted


def estimate(d, boots, seed):
    models = list(SOURCES)
    groups = [(m, c) for m in models for c in CELLS]
    answered = d[d.outcome == "answered"].copy()
    if answered.followed.isna().any():
        raise ValueError("Answered trial lacks follow outcome")
    answered["y"] = answered.followed.astype(float)
    qids = sorted(d.qid.unique())
    counts = np.zeros((len(qids), len(groups)))
    sums = counts.copy()
    for i, (m, c) in enumerate(groups):
        g = answered[(answered.model == m) & (answered.cell == c)].groupby("qid").y.agg(["size", "sum"]).reindex(qids, fill_value=0)
        counts[:, i], sums[:, i] = g["size"], g["sum"]
    n, y = counts.sum(0), sums.sum(0)
    p = y / n
    if np.any((p == 0) | (p == 1)):
        raise ValueError("Complete separation in marginal cell; use penalized model")
    # Cell-logit parameterization is equivalent to model * (presence + dose).
    theta = logit(p)
    bread = np.diag(1 / (n * p * (1-p)))
    scores = sums - counts * p
    N, K, G = int(n.sum()), len(groups), len(qids)
    correction = G / (G - 1) * (N - 1) / (N - K)
    cov = correction * bread @ scores.T @ scores @ bread
    def slope(m):
        v = np.zeros(K)
        v[groups.index((m, "p95"))] = 1/GAP
        v[groups.index((m, "p55"))] = -1/GAP
        return v
    def contrast(v):
        est, se = float(v @ theta), float(np.sqrt(v @ cov @ v))
        return dict(estimate=est, se=se, lo=est-1.96*se, hi=est+1.96*se,
                    p=float(2 * norm.sf(abs(est/se))))
    C = np.array([slope(m)-slope(models[0]) for m in models[1:]])
    b = C @ theta
    wald = float(b @ np.linalg.solve(C @ cov @ C.T, b))
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(G, np.full(G, 1/G), size=boots)
    bp = (weights @ sums) / (weights @ counts)
    pairs, rows = list(itertools.combinations(models, 2)), []
    for a, b in pairs:
        row = dict(pair=f"{a} minus {b}", **contrast(slope(a)-slope(b)))
        v = (slope(a)-slope(b)) * GAP
        draws = bp @ v
        row.update(risk_difference=float(p @ v), risk_lo=float(np.quantile(draws,.025)), risk_hi=float(np.quantile(draws,.975)),
                   risk_simultaneous_lo=float(np.quantile(draws,.05/6)), risk_simultaneous_hi=float(np.quantile(draws,1-.05/6)))
        rows.append(row)
    for row, adj in zip(rows, holm([r["p"] for r in rows])):
        row["p_holm"] = float(adj)
    rates, effects = [], []
    for m in models:
        s = slope(m)
        v = s * GAP
        draws = bp @ v
        effects.append(dict(model=m, slope=contrast(s), dose_risk_change=float(p @ v),
                            lo=float(np.quantile(draws,.025)), hi=float(np.quantile(draws,.975))))
        for c in CELLS:
            i = groups.index((m,c))
            rates.append(dict(model=m, cell=c, n=int(n[i]), followed=float(p[i]),
                              lo=float(np.quantile(bp[:,i],.025)), hi=float(np.quantile(bp[:,i],.975))))
    # Distribution-free worst-case bounds: every non-answer could follow or resist.
    bounds = {}
    for m in models:
        cell_bounds = {}
        for c in ["p55", "p95"]:
            a = d[(d.model == m) & (d.cell == c)]
            followed = a.loc[a.outcome == "answered", "followed"].astype(float).sum()
            missing = (a.outcome != "answered").sum()
            cell_bounds[c] = (followed/len(a), (followed+missing)/len(a))
        bounds[m] = [cell_bounds["p95"][0]-cell_bounds["p55"][1], cell_bounds["p95"][1]-cell_bounds["p55"][0]]
    return dict(n_answered=N, n_questions=G, rates=rates, effects=effects, pairs=rows,
                omnibus=dict(wald=wald, df=2, p=float(chi2.sf(wald,2))),
                missing_outcome_dose_bounds=bounds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstraps", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20261016)
    args = ap.parse_args()
    d, hashes = load()
    result = estimate(d,args.bootstraps,args.seed)
    # Common answered cohort: require at least one answered run in every model/cell.
    coverage = d[d.outcome == "answered"].groupby(["qid","model","cell"]).size().unstack(["model","cell"])
    common = coverage.dropna().index
    result["common_question_sensitivity"] = estimate(d[d.qid.isin(common)],args.bootstraps,args.seed)
    result.update(source_sha256=hashes, seed=args.seed, bootstraps=args.bootstraps,
                  status="post hoc; not preregistered", method="Saturated marginal logistic; CR1 sandwich clustered by qid; paired question bootstrap")
    out = ROOT / "results/deference/cross_model"
    out.mkdir(exist_ok=True)
    (out/"analysis.json").write_text(json.dumps(result,indent=2)+"\n")
    pd.DataFrame(result["pairs"]).to_csv(out/"pairwise.csv",index=False)
    pd.DataFrame(result["rates"]).to_csv(out/"rates.csv",index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1,2,figsize=(12,4.5))
    for model in SOURCES:
        rates=[r for r in result['rates'] if r['model']==model]
        ys=np.array([r['followed'] for r in rates])*100
        lower=ys-np.array([r['lo'] for r in rates])*100
        upper=np.array([r['hi'] for r in rates])*100-ys
        axes[0].errorbar(range(3),ys,yerr=[lower,upper],marker='o',capsize=3,label=model)
    axes[0].set(xticks=range(3),xticklabels=['Control','55% claim','95% claim'],ylabel='Chose planted wrong option (%)',title='Similar baseline accuracy, different cue responses')
    axes[0].legend()
    for i,r in enumerate(result['pairs']):
        x=r['risk_difference']*100
        axes[1].errorbar(x,i,xerr=[[x-r['risk_simultaneous_lo']*100],[r['risk_simultaneous_hi']*100-x]],fmt='o',color='#2563eb',capsize=4)
    axes[1].axvline(0,color='grey',ls='--',lw=1)
    axes[1].set(yticks=range(3),yticklabels=[r['pair'] for r in result['pairs']],xlabel='Difference in 95%−55% response (percentage points)',title='Paired question bootstrap; simultaneous intervals')
    axes[1].invert_yaxis()
    fig.tight_layout()
    fig.savefig(out/'comparison.png',dpi=180)
    plt.close(fig)
    o = result["omnibus"]
    lines = ["# Cross-model deference comparison", "", "Post hoc analysis dated 2026-10-16. Historical analyses are unchanged. No API calls.", "",
             "Uses R1's key-audit replication without the peer-reviewed tag, Qwen3-32B and gpt-oss-120b: the same 100 questions, four controls and two repeats at each dose per model. R1 controls were collected earlier and reused; the hinted comparisons use the matching clear wording. All providers were DeepInfra.", "",
             "## Primary joint comparison", "",
             "Marginal logistic regression: follow ~ model * (cue_present + cue_present × [logit(r) − logit(.55)]). A saturated nine-cell fit permits separate control, 55%, and 95% rates for each model. Covariance clusters all models, cells and repeats by question with the CR1 finite-sample correction. These population-level slopes differ from the conditional random-intercept slopes in the historical reports; they are not own-knowledge integration weights.", "",
             f"Omnibus model × reliability interaction: Wald χ²(2) = {o['wald']:.2f}, p = {o['p']:.4g}. This tests equality of the three 55%→95% log-odds slopes, not equality of all model behavior.", "",
             "| Model | Answered: control / 55% / 95% | Follow: control / 55% / 95% | 55%→95% change (95% question-bootstrap interval) |", "| --- | --- | --- | --- |"]
    for e in result["effects"]:
        rs = [r for r in result["rates"] if r["model"]==e["model"]]
        ns = ' / '.join(str(r['n']) for r in rs)
        ps = ' / '.join(f"{100*r['followed']:.1f}%" for r in rs)
        lines.append(f"| {e['model']} | {ns} | {ps} | {100*e['dose_risk_change']:+.1f} pp ({100*e['lo']:+.1f}, {100*e['hi']:+.1f}) |")
    lines += ["", f"Pairwise p-values are Holm-adjusted across three log-odds interaction contrasts. Risk differences compare the two models' 55%→95% changes, in percentage points. Their displayed intervals use Bonferroni-adjusted bootstrap quantiles (98.33% per contrast; approximate 95% familywise coverage). All {args.bootstraps:,} bootstrap draws resample questions jointly across models and repeats.", "",
              "| Pair | Slope difference (pointwise 95%) | Holm p | Difference in dose response (simultaneous interval) |", "| --- | --- | --- | --- |"]
    for r in result["pairs"]:
        lines.append(f"| {r['pair']} | {r['estimate']:+.3f} ({r['lo']:+.3f}, {r['hi']:+.3f}) | {r['p_holm']:.4g} | {100*r['risk_difference']:+.1f} pp ({100*r['risk_simultaneous_lo']:+.1f}, {100*r['risk_simultaneous_hi']:+.1f}) |")
    common_result=result['common_question_sensitivity']
    lines += ["", "## Selection and sensitivity", "",
              f"Primary analysis conditions on answered runs ({result['n_answered']}/2400). Non-answers are not coded as incorrect or resistant. The 11 gpt-oss unparseable runs were previously identified as refusals; their historic labels remain intact. The common answered cohort has {len(common)} questions with at least one answer in all nine model/cell combinations; its interaction p = {common_result['omnibus']['p']:.4g}. This is an outcome-selected sensitivity cohort, not an independent replication.", "",
              "Worst-case 55%→95% changes if every non-answer is assigned to either following or resisting (identification bounds, not confidence intervals):"]
    for m,(lo,hi) in result['missing_outcome_dose_bounds'].items():
        lines.append(f"- {m}: {100*lo:+.1f} to {100*hi:+.1f} pp.")
    lines += ["", "## Safety interpretation", "",
              "Differences in responses to claimed source reliability are measurable on this task; baseline accuracy alone does not describe that response. Evidence for one pair does not establish all three pairwise differences. This analysis does not identify internal mechanisms, establish deception, measure rationality against calibrated external evidence, or rank overall model safety. Claimed reliability was manipulated while the planted answer was always wrong. Model versions, provider implementations and collection dates are part of the tested systems.", "",
              "The new wording experiment is specified separately in docs/CROSS_MODEL_FOLLOWUP.md. It must be evaluated without selecting wording based on its observed effects.", "",
              "## Reproduce", "", "`.venv/bin/python scripts/28_cross_model.py`", "",
              "Machine-readable analysis.json records input SHA-256 hashes, random seed, all marginal slopes, pairwise contrasts and the common-question sensitivity. pairwise.csv and rates.csv provide reusable tables. comparison.png visualizes rates and simultaneous probability-scale contrasts."]
    (out/"REPORT.md").write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()

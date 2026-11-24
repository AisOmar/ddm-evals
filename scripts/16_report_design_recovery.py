"""Build a guarded report of complete replicated screening, not Bayesian power."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/ddm-mpl')
import importlib.util,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/design_recovery'
spec=importlib.util.spec_from_file_location('suite',ROOT/'scripts/12_design_recovery.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
LABELS=dict(ddm_calibrated='DDM: pilot parameters',ddm_question_time='DDM: question timing / early stops',
            ddm_high_sdv='DDM: 4× trial drift SD',baseline_calibrated='Baseline: pilot parameters',
            baseline_correlated='Baseline: correlated question effects',baseline_contaminated='Baseline: 8% contaminants',
            ddm_lognormal_questions='DDM: positive lognormal question drift',ddm_low_variation='DDM: homogeneous limit')


def main():
    plan=json.loads((BASE/'plan.json').read_text());profiles=s.PROFILES+s.EXTENSIONS
    s.PROFILES=profiles;s.OUT=BASE/'composite';s.summarize(plan)
    comparisons=pd.read_csv(s.OUT/'comparisons.csv');expected=len(profiles)*20*2*3
    assert len(comparisons)==expected,(len(comparisons),expected)
    assert comparisons.groupby(['profile','cap','component']).size().eq(20).all()
    assert np.isfinite(comparisons[['delta','se']]).all().all()
    rates=json.loads((s.OUT/'recovery_rates.json').read_text())
    rows=[]
    for profile in profiles:
        for cap in [32768,8192]:
            x=next(x for x in rates if x['profile']==profile and x['cap']==cap)
            lo,hi=x['correct_ci'];rows.append(f"| {LABELS[profile]} | {cap:,} | {x['correct']}/20 ({lo:.0%}–{hi:.0%}) | {x['wrong']}/20 | {x['inconclusive']}/20 | {x['failures']}/20 |")
    # Observable calibration: matched caps; no claims that fitted hypotheses
    # reproduce all observed R1 features or constitute a real-data replication.
    obs=pd.read_csv(ROOT/'results/robustness/pilot_r1_with_provider.csv')
    observed=dict(profile='observed R1',replicate=-1,cap=8192,censored=171/400,accuracy=219/229)
    calibration=[observed]
    for profile in profiles:
        for rep in range(20):
            d=pd.read_csv(BASE/'data'/f'{profile}_{rep:02d}.csv')
            for cap in [8192,32768]:
                x=s.censor(d,cap);a=x[~x.censored]
                calibration.append(dict(profile=profile,replicate=rep,cap=cap,censored=float(x.censored.mean()),
                                        accuracy=float(a.correct.mean()),median_answered_tokens=float(a.rt.median()*100)))
    cal=pd.DataFrame(calibration);cal.to_csv(BASE/'observable_calibration.csv',index=False)
    calrows=[]
    for profile in profiles[:6]:
        g=cal[(cal.profile==profile)&(cal.cap==8192)]
        calrows.append(f"| {LABELS[profile]} | {g.censored.mean():.1%} | {g.accuracy.mean():.1%} |")
    # Selected hierarchical MAP checks only; do not silently turn missing or
    # invalid confirmations into successful recovery.
    selected=[]
    for profile in profiles:
        for cap in [32768,8192]:
            case=f'{profile}_00_cap{cap}';path=BASE/'scores'/f'{case}.csv';diag=BASE/'fits'/f'{case}.json'
            if not path.exists() or not diag.exists():continue
            ds=json.loads(diag.read_text())
            if not all(x.get('fit_version') in [3,4] for x in ds):continue
            d=pd.read_csv(path);q=(d.lpd_ddm_sdv_lapse_joint-d.lpd_baseline_joint).groupby(d.qid).sum()
            delta=float(q.sum());se=float(np.sqrt(len(q)*q.var(ddof=1)));valid=all(x['valid'] for x in ds)
            winner=('ddm' if delta>2*se else 'baseline' if delta< -2*se else 'inconclusive') if valid else 'fit failure'
            cf=comparisons[(comparisons.case==case)&(comparisons.component=='joint')].iloc[0]
            selected.append(dict(case=case,delta=delta,se=se,valid=valid,winner=winner,composite_winner=cf.winner))
    pd.DataFrame(selected).to_csv(BASE/'hierarchical_confirmation.csv',index=False)
    diags=[]
    for folder in ['bayesian','bayesian_dense']:
        for p in (BASE/folder/'posteriors').glob('*diagnostics.json'):
            x=json.loads(p.read_text());x['path']=str(p.relative_to(ROOT));x['valid']=x['divergences']==0 and x['max_rhat']<=1.05 and x['min_ess']>=50
            diags.append(x)
    pd.DataFrame(diags).to_csv(BASE/'bayesian_diagnostics.csv',index=False)
    # Confusion matrix includes optimizer failure as an outcome.
    fig,axes=plt.subplots(1,2,figsize=(12,6),sharey=True)
    for ax,cap in zip(axes,[32768,8192]):
        matrix=[]
        for profile in profiles:
            g=comparisons[(comparisons.profile==profile)&(comparisons.cap==cap)&(comparisons.component=='joint')]
            matrix.append([(g.winner==w).sum() for w in ['ddm','baseline','inconclusive','fit failure']])
        matrix=np.array(matrix);ax.imshow(matrix,vmin=0,vmax=20,cmap='Blues',aspect='auto')
        for (i,j),val in np.ndenumerate(matrix):ax.text(j,i,str(val),ha='center',va='center',color='white' if val>12 else '#12263a')
        ax.set_xticks(range(4),['DDM','Baseline','Tie','Fit failure']);ax.set_title(f'{cap:,}-token cap');ax.set_yticks(range(8),[LABELS[x] for x in profiles])
    fig.suptitle('Approximate model recovery: 20 independent datasets per row',fontsize=13)
    fig.tight_layout();fig.savefig(BASE/'recovery_confusion.png',dpi=180);plt.close(fig)
    passing=sum(x['valid'] for x in selected);agree=sum(x['valid'] and x['winner']==x['composite_winner'] for x in selected)
    report=f'''# Two-repeat design: realistic simulation screening

**The design is promising under the fitted model families, but reliable end-to-end Bayesian recovery has not been established. These results do not establish an accumulation mechanism or a validated power calculation for the full experiment.**

This extends the earlier, milder recovery simulations. Following [Wilson and Collins (2019)](https://elifesciences.org/articles/49547), recovery reports correct selections, opposite-family selections, inconclusive results and fitting failures, rather than counting every positive score as success. No model API calls were made.

## Design and what was fitted

160 independent simulated datasets, each with 400 questions × four conditions × two repeats (3,200 trials). Two paired views apply 32,768- and 8,192-token caps to the same underlying trials: 320 comparisons, not 320 independent datasets. The first six scenarios were specified in `results/design_recovery/plan.json`; two exploratory difficulty/parameter-regime checks were specified separately before their fits in `extensions_plan.json`. Correct-option position is balanced independently of repeat index. No positional bias was simulated.

Population hyperparameters are joint draws from the five saved R1 CV posteriors, with fresh question effects and trial noise; code prevalence is 44%. This incorporates uncertainty in fitted hypotheses, rather than fixing one convenient textbook parameter set. Question timing stress adds a common question delay (median 150 prose / 750 code tokens, log SD 0.7) and assigns independent early deadlines to 3.75% of trials; an assigned deadline yields an incomplete observation only if it actually interrupts the trace. Contaminants have lognormal length (median 2,000 tokens, log SD 2) and fair responses. Correlated baseline effects have correlation +0.6.

The primary batch uses **composite-likelihood population MAP**, fitting trial marginals and omitting within-question covariance from the fitting objective. Data retain that dependence; validation holds out entire questions, and SEs sum scores within questions. Predictions integrate population Normal effects. This is a fast screening approximation, **not the full hierarchical Bayesian fitting workflow** and not parameter recovery. It cannot identify the split between question and trial variance. Three grouped folds, two optimization starts, shared priors and the same score target are used for both models. Here joint means length and correctness for each trial, summed over held-out rows; it is not the joint probability of all eight outcomes of a question. Winner requires that score difference beyond two question-level SEs. Failed optimizations stay in the denominator. Length and correctness components, each with question-level SE, are saved alongside joint scores.

## Recovery outcomes

“Correct” means selection consistent with the generating family. In the timing, correlated-effects, contamination and positive-drift stresses, the fitted candidates need not include the exact generator; an opposite-family result illustrates the limits of a mechanism interpretation, rather than a mistake in choosing the best predictive approximation.

| Generator | Cap | Correct (95% Wilson interval) | Opposite family | Inconclusive | Fit failure |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

![Recovery confusion matrix](../results/design_recovery/recovery_confusion.png)

Twenty successes out of twenty give an interval of 83.9%–100%. Zero opposite-family selections out of twenty still permit a rate as high as 16.1% at the 95% Wilson limit; they do not certify a false-selection rate below 5%. Caps are paired and must not be pooled as independent repetitions. These intervals describe simulation variation conditional on these generators and this screening method, not uncertainty about all possible LLM behavior.

## Calibration and confirmation limits

The generators are calibrated to **fitted parameter hypotheses**, not exact reproductions of R1. At the historical 8,192 cap, R1 has 42.8% censored rows and 95.6% accuracy among answers. The table shows means over the 20 simulations; full replicate statistics are saved in `observable_calibration.csv`.

| Generator | Censored at 8,192 | Answered accuracy |
| --- | ---: | ---: |
{chr(10).join(calrows)}

Therefore favorable exact-family recovery cannot by itself establish power for the actual data-generating process. Positive lognormal question drift specifically tests the Normal latent-difficulty assumption; the homogeneous limit fixes question drift SD to 0.08, trial drift SD to zero and contamination to zero, and is a deliberate boundary case rather than an R1 estimate.

Selected hierarchical MAP confirmations: {len(selected)} complete comparisons, {passing} passing the fit flag, {agree} agreeing with the composite selection among passing checks. See `hierarchical_confirmation.csv`; missing confirmations are not counted as successes. Completed Bayesian attempts and their convergence flags are recorded in `bayesian_diagnostics.csv`. Full Bayesian confirmations are incomplete, and some completed attempts fail the Rhat/ESS criteria. Dense-mass refinements have separate checkpoints. Their raw scores must not be presented as validated recovery rates.

Numerical checks compare the simulator CDF, independent likelihood implementations, direct adaptive integration, gradients and all option schedules. The selected direct-integration checks differ by at most about 0.0003 nats; the simulator check has a maximum empirical CDF discrepancy of 1.03 percentage points at 20,000 draws and time step 0.005. The simulation's infinite latent-time sentinel means “not resolved before the maximum simulated deadline,” not a literally infinite decision time. Numerical pilot approximations that failed validation were archived and excluded from the recovery rates.

## Decision

In the 32,768-cap screen, the two calibrated families each recover in 20/20 datasets. Positive lognormal question drift recovers in only {next(x['correct'] for x in rates if x['profile']=='ddm_lognormal_questions' and x['cap']==32768)}/20; this generator changes the latent difficulty distribution while retaining a DDM decision process. That is a direct warning about interpreting model preference as mechanism evidence. Fitting failures in the homogeneous limit are computational failures, and should not be relabeled as statistical indistinguishability.

Keep the modeling idea, but **do not claim that the proposed experiment is already validated for reliable Bayesian discrimination**. The simulation screen establishes conditional distinguishability of statistical families. Before launching the full collection, complete diagnostic-passing Bayesian recovery on realistic repeated datasets, examine the observed-versus-simulated discrepancies, and check alternative difficulty/outlier assumptions. A DDM victory establishes neither unique drift variability nor an internal accumulation mechanism.

## Reproduction and artifacts

Run from the repository root:

```bash
.venv/bin/python scripts/12_design_recovery.py --stage generate
.venv/bin/python scripts/12_design_recovery.py --stage generate --profile ddm_lognormal_questions
.venv/bin/python scripts/12_design_recovery.py --stage generate --profile ddm_low_variation
.venv/bin/python scripts/13_validate_design_recovery.py
.venv/bin/python scripts/14_recovery_screen.py
.venv/bin/python scripts/16_report_design_recovery.py
```

`12_design_recovery.py --rep 0 --profile ...` runs the more expensive hierarchical MAP check. `15_bayesian_design_recovery.py --profile ddm_calibrated` (or `baseline_calibrated`) runs Bayesian confirmation; it is checkpointed separately and may require further diagnostic refinement. Previously started `12_power_simulation.py` experiments under `results/power` are separate Bayesian checks, not independent replications of this batch; incomplete or diagnostic-failing comparisons must not be pooled into these rates.

[Comparison scores and question-level uncertainty](../results/design_recovery/composite/comparisons.csv), [recovery counts and intervals](../results/design_recovery/composite/recovery_rates.json), [observable calibration](../results/design_recovery/observable_calibration.csv), [numerical checks](../results/design_recovery/numerical_validation.json), [hierarchical confirmations](../results/design_recovery/hierarchical_confirmation.csv), [Bayesian diagnostics](../results/design_recovery/bayesian_diagnostics.csv). Generator metadata, source posterior hashes, per-fold parameters, diagnostics and per-trial scores are preserved under `results/design_recovery`.
'''
    (ROOT/'docs/DESIGN_RECOVERY.md').write_text(report)
    target=ROOT/'docs/FINAL_REPORT.md';text=target.read_text();start='<!-- DESIGN_RECOVERY_START -->';end='<!-- DESIGN_RECOVERY_END -->'
    block=f'''{start}
## Realistic design recovery (2026-10-09)

A new offline screen simulates 160 independent datasets at 400 questions × four conditions × two repeats, with paired 8,192/32,768 caps, pilot-posterior parameter uncertainty, timing/outlier stresses and alternative difficulty regimes. It reports correct/opposite-family selection, ties and fit failures, with question-level score uncertainty and Monte Carlo intervals. **This uses composite-likelihood screening; reliable full Bayesian power remains unvalidated.** Some completed Bayesian attempts fail convergence checks. Keep the modeling idea, but complete that validation before treating the proposed collection as ready or assigning a mechanism. See [the full design-recovery report](DESIGN_RECOVERY.md) for results, assumptions and reproducible commands.

{end}

'''
    if start in text:text=text[:text.index(start)]+block+text[text.index(end)+len(end):].lstrip('\n')
    else:text=text.replace('## Recommended next pre-registration',block+'## Recommended next pre-registration')
    target.write_text(text)
    s.dump(BASE/'report_provenance.json',dict(comparisons=len(comparisons),independent_datasets=160,
             code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'scripts').glob('*recovery*.py')}))
    print('Complete screening report:',ROOT/'docs/DESIGN_RECOVERY.md')


if __name__=='__main__':main()

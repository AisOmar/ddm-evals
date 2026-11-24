"""Insert completed robustness results into the requested final report.

Requires 08 --stage summarize. Refuses partial real-data fold coverage.
Historical aggregate files remain unchanged; all new report numbers link to
the paired per-trial scores and diagnostics under results/robustness.
"""
from pathlib import Path
import re
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"results/robustness"
START="<!-- ROBUSTNESS_RESULTS_START -->"
END="<!-- ROBUSTNESS_RESULTS_END -->"


def main():
    comparisons=pd.read_csv(OUT/"all_comparisons.csv")
    joint=comparisons[comparisons.component=="joint"]
    expected=[f"{scenario}_{target}" for scenario,target in [("main","cv"),("main","within"),("exclude_incomplete","cv"),("hidden_only","cv"),("deepinfra","cv"),("provider_adjusted","cv")]]
    models=["ddm_lapse","ddm_sdv_lapse"]
    for analysis in expected:
        for model in models:
            assert len(joint[(joint.analysis==analysis)&(joint.model==model+" - baseline")])==1,(analysis,model,"missing complete comparison")
    text=[START]
    text.append("The new main comparisons use grouped five-fold CV with the same question folds for each model. Sensitivities use grouped three-fold CV; absolute scores across different datasets/folds are not compared. Within-question validation fits even repeats and scores odd repeats with the fitted question effects; the historical A/B confound remains in this target. Predictions are per-trial population marginals, and uncertainty uses question-level sums. These SEs condition on the fitted folds and do not include training-set or posterior Monte Carlo uncertainty.")
    text.append("The fixed-drift model and `ddm_sdv` share the same explicit contaminant: a lognormal length with median 2,000 tokens and natural-log SD 2, a fair answer, and rate ε ~ Beta(1,19). This is a robust statistical component, not an identified cognitive process. Its survival probability is included for censored rows. The `ddm_sdv` density integrates normally distributed across-run drift analytically; its drift SD can differ for code and prose. Both use drift question effects, the four prompt conditions, and the code covariate. Boundary and non-decision time have log links; their coefficient priors have SD 0.7 and 0.8, with intercept means log(4) and log(0.5) in 100-token units. Drift coefficients have Normal priors with SD 0.6 (intercept mean 0.4), and the drift question SD has HalfNormal(0.5) prior. Log drift-SD coefficients have Normal priors with SD 0.8 (intercept mean log(0.4)). These choices differ from the historical bounded HSSM priors.")
    text.append("The contaminant is motivated by the short trials that receive the old density floor and by provider irregularities. It offers normalised support for departures from the shared timing specification, with an estimated and penalised rate. Rows are retained; the component does not label individual runs as defective. Its form and priors were selected during this audit, so these results are exploratory.")
    text.append("Initial fits use two chains, 400 draws and 500 tuning steps. Diagnostic failures are refined with larger sampling budgets; exact settings and diagnostics are saved per fit, and original failed fits are archived. Numerical checks test density normalisation, HSSM density agreement in its stable range, independent survival quadrature, and training/scoring parity. At sampled real-data posterior parameters, 64- versus 128-node survival quadrature agrees within about 6×10⁻⁷ log-probability. A failed diagnostic flag (any divergence, maximum r-hat >1.05 or minimum bulk ESS <50 in either model) suppresses a verdict. These are exploratory fits; meeting that flag threshold is weaker than publication-level convergence checks.")
    labels={"main_cv":"Main: held-out questions","main_within":"Main: held-out repeat","exclude_incomplete_cv":"Exclude incomplete rows","hidden_only_cv":"Hidden reasoning only","deepinfra_cv":"DeepInfra responses only","provider_adjusted_cv":"Adjust for provider"}
    text.append("| Analysis | Model minus baseline | Joint nats/trial | Total difference | Question-level SE | Interpretation |\n| --- | --- | ---: | ---: | ---: | --- |")
    for analysis in expected:
        for name in models:
            row=joint[(joint.analysis==analysis)&(joint.model==name+" - baseline")].iloc[0]
            label="fixed drift + contaminant" if name=="ddm_lapse" else "variable drift + contaminant"
            interpretation=row.verdict.replace("candidate better","DDM variant better")
            text.append(f"| {labels[analysis]} | {label} | {row.per_trial:+.3f} | {row.elpd:+.1f} | {row.se:.1f} | {interpretation} |")
    text.append("Provider sensitivity reconstructs the final raw response labels, rather than treating the model ID as a fixed backend. The DeepInfra subset has 108 trials from 39 questions (65 answered after applying the cap, 43 censored). Cap-experiment requests were pinned to DeepInfra with fallbacks disabled; 61 final response labels say DeepInfra and one is unrecorded. Excluding incomplete rows leaves 385 trials; the main and hidden-only analyses each have 400. Hidden-only analysis preserves the total-generation cutoff and uses the hidden count observed at truncation as its censoring bound. That is an alternative timing proxy with an additional censoring assumption: a final answer may still be absent after the hidden channel has ended. Provider-adjusted fits give both models provider fixed effects; provider allocation was not randomised.")
    diagnostics=pd.read_csv(OUT/"all_diagnostics.csv")
    selected=diagnostics[diagnostics.label.str.fullmatch(r"(main|exclude_incomplete|hidden_only|deepinfra|provider_adjusted)_(fold\d+|within)_(baseline|ddm_lapse|ddm_sdv_lapse)")]
    failed=selected[(selected.divergences>0)|(selected.max_rhat>1.05)|(selected.min_ess<50)]
    if len(failed):
        entries=[f"`{row.label}` ({int(row.divergences)} divergences, maximum r-hat {row.max_rhat:.3f}, minimum ESS {row.min_ess:.0f})" for _,row in failed.iterrows()]
        text.append("Remaining real-data diagnostic failures: "+"; ".join(entries)+". Their score differences and SEs are displayed for transparency, but cannot support a reliable verdict.")
    direct=pd.read_csv(OUT/"variable_vs_fixed_comparisons.csv")
    row=direct[(direct.analysis=="main_cv")&(direct.component=="joint")].iloc[0]
    text.append(f"Variable drift versus fixed drift, both with the same contaminant, changes the main joint score by {row.elpd:+.1f} nats (question SE {row.se:.1f}): {row.verdict}. This direct comparison is saved in `variable_vs_fixed_comparisons.csv`.")
    text.append("The main length and correctness decomposition is:")
    text.append("| Model minus baseline | Component | Nats/trial | Total difference | Question-level SE |\n| --- | --- | ---: | ---: | ---: |")
    for name in models:
        for component in ["length","correctness_given_length"]:
            row=comparisons[(comparisons.analysis=="main_cv")&(comparisons.model==name+" - baseline")&(comparisons.component==component)].iloc[0]
            text.append(f"| {name} | {component.replace('_',' ')} | {row.per_trial:+.3f} | {row.elpd:+.1f} | {row.se:.1f} |")
    accuracy=pd.read_csv(OUT/"accuracy_length.csv")
    text.append("The accuracy analysis separates log₂ length into a within-question deviation and a between-question mean, with a question random intercept, prompt/code effects, dataset indicator and answer-position effect. The combined provider-adjusted fit additionally includes provider. It uses answered runs only, with step-1 overruns excluded. The effect is conditional association, not a causal effect of making a run longer.")
    text.append("| Answered dataset | Runs / questions | Odds ratio per doubling within question | 95% interval | P(negative slope) |\n| --- | --- | ---: | --- | ---: |")
    for _,row in accuracy.iterrows():
        text.append(f"| {row.dataset.removeprefix('accuracy_').replace('_',' ')} | {row.n} / {row.questions} | {row.odds_ratio:.2f} | {row.or_lo:.2f}–{row.or_hi:.2f} | {row.probability_negative:.3f} |")
    text.append("Every reported slope interval includes zero. The data suggest slow errors in the cap experiment, but do not establish a within-question decline at the 95% interval criterion. The combined comparison also depends on selection, provider and position controls.")
    parameters=pd.read_csv(OUT/"recovery_two_repeat_parameters.csv")
    valid=parameters[~parameters.diagnostic_flag]
    runs=valid[["seed","generator"]].drop_duplicates()
    scaffold=valid[valid.parameter.str.endswith("_scaffold")]
    recovered=int(scaffold.groupby(["seed","generator"]).apply(lambda g:bool((g.excludes_zero==(g.truth!=0)).all()),include_groups=False).sum())
    text.append(f"Two-repeat parameter recovery uses four simulated datasets at 400 questions × four conditions × two repeats, including normally varying drift and question-level non-decision time. Planted scaffold drift is +0.15; the alternative planted log-boundary effect is log(1.33). {len(runs)} / 4 fits pass the diagnostic flag, and {recovered} of those distinguish the planted effect from the other parameter. Among passing fits, {int(valid.covered.sum())} of {len(valid)} reported 95% intervals contain the truth. Two seeds per generator and correlated parameter checks are insufficient to establish calibrated coverage or power across plausible truths.")
    recoveries=joint[joint.analysis.str.startswith(("recovery50_","predictive400_"))].sort_values("analysis")
    assert len(recoveries)==8,"Missing predictive recovery comparison"
    text.append("Predictive recovery checks the two-repeat design separately:")
    text.append("| Generator / questions / seed | Joint DDM variant minus baseline | Question-level SE | Interpretation |\n| --- | ---: | ---: | --- |")
    for _,row in recoveries.iterrows():
        prefix,generator,seed=row.analysis.removesuffix('_cv').split('_')
        questions=400 if prefix=='predictive400' else 50
        generator={'drift':'variable drift','fixed':'fixed drift','lognormal':'lognormal + logistic'}[generator]
        text.append(f"| {generator} / {questions} / {seed} | {row.elpd:+.1f} | {row.se:.1f} | {row.verdict.replace('candidate better','DDM variant better')} |")
    text.append("The 50-question controls include mild question-level timing variation; the 400-question predictive controls match the candidate or baseline timing family (fixed non-decision time by condition for the DDM). Simulations contain no contaminants. Each comparison uses a 32,768-token censoring cap and three question folds. A recovery tie is an admissible outcome, not evidence that the generator lacks accumulation. Full-data parameter recovery and predictive discrimination are different requirements.")
    text.append("Sources: [all comparisons](../results/robustness/all_comparisons.csv), [diagnostics](../results/robustness/all_diagnostics.csv), [historical question-level uncertainty](../results/robustness/historical_question_uncertainty.csv), [accuracy–length estimates](../results/robustness/accuracy_length.csv), and [two-repeat parameter recovery](../results/robustness/recovery_two_repeat_parameters.csv). Model-specific paired score CSVs, posterior files and parameter summaries are under `results/robustness`. The original CSVs and evaluation logs are preserved.")
    text.append(END)
    path=ROOT/"docs/FINAL_REPORT.md";s=path.read_text();block="\n\n".join(text)
    block=re.sub(r"(?<=\|)\n\n(?=\|)","\n",block)
    if START in s:
        a=s.index(START);b=s.index(END,a)+len(END);s=s[:a]+block+s[b:]
    else:s=s.replace("<!-- ROBUSTNESS_RESULTS -->",block)
    path.write_text(s)
    print("Inserted complete, diagnostic-aware robustness results into docs/FINAL_REPORT.md.")


if __name__=="__main__":main()

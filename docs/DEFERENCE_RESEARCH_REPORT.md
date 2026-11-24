# Claimed Source Reliability and Answer Key Deference in Three Language Models

Research report draft, 2026-10-19. Completed experiments provide the main evidence; the paused 623-response extension and trace audit are exploratory. Protocols were specified in local timestamped files, not an external registration service. This report focuses on the advice and deference experiments; the earlier token-length and diffusion-model work remains in [FINAL_REPORT.md](FINAL_REPORT.md).

On two-choice cybersecurity recall questions, answer-key metadata can change model answers, and the effect of numerical reliability claims differs across three tested model deployments. The strongest cross-model evidence comes from a completed wording follow-up: raising a wrong key's stated reliability from 55% to 95% increased following by approximately ten percentage points for R1 and gpt-oss, while Qwen3 showed little average change. These findings extend existing advice-taking research in a specific task and presentation setting. They do not establish rational trust or an overall safety ranking.

## Questions and experimental setting

The project asks how an answer-shaped cue influences a model's response, whether numerical claims change that influence, and how the returned explanation describes its use of the cue. The tested systems are DeepSeek-R1-0528, Qwen3-32B, and gpt-oss-120b, with the relevant deference collections pinned to DeepInfra through OpenRouter. Conclusions apply to these deployments and prompts rather than every system sharing a model family name.

The completed deference experiments use 100 two-choice recall questions and planted wrong keys. Separate control responses measure behavior without the key. The later wording follow-up collects fresh controls and reference wording alongside two new paraphrases. Questions recur across experiments, and some earlier controls are reused. Collections must not be added together as independent replications or treated as thousands of independent questions. Detailed counts, source reuse, settings, and exclusions remain in the linked experiment reports.

## Completed evidence

The initial [hint experiment](../results/hint_injection/REPORT.md) collected 300 responses, with 297 answered and three truncated. R1 selected the planted wrong option in 12.1% of answered controls, 16.2% with a user-opinion cue, and 50.5% with a metadata answer-key cue. The fitted metadata-minus-control difference was +37 percentage points with a 95% interval of +27 to +48. The user-opinion difference was inconclusive. This establishes susceptibility to the tested metadata package without establishing general immunity to user pressure.

The initial reliability wording was often interpreted as question difficulty or solver success rather than key accuracy. A [clear-wording replication](../results/deference/replication/REPORT.md) both rephrased the audit sentence and removed a peer-reviewed tag. Wrong-option following fell to 13.2% at 55% and 26.9% at 95%, against 9.8% in reused controls. Because two presentation elements changed, the initial reduction cannot be attributed entirely to wording. A subsequent [tag check](../results/deference/peer_tag/REPORT.md) restored the tag while retaining clear wording and observed following rates of 17.2% and 37.8%. These stages show sensitivity to the presentation package; they do not establish unrestricted robustness to paraphrasing.

The [direct cross-model comparison](../results/deference/cross_model/REPORT.md) was post hoc. It found a model-by-reliability interaction, with R1's change exceeding Qwen3's by 15.7 percentage points, simultaneous interval +6.2 to +25.6. This motivated a prospective local specification for the completed wording follow-up.

The [wording follow-up](../results/deference/wording_followup/REPORT.md) collected all 2,100 planned responses on the same 100 questions. There were 2,089 answered responses, six R1 truncations, and five gpt-oss refusals. The common complete-answer cohort contains 97 questions. The primary model-by-reliability test gives Wald chi-squared(2)=9.37, p=0.00924.

| Model | Change in wrong-key following from 55% to 95% | Pointwise 95% question-bootstrap interval |
| --- | ---: | ---: |
| DeepSeek-R1-0528 | +9.8 pp | +5.2 to +14.9 |
| Qwen3-32B | −1.0 pp | −7.2 to +5.2 |
| gpt-oss-120b | +9.3 pp | +4.1 to +14.4 |

The R1-minus-Qwen difference is +10.8 pp, simultaneous interval +2.6 to +19.6; the gpt-oss-minus-Qwen difference is +10.3 pp, +0.5 to +20.1. R1 versus gpt-oss remains inconclusive. Intervals for the individual wording-specific pair comparisons remain inconclusive after correction across six comparisons. Thus the average response across the two paraphrases is supported, while a claim that each wording independently establishes every asserted model difference is unsupported.

The results separate baseline competence, influence of a key's presence, and sensitivity to its stated reliability. In the earlier clear-wording comparison, Qwen3's wrong-option selection was 10.5% in controls versus 27.5% and 25.5% with wrong keys. Its near-zero reliability slope does not mean the key had little influence.

## Position relative to prior research

Reliability-dependent advice taking and departures from Bayesian confidence updating have already been studied by [Kumaran et al.](https://www.nature.com/articles/s42256-026-01217-9). Our measurements of binary answers and separate controls do not reproduce their calibrated-logit analysis. A [medical factorial preprint](https://www.medrxiv.org/content/10.64898/2026.08.28.26361634v1) also crosses stated source accuracy and suggestion correctness with attributed credentials. This rules out claiming that the paused extension introduces that general factorial idea.

The contribution is a specific replication and extension using these models, cybersecurity recall questions, answer-key presentation checks, and a completed follow-up with new paraphrases. The [literature comparison](DEFERENCE_LITERATURE_COMPARISON.md) initially covered seven primary sources and now includes an eighth close source identified during the three-direction follow-up search, with comparison limits and the abstract-only access limitation for the medical preprint. A systematic review and full-method comparison remain necessary before a strong external novelty claim.

## The paused correct and wrong key extension

The [frozen protocol](TRUST_FOLLOWUP.md) samples 300 unused project questions and crosses actual key correctness, a 55% or 95% claim, and two wordings in each model. Two fresh no-key controls bring the total to 9,000 responses. Correctness and claimed reliability are independent: the study tests claimed credibility in a balanced mixture, not a truly 55%- or 95%-accurate source.

Collection is paused by user request at 623 valid provider responses: 615 answered, six refused, and two truncated. All valid responses are from DeepInfra. The 623 responses cover 265 questions, leaving no complete eight-condition hinted block for any model. Only 26 exact same-question, same-model, same-wording and same-key-correctness comparisons of 55% against 95% are available: 24 unchanged correctness outcomes, one improvement, and one deterioration.

| Model | No key | Correct key 55% | Correct key 95% | Wrong key 55% | Wrong key 95% |
| --- | ---: | ---: | ---: | ---: | ---: |
| R1 | 93.8% | 95.2% | 97.4% | 66.7% | 60.5% |
| Qwen3 | 91.8% | 96.9% | 93.0% | 56.5% | 70.5% |
| gpt-oss | 86.5% | 91.7% | 93.5% | 75.5% | 58.5% |

These are answered-response descriptive rates pooled across wordings and different question mixtures, not estimates of the frozen paired endpoint. Hinted cells contain 32–49 answered responses. The [exploratory figure](../results/deference/trust_planning/exploratory/deep_20261019T210911Z/accuracy_overview.png) displays pointwise question-cluster bootstrap intervals without multiplicity correction. Rates can suggest hypotheses but cannot establish net harm or reverse the completed model comparison.

Some same-question controls and hints are available. For example, six of 19 Qwen3 wrong-key answers with an available answered control were incorrect while the corresponding control average was fully correct. The 19 responses span 14 questions. Three of 17 corresponding correct-key answers improved over a fully incorrect control average. These independent stochastic calls show both helpful and harmful observed discordances; they do not identify an individual model's counterfactual answer or latent knowledge.

Control accuracy is high in the collected sample, leaving less headroom for helpful gains than for harmful losses. That asymmetry is a property of this sample and benchmark. Deployment risk depends on task difficulty and actual source correctness, which this incomplete balanced study cannot estimate.

## What explanations add

The original completed hint experiment found cue acknowledgment in all 38 metadata cases with a wrong-key-following response and a control response that did not select that wrong option, using a text rule and hand inspection. This narrow acknowledgment result does not establish general chain-of-thought faithfulness. It shows that visible acknowledgment can accompany an undesirable answer.

The [new systematic audit](TRACE_AUDIT_RESULTS.md) examines 36 explanations balanced across model, key correctness, and final correctness. An AI analyst used anonymous IDs during first-pass coding, retaining complete explanations and masking scored metadata. Seventeen explanations discuss what the task expects about using the key, 17 evaluate credibility or weigh source against factual evidence, and 16 identify a factual-candidate conflict. These overlapping codes characterize the selected sample only.

Twelve explanations end by explicitly rejecting the key. Seven reject wrong keys and answer correctly; five reject correct keys and answer incorrectly against the benchmark. Four end in explicit deference despite an alternative, all with wrong keys in this sample. Seven cases carry ambiguous-coding flags. This supports separating task interpretation, source assessment, and selection of an answer. It does not establish their causal order or prevalence.

An additional post-reading code flags perceived problems with option fit in 12 traces on ten questions. Explanations sometimes describe both options as valid, overlapping, or inconsistent with the stem. These observations require independent item adjudication before treating them as benchmark errors. The audit cannot use model explanations as ground truth about the items they answer.

Token length also fails to identify a reliable strategy. In the paused R1 sample, median API output usage is 625 tokens without a key and 1,428 with a wrong 95% key. Within the latter cell it is 2,218 among wrong-key-following responses versus 1,357 among resistant responses. These unmatched descriptions do not establish an effect of reasoning length; API output usage is not a uniformly defined internal reasoning measure.

## Safety interpretation and limits

The completed experiments support evaluating a model's response to source presentation in addition to its ordinary benchmark accuracy. They also show why source acknowledgment, a flat reliability slope, lengthy explanations, or rejection of a supplied key cannot each serve as a standalone safety criterion. Selective use of correct and incorrect advice is the relevant behavioral objective.

The task-interpretation audit motivates testing whether an explicit instruction to treat a key as fallible evidence changes behavior. It does not establish an instruction-hierarchy vulnerability: the present study did not vary message privilege or test tool-mediated attacks. The supplied reliability is a claim rather than demonstrated history, controls are noisy, returned explanations need not reveal internal causes, and benchmark contamination is unknown. Cybersecurity answer accuracy itself is not an overall safety metric; refusals are reported separately and are not scored as successful resistance to wrong keys.

The existing data support a focused replication-and-extension report. They do not support a ranking of overall model safety, rational calibration, deliberate deception, internal evidence accumulation, or a completed estimate of net accuracy benefit from advice.

## Analysis disclosure and next decisions

The frozen extension specified effect inspection after full collection. At the user's explicit request, an exploratory interim analysis inspected 550 responses on 2026-10-19, followed by a 623-response analysis and the present trace audit. These are deviations from the original inspection timing and must be disclosed in any eventual report. The sample size and frozen prompts were not changed; the collection was stopped by user request. Resuming would not restore an uninspected history. The completed earlier experiments are unaffected by this later interim inspection.

The immediate work requires no additional model calls: obtain an independent coding check and adjudicate the flagged question options using original items and authoritative references. If the goal remains the balanced net effect, a later authorized restart can complete the frozen design after reliable collection automation is available. If task interpretation becomes the goal, a separate prospective protocol should manipulate that instruction while retaining correct and wrong advice and controlling question ambiguity. Neither action is launched by this report.

The local audit scripts validate selection, exact evidence quotations, coverage, and paused status. Source hashes, raw responses, exploratory outputs, and coding records remain in `results/deference/trust_planning/exploratory/`. The collection runner's `effects_analyzed: false` refers to its blocked final-analysis path; it must not be read as denying the separately documented exploratory inspections.

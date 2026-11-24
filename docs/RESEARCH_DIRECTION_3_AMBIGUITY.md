# Does Question Ambiguity Change Susceptibility to Advice

Research assessment and review packet, updated after independent AI review. Primary references support some concerns about the retained answer options, while also refuting one model-expressed concern. This establishes a need for item adjudication; it does not yet establish an association or causal interaction between ambiguity and deference.

## Prior work and the specific gap

[Cole et al. 2023](https://arxiv.org/abs/2305.14613) study selective answering under ambiguity, distinguishing uncertainty about an answer from uncertainty about a question's interpretation. [Knowing but Not Showing 2026](https://arxiv.org/abs/2605.25284) examines whether recognizing ambiguity produces clarifying questions. These works mean that ambiguity detection or selective answering alone is not a new research topic.

The proposed project-specific question is whether independently assessed semantic ambiguity changes the effect of a supplied answer key, and whether disambiguating the question improves selective use of correct and incorrect advice. It must distinguish actual item ambiguity, factual difficulty, and a model merely claiming uncertainty.

## Evidence possible now

The previous trace audit flagged 12 explanations concerning ten questions. That was an outcome-balanced sample selected after model responses existed. It cannot estimate benchmark prevalence or an ambiguity-by-advice effect. The offline review packet contains those ten questions and ten deterministic random other paused-study questions, with original four-option items and the retained two-choice options. Official keys, model outcomes, and flag status are absent from the review file and retained in a separate sidecar.

A source-supported first pass examines four flagged cases. This pass is by the same AI analyst and is not independent adjudication.

| Case | Primary-source evidence | Preliminary assessment |
| --- | --- | --- |
| Android screenshot item | Android's [official adb documentation](https://developer.android.com/tools/adb#screencap) describes both saving a screenshot on the device and streaming it to a local file. Both retained alternatives implement those documented approaches. | Supported overlap under a stem asking only which command captures a screenshot; destination is unspecified. The original four-option item already contains these alternatives, so this is not necessarily a defect introduced by the two-choice transformation. |
| Shor capability item | [NISTIR 7856](https://nvlpubs.nist.gov/nistpubs/ir/2012/nist.ir.7856.pdf) discusses quantum attacks on RSA and other public-key systems. The retained alternatives state a broad capability and a specific RSA capability. | The RSA alternative is nested within the broad alternative; ordinary literal readings can make both true. This is a semantic concern even if a test intended the more comprehensive answer. |
| No-direct-interaction network item | Nmap's [banner documentation](https://nmap.org/nsedoc/scripts/banner.html) describes making a connection; its [SNMP documentation](https://nmap.org/nsedoc/scripts/snmp-info.html) describes a request/probe. | Under the conventional active techniques represented by these references, neither retained option clearly satisfies a literal no-direct-interaction requirement. This supports a stem/option mismatch concern, not a universal ranking of detectability. |
| Token-privilege item | The vendor's [documentation](https://hstechdocs.helpsystems.com/manuals/cobaltstrike/current/userguide/content/topics/post-exploitation_privilege-escalation.htm) explicitly identifies the retained `getprivs` option as enabling assigned token privileges. | The explanation's claim that the relevant operation is missing is not substantiated. A model-expressed option concern can be a factual mistake rather than an item defect. |

The initial four-case pass has been superseded by source checks of all 20 items, a fresh-context AI review, and recorded adjudication: seven retain candidates, eleven repairs, and two exclusions. The two reviews agreed on overall disposition for 19/20 items. A separately masked validation accepts all 20 rewritten candidates. See [current review results](REVIEWED_PACKET_RESULTS.md). No original benchmark key or frozen dataset has changed, and no original treatment effects were recomputed after selecting exclusions.

## Independent adjudication

Two domain reviewers should first assess masked original and retained options without model responses. Code unique correct answer, semantic overlap, sufficient context, version dependence, and factual difficulty separately, retaining unresolved cases. Review original four-option quality and the effect of removing alternatives as separate questions. Resolve disagreements using sources and record both initial judgments before adjudication. In the reviewed set, report agreement and uncertainty; do not extrapolate prevalence from this deliberately enriched sample.

The random comparison items were reviewed together with the previously flagged items; inclusion as a random comparison does not certify clarity. Models' error rates or expressed uncertainty must not determine the ambiguity label. Do not infer a benchmark error solely from an explanation or discard a question because its effect estimate is inconvenient.

## Prospective paired experiment

After independent review, construct matched original and disambiguated versions of selected items, keeping their factual topic and answer options constant where possible. Validate that each repaired version has a uniquely supported answer. For each version collect no-advice, correct-advice, and wrong-advice conditions on the same pinned models, balancing option order and randomizing within complete item blocks.

Disambiguation should add the missing scope or context rather than state the answer or disproportionately favor one option through copied wording. For an overlapping-answer item, it may be necessary to replace a distractor; analyze those changes separately from stem-only repairs. Exclude irreparable items prospectively, not after examining model outcomes.

For no-key and wrong-key conditions, define the wrong-advice accuracy loss as baseline accuracy minus wrong-key accuracy. The primary contrast is that loss in the original version minus the loss in the repaired version. A positive interaction would indicate a larger advice-associated loss before repair, conditional on the specified rewrite. Report correct-advice gains as a paired safeguard, baseline difficulty changes, and non-answers. Cluster uncertainty by original item across versions, models, and repeats.

Because the original version may genuinely have multiple valid answers, report two explicitly different outcomes: agreement with the original benchmark key and correctness under a reviewer-adjudicated acceptable-answer set. A comparison based on the first is an effect on benchmark scoring; a comparison based on the second concerns semantic correctness. Never label a source hint “wrong” when it is acceptable under that version's adjudicated answer set. Where the binary pair has no unambiguously wrong option, the correctness-by-advice factorial is not identifiable as designed: use that item in a separate ambiguous-answer behavior analysis or replace it prospectively. Do not force a causal harmful-advice interpretation onto it.

There is no fixed full sample size yet. A small reviewed item pilot can estimate variance and check whether the intervention preserves the underlying factual task; simulation must then size the interaction, not just a main accuracy difference. Prompt repair can change difficulty, so even a positive result would not uniquely identify an internal authority mechanism.

## Artifacts and remaining work

[`scripts/39_ambiguity_review_packet.py`](../scripts/39_ambiguity_review_packet.py) generated the [`review packet`](../results/research_directions/ambiguity_review/). `masked_items.jsonl` contains the 20 items, `independent_review_template.csv` is unfilled, and `keys_and_selection.csv` is a separate unmasking file. `preliminary_source_review.json` records the four first-pass cases and citations. No independent reviewers have completed the packet, and no new model calls have been made.

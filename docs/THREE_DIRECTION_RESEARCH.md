# Research Results and Plans for Three Follow Up Studies

The initial offline research phase was followed by an independent AI question review and a separately authorized 240-response instruction pilot. All 240 responses were delivered and parsed for about $0.02. The previous collection remains paused at 623/9,000. [The pilot results](REVIEWED_PILOT_RESULTS.md) show a descriptive instruction pattern, not demonstrated efficacy or safety.

| Direction | Work completed now | What the evidence supports | What remains |
| --- | --- | --- | --- |
| [Explicit evidence instructions](RESEARCH_DIRECTION_1_INSTRUCTIONS.md) | Prior-work comparison, six-cell design, separate masked question validation, and completed 240-call feasibility pilot | Feasible delivery and answer formatting; promising descriptive gpt-oss pattern, no established efficacy | Fresh question set, human domain validation, full close-paper methods check, power simulation, justified preservation margin, and separate full-study decision |
| [Reasoning-text monitoring](RESEARCH_DIRECTION_2_MONITORING.md) | Fixed-feature models trained on completed data and evaluated on distinct paused-study questions; grouped validation and uncertainty | Moderate end-of-trace predictive signal, with no clear pooled early-prefix gain | Untouched validation, ambiguity-aware labels, cross-model robustness, and a separate intervention test |
| [Ambiguity and advice](RESEARCH_DIRECTION_3_AMBIGUITY.md) | Source checks and fresh-context AI review of all 20 original items; recorded adjudication and validation of 20 revised candidates | Some option-fit concerns have source support, while one concern is contradicted by vendor documentation | Human domain review and a design identifying truly correct/wrong advice under each version; several pilot revisions replace the original task |

## Literature position

All three directions have substantial predecessors. A newly identified close study, [Kumar and Chopra 2026](https://arxiv.org/abs/2609.37616), directly distinguishes source deference from user agreement. The first direction should therefore test selective improvement from a specific instruction intervention, rather than claim the distinction itself as new. Related medical framing work also makes a blanket framing-novelty claim inappropriate.

For monitoring, the relevant contribution would be a carefully validated transfer result and a separation between diagnosis and early warning. For ambiguity, it would be the interaction with advice under independently adjudicated items; ambiguity detection alone is already established. The linked direction documents distinguish full-text sources from indexed-primary-text access and describe unresolved literature-review limits.

## New offline finding on monitoring

The evaluation trains on 1,195 answered hinted responses from 100 completed-study questions and tests on 259 wrong-key responses from 171 different questions. There is no overlap in IDs or normalized question text. Labels are observed wrong-key following, which equals benchmark error here; they do not establish causal influence on a response. The analyst had already inspected aggregate effects and some examples from the test collection, so the evaluation remains exploratory.

Using only model, wording, and claimed reliability gives AUROC 0.539. Adding available-text length gives 0.583; adding uncertainty gives 0.642; combining source, conflict, and task-language features gives 0.679. The combined model's pointwise 95% question-bootstrap interval is 0.604–0.752, conditional on the fitted model. At a review budget of 52/259 responses it catches 35/91 wrong-key-following answers and flags 17 resistant answers. It misses most positives and is not a deployed safety gate.

Using only the first 80 words of continuing traces gives AUROC 0.580 versus 0.535 for context, with the improvement interval including zero. Its probability calibration is also worse by Brier score. Full-trace classification can exploit how the reasoning ended; it cannot be presented as an early-warning success. These results make the end-of-trace diagnostic direction more plausible than the current early-prefix approach.

## New evidence about question quality

The Android documentation supports both retained screenshot options. The Shor item uses nested broad/specific capabilities. The conventional methods in the network item do not clearly fit its no-direct-interaction requirement. These are source-supported first-pass concerns. In contrast, a vendor reference supports the token-privilege option that one model explanation treated as missing. This counterexample shows why model uncertainty cannot itself adjudicate question quality.

The review packet enriches for previously flagged cases and cannot estimate prevalence. All 20 originals now have fresh-context AI review: seven retain candidates, eleven repairs, and two exclusions, with 19/20 overall-disposition agreement with the original analyst. All 20 revised candidates have separately masked validation and matching supported answer indexes. This is independent AI review, not human validation. Nothing has been removed from the original study, and its existing effects have not been recomputed after selecting exclusions.

## Next research decisions

The separate instruction pilot completed all 240 calls and passed its feasibility gates. Wrong-advice accuracy was 10/20 versus 20/20 under ordinary versus explicit instruction for gpt-oss, and 17/20 versus 18/20 for Qwen3. Correct-advice accuracy was 20/20 in both gpt-oss conditions and 20/20 versus 19/20 for Qwen3. These are descriptive counts on a small convenience set, with near-ceiling no-advice accuracy; they do not establish efficacy, preservation, or a mechanism.

Before a larger run, source a fresh, independently reviewed question set with more difficulty variation, exclude all pilot originals and rewrites, check the closest papers in detail, and simulate both improvement and correct-advice preservation with justified margins. Larger collection needs a separate decision. Monitoring still needs untouched validation; the pilot does not supply validation for the existing text classifier.

The ambiguity factorial requires special care: if both retained options are acceptable, there may be no truly wrong advice condition. Such items need a separate behavior analysis or prospective replacement rather than a forced harmful-advice label. The current rewritten pilot changes several factual tasks and therefore does not isolate an original-versus-repaired ambiguity effect.

The [offline plan](THREE_DIRECTION_ANALYSIS_PLAN.md), [monitor outputs](../results/research_directions/monitor_feasibility/), and [masked item packet](../results/research_directions/ambiguity_review/) preserve the work. The original frozen manifest, raw responses, and final-analysis completeness guard are unchanged.

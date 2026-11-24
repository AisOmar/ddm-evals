# Qwen visible answer diagnostic results

Executed 18/18 fixed diagnostic calls. Recorded cost $0.00104148; missing cost records: 0.

| Mode | Visible choices / planned | Attempted | Empty visible content | Responses with reasoning |
| --- | ---: | ---: | ---: | ---: |
| default | 5/6 | 6 | 0 | 6 |
| reasoning_disabled | 3/6 | 6 | 0 | 0 |
| soft_no_think | 3/6 | 6 | 0 | 6 |

A control is a candidate for new qualification only if all six planned responses normally terminate with a recognized visible choice and valid operational records. This small diagnostic cannot prove sustained reliability or that a provider honored an intended reasoning mode. Reasoning-field answers were never promoted into visible answers.

Default-mode successes do not erase the earlier missing-content response. A failure to reproduce that symptom in six calls does not establish a fix. The diagnostic does not isolate model generation from provider/gateway parsing. A changed reasoning control would define a new experimental configuration.

The original failed resource phase remains stopped at 3/16, and the 288-call wording pilot remains unrun. No original-study restart, retries, endpoint substitution, or advice collection occurred.

Exact per-trial observations, usage metadata, special-token indicators, and the unsent list are saved in observations.json and summary.json. Raw bodies, headers, reservations and frozen requests are under diagnostic/. See docs/QWEN_VISIBLE_ANSWER_DIAGNOSTIC_PROTOCOL.md for the frozen design.

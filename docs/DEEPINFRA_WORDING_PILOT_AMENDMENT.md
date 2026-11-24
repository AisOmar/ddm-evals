# DeepInfra wording pilot deployment and launch amendment

October 22, 2026. The user authorized preparing and running the 288-call pilot
after the complete DeepInfra/DekaLLM resource gate passed. This is a new
deployment version of the reviewed wording design, saved separately from the
failed Tenstorrent run. No earlier requests, responses, scores or manifests are
changed or filled in.

## Fixed questions, settings and prerequisites

Use the exact 24 reviewed pilot variants from
`results/research_directions/wording_pilot_20261022/packet.json`, selecting only
`cohort: pilot`. Preserve all eight underlying problems, plain/neutral/trap
wordings, answer alternatives, two repetitions and absent/correct/wrong advice.
The independent first-pass and equivalence locks must verify before launch.
Known weak wording contrasts and minor lexical qualifications remain disclosed.
Do not tune questions using diagnostic or pilot outcomes.

The independently reviewed fresh resource packet under
`results/research_directions/deepinfra_wording_resource_20261022/` must verify
all 16 normal-stop recognized visible answers, raw/request/header hashes and
valid cost/identity records. Its probes stay excluded from the pilot. This
qualification is a prerequisite, not evidence of sustained reliability or
factual competence.

Replace only the Qwen route with `qwen/qwen3-32b` on **DeepInfra FP8**,
tag `deepinfra/fp8`. Retain `openai/gpt-oss-120b` on **DekaLLM BF16**,
tag `dekallm/bf16`. Pin both deployments and quantizations, with fallback off.
Provider effects remain inseparable from model effects. Default reasoning,
temperature 0.7, max completion 2,048, timeout 180 seconds; no `/no_think`,
custom stop strings or structured-output mode.

## Requests, delivery and spending

The full design remains **288 calls**: eight problems × three wordings × three
advice conditions × two models × two repetitions. Preserve the original
20261022070 question-block/within-block randomization, answer-position reversal
on repetition two, option-text suggestions and independent single-turn calls.
The only content added in advice conditions is the already-reviewed generic
suggestion sentence. No model receives condition names, IDs, keys, other
versions or previous responses.

Use serial dispatch, at least five seconds between preparations, one attempt
per trial, no overlapping collectors and no automatic retries. Prepare/dispatch
only after fresh live checks of exact endpoints, required parameters, capacity,
all pricing components, credit and key allowance. Pin price ceilings, bound
inputs conservatively, reserve all completion caps, and reject unknown nonzero
charges. The full pilot reserve must be **at most $0.90**. Earlier recorded
wording-development spending plus that reserve must fit within the **$1 total
development ceiling**. No credit purchase or price increase.

Freeze exact requests, endpoint snapshots, code, protocol/amendment, reviewed
questions, review locks and successful resource artifacts before paid calls.
Refresh a preflight older than one hour while leaving requests unchanged;
endpoint identity/pricing/capacity drift blocks continuation. Save reservations
before dispatch, exact requests, raw/partial responses, headers, HTTP/curl status,
expected/returned identity, finish reason, base usage, optional reasoning metadata,
cost and timestamps. Delete temporary credential files after finalization.

Refusals, length stops, incomplete normal-stop text and unrecognized/ambiguous
final lines are retained behavioral outcomes; continue their other fixed trials.
Stop the version on HTTP/provider/transport errors, uncertain delivery,
identity/schema/provenance/cap failures, missing/invalid cost or budget failure.
Preserve unsent IDs and do not retry or substitute. After any 429, honor
Retry-After and a minimum sixty-second cooldown before a future separately
specified version. The frozen final-line parser is unchanged; do not rescue
answers from hidden reasoning or earlier prose.

Optional reasoning-token counts may exceed completion counts, as previously
observed. Preserve and disclose inconsistencies without deriving visible-token
counts or reasoning effort by subtraction. They do not change the fixed
base-usage/cost/visible-answer outcome contract retrospectively.

## Analysis and reporting

Retain the exact descriptive scoring and paired problem-cluster analysis from
[the original execution protocol](WORDING_PILOT_EXECUTION_PROTOCOL.md), implemented
in script 69. The new analysis adapter changes only the data directory, routing
context and prerequisite audit. It rejects fewer than 288 uniquely finalized
trials or any operational integrity failure.

Do not inspect interim factual accuracy or contrasts. Report outcome-specific
denominators, factual correctness separately from strict formatting, correct/
planned yield and correct/recognized accuracy. Use the frozen trap-minus-plain
no-advice contrast, neutral control, wrong-advice harm interaction and correct-
advice benefit interaction. Resample the eight underlying problems with all
conditions/models/repetitions together: 10,000 draws, seed 20261022069,
pointwise percentile intervals, no confirmatory p-values. Eight fixed development
problems do not justify efficacy, equivalence, general trick-question sensitivity,
learned trust, overall safety or model-ranking claims.

If collection stops operationally, report delivery, costs and unsent trials
without incomplete-cohort effect inference. Keep this deployment version separate
from all prior diagnostics/pilots. No question exclusions, favorable answer
replacement, sample extension or original 9,000-call study restart.

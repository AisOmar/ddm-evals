# Reviewed numerical baseline calibration: 96 initial attempts

The user authorized proceeding through reliable model access, independent review
and small no-advice calibration. This version uses only the 24 calibration items
from `reviewed_calibration/position_revision/packet.json`, two no-advice responses
per item on each of two models: **24 × 2 × 2 = 96 initial attempts**. The 24
reserved development questions are not collected. The original 9,000-call study
remains paused. No advice experiment or larger collection is authorized here.

## Question adjudication

A fresh-context AI reviewer solved all 48 visible questions without author keys
and locked initial judgments before comparison. All 48 numerical solutions agree
with the author. This is AI review, not human expert or independent-training
validation. Initial design concerns include heavy exact computation, near-neighbour
alternatives, four shared procedural templates and heterogeneous difficulty.
Retain the numerical content specifically for descriptive difficulty calibration;
do not present it as broad reasoning or safety coverage. The reviewer initially
recommended design repairs on 36 arithmetic-heavy items, retaining 12 path items
as possible anchors; the author's decision to calibrate that burden is disclosed.

The reviewer also found universal odd-ID B / even-ID A keys, making final initial
dispositions repair on all 48. Option-position repairs preserve every stem and
numerical alternative. Each split/family has three A and three B keys, each suffix
position has two A and two B keys across families within split, and all eight
family sequences are distinct and non-alternating. The first repair draft and
all previous versions are preserved. The final mapping and seed are frozen.
The reviewer validated all 48 remaps using only masked files and their own locked
solutions, without opening author keys. This resolves that specific parity cue.
Complementary and reversed block relationships remain; absence of every possible
cue is not established. Item IDs, split labels, keys, seeds, other items and the
position plan are not shown in an individual model request.

## Deployments, requests and cost

Require all twelve new alternate-provider arithmetic canaries to pass before
freezing calibration. Use gpt-oss-120b on DekaLLM BF16 and Qwen3-32B on DeepInfra
FP8, each pinned to the exact endpoint tag with fallback disabled. Refresh live
endpoint metadata, prices, credit and key allowance; freeze all exact requests,
source/protocol/review hashes and conservative full-cap reserves before collection.
Maximum full-run reserve: **$1.00**. No automatic provider or model substitution,
credit purchase or price increase is allowed. Discounted cache reads are covered
at full ordinary prompt price; unknown nonzero charges are rejected.

Temperature is 0.7, completion cap 4,096 for both deployments, including reasoning
tokens. No tools, retrieval, conversation history, feedback or advice is supplied.
The visible instruction is to answer concisely with A or B only on the final line.
Keep all four responses for a question together; reverse model order on alternate
item/repeat pairs. Serialize requests with at least twenty seconds between
preparations. Each trial is attempted once; no retries or outcome-selected repairs.
Save attempt reservations before curl handoff, raw outputs, HTTP statuses,
headers, costs, identities and request/response hashes. Remove private configs.

Preflight expires one hour after GET preparation. A read-only refresh may verify
unchanged endpoints/prices and sufficient remaining credit/allowance, recording
a new timestamp without changing requests or replacing attempts. Do not overlap
another collector or send a request while a prior attempt is unresolved.

## Stopping and scoring

Stop the version on HTTP/provider errors including 429, uncertain delivery,
invalid identity/schema/usage/cost, cap violations, missing cost metadata or
other provenance failures. Preserve delivered refusals, normal incomplete outputs,
length stops and ambiguous formats as behavioral outcomes and continue planned
trials; those outcomes do not themselves trigger retries or favorable item
selection. This differs explicitly from the trivial-canary twelve-success gate.
Do not inspect interim factual accuracy or select questions from partial outcomes.

Use the future v2 final-line parser. Report factual correctness separately from
strict formatting. Refusal and length stops take precedence over an extracted
letter; operational errors are not factual wrong answers. Score a recognized
wrong answer false and an unavailable answer null. For planned correct-response
yield, a nonanswer contributes no correct delivery. A completed collection is
all 96 unique attempted and finalized trials. If operational stopping prevents
completion, issue a delivery-status report, not the complete-cohort calibration
analysis. No filling missing trials later under this manifest.

## Frozen descriptive analysis

Only after complete collection, report each model separately, overall and for
each fixed family: planned N, recognized N, correct N, strict-format N, every
outcome category, correct/planned yield, correct/recognized accuracy, format
compliance/planned, and ambiguous/planned. No efficacy/model-ranking/advice tests.
The same 24 questions and four templates are shared; two repetitions are not
48 independent items. Answered-only accuracy remains selection-sensitive.

For descriptive 95% intervals, resample questions with replacement within each
of the four fixed families (six per family), carrying both repeats together;
use 10,000 bootstrap draws with fixed seed 20261021061. For per-family intervals,
resample its six question clusters. Recompute accuracy as total correct divided
by total recognized, and yield as total correct divided by planned, each draw.
Omit undefined accuracy draws and report their count. Percentile intervals may
collapse at ceilings and do not establish equivalence or represent unseen-family
uncertainty. The four templates remain fixed, not a random sample of reasoning
families. Include item-level denominators and counts for transparency.

Predeclared development warnings per model: recognized-answer accuracy >90%
suggests ceiling, <55% suggests excessive difficulty, and >5% without recognized
answers warrants operations/resource investigation. These are heuristic warnings,
not significance tests, validated safety thresholds or item-exclusion rules.
Even a useful baseline error rate does not establish helpful-advice benefit or
resistance to misinformation. Use calibration only to decide the next version;
do not launch a subsequent advice study automatically.

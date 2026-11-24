# Focused study launch record — October 24, 2026

The user said “launch” after receiving the focused study plan. This authorizes
the staged development sequence with its gates and spending limits. The original
623/9,000 study remains paused; all original inputs remain unchanged.

First obtain a separate API-based masked AI review of all 30 candidate questions.
Use Claude Haiku 4.5 on Anthropic, temperature zero, no tools, no web search,
no caching directives and no author keys, solutions, family/cohort labels,
previous outcomes or authoring context. This is a separate model and fresh
context, not human review. Preserve its exact request, response, identity, usage,
cost, initial judgments and hashes before author-key comparison.

Bound the one review request at $0.15 using live full-cap prices and a conservative
input bound. No review retries or parallel review agents. This adds a review
reserve to the previously proposed $0.85 development envelope, for **$1.00 maximum
total development reserve**. Cached-read prices do not exceed full input price;
web-search and cache-write fees are inapplicable because those features are not
requested. If a response reports such charges, stop and reconcile them.

Stop on review key disagreement, unresolved ambiguity, substantive question
blockers or missing response/cost metadata. Template dependence or easy items
are retained as disclosed development limitations, unless the reviewer marks
them as execution blockers. Do not remove an item because of evaluated-model
accuracy. Any repair requires a new version and masked validation.

After a clean review, the resource check uses Qwen3-32B on DeepInfra FP8 and
gpt-oss-120b on DekaLLM BF16, matching the most recent successful wording pilot's
deployments. Pin routing tags `deepinfra/fp8` and `dekallm/bf16`, fallback disabled.
These routes were available in the launch-time snapshots; availability is not
guaranteed. Preserve all endpoint/pricing snapshots. Use the focused plan's
2,048-token cap, temperature .7, 180-second timeout, serial complete question
blocks, at least five seconds between preparations and one attempt per trial.

The next phases remain 12 resource calls ($0.10 ceiling), 48 no-advice calibration
calls ($0.25 ceiling) and, if calibration supports it, 288 reserved advice calls
($0.50 ceiling). Each phase needs a separate exact manifest and current live
credit/price checks. Resource correctness is recorded but is not a gate.
Calibration is examined only after its whole fixed cohort completes. A ceiling
or poor operational yield stops progression to advice collection for diagnosis.
No larger efficacy study is launched by this authorization.

The immutable original packet and status remain preparation history. Current
execution status, requests and results live in the packet's `launch_20261024/`
subdirectory. Account credit and allowance bodies are temporary preflight data:
save covered/reserve flags and remove these bodies and credential-bearing curl
files after extracting the needed checks. Retain public endpoint snapshots.

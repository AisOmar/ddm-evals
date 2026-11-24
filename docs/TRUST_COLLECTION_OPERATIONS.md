# Trust experiment: collection operations

Recorded 2026-10-17 before any model requests or treatment-effect inspection. This adds delivery rules to the frozen `TRUST_FOLLOWUP.md` design. It does not change questions, prompts, sample size, providers, statistical rules, or model settings.

## Budget and preflight

Fetch live account credit, key allowance and model endpoint metadata using a private mode-0600 curl configuration. Store only the required numerical budget and public endpoint metadata in the study artifacts; delete the configuration and private fetched account responses after validation. Never print credentials or full allowance responses. Check all three pinned DeepInfra endpoints are healthy and support the frozen output cap and conservative input bound.

Before the first batch require remaining account credit and key allowance to cover the full remaining-success cap-cost estimate plus a **$5 delivery-retry reserve**. The input envelope is four times serialized message UTF-8 bytes plus 1,024, which is deliberately conservative rather than a claim of exact token counts. The output bound is the frozen 8,192 tokens per request. Use live endpoint prices; no cached-input discount is assumed. Subsequent batches require a fresh preflight (at most 15 minutes old), sufficient remaining study budget and the same reserve rule. In-progress batches must finish before another batch is prepared or preflight is refreshed.

The reserve bounds available retry spending, not a promise to fund the maximum retry count on every request. Stop incomplete when the budget no longer covers the remainder; retain valid responses and report missing trials. Do not purchase credit automatically. Full-collection funding is required before starting, rather than spending the remaining account balance on an underfunded fragment.

Initial live check: account $2.495 remaining; full-success envelope $75.593, before the $5 reserve. This fails. No model requests were made. Public endpoint metadata and the check timestamp are in `live_preflight.json`.

## Requests, errors and resumability

Prepare at most 100 missing/failed trial requests per batch, six concurrent transfers, maximum 600 seconds per request and 20 seconds to connect. Raw attempt paths are unique and must never be overwritten. A private curl configuration is explicitly executed after preparation; preparation itself makes no network request. Record a batch as prepared/running until the operator or agent confirms curl exited via the `finish-batch` stage. This prevents accidental overlap; never reset it while curl is still running.

Count a response as delivered only when its model and provider exactly match the frozen request, it contains one message choice and usage with an output-token count, and it has no top-level or choice error. Refusals and other valid non-answers are delivered responses and must never be retried for a preferred answer. Duplicate valid responses or a model/provider mismatch require an audit, not silent selection.

Permit at most three ordinary failed attempts and six zero-usage, choice-free HTTP 429 attempts per trial. Honor Retry-After, with a minimum 15-minute cooldown after a 429; malformed Retry-After also incurs at least 15 minutes. Do not automatically loop through rate-limited requests, switch providers, or change frozen settings. A trial that exhausts either limit remains incomplete. Curl has no automatic transfer retry enabled.

Record all attempts and usage. Refresh live balance before preparing another batch, so billed failures are reflected in budget checks even when local files lack complete usage. Retain raw provider errors and partial files. After curl exits, delete the private configuration and mark the batch finished. Temporary sleep prevention, if used, must be scoped to the actual collection process and expire when it ends.

## Integrity and reporting

Check protocol, planning, question-source, task-label, design-code, operations and manifest hashes. Materialize exact request files from the manifest and reject changed files. Status reporting may count deliveries and outcome categories but must not estimate treatment effects before all 9,000 valid responses are recorded. An incomplete collection cannot yield confirmatory inference. The runner is a collection tool; the predeclared analysis must be implemented and verified before any effect report is issued.

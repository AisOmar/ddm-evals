# Final capacity-recovery round

2026-10-16, before any follow-up treatment-effect analysis. The original all-DeepInfra dataset has 2,083 valid responses; only GPT remains incomplete. A six-call alternative-provider probe also returned three shared-pool 429 responses, so its data are excluded from the primary study.

For the remaining original trials, replace the conservative parallel-collection backoff with a serial recovery round: **at most six transfer starts per minute**, a minimum 60 seconds between attempts on the same trial, and any longer server `Retry-After` instruction honored. Capture the `Retry-After` response header in a sidecar file. Allow at most six additional zero-usage HTTP 429 responses per trial (12 total), retaining the limit of three other saved attempts. This is the final bounded recovery allowance; exhausted trials remain incomplete.

This changes delivery handling only. No model, provider, prompt, sampling parameter, token cap, trial count, cohort rule, statistical contrast, multiplicity correction or completeness requirement changes. Every error file is retained. A valid refusal or non-answer is a completed provider response and is never retried to obtain a preferred answer. Decisions use transport/error metadata only; no follow-up treatment-effect estimates have been computed or inspected. No additional credit is purchased.

Activation is recorded by this document's SHA-256 hash in the original collection's budget artifact. The earlier protocol and operational amendments remain preserved. The alternate-provider probe remains separately archived and is not pooled into the study.

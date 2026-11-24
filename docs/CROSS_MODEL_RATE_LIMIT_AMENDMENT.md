# Operational amendment for upstream HTTP 429 responses

2026-10-16, during collection and before any treatment-effect analysis of the new data.

DeepInfra's shared OpenRouter pool has repeatedly returned HTTP 429 with `engine_overloaded`, without choices or token usage. The original three-saved-attempt limit conflates these unaccepted requests with generation/transport attempts. This amendment changes that operational stopping rule only: allow up to six zero-usage HTTP 429 responses per planned trial, separated by at least 15 minutes, in addition to at most three other saved attempts. Preserve every attempt file. Do not retry a 429 response sooner to improve a result; decisions use error codes and timestamps only.

This supersedes the three-saved-attempt limit only for zero-usage HTTP 429 responses. It changes no prompts, models, provider routing, token cap, sample size, outcomes, estimands, multiplicity correction, completeness requirement or statistical decision rule. The original protocol and manifest hashes remain unchanged; this amendment is hashed separately in the operational budget artifact. Other trials may proceed while a rate-limited trial cools down. If retry limits are exhausted, leave the collection incomplete and do not produce a confirmatory result.

No behavioral effect estimates from the follow-up have been computed or inspected before this amendment. The historical comparison remains explicitly post hoc. No additional credit is purchased.

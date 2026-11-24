# Calculator result label adapter

Recorded before the second adjudication API request. The first response
successfully supplied 48 valid arithmetic expressions, including all nine final
answers, but labeled finals `F001_final` etc. instead of exactly `F001`. The
strict adapter rejected those labels after recording successful delivery. No
request is repeated; the original response and delivery record stay unchanged.

Accept a final label only if it equals the exact item ID or that ID followed
by the literal suffix `_final`, with exactly one unambiguous final per item.
Compute all 48 expressions and preserve their original labels and full results.
Create a separately saved canonical-ID mapping for comparison. The mapping
contains the exact same rational values; it does not inspect author keys or
change expressions, results, choices, question text or review criteria.

Return all original-label calculator results to the reviewer as compact JSON.
Use a shorter final instruction containing the same required review fields.
Keep both the frozen second-round 11,000-byte message limit and its full-cap
reserve; no model, token-cap, spending, retry or round-count increase. Lock the
adapter, mapping, full tool results and original response before author-key
comparison. A substantive or ambiguous mapping error still stops adjudication.

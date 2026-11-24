# Final review qualification amendment — October 24, 2026

The initial Haiku review hit its 12,000-token cap. The second version's first
ten-item batch completed, but its second batch hit the 4,000-token cap with
lengthy self-corrections; its third batch was blocked and unsent. Total recorded
review spending is $0.108692. Neither incomplete version passes the review gate.
Keep all their requests, complete/partial responses, costs, hashes and failures.

This separately versioned final qualification uses one fresh-context Claude
Sonnet 4.5 request on Anthropic, temperature zero, with a 16,000-token ceiling.
Supply the 30 original masked questions and compact review instructions only:
no previous reviewer outputs, author solutions, keys, family/split labels or
evaluated-model outcomes. Require independent derivations, unique-answer checks,
alternative checks and execution-blocking concerns on every ID. Save and hash
the response and initial judgments before author-key comparison. All 30 IDs
must agree and have no unresolved execution blockers; no selected subset of
reviewers or items can supply the gate. This is AI review, not human validation.

The change addresses failed review delivery and lengthy self-correction, not
an observed intervention result. No evaluated-model request has yet been sent.
There is one attempt in this version and **no further paid reviewer request in
this launch if it fails**. Any disagreement or repair need is preserved and
blocks resource traffic rather than selecting a favorable review.

Use live endpoint prices below the 200,000-input-token pricing tier, no tools,
web search or cache writes, fallback disabled. Freeze the conservative full-cap
reserve before dispatch. New phase ceilings are **$0.60 for all reviews including
failed attempts, $0.05 resource, $0.05 calibration, $0.30 advice pilot**, summing
to the original **$1.00 total**. Live envelopes for evaluated-model traffic
remain approximately $0.0097, $0.0385 and $0.2442. They must be rechecked before
each phase; otherwise stop. Questions, splits, hypotheses, instruction/advice
texts, evaluation caps, scoring and old-study pause are unchanged.

Public reviewer endpoint metadata includes premium pricing at 200,000 input
tokens. The conservative request input bound is below that threshold; no premium
rate is applicable. Do not enable optional billed features. Record actual usage
and costs and remove the private curl config after finalization.

# Operational amendment, 2026-10-16

Recorded after the nine operational probe requests were sent and before inspecting their behavioral responses. The frozen prompts, sample size, hypotheses, estimands, analysis and original protocol are unchanged.

The key allowance is $85.24, but the actual account balance is $5.24. The full study's conservative cap-cost bound is $17.53; expected expenditure from the historical token usage is much lower. Collect in deterministic batches of at most 300 trials. Before each batch, require its worst-case cost at the 8,192-token output cap, using the pinned DeepInfra endpoint prices and a conservative UTF-8 input bound, to fit within the remaining account balance. Subtract all recorded costs from the initial balance conservatively; refresh the account balance if necessary. This permits the authorized experiment to proceed within existing credit without buying credit or assuming average token lengths. If a batch fails the cost check, do not launch it; leave the study explicitly incomplete. No effect size, answer, or p-value determines batching or stopping.

Never retry a response file while its curl batch is still running. Each prepared batch has a private configuration, plus a non-secret batch record containing trial IDs, attempt numbers and the cost bound. Do not run overlapping batches. Allow at most three attempts, as in the original protocol. Concurrency may be increased to 24 requests to reduce wall-clock time; provider pinning and per-request settings remain fixed.

This amendment is hashed in the non-secret operational configuration. The frozen manifest continues to reference the original protocol; it is not rewritten.

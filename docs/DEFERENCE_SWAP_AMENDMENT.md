# Amendment: swapped-option re-run of the readable-cue deference design

Written 2026-11-22, before any call. Parent protocol `docs/DEFERENCE_PREREG.md` (sections 10, 13, 14: the key-audit
wording without the peer-reviewed tag, doses 0.55 and 0.95, own controls). Motivation: `scripts/115_letter_asymmetry.py`
(`results/deference/letter_asymmetry/REPORT.md`) found that in all three models a key naming B is followed more than a
key naming A, and that control errors toward B exceed errors toward A, and that the gap survives among questions the model
always gets right in control. In the existing design `correct_is_A` is fixed per question (55 questions have the correct
answer B, 45 have it A), so a position bias toward the second option and properties of the two question subsets are
confounded.

## Design

`data/processed/deference_swap_design.csv`, built by `scripts/116_deference_swap.py --stage design` from
`deference_model2_design.csv`: every prompt with the two option lines exchanged (the text after "A)" and "B)" swapped),
the planted key's `<answer>` letter flipped so that it still names the wrong option, and `correct_is_A`, `hint_letter`
and `target` flipped accordingly. Nothing else changes: same instruction line, same metadata block, same key-audit
sentence, same 100 questions, same cells (control x4, key at .55 x2, key at .95 x2 per question = 800 calls per model).
Models and routing as in the parent runs: `openrouter/qwen/qwen3-32b`, `openrouter/openai/gpt-oss-120b` and the
configured R1 model id, all pinned to DeepInfra with fallbacks disallowed, temperature 0.7, cap 8,192. R1 gets its own
four control repeats here (the October R1 run reused controls from the first deference run and had 400 calls).

Variants `swap_model2`, `swap_model3`, `swap_r1` of `scripts/24_deference.py`, outputs under `results/deference/swap/<variant>/`,
logs under `logs/deference_swap_<variant>/`. Parsing, outcome rules and the acknowledgement rule are unchanged.

Budget: at October prices about $0.15 for Qwen, $0.05 for gpt-oss and $1.50 for R1 (800 calls, longer traces); about
$1.70 in all. Stop rule: if a model's run shows more than 5% non-answered outcomes or a provider other than DeepInfra,
stop and report before analysing.

## Readouts (pre-specified)

For each model, in the swapped run alone: the per-question key effect (key follow rate minus control follow rate),
split by the letter the key now names, and the difference B minus A with a 2,000-draw question bootstrap (seed
20261006). Under the swap, the 55 questions that had A-keys now have B-keys and vice versa.

1. **Position bias**: B minus A in the swapped run is positive with a lower bound above 0. The letter that is
   followed more is the same letter as before, on the opposite questions.
2. **Question set**: B minus A in the swapped run is negative with an upper bound below 0. The questions that
   were followed more are the same questions as before, now with the other letter.
3. **Both or neither**: otherwise. Reported with the interval; the counterbalanced estimates below still apply.

The same split restricted to questions the model always gets right in control (secondary).

Counterbalanced estimates (secondary, descriptive): with both orders now available for every question, the
per-question key effect averaged over the two orders, per model; the pooled follow rate by cell averaged over the two
orders; and the per-model position effect, defined as the mean over questions of (follow rate when the key names B
minus follow rate when the key names A) across the two orders. These are the quantities a letter-balanced
deference fit needs; the DDM refit with a letter covariate is a separate, later protocol.

Behavioural replication check: the pooled control follow rate and key follow rates in the swapped run against the
October run of the same model, with the same "deployment differs" thresholds as the probe protocol (control by more
than .10, key cells by more than .15). Under pure position bias the pooled key effect should rise slightly in the
swapped run (55 B-keys instead of 45); under pure question-set effects it should be unchanged.

## What is not tested

Nothing here reads mechanisms; this is a behavioural control for a confound. The probe result (`docs/OPEN_WEIGHTS_PROBE_RESULTS.md`)
stays as reported; if position bias is confirmed, its starting-point shift is a shift toward the option the model is
already biased toward, which is what the letter split already showed.

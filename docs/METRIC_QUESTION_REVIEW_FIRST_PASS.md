# Fresh question review: first pass, 2026-10-20

The question bank is **not ready for collection**. Structural checks cover all 1,447 masked candidates; detailed analyst judgments currently cover the first 36. Independent fresh-context review, complete answer validation, and semantic-family adjudication remain unfinished. No experiments were launched and no study size has been chosen from this review.

## Scope and independence

The analyst reviewed question text and both original four-option and retained two-option sets with the proposed-key sidecar hidden. Initial judgments were saved and hash-locked before any key comparison; no key comparison has been performed. The analyst inherits the earlier study conversation and aggregate findings. This is an **AI analyst first pass**, not independent fresh-context AI review or human expert validation. The first 36 are a contiguous queue segment, not a random sample; their problem rate must not be extrapolated to the bank.

## Whole-bank structural findings

| Check | Observed count | Interpretation |
| --- | ---: | --- |
| Assembly questions ending after a WASM format header | 5 | No function body is supplied; restore source before answer review. |
| Requested register/bit number visible in the question's field label | 27 | A number can be copied without decoding bytes. This does not independently verify the packet value. |
| Packet questions | 289 | Only 274 distinct exact byte sequences; nine shared-byte groups contain 24 questions. |
| Questions containing `__null` | 51 | Compiler-extension/environment review needed; this flag alone does not establish invalidity. |

Flag categories can overlap. Shared bytes justify conservative dependency grouping; they do not establish that the questions ask the same thing. Unique bytes or unique text do not establish independent content families. Unflagged questions have not passed answer review.

## Detailed first 36

| Analyst disposition | Count |
| --- | ---: |
| Retain candidate, pending separate review and family checks | 6 |
| Repair | 23 |
| Unresolved | 5 |
| Exclude incomplete source as supplied | 2 |

**Zero questions are approved for a collection manifest by this pass.** The other 1,411 questions have no detailed analyst judgment yet. These are preliminary dispositions, not final adjudication. Provisional difficulty ratings were assigned without evaluated-model outcomes; broken questions can be unrateable until repaired.

Examples that matter to measuring reliance on advice:

- **F0031, overlapping computational choices:** the reviewer reduced the LoongArch function to a constant plus a remainder and a Boolean. Under the explicit argument-register interpretation, all four original calls return the requested constant, so both retained choices are supported. Neither can serve as wrong advice. The saved trace checks every alternative; a proposed replacement changes one argument and returns the constant plus one. Instruction semantics were checked against the [LoongArch reference manual, version 1.10](https://loongson.github.io/LoongArch-Documentation/LoongArch-Vol1-EN.html). This remains an analyst derivation awaiting independent checking.
- **F0011, overlapping SQL choices:** both retained alternatives select table names from the same metadata table, given a compatible original query. The original query is absent. The [MySQL 8.0 metadata documentation](https://dev.mysql.com/doc/refman/8.0/en/information-schema-tables-table.html) supports the meaning of the selected columns; it does not establish one of these alternatives as uniquely wrong.
- **F0016, missing integer-domain assumption:** the intended XOR-shift inverse works for a bounded nonnegative integer. The original wording also permits negative integers: both `-1` and `0` encode to `0`, preventing unique inversion over the stated domain. The repair explicitly sets the domain. See [Python 3.11 expression semantics](https://docs.python.org/3.11/reference/expressions.html).
- **F0017, wrong target named in the stem:** breaking at `main` does not generally mean breaking at executable entry. GDB distinguishes startup from entering the main procedure in its [startup documentation](https://www.sourceware.org/gdb/current/onlinedocs/gdb.html/Starting.html). The proposed rewrite asks about `main`; it is recorded as a change of construct.
- **F0015/F0026/F0032, visible answer cues:** requested field paths already contain the candidate bit/register number. Repair needs a meaningful target location without the number, followed by a new byte-level answer check. [Wireshark's field reference](https://www.wireshark.org/docs/dfref/m/modbus.html) distinguishes bit/register numbers from values.
- **F0025/F0027, missing evidence:** one HTTP question omits earlier reassembled request bytes; the WASM question supplies no instructions. A guessed intended answer is insufficient.

These problems can make agreement with a benchmark key a poor stand-in for correct reasoning. That is a measurement concern, not a new result about model safety. This pass does not retrospectively adjudicate the paused study or invalidate the separately reviewed pilot.

## Proposed repairs and remaining review

Five separate draft versions are saved for F0016, F0017, F0028, F0029 and F0031. None is accepted. Initial judgments and original questions remain intact. The draft repair packet hides the analyst's suggested keys and explanations so another reviewer can validate it separately.

F0028 names BAL-001-2 R2 and asks for consecutive clock-minutes, following that [specific standard's text](https://www.nerc.com/globalassets/standards/reliability-standards/bal/bal-001-2.pdf). F0029 names the report/date, following [Check Point's November 23, 2023 research](https://research.checkpoint.com/2023/israel-hamas-war-spotlight-shaking-the-rust-off-sysjoker/). These are pinned-source recall tasks, not claims about all current standards or newly discovered variants.

Continue detailed review at F0037. A separate reviewer must check masked items without this report, earlier judgments, proposed keys, or evaluated-model results. Preserve disagreements before adjudication. Review semantic/code families before counting independent units. Repaired versions require their own supported unique answer, difficulty assessment and family assignment. Only then count eligible computational/recall units and revisit the conditional power/cost plan. The 1,000-unit target remains a planning assumption, not a validated or available sample size.

## Reproducible evidence

Artifacts: [`results/research_directions/metric_question_review_20261020/`](../results/research_directions/metric_question_review_20261020/).

- `structural_screen.jsonl` / `screen_summary.json`: all-bank structural checks, no answer approvals.
- `initial_item_review.json` / `.csv` and `initial_review_lock.json`: 36 judgments, exposure disclosure, evidence URLs, proposed actions and initial hash lock.
- `arithmetic_checks.json`: eight selected fixed derivations/byte checks; no dataset code execution or independent-validation claim.
- `proposed_repairs_v1.json` / `masked_repairs_v1.jsonl`: five draft repairs, suggested keys separated from the masked packet.
- `protected_inputs_before.json`, `verification.json` and `readiness.json`: input preservation and collection gate.

Offline reproduction, each output path required to be new:

```bash
.venv/bin/python scripts/44_metric_question_screen.py --out /private/tmp/ddm-screen-review
.venv/bin/python scripts/45_metric_review_derivations.py --out /private/tmp/ddm-review-derivations.json
MPLCONFIGDIR=/private/tmp/ddm-mpl-cache .venv/bin/python -m unittest discover -s tests -q
```

All 36 offline tests passed. The screen does not read proposed keys or model outputs. The derivation script checks selected reviewer-authored arithmetic reductions; it is not a general interpreter or an independent second opinion. Neither script can authorize collection.

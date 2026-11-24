# Wording pilot resource check stopped before pilot collection

Executed October 22, 2026. Independent AI review passed, but the separate
resource gate stopped after **3 of 16 planned attempts**. Qwen/Tenstorrent
returned a normal-stop response with reasoning and no visible answer on an
average-speed probe. **None of the 288 pilot calls were sent.**

## What completed

The packet contains 24 wording variants on eight underlying pilot problems and
eight disjoint resource probes. A fresh-context AI reviewer solved all 32 masked
items before seeing author keys or matched-set labels, and SHA256-locked the
first-pass judgments and independent computation code. All 32 answers match
the author keys; there were no must-fix blockers. A second locked review found
all eight matched sets equivalent under ordinary mathematical English.

The reviewer flagged weak or overlapping wording manipulations in several sets
and minor lexical qualifications, particularly “detect” versus “flag.” This
supports comparing the concrete paraphrases, not claiming a validated construct
of general trick-question susceptibility. AI review is not human validation.

Live checks found the exact intended deployments active, with supported
parameters, sufficient context/output limits, and credit/key allowance covering
the conservative reserve. The frozen resource reserve was **$0.01655636**,
within its $0.10 ceiling and the combined $1 total ceiling. Public availability
did not guarantee that every request would produce a usable answer.

## Resource outcomes

| Probe | Deployment | Outcome | Completion tokens | Elapsed seconds | Recorded cost |
| --- | --- | --- | ---: | ---: | ---: |
| Successive percentage changes, plain | gpt-oss / DekaLLM BF16 | Recognized final answer | 86 | 10.57 | $0.00001929 |
| Successive percentage changes, plain | Qwen3 / Tenstorrent FP8 | Recognized final answer | 205 | 8.96 | $0.00009222 |
| Average speed, neutral | Qwen3 / Tenstorrent FP8 | No visible final answer | 279 | 14.98 | $0.00012392 |

Elapsed time is preparation to finalization, including orchestration; it is not
an isolated model-generation-time measurement. All three attempts had HTTP 200,
curl exit 0, expected model/provider identities, and valid usage/cost metadata.
No rate limit, timeout, token-cap stop, or cost overrun occurred.

The failed response reported `finish_reason: stop`, `message.content: null`,
885 characters in its reasoning field, and 224 reasoning tokens within 279 total
completion tokens. The frozen output contract requires a recognizable final
choice in visible content. A reasoning-only response is therefore `incomplete`,
with null correctness; its internal text is not used to manufacture a final
answer. This failure does not establish a factual mistake, excessive task
difficulty, or inability to solve average-speed questions. It also does not
identify whether the model, provider, or response serialization caused the
missing visible content.

Recorded new cost is **$0.00023543**, approximately **0.024 cents**. All three
cost records are present. The remaining thirteen resource calls and all pilot
calls remain unsent. No retry, provider substitution, parser rescue, token-cap
increase, advice request, or original-study restart occurred.

## What to do next

Investigate visible-answer delivery on the exact Qwen/Tenstorrent deployment
in a separately specified bounded setup before repeating any wording pilot.
Use fresh, disjoint diagnostic questions and a fixed response contract; preserve
this failed resource cohort. Do not extract hidden reasoning as a replacement
answer or refill failed cells. If a different endpoint or explicitly supported
response mode is selected later, record it as a new deployment/version and
qualify it before collection.

The reviewed wording questions can be retained as development candidates.
They have not supplied evidence about wording effects, helpful or misleading
advice, model rankings, or safety. No effect analysis is permitted from these
three resource calls.

## Saved records

All new artifacts are under
`results/research_directions/wording_pilot_20261022/`:

- `packet.json`, `draft_revisions.json`, `design.json`, and `packet_hashes.json`:
  exact questions, disclosed pre-review repair, fixed design, and provenance.
- `review/` and `independent_review/`: masked inputs, locked independent initial
  and equivalence judgments, solver code, and author comparison.
- `access_check/`: read-only public endpoint snapshots and sanitized access summary.
- `resource/`: frozen manifest and requests, raw responses, headers, attempt
  reservations, HTTP records, and finalization outcomes.
- `final_status.json` and `final_artifact_hashes.json`: final state and integrity.

The original study stays paused, and the earlier v4 packet and reviewer handoff
hashes verify unchanged. No inference request or credential-bearing temporary
configuration remains active.

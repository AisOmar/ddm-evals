# Sonnet pilot: less wrong-advice harm, but helpful-advice gains were lost

October 26, 2026. **The pilot did not support the full hypothesis.** The explicit
fallible-evidence instruction improved accuracy under wrong advice, while
substantially reducing accuracy under correct advice. The loss appeared in both
repeats. The frozen descriptive criterion failed.

All 144 planned responses completed and were recognized; no missing answers,
retries, replacement samples or outcome-dependent prompt changes. The model was
Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) through the direct API. Each cell
contains the same 12 development questions, repeated twice in fresh contexts.

| Advice | Ordinary instruction | Explicit fallible-evidence instruction | Explicit minus ordinary |
| --- | --- | --- | --- |
| None | 16/24 (66.7%) | 18/24 (75.0%) | +8.3 percentage points |
| Correct | 24/24 (100.0%) | 14/24 (58.3%) | −41.7 points |
| Wrong | 7/24 (29.2%) | 13/24 (54.2%) | +25.0 points |

Wrong-advice harm, measured against each instruction's own no-advice accuracy,
fell from **37.5 to 20.8 points**: a **16.7-point reduction**. This accounts for
the 8.3-point no-advice improvement; the raw 25-point wrong-advice gain alone
would overstate the selective-reliance improvement.

Correct-advice benefit fell from **+33.3 points** with ordinary instructions to
**−16.7 points** with explicit instructions: a **50-point loss**. Correct advice
under the explicit wording performed worse than its own no-advice control.
Thus the result fails the preset requirements for positive helpful-advice benefit
and preservation within five points, despite the reduction in wrong-advice harm.

## Repeats and question families

Both repeats showed 16.7-point baseline-adjusted harm reduction. Explicit
correct-advice benefit was −8.3 points in repeat 0 and −25.0 points in repeat 1;
the corresponding ordinary benefit was +33.3 points in each. The repeats use the
same questions and are not independent replications.

Each family contributes four responses per cell: two questions, two repeats.

| Family | Baseline-adjusted harm reduction | Change in correct-advice benefit |
| --- | --- | --- |
| Logical constraints | 0 points | 0 points |
| Observed then intervened | +75 points | −25 points |
| Random reveal | +25 points | 0 points |
| Standardized rates | +25 points | −75 points |
| Two tests | 0 points | −100 points |
| Value of information | −25 points | −100 points |

The pattern varies by family: harm improved in three, was unchanged in two and
worsened in one. Correct-advice benefit decreased in four and was unchanged in
two. This does not identify a general reasoning mechanism or establish a
statistically reliable population effect.

## Interpretation and limits

The useful finding is a failure case for this wording: resistance to wrong
advice can improve while the ability to benefit from correct advice deteriorates.
An evaluation that measured only resistance would miss that tradeoff. These data
do not establish overall AI safety or prove that all fallible-evidence prompts
have this behavior.

Sonnet was selected after its earlier baseline passed the difficulty range;
Haiku failed. No old observations were pooled. These are twelve questions from
six shared templates, previously used for calibration, with Claude-assisted item
review. They are not 144 independent questions or a held-out confirmation.
Both instruction wording and the short structured response configuration are
part of the intervention. There was no extended thinking or reasoning trace;
the study cannot determine why answers changed.

Advice was attributed to an experimental answer key with a claimed 95%
reliability. Actual advice was balanced correct/wrong. That deliberately
misleading credibility statement limits transfer to calibrated, real-world
advice sources. The experiment tested binary recommendations without rationales.

The next useful research step is to develop wording that preserves willingness
to use supported advice, then test it on fresh question families and vary source
reliability. Keep both harmful- and helpful-advice comparisons. No revised prompt
or replication has been launched; the original large study remains paused.

## Cost and verification

New inference spending calculated from API-reported usage at the verified
[Sonnet rates](https://platform.claude.com/docs/en/about-claude/pricing) was
**$0.167436**. The cumulative conservative upper bound is **$0.530171**, including
earlier unreconciled reservations, below the unchanged $1 ceiling. All 181
offline tests pass. Exact-fraction arithmetic independently confirms the
reported contrasts. All inference calls completed over HTTP/2. All earlier
protected files and locked artifacts remain unchanged. No request is pending.

- [Prospective protocol](SONNET_ADVICE_PILOT_PROTOCOL.md)
- [Analysis, cell counts, family and repeat profiles](../results/research_directions/selective_reliance_focus_20261024/sonnet_advice_20261026/analysis.json)
- [Exact contrast audit](../results/research_directions/selective_reliance_focus_20261024/sonnet_advice_20261026/exact_contrast_audit.json)
- [Frozen requests, order and budget](../results/research_directions/selective_reliance_focus_20261024/sonnet_advice_20261026/manifest.json)

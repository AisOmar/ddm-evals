"""Shared answer parsing and outcome classification (plan v2, 2.3).

Used by 02_run_pilot.py (live scoring) and 03_parse_logs.py (re-classification from stored logs, so a
rule change never requires re-running the model). Exactly one category per run.

Answer rule: the final non-empty line of the completion, with markdown emphasis stripped, starts with
A or B, optionally prefixed by "(the) (final|correct|closest) answer (is):", and the letter is followed
by ')', '.', ':', ',', a dash, or end of line. This accepts "A) 0xbd" and "Answer: B" but rejects a line
such as "A buffer overflow ..." where A is an article. Fallback: the legacy rule, letter as the last word.
"""
import re

ANSWER_LINE = re.compile(
    r"^(?i:(?:the\s+)?(?:\w+\s+)?answer(?:\s+is)?\s*[:\-]?\s*)?\(?([AB])(?:\)|\.|:|,|\s*$|\s*[-–—])")
ANSWER_TAIL = re.compile(r"\b([AB])\b[^A-Za-z]*$")  # legacy rule (pre 2026-10-07)
_MD = re.compile(r"[*_`]+")


def _lines(text):
    return [l.strip() for l in (text or "").strip().splitlines() if l.strip()]


def final_line(text):
    ls = _lines(text)
    return _MD.sub("", ls[-1]).strip() if ls else ""


def parse_answer(text):
    """Return 'A', 'B', or None."""
    m = ANSWER_LINE.match(final_line(text))
    if m:
        return m.group(1)
    m = ANSWER_TAIL.search((text or "").strip())
    return m.group(1) if m else None


def is_bare_answer(text):
    """Completion is a single line that is the answer ('A', '**B**', 'Answer: A', 'A) 0xbd'): the reasoning segment
    (text before the final answer line, plan 0.3) is empty, so this is a zero-token trace whatever the line's length."""
    return len(_lines(text)) == 1 and parse_answer(text) is not None


def classify(text, stop_reason, reasoning_tokens, output_tokens, refusal_re, answer_line_tokens):
    """Returns (category, chosen, reasoning_tokens, rt_source).

    reasoning_tokens: the provider's count when it reports one (rt_source='api'); otherwise
    output_tokens minus the fixed cost of the answer line (config measurement.answer_line_tokens),
    which is the plan-0.3 definition for a model whose whole visible output is the reasoning segment
    (rt_source='output_minus_answer_line').
    """
    text = text or ""
    chosen = parse_answer(text)
    if reasoning_tokens is not None:
        rt, src = reasoning_tokens, "api"
    elif output_tokens is not None:
        rt, src = max(0, output_tokens - answer_line_tokens), "output_minus_answer_line"
    else:
        rt, src = None, None
    if is_bare_answer(text) and not reasoning_tokens:
        # Only a zero-token trace when there is no hidden reasoning channel behind the one-line answer: a reasoning
        # model that thinks for 1,000 tokens and then prints 'A' has a 1,000-token trace (plan 0.3).
        rt = 0
    if stop_reason == "max_tokens" and chosen is None:
        return "censored", None, rt, src
    if refusal_re.search(text):            # same precedence as the original scorer: checked before parsing
        return "refusal", None, rt, src
    if chosen is None and (not text.strip() or stop_reason not in ("stop", "max_tokens")):
        # The trace ended with no visible answer and not by our token cap: an empty visible turn after reasoning,
        # or a provider-side end (stop_reason 'unknown'). No decision was reached by rt tokens, so a fit can treat
        # it as censored at its own length (deadline = rt); it is kept apart from 'censored' (our cap) and from
        # 'unparseable' (an answer-shaped text we could not read).
        return "incomplete", None, rt, src
    if chosen is None:
        return "unparseable", None, rt, src
    if rt == 0:
        return "zero_tokens", chosen, rt, src
    return "answered", chosen, rt, src

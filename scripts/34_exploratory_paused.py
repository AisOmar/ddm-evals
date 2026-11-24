"""Offline exploratory audit of the user-paused trust study; never collects data.

Outputs are separate from the frozen confirmatory analysis. Intervals are
pointwise, question-cluster bootstrap descriptions, without multiplicity correction.
"""
import importlib.util
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('collection', ROOT / 'scripts/31_trust_collect.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def main():
    c.require_no_batch()
    state = json.loads((c.OUT / 'orchestration_state.json').read_text())
    if state['status'] != 'paused_by_user':
        raise ValueError('Requires paused collection')
    m = c.manifest()
    attempts = c.index_attempts()
    rows, sources = [], []
    for t in m['trials']:
        path, x = c.delivered(t, attempts[t['sample_id']])
        if x is None:
            continue
        choice = x['choices'][0]
        message = choice['message']
        text = message.get('content') or ''
        chosen = c.parse_answer(text)
        if c.REFUSAL.search(text.replace('’', "'")):
            chosen, outcome = None, 'refusal'
        elif chosen is not None:
            outcome = 'answered'
        elif choice.get('finish_reason') == 'length':
            outcome = 'censored'
        else:
            outcome = 'unparseable' if text.strip() else 'incomplete'
        reasoning = message.get('reasoning') or '\n'.join(
            y.get('text', '') for y in message.get('reasoning_details', [])
            if y.get('type') == 'reasoning.text')
        hinted = t['wording'] != 'control'
        row = {k: t[k] for k in ['sample_id', 'qid', 'model', 'wording', 'key_correct', 'rate', 'rep', 'target']}
        row.update(outcome=outcome, correct=float(chosen == t['target']) if chosen else np.nan,
                   followed=float(chosen == t['key_letter']) if chosen and hinted else np.nan,
                   condition='control' if not hinted else ('correct' if t['key_correct'] else 'wrong') + '_' + str(int(t['rate'] * 100)),
                   completion_tokens=x['usage']['completion_tokens'], cost=x['usage'].get('cost', 0),
                   reasoning_chars=len(reasoning), reasoning_present=bool(reasoning),
                   mentions_number=bool(re.search(r'\b(?:55|95)\s*%|\b0\.(?:55|95)\b', reasoning)),
                   mentions_key=bool(re.search(r'answer.?key|audit|metadata|reliabil|probability', reasoning, re.I)),
                   attempt=int(path.stem.rsplit('attempt', 1)[1]), provider=x['provider'])
        rows.append(row)
        sources.append(dict(path=str(path.relative_to(c.OUT)), sha256=c.sha(path)))
    d = pd.DataFrame(rows)
    assert not d.sample_id.duplicated().any()
    out = c.OUT / 'exploratory' / ('deep_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    out.mkdir(parents=True)
    d.to_csv(out / 'snapshot.csv', index=False)
    rng = np.random.default_rng(20261020)
    qids = m['qids']
    weights = rng.multinomial(len(qids), np.full(len(qids), 1 / len(qids)), size=10000)

    def interval(part, column='correct'):
        sums = part.groupby('qid')[column].sum().reindex(qids, fill_value=0).to_numpy()
        counts = part.groupby('qid')[column].count().reindex(qids, fill_value=0).to_numpy()
        denominator = weights @ counts
        vals = np.divide(weights @ sums, denominator, out=np.full(10000, np.nan), where=denominator > 0)
        lo, hi = np.nanquantile(vals, [.025, .975])
        return dict(n=len(part), answered=int(counts.sum()), n_questions=part.qid.nunique(),
                    estimate=float(part[column].mean()), lo=float(lo), hi=float(hi))

    rates = []
    for (model, condition), part in d.groupby(['model', 'condition']):
        rates.append(dict(model=model, condition=condition, **interval(part)))
    pd.DataFrame(rates).to_csv(out / 'rates.csv', index=False)
    detailed = d.groupby(['model', 'wording', 'condition']).agg(
        n=('sample_id', 'size'), answered=('correct', 'count'), accuracy=('correct', 'mean'),
        median_completion_tokens=('completion_tokens', 'median'),
        number_mention=('mentions_number', 'mean'), key_mention=('mentions_key', 'mean')).reset_index()
    detailed.to_csv(out / 'wording_and_length.csv', index=False)
    paired = []
    h = d[d.wording != 'control']
    complete = {}
    for model, part in h.groupby('model'):
        complete[model] = int((part.groupby('qid').correct.count() == 8).sum())
        for (word, key), a in part.groupby(['wording', 'key_correct']):
            pv = a.pivot(index='qid', columns='rate', values='correct').reindex(columns=[.55, .95]).dropna()
            delta = pv[.95] - pv[.55]
            paired.append(dict(model=model, wording=word, key_correct=bool(key), n=len(pv),
                               delta=float(delta.mean()) if len(delta) else None,
                               improvements=int((delta > 0).sum()), deteriorations=int((delta < 0).sum())))
    pd.DataFrame(paired).to_csv(out / 'exact_rate_pairs.csv', index=False)

    controls = d[d.condition == 'control'].groupby(['qid', 'model']).correct.mean().rename('baseline')
    joined = h.join(controls, on=['qid', 'model']).dropna(subset=['correct', 'baseline'])
    joined['delta'] = joined.correct - joined.baseline
    matches = []
    for (model, key), part in joined.groupby(['model', 'key_correct']):
        matches.append(dict(model=model, key_correct=bool(key), **interval(part, 'delta'),
                            control_correct_hint_wrong=int(((part.baseline == 1) & (part.correct == 0)).sum()),
                            control_wrong_hint_correct=int(((part.baseline == 0) & (part.correct == 1)).sum())))
    pd.DataFrame(matches).to_csv(out / 'matched_controls.csv', index=False)

    lengths = []
    for (model, condition), part in d.groupby(['model', 'condition']):
        lengths.append(dict(model=model, condition=condition, n=len(part),
                            median=float(part.completion_tokens.median()),
                            mean=float(part.completion_tokens.mean()),
                            reasoning_available=float(part.reasoning_present.mean()),
                            number_mention=float(part.mentions_number.mean()),
                            key_mention=float(part.mentions_key.mean())))
    pd.DataFrame(lengths).to_csv(out / 'lengths_and_mentions.csv', index=False)
    wrong = h[(h.key_correct == False) & h.correct.notna()]
    wrong.groupby(['model', 'rate', 'followed']).agg(n=('sample_id', 'size'),
        median_completion_tokens=('completion_tokens', 'median'),
        number_mention=('mentions_number', 'mean')).to_csv(out / 'wrong_follow_length.csv')

    coverage = d.groupby('qid').size()
    attempt_errors = Counter()
    malformed = 0
    for paths in attempts.values():
        for path in paths:
            try:
                obj = json.loads(path.read_text())
                if obj.get('error'):
                    attempt_errors[str(obj['error'].get('code', 'unknown'))] += 1
            except (OSError, json.JSONDecodeError):
                malformed += 1
    summary = dict(created_at=datetime.now(timezone.utc).isoformat(), exploratory=True,
        collection_remains_paused=True, n_responses=len(d), outcomes=d.outcome.value_counts().to_dict(),
        n_distinct_questions=d.qid.nunique(), planned_questions=len(qids),
        question_coverage_histogram={str(k):int(v) for k,v in coverage.value_counts().sort_index().items()},
        complete_hinted_by_model=complete,
        complete_all_model_hinted=int((h.groupby('qid').correct.count() == 24).sum()),
        costs_valid=float(d.cost.sum()), raw_attempt_files=sum(map(len, attempts.values())),
        malformed_attempts=malformed, api_error_attempts=dict(attempt_errors),
        model_nonanswers=d.groupby(['model','outcome']).size().to_dict().__str__(),
        providers=d.provider.value_counts().to_dict(), manifest_sha256=c.sha(c.OUT/'manifest.json'),
        script_sha256=c.sha(Path(__file__)), sources=sources,
        intervals='10,000 question-cluster bootstrap, pointwise 95%, exploratory, no multiplicity correction',
        limitations=['Unmatched cells contain different question mixtures and unequal wording weights',
                     'Complete-case observations may depend on delivery and nonanswers',
                     'Matched control comparisons contain independent stochastic calls, not latent belief or causal individual flips',
                     'Completion tokens are API output usage, not uniformly measured reasoning tokens',
                     'Lexical mention rules are unvalidated descriptions, not faithfulness measurements'])
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print('OUTPUT',out)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['sources','script_sha256','manifest_sha256']},indent=2))
    print('RATES\n',pd.DataFrame(rates).to_string(index=False))
    print('MATCHED CONTROLS\n',pd.DataFrame(matches).to_string(index=False))
    print('LENGTHS\n',pd.DataFrame(lengths).to_string(index=False))
    print('EXACT RATE PAIRS\n',pd.DataFrame(paired).to_string(index=False))


if __name__ == '__main__':
    main()

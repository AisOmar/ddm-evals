"""Frozen descriptive analysis; rejects incomplete or operationally failed pilots."""
from collections import Counter
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wording_collection', ROOT/'scripts/70_wording_collect.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
BASE = w.BASE
VERSIONS = ('plain','neutral','trap')
ADVICE = ('none','correct','wrong')


def summarize(records):
    """Use planned denominators for contrasts; show selected conditional accuracy separately."""
    expected = {(f'W{i:02}',model,version,advice,repeat)
                for i in range(1,9) for model in w.p.MODELS for version in VERSIONS
                for advice in ADVICE for repeat in (1,2)}
    keys = [(r['item_id'],r['model'],r['version'],r['advice'],r['repeat']) for r in records]
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError('All 288 distinct finalized pilot trials required')
    cells = []
    metric_arrays = {}
    item_ids = [f'W{i:02}' for i in range(1,9)]
    for model in w.p.MODELS:
        rates = {}
        for version in VERSIONS:
            for advice in ADVICE:
                rows = [r for r in records if (r['model'],r['version'],r['advice']) == (model,version,advice)]
                n_correct = sum(r['outcome']['correct'] is True for r in rows)
                n_answered = sum(r['outcome']['status']=='answered' for r in rows)
                cells.append(dict(model=model,version=version,advice=advice,planned=len(rows),
                    recognized=n_answered,correct=n_correct,
                    strict_format=sum(r['outcome']['strict_format'] is True for r in rows),
                    outcomes=dict(Counter(r['outcome']['status'] for r in rows)),
                    correct_planned=n_correct/len(rows),
                    correct_recognized=n_correct/n_answered if n_answered else None))
                rates[version,advice] = np.array([sum(r['outcome']['correct'] is True for r in rows if r['item_id']==item)/2 for item in item_ids])
        harm = {v:rates[v,'none']-rates[v,'wrong'] for v in VERSIONS}
        benefit = {v:rates[v,'correct']-rates[v,'none'] for v in VERSIONS}
        metric_arrays[model] = dict(
            trap_minus_plain_no_advice=rates['trap','none']-rates['plain','none'],
            neutral_minus_plain_no_advice=rates['neutral','none']-rates['plain','none'],
            trap_minus_plain_wrong_advice_harm=harm['trap']-harm['plain'],
            trap_minus_plain_correct_advice_benefit=benefit['trap']-benefit['plain'])
    # Share resampled underlying problems across all models and conditions.
    draws = np.random.default_rng(20261022069).integers(0,8,size=(10000,8))
    contrasts = []
    for model, metrics in metric_arrays.items():
        for name, values in metrics.items():
            boot = values[draws].mean(axis=1)
            low, high = np.quantile(boot,[.025,.975])
            contrasts.append(dict(model=model,contrast=name,estimate=float(values.mean()),
                pointwise_95_low=float(low),pointwise_95_high=float(high),
                by_problem={key:float(value) for key,value in zip(item_ids,values)},
                independent_units=8,bootstrap_draws=10000))
    return dict(cells=cells,contrasts=contrasts,n_finalized=len(records),
                inference='descriptive fixed-item pilot; pointwise intervals, no efficacy or safety claim')


def analyze():
    w.configure('pilot')
    manifest, indexed = w.audit_phase('pilot')
    records = [dict(**{k:t[k] for k in ('sample_id','item_id','model','version','advice','repeat')},
                    outcome=indexed[t['sample_id']]['outcome']) for t in manifest['trials']]
    result = summarize(records)
    finals = list(indexed.values())
    result.update(recorded_cost_usd=str(sum((Decimal(f['recorded_cost_usd']) for f in finals if f['recorded_cost_usd'] is not None),Decimal(0))),
                  missing_cost_metadata=sum(f['missing_cost_metadata'] for f in finals),
                  manifest_sha256=w.p.sha(BASE/'pilot/manifest.json'))
    w.p.save(BASE/'pilot/analysis.json',result)
    w.p.save(BASE/'pilot/scored_runs.json',records)
    lines = ['# Wording pilot results','',
        'All 288 planned pilot trials were finalized with valid operational records. '
        'This is a descriptive experiment on eight fixed problems, not a general robustness or safety result.','',
        '| Model | Wording | Advice | Correct / planned | Correct / recognized | Strict format |',
        '| --- | --- | --- | --- | --- | --- |']
    for cell in result['cells']:
        lines.append(f"| {cell['model']} | {cell['version']} | {cell['advice']} | {cell['correct']}/{cell['planned']} | {cell['correct']}/{cell['recognized']} | {cell['strict_format']}/{cell['planned']} |")
    lines += ['', '## Paired descriptive contrasts', '',
        'Values are percentage points of correct-response yield. Intervals resample the eight '
        'underlying problems, carrying all calls together; they are pointwise and unadjusted.', '',
        '| Model | Contrast | Estimate | Pointwise 95% interval |','| --- | --- | ---: | --- |']
    for contrast in result['contrasts']:
        lines.append(f"| {contrast['model']} | {contrast['contrast']} | {100*contrast['estimate']:.1f} | {100*contrast['pointwise_95_low']:.1f} to {100*contrast['pointwise_95_high']:.1f} |")
    lines += ['', '## Limits and accounting','',
        'A yield difference can reflect nonanswers rather than factual errors; inspect the outcome counts '
        'in analysis.json. Conditional accuracy uses selected recognized subsets. Ceiling-degenerate '
        'intervals do not show equivalence. Several independently reviewed plain/trap manipulations '
        'are weak; familiar templates and length differences limit interpretation. '
        'Do not combine these calls with previous studies.', '',
        'Recorded pilot cost: $'+result['recorded_cost_usd']+'. Missing cost records: '+str(result['missing_cost_metadata'])+'. '
        'Resource checks and their cost are reported separately. No original-study restart.', '']
    with (BASE/'pilot/REPORT.md').open('x') as f:
        f.write('\n'.join(lines))
    print(json.dumps(dict(n_finalized=288,recorded_cost_usd=result['recorded_cost_usd'],report=str(BASE/'pilot/REPORT.md'))))


if __name__ == '__main__':
    analyze()

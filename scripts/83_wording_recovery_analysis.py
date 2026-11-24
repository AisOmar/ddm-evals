"""Complete-cohort analysis with original statistics and explicit retry/cost lineage."""
from collections import Counter
from decimal import Decimal
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


r=module('recovered_pilot','82_wording_bounded_recovery.py')
analysis=module('original_wording_statistics','69_wording_analysis.py')


def delivery_report():
    r.configure();m=r.manifest();s=r.state(m)
    new_finals=[r.c.load(r.OUT/'finished'/(x['sample_id']+'.json')) for x in s['records']]
    old_finals=[r.c.load(p) for p in (r.q.OUT/'finished').glob('*.json')]
    all_finals=old_finals+new_finals
    summary=dict(verified_at=r.p.now(),logical_completed=len(s['completed']),logical_planned=288,
        retained_original=125,new_attempts=len(s['records']),new_retries=s['retries'],stop=s['stop'],
        new_attempt_outcomes=dict(Counter(f['outcome']['status'] for f in new_finals)),
        all_attempt_outcomes=dict(Counter(f['outcome']['status'] for f in all_finals)),
        recorded_new_recovery_cost_usd=str(sum((Decimal(f['recorded_cost_usd']) for f in new_finals if f['recorded_cost_usd'] is not None),Decimal(0))),
        recorded_pilot_cost_usd=str(sum((Decimal(f['recorded_cost_usd']) for f in all_finals if f['recorded_cost_usd'] is not None),Decimal(0))),
        missing_cost_records=sum(f['missing_cost_metadata'] for f in all_finals),
        recovery_full_reserve_usd=m['maximum_cost_usd'],attempt_reservations_used_usd=str(s['reserved']),
        unresolved_ids=[t['sample_id'] for t in m['trials'] if t['sample_id'] not in s['completed']],
        original_manifest_sha256=m['original_manifest_sha256'],recovery_manifest_sha256=r.p.sha(r.OUT/'manifest.json'),
        original_study_remains_paused=True)
    r.p.save(r.BASE/'delivery_summary.json',summary)
    print(r.c.json.dumps({k:v for k,v in summary.items() if k!='unresolved_ids'},indent=2))
    return summary


def analyze():
    r.configure();r.q.gates();m,s=r.audit_complete()
    records=[];lineage=[]
    for trial in m['trials']:
        rid=trial['sample_id'];path=ROOT/s['completed'][rid];final=r.c.load(path)
        records.append(dict(**{k:trial[k] for k in ('sample_id','item_id','model','version','advice','repeat')},outcome=final['outcome']))
        lineage.append(dict(sample_id=rid,final_path=str(path.relative_to(ROOT)),final_sha256=r.p.sha(path),
            retained_original=rid in m['retained_deliveries'],attempt_id=final['sample_id'],total_attempts=s['counts'].get(rid,1)))
    result=analysis.summarize(records)
    delivery=r.c.load(r.BASE/'delivery_summary.json')
    result.update(recorded_cost_usd=delivery['recorded_pilot_cost_usd'],missing_cost_metadata=delivery['missing_cost_records'],
        recovery_manifest_sha256=r.p.sha(r.OUT/'manifest.json'),original_manifest_sha256=m['original_manifest_sha256'],
        collection_disclosure='Original 125 deliveries retained; operational-metadata-only recovery amendment before accuracy inspection; rejected attempts preserved separately.')
    r.p.save(r.BASE/'analysis.json',result);r.p.save(r.BASE/'scored_runs.json',records);r.p.save(r.BASE/'response_lineage.json',lineage)
    lines=['# Completed wording pilot after bounded delivery recovery','',
        'All 288 original logical trials have one delivered response. The first 125 responses were retained '
        'unchanged; rate-limit rejections were preserved separately under the frozen delivery amendment. '
        'Questions, requests, model deployments, scoring and statistical calculations stayed fixed.','',
        '| Model | Wording | Advice | Correct / planned | Correct / recognized | Strict final A/B |',
        '| --- | --- | --- | ---: | ---: | ---: |']
    for cell in result['cells']:
        lines.append(f"| {cell['model']} | {cell['version']} | {cell['advice']} | {cell['correct']}/{cell['planned']} | {cell['correct']}/{cell['recognized']} | {cell['strict_format']}/{cell['planned']} |")
    lines+=['','## Paired descriptive contrasts','',
        'Percentage points of correct-response yield; pointwise 95% intervals from 10,000 resamples '
        'of the eight underlying problems. No confirmatory p-values or multiplicity-adjusted discoveries.','',
        '| Model | Contrast | Estimate | Pointwise 95% interval |','| --- | --- | ---: | --- |']
    for row in result['contrasts']:
        lines.append(f"| {row['model']} | {row['contrast']} | {100*row['estimate']:.1f} | {100*row['pointwise_95_low']:.1f} to {100*row['pointwise_95_high']:.1f} |")
    lines+=['','## Interpretation and accounting','',
        'This fixed-item development pilot does not establish general trick-question robustness, '
        'efficacy, equivalence, learned trust or overall safety. Several wording manipulations are weak. '
        'Conditional accuracy selects recognized outputs; yield can mix correctness with nonanswers. '
        'Ceiling-degenerate intervals are not equivalence evidence. Collection spans a capacity pause '
        'and a prospectively recorded operational amendment, without interim accuracy inspection.','',
        f"Recorded pilot charges across original and recovery attempts: ${delivery['recorded_pilot_cost_usd']}. "
        f"New recovery charges: ${delivery['recorded_new_recovery_cost_usd']}. "
        f"Missing cost records across all attempts: {delivery['missing_cost_records']}. "
        'Error reservations are preserved; recorded sums are not a billing reconciliation.','',
        'See delivery_summary.json for all attempt outcomes and retry allocation, response_lineage.json '
        'for exactly one delivered response per trial, and scored_runs.json for final outcome-specific '
        'denominators. Prior failures and the original 9,000-call study remain unchanged.','']
    with (r.BASE/'REPORT.md').open('x') as f:f.write('\n'.join(lines))
    print(r.c.json.dumps(dict(logical_completed=288,report=str(r.BASE/'REPORT.md'),recorded_pilot_cost_usd=delivery['recorded_pilot_cost_usd'])))


if __name__=='__main__':
    delivery_report()
    analyze()

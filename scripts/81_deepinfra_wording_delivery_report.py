"""Audit a stopped pilot cohort and report operations only, without accuracy inspection."""
from collections import Counter
from decimal import Decimal
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('stopped_wording_pilot',ROOT/'scripts/79_deepinfra_wording_pilot.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)


def report():
    q.configure();q.gates();m=q.w.manifest();attempts=q.c.history(m)
    if (q.OUT/'active.json').exists():raise ValueError('Unresolved attempt')
    paths=list((q.OUT/'finished').glob('*.json'));finals={p.stem:q.c.load(p) for p in paths}
    if len(finals)!=len(paths) or set(finals)!={a['sample_id'] for a in attempts}:
        raise ValueError('Each attempt must have exactly one finalization')
    rows=[]
    for trial in m['trials'][:len(attempts)]:
        rid=trial['sample_id'];f=finals[rid]
        for folder,suffix,key in [('requests','.json','request_sha256'),('raw','.json','raw_sha256'),('headers','.txt','headers_sha256')]:
            path=q.OUT/folder/(rid+suffix)
            if path.exists():
                if q.p.sha(path)!=f[key]:raise ValueError('Artifact changed: '+rid)
            elif f[key] is not None:raise ValueError('Missing artifact: '+rid)
        if q.c.load(q.OUT/'requests'/(rid+'.json'))!=trial['request'] or f['manifest_sha256']!=q.p.sha(q.OUT/'manifest.json'):
            raise ValueError('Request or manifest drift')
        try:raw=q.c.load(q.OUT/'raw'/(rid+'.json'))
        except (ValueError,OSError):raw={}
        usage=(raw.get('usage') or {}) if isinstance(raw,dict) else {}
        reasoning=(usage.get('completion_tokens_details') or {}).get('reasoning_tokens')
        completion=usage.get('completion_tokens')
        # Do not read, summarize or export the factual correctness field.
        rows.append(dict(sample_id=rid,model=trial['model'],expected_provider=trial['expected_provider'],
            status=f['outcome']['status'],strict_format=f['outcome']['strict_format'],
            recorded_cost_usd=f['recorded_cost_usd'],missing_cost_metadata=f['missing_cost_metadata'],
            continue_permitted=f['continue_permitted'],curl_exit=f['curl_exit'],http_status=f['http_status'],
            completion_tokens=completion,reported_reasoning_tokens=reasoning,
            reasoning_count_exceeds_completion=isinstance(reasoning,int) and isinstance(completion,int) and reasoning>completion))
    by_model=[]
    for model in q.p.MODELS:
        group=[row for row in rows if row['model']==model]
        by_model.append(dict(model=model,planned=144,attempted=len(group),
            outcomes=dict(Counter(row['status'] for row in group)),strict_format=sum(row['strict_format'] is True for row in group),
            recorded_cost_usd=str(sum((Decimal(row['recorded_cost_usd']) for row in group if row['recorded_cost_usd'] is not None),Decimal(0))),
            missing_cost_metadata=sum(row['missing_cost_metadata'] for row in group)))
    summary=dict(verified_at=q.p.now(),planned=288,attempted=len(rows),finalized=len(rows),
        outcomes=dict(Counter(row['status'] for row in rows)),by_model=by_model,
        stopped=any(not row['continue_permitted'] for row in rows),
        recorded_cost_usd=str(sum((Decimal(row['recorded_cost_usd']) for row in rows if row['recorded_cost_usd'] is not None),Decimal(0))),
        missing_cost_metadata=sum(row['missing_cost_metadata'] for row in rows),
        reasoning_count_inconsistencies=sum(row['reasoning_count_exceeds_completion'] for row in rows),
        unsent_ids=[t['sample_id'] for t in m['trials'][len(attempts):]],
        manifest_sha256=q.p.sha(q.OUT/'manifest.json'),accuracy_inspected=False,effects_analyzed=False,
        original_study_remains_paused=True)
    q.p.save(q.BASE/'delivery_observations.json',rows);q.p.save(q.BASE/'delivery_summary.json',summary)
    lines=['# DeepInfra wording pilot delivery status','',
        f"Finalized {len(rows)}/288 planned attempts. Collection stopped: {summary['stopped']}. "
        f"Outcomes: {summary['outcomes']}.",'',
        '| Model | Attempted / planned | Outcome counts | Strict final A/B | Recorded cost | Missing costs |',
        '| --- | ---: | --- | ---: | ---: | ---: |']
    for s in by_model:
        lines.append(f"| {s['model']} | {s['attempted']}/144 | {s['outcomes']} | {s['strict_format']} | ${s['recorded_cost_usd']} | {s['missing_cost_metadata']} |")
    lines+=['',f"Recorded new cost: ${summary['recorded_cost_usd']}. Unsent requests: {len(summary['unsent_ids'])}.",'',
        'This report audits delivery and costs only. It does not inspect factual correctness '
        'or calculate incomplete-cohort wording/advice effects. Failed trials were not retried '
        'or replaced. Non-strict recognized answers retain their frozen classification. '
        'All earlier artifacts remain separate, and the original study stays paused.','']
    with (q.BASE/'DELIVERY_REPORT.md').open('x') as f:f.write('\n'.join(lines))
    print(q.c.json.dumps({k:v for k,v in summary.items() if k!='unsent_ids'},indent=2))


if __name__=='__main__':report()

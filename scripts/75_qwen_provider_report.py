"""Audit the fixed paired provider cohort and report delivery without accuracy claims."""
from collections import Counter
from datetime import datetime
from decimal import Decimal
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


q=module('provider_comparison','74_qwen_provider_comparison.py')
helper=module('provider_observations','73_qwen_diagnostic_report.py')


def summarize(rows,complete):
    providers=[]
    for name in q.ROUTES:
        group=[r for r in rows if r['mode']==name]
        recognized=sum(r['visible_recognized'] for r in group)
        providers.append(dict(provider=name,planned=6,attempted=len(group),recognized=recognized,
            strict_format=sum(r['strict_format'] is True for r in group),
            empty_content=sum(r['content_empty'] for r in group),
            outcomes=dict(Counter(r['status'] for r in group)),
            candidate_for_new_resource_gate=complete and len(group)==6 and recognized==6))
    return dict(complete=complete,planned=12,attempted=len(rows),providers=providers,
        recorded_cost_usd=str(sum((Decimal(r['recorded_cost_usd']) for r in rows if r['recorded_cost_usd'] is not None),Decimal(0))),
        missing_cost_metadata=sum(r['missing_cost_metadata'] for r in rows),
        comparison='Same fresh questions/settings; different explicitly pinned FP8 serving deployments',
        inference='Small operational development cohort; no accuracy ranking or sustained reliability claim')


def report():
    q.configure();m=q.w.manifest();attempts=q.c.history(m)
    if (q.OUT/'active.json').exists():raise ValueError('An attempt remains active')
    paths=list((q.OUT/'finished').glob('*.json'));finals={path.stem:q.c.load(path) for path in paths}
    if len(finals)!=len(paths) or set(finals)!={x['sample_id'] for x in attempts}:
        raise ValueError('All attempts must be finalized exactly once')
    rows=[]
    for t in m['trials'][:len(attempts)]:
        rid=t['sample_id'];f=finals[rid]
        for folder,suffix,key in [('requests','.json','request_sha256'),('raw','.json','raw_sha256'),('headers','.txt','headers_sha256')]:
            path=q.OUT/folder/(rid+suffix)
            if path.exists():
                if q.p.sha(path)!=f[key]:raise ValueError('Artifact changed: '+rid)
            elif f[key] is not None:raise ValueError('Missing artifact: '+rid)
        if q.c.load(q.OUT/'requests'/(rid+'.json'))!=t['request'] or f['manifest_sha256']!=q.p.sha(q.OUT/'manifest.json'):
            raise ValueError('Request or manifest mismatch')
        try:raw=q.c.load(q.OUT/'raw'/(rid+'.json'))
        except (OSError,ValueError):raw={}
        row=helper.observations(t,raw,f)
        row['elapsed_preparation_to_finalization_seconds']=(datetime.fromisoformat(f['finished_at'])-datetime.fromisoformat(f['prepared_at'])).total_seconds()
        rows.append(row)
    complete=len(rows)==12 and all(f['continue_permitted'] for f in finals.values())
    summary=summarize(rows,complete)
    summary.update(verified_at=q.p.now(),manifest_sha256=q.p.sha(q.OUT/'manifest.json'),full_reserve_usd=m['maximum_cost_usd'],
                   unsent_ids=[t['sample_id'] for t in m['trials'][len(attempts):]])
    q.p.save(q.BASE/'observations.json',rows);q.p.save(q.BASE/'summary.json',summary)
    lines=['# Qwen provider delivery comparison results','',
        f"Attempted {len(rows)}/12 fixed calls. Recorded cost ${summary['recorded_cost_usd']}; missing cost records: {summary['missing_cost_metadata']}.",'',
        '| Provider / FP8 | Recognized choices / planned | Strict final A/B | Empty content | Attempted |',
        '| --- | ---: | ---: | ---: | ---: |']
    for s in summary['providers']:
        lines.append(f"| {s['provider']} | {s['recognized']}/6 | {s['strict_format']}/6 | {s['empty_content']} | {s['attempted']} |")
    lines += ['', 'Only a complete six-of-six recognized cohort qualifies a provider as a candidate for '
        'new resource checks. Strict format is reported separately. The unchanged final-line parser '
        'never searches earlier prose or reasoning for a replacement final answer.','',
        'This small paired development comparison cannot establish sustained reliability or identify '
        'which model/serving/gateway component caused earlier failures. Questions are fresh instances '
        'of shared reasoning templates; no factual-competence or safety ranking is inferred.','',
        'Earlier failed cells were not retried or replaced. No new resource gate or 288-call pilot '
        'was started, and the original 9,000-call study stays paused. Frozen requests, reservations, '
        'raw responses, headers, HTTP/finalization records, and exact unsent IDs are preserved.','']
    with (q.BASE/'REPORT.md').open('x') as f:f.write('\n'.join(lines))
    print(q.c.json.dumps(summary,indent=2))


if __name__=='__main__':report()

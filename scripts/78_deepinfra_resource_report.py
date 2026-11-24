"""Integrity audit and resource-only report; never infers wording/advice effects."""
from collections import Counter
from datetime import datetime
from decimal import Decimal
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('deepinfra_resource_report',ROOT/'scripts/77_deepinfra_resource_collect.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)


def gate_passed(rows):
    return len(rows)==16 and all(r['status']=='answered' and r['continue_permitted'] for r in rows)


def report():
    q.configure();q.review_gate();m=q.w.manifest();attempts=q.c.history(m)
    if (q.OUT/'active.json').exists():raise ValueError('Active attempt remains')
    paths=list((q.OUT/'finished').glob('*.json'));finals={path.stem:q.c.load(path) for path in paths}
    if len(finals)!=len(paths) or set(finals)!={a['sample_id'] for a in attempts}:
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
            raise ValueError('Request or manifest changed')
        try:raw=q.c.load(q.OUT/'raw'/(rid+'.json'))
        except (ValueError,OSError):raw={}
        choices=raw.get('choices') if isinstance(raw,dict) else None
        choice=choices[0] if isinstance(choices,list) and choices else {}
        message=choice.get('message') or {};usage=(raw.get('usage') or {}) if isinstance(raw,dict) else {}
        completion=usage.get('completion_tokens');reasoning=(usage.get('completion_tokens_details') or {}).get('reasoning_tokens')
        rows.append(dict(sample_id=rid,family=t['family'],model=t['model'],provider=t['expected_provider'],
            status=f['outcome']['status'],strict_format=f['outcome']['strict_format'],
            continue_permitted=f['continue_permitted'],finish_reason=choice.get('finish_reason'),
            empty_visible_content=not (message.get('content') or '').strip(),completion_tokens=completion,
            reasoning_tokens=reasoning,reasoning_count_exceeds_completion=isinstance(reasoning,int) and isinstance(completion,int) and reasoning>completion,
            elapsed_preparation_to_finalization_seconds=(datetime.fromisoformat(f['finished_at'])-datetime.fromisoformat(f['prepared_at'])).total_seconds(),
            recorded_cost_usd=f['recorded_cost_usd'],missing_cost_metadata=f['missing_cost_metadata']))
    passed=gate_passed(rows)
    summary=dict(verified_at=q.p.now(),planned=16,attempted=len(rows),resource_gate_passed=passed,
        outcomes=dict(Counter(r['status'] for r in rows)),strict_format=sum(r['strict_format'] is True for r in rows),
        reasoning_count_inconsistencies=sum(r['reasoning_count_exceeds_completion'] for r in rows),
        recorded_cost_usd=str(sum((Decimal(r['recorded_cost_usd']) for r in rows if r['recorded_cost_usd'] is not None),Decimal(0))),
        missing_cost_metadata=sum(r['missing_cost_metadata'] for r in rows),
        full_reserve_usd=m['maximum_cost_usd'],unsent_ids=[t['sample_id'] for t in m['trials'][len(attempts):]],
        pilot_calls=0,original_study_remains_paused=True,factual_correctness_not_used_for_gate=True,
        manifest_sha256=q.p.sha(q.OUT/'manifest.json'))
    q.p.save(q.BASE/'observations.json',rows);q.p.save(q.BASE/'summary.json',summary)
    lines=['# DeepInfra wording resource qualification results','',
        f"Resource gate {'passed' if passed else 'did not pass'}: {len(rows)}/16 planned calls attempted. No pilot calls were sent.",'',
        '| Trial | Provider | Outcome | Strict format | Completion tokens | Elapsed seconds | Recorded cost |',
        '| --- | --- | --- | --- | ---: | ---: | ---: |']
    for row in rows:
        lines.append(f"| {row['sample_id']} | {row['provider']} | {row['status']} | {row['strict_format']} | {row['completion_tokens']} | {row['elapsed_preparation_to_finalization_seconds']:.2f} | ${row['recorded_cost_usd']} |")
    lines+=['',f"Recorded new cost: ${summary['recorded_cost_usd']}; missing cost records: {summary['missing_cost_metadata']}. "
        f"Optional reasoning-token inconsistencies: {summary['reasoning_count_inconsistencies']}.",'',
        'Elapsed time includes preparation and orchestration, not isolated generation time. '
        'Factual correctness never determined qualification. No hidden-reasoning rescue, '
        'retry, provider substitution or original-study restart occurred.','',
        'A pass qualifies this deployment pair on eight representative development probes only. '
        'It does not guarantee sustained reliability, establish factual competence, or validate '
        'a safety metric. A failed gate blocks pilot preparation under this qualification. '
        'No 288-call pilot is launched automatically.','']
    with (q.BASE/'REPORT.md').open('x') as f:f.write('\n'.join(lines))
    print(q.c.json.dumps(summary,indent=2))


if __name__=='__main__':report()

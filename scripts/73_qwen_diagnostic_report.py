"""Audit all attempted diagnostic trials and report visible-answer delivery by mode."""
from collections import Counter
from decimal import Decimal
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qwen_diagnostic',ROOT/'scripts/72_qwen_delivery_diagnostic.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


def observations(trial,raw,final):
    choices=raw.get('choices') if isinstance(raw,dict) else None
    choice=choices[0] if isinstance(choices,list) and choices and isinstance(choices[0],dict) else {}
    message=choice.get('message') or {}
    content=message.get('content')
    reasoning=message.get('reasoning')
    usage=raw.get('usage') or {} if isinstance(raw,dict) else {}
    details=usage.get('completion_tokens_details') or {}
    return dict(sample_id=trial['sample_id'],item_id=trial['item_id'],repeat=trial['repeat'],mode=trial['mode'],
        status=final['outcome']['status'],visible_choice=final['outcome']['choice'],
        visible_recognized=final['outcome']['status']=='answered',strict_format=final['outcome']['strict_format'],
        content_null=content is None,content_empty=not isinstance(content,str) or not content.strip(),
        content_characters=len(content) if isinstance(content,str) else None,
        reasoning_characters=len(reasoning) if isinstance(reasoning,str) else None,
        leaked_im_end_in_reasoning=isinstance(reasoning,str) and '<|im_end|>' in reasoning,
        leaked_im_end_in_content=isinstance(content,str) and '<|im_end|>' in content,
        finish_reason=choice.get('finish_reason'),completion_tokens=usage.get('completion_tokens'),
        reported_reasoning_tokens=details.get('reasoning_tokens'),
        recorded_cost_usd=final['recorded_cost_usd'],missing_cost_metadata=final['missing_cost_metadata'],
        operational_continue_permitted=final['continue_permitted'])


def summarize(rows,complete):
    summaries=[]
    for mode in d.MODES:
        group=[r for r in rows if r['mode']==mode]
        visible=sum(r['visible_recognized'] for r in group)
        summaries.append(dict(mode=mode,planned=6,attempted=len(group),visible_recognized=visible,
            strict_format=sum(r['strict_format'] is True for r in group),
            empty_visible_content=sum(r['content_empty'] for r in group),
            reasoning_present=sum((r['reasoning_characters'] or 0)>0 for r in group),
            outcomes=dict(Counter(r['status'] for r in group)),
            candidate_for_new_qualification=complete and len(group)==6 and visible==6))
    return dict(complete=complete,n_planned=18,n_attempted=len(rows),modes=summaries,
        recorded_cost_usd=str(sum((Decimal(r['recorded_cost_usd']) for r in rows if r['recorded_cost_usd'] is not None),Decimal(0))),
        missing_cost_metadata=sum(r['missing_cost_metadata'] for r in rows),
        interpretation='operational development diagnostic; no original-run rescue, accuracy inference, or verified root cause')


def report():
    d.configure();m=d.w.manifest();attempts=d.c.history(m)
    if (d.OUT/'active.json').exists():raise ValueError('An attempt is still active')
    paths=list((d.OUT/'finished').glob('*.json'))
    indexed={path.stem:d.c.load(path) for path in paths}
    if len(indexed)!=len(paths) or set(indexed)!={a['sample_id'] for a in attempts}:
        raise ValueError('Every attempt must be finalized exactly once')
    rows=[]
    for trial in m['trials'][:len(attempts)]:
        rid=trial['sample_id'];f=indexed[rid]
        for folder,suffix,key in [('requests','.json','request_sha256'),('raw','.json','raw_sha256'),('headers','.txt','headers_sha256')]:
            path=d.OUT/folder/(rid+suffix)
            if path.exists():
                if d.p.sha(path)!=f[key]:raise ValueError('Artifact changed: '+rid)
            elif f[key] is not None:raise ValueError('Missing artifact: '+rid)
        if d.c.load(d.OUT/'requests'/(rid+'.json'))!=trial['request'] or f['manifest_sha256']!=d.p.sha(d.OUT/'manifest.json'):
            raise ValueError('Request or manifest drift')
        try:raw=d.c.load(d.OUT/'raw'/(rid+'.json'))
        except (OSError,ValueError):raw={}
        rows.append(observations(trial,raw,f))
    complete=len(rows)==18 and all(f['continue_permitted'] for f in indexed.values())
    summary=summarize(rows,complete)
    summary.update(verified_at=d.p.now(),manifest_sha256=d.p.sha(d.OUT/'manifest.json'),
        unsent_ids=[t['sample_id'] for t in m['trials'][len(attempts):]],full_reserve_usd=m['maximum_cost_usd'])
    d.p.save(d.BASE/'observations.json',rows);d.p.save(d.BASE/'summary.json',summary)
    lines=['# Qwen visible answer diagnostic results','',
        f"Executed {len(rows)}/18 fixed diagnostic calls. Recorded cost ${summary['recorded_cost_usd']}; missing cost records: {summary['missing_cost_metadata']}.",'',
        '| Mode | Visible choices / planned | Attempted | Empty visible content | Responses with reasoning |',
        '| --- | ---: | ---: | ---: | ---: |']
    for s in summary['modes']:
        lines.append(f"| {s['mode']} | {s['visible_recognized']}/6 | {s['attempted']} | {s['empty_visible_content']} | {s['reasoning_present']} |")
    lines += ['', 'A control is a candidate for new qualification only if all six planned responses '
        'normally terminate with a recognized visible choice and valid operational records. '
        'This small diagnostic cannot prove sustained reliability or that a provider honored an intended reasoning mode. '
        'Reasoning-field answers were never promoted into visible answers.','',
        'Default-mode successes do not erase the earlier missing-content response. A failure to reproduce '
        'that symptom in six calls does not establish a fix. The diagnostic does not isolate model generation '
        'from provider/gateway parsing. A changed reasoning control would define a new experimental configuration.','',
        'The original failed resource phase remains stopped at 3/16, and the 288-call wording pilot remains '
        'unrun. No original-study restart, retries, endpoint substitution, or advice collection occurred.','',
        'Exact per-trial observations, usage metadata, special-token indicators, and the unsent list are saved '
        'in observations.json and summary.json. Raw bodies, headers, reservations and frozen requests are '
        'under diagnostic/. See docs/QWEN_VISIBLE_ANSWER_DIAGNOSTIC_PROTOCOL.md for the frozen design.','']
    with (d.BASE/'REPORT.md').open('x') as f:f.write('\n'.join(lines))
    print(d.c.json.dumps(summary,indent=2))


if __name__=='__main__':report()

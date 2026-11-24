"""Complete-cohort, descriptive numerical calibration; no partial inference."""
from collections import Counter
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('baseline_runner',ROOT/'scripts/60_calibrate_reviewed_packet.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
OUT=b.OUT
FAMILIES=('recurrence','subset_count','shortest_path','urn_posterior')


def counts(rows):
    recognized=sum(r['outcome']['status']=='answered' for r in rows)
    correct=sum(r['outcome']['correct'] is True for r in rows)
    strict=sum(r['outcome']['strict_format'] is True for r in rows)
    n=len(rows);accuracy=correct/recognized if recognized else None
    return dict(n_planned=n,n_recognized=recognized,n_correct=correct,n_strict_format=strict,
        outcomes=dict(Counter(r['outcome']['status'] for r in rows)),
        correct_yield=correct/n if n else None,answered_accuracy=accuracy,
        strict_format_rate=strict/n if n else None,
        ambiguous_rate=sum(r['outcome']['status']=='ambiguous_format' for r in rows)/n if n else None,
        ceiling_warning=accuracy is not None and accuracy>.90,
        excessive_difficulty_warning=accuracy is not None and accuracy<.55,
        unavailable_warning=(n-recognized)/n>.05 if n else None)


def bootstrap(rows,seed=20261021061,n_draws=10000):
    rng=np.random.default_rng(seed);totals=np.zeros((n_draws,3),dtype=int)
    for family in sorted({r['family'] for r in rows}):
        group=[r for r in rows if r['family']==family]
        ids=sorted({r['item_id'] for r in group})
        values=[]
        for item in ids:
            items=[r for r in group if r['item_id']==item]
            values.append([sum(r['outcome']['correct'] is True for r in items),
                           sum(r['outcome']['status']=='answered' for r in items),len(items)])
        array=np.asarray(values)
        totals+=array[rng.integers(0,len(ids),size=(n_draws,len(ids)))].sum(axis=1)
    valid=totals[:,1]>0
    return dict(n_draws=n_draws,undefined_accuracy_draws=int((~valid).sum()),
        correct_yield_95=list(np.quantile(totals[:,0]/totals[:,2],[.025,.975])),
        answered_accuracy_95=list(np.quantile(totals[valid,0]/totals[valid,1],[.025,.975])) if valid.any() else None,
        method='Percentile question-cluster bootstrap within fixed family; repeats kept together; ceiling intervals can collapse')


def audit():
    m=b.manifest()
    if (OUT/'active.json').exists():raise ValueError('Active collection; no analysis')
    attempts=b.c.history(m)
    if len(attempts)!=96:raise ValueError('All 96 attempts required before calibration analysis')
    rows=[];cost=Decimal(0)
    for trial in m['trials']:
        rid=trial['sample_id'];path=OUT/'finished'/(rid+'.json')
        if not path.exists():raise ValueError('Attempt not finalized')
        final=b.c.load(path)
        if not final['continue_permitted']:raise ValueError('Operational stop prevents complete-cohort analysis')
        for folder,suffix,key in [('raw','.json','raw_sha256'),('headers','.txt','headers_sha256'),('requests','.json','request_sha256')]:
            if b.p.sha(OUT/folder/(rid+suffix))!=final[key]:raise ValueError('Artifact changed')
        if b.c.load(OUT/'requests'/(rid+'.json'))!=trial['request']:raise ValueError('Request mismatch')
        actual=b.a.result(trial,b.c.load(OUT/'raw'/(rid+'.json')),final['http_status'])
        if actual!=final['outcome']:raise ValueError('Outcome mismatch')
        amount=Decimal(final['recorded_cost_usd'])
        if not amount.is_finite() or not 0<=amount<=b.p.trial_bound(trial):raise ValueError('Cost invalid')
        cost+=amount
        rows.append(dict(sample_id=rid,item_id=trial['item_id'],family=trial['family'],repeat=trial['repeat'],
            model=trial['model'],provider=trial['expected_provider'],outcome=actual,usage=b.c.load(OUT/'raw'/(rid+'.json')).get('usage'),
            recorded_cost_usd=str(amount)))
    for folder in ('raw','requests','finished','http'):
        if {p.stem for p in (OUT/folder).glob('*.json')}!={t['sample_id'] for t in m['trials']}:raise ValueError('Unexpected/missing artifacts')
    if cost>Decimal(m['maximum_cost_usd']):raise ValueError('Total cost exceeds reserve')
    return m,rows,cost


def main():
    if (OUT/'analysis.json').exists():raise ValueError('Analysis exists; do not overwrite')
    m,rows,cost=audit();profiles=[]
    for model in b.a.ROUTES:
        for family in ('all',)+FAMILIES:
            selected=[r for r in rows if r['model']==model and (family=='all' or r['family']==family)]
            profiles.append(dict(model=model,provider=selected[0]['provider'],family=family,
                **counts(selected),intervals=bootstrap(selected)))
    result=dict(created_at=b.p.now(),complete=True,n_attempted=96,n_questions=24,n_fixed_families=4,
        manifest_sha256=b.p.sha(OUT/'manifest.json'),recorded_cost_usd=str(cost),full_reserve_usd=m['maximum_cost_usd'],
        profiles=profiles,rows=rows,advice_effect_measured=False,safety_metric_validated=False,
        original_study_remains_paused=True,followup_automatically_authorized=False)
    b.p.save(OUT/'analysis.json',result)
    lines=['# Reviewed numerical baseline calibration','','Complete: 96 initial attempts, 24 questions, two repetitions per model; no advice.',
        f'Recorded cost ${cost}; full reserve ${m["maximum_cost_usd"]}.','',
        '| Model / provider | Correct / recognized | Recognized / planned | Correct yield | Strict format / planned |',
        '| --- | ---: | ---: | ---: | ---: |']
    for row in profiles:
        if row['family']=='all':lines.append(f'| {row["model"]} / {row["provider"]} | {row["n_correct"]}/{row["n_recognized"]} | {row["n_recognized"]}/{row["n_planned"]} | {row["correct_yield"]:.1%} | {row["n_strict_format"]}/{row["n_planned"]} |')
    lines+=['','## Family detail','','| Model | Family | Correct / recognized | Recognized / planned |','| --- | --- | ---: | ---: |']
    for row in profiles:
        if row['family']!='all':lines.append(f'| {row["model"]} | {row["family"]} | {row["n_correct"]}/{row["n_recognized"]} | {row["n_recognized"]}/{row["n_planned"]} |')
    lines+=['','## Predeclared development warnings','']
    for row in profiles:
        if row['family']=='all':lines.append(f'- {row["model"]}: ceiling (>90%)={row["ceiling_warning"]}; excessive difficulty (<55%)={row["excessive_difficulty_warning"]}; unavailable answers (>5%)={row["unavailable_warning"]}.')
    lines+=['','These are development heuristics, not safety thresholds. Answered-only accuracy excludes nonanswers and can be selected. Full outcome categories, per-item denominators, and 10,000-draw within-family question-cluster bootstrap intervals are in analysis.json. Intervals can collapse at ceilings. Both repeats stay together; the four families remain fixed, and variants are not independent mechanisms.',
        '', 'This is fresh-context AI-reviewed, narrow numerical calibration. It measures neither helpful-advice benefit nor misleading-advice harm. Provider differences prevent direct attribution of cross-model differences to model weights. No efficacy, equivalence, ranking, unseen-family generalization or safety metric is established. The original 9,000-call study remains paused. No advice collection starts automatically.']
    with (OUT/'REPORT.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    print(json.dumps({k:result[k] for k in ('complete','n_attempted','recorded_cost_usd','safety_metric_validated')},indent=2))


if __name__=='__main__':main()

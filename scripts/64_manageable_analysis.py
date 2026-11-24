"""Complete-cohort descriptive analysis for the separate manageable packet."""
from decimal import Decimal
import importlib.util
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('manageable_runner',ROOT/'scripts/63_manageable_collect.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.configure('calibration');OUT=r.OUT
spec2=importlib.util.spec_from_file_location('prior_analysis',ROOT/'scripts/61_analyze_baseline_calibration.py')
h=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(h)


def audit():
    m=r.manifest()
    if (OUT/'active.json').exists():raise ValueError('Active collection')
    attempts=r.c.history(m)
    if len(attempts)!=64:raise ValueError('All 64 calibration attempts required before analysis')
    rows=[];cost=Decimal(0)
    for trial in m['trials']:
        rid=trial['sample_id'];final=r.c.load(OUT/'finished'/(rid+'.json'))
        if not final['continue_permitted']:raise ValueError('Operationally stopped collection')
        for folder,suffix,key in [('raw','.json','raw_sha256'),('headers','.txt','headers_sha256'),('requests','.json','request_sha256')]:
            if r.p.sha(OUT/folder/(rid+suffix))!=final[key]:raise ValueError('Changed artifact')
        if r.c.load(OUT/'requests'/(rid+'.json'))!=trial['request']:raise ValueError('Changed request')
        data=r.c.load(OUT/'raw'/(rid+'.json'));actual=r.a.result(trial,data,final['http_status'])
        if actual!=final['outcome']:raise ValueError('Outcome mismatch')
        amount=Decimal(final['recorded_cost_usd'])
        if not amount.is_finite() or not 0<=amount<=r.p.trial_bound(trial):raise ValueError('Cost invalid')
        cost+=amount
        from datetime import datetime
        elapsed=(datetime.fromisoformat(final['finished_at'])-datetime.fromisoformat(final['prepared_at'])).total_seconds()
        rows.append(dict(sample_id=rid,item_id=trial['item_id'],family=trial['family'],model=trial['model'],provider=trial['expected_provider'],
            repeat=trial['repeat'],outcome=actual,usage=data.get('usage'),recorded_cost_usd=str(amount),elapsed_seconds=elapsed))
    expected={t['sample_id'] for t in m['trials']}
    for folder in ('raw','requests','finished','http'):
        if {p.stem for p in (OUT/folder).glob('*.json')}!=expected:raise ValueError('Artifact coverage mismatch')
    if cost>Decimal(m['maximum_cost_usd']):raise ValueError('Cost exceeds reserve')
    return m,rows,cost


def main():
    if (OUT/'analysis.json').exists():raise ValueError('Analysis exists')
    m,rows,cost=audit();profiles=[]
    import numpy as np
    for model in r.a.ROUTES:
        for family in ('all',)+h.FAMILIES:
            selected=[x for x in rows if x['model']==model and (family=='all' or x['family']==family)]
            tokens=[x['usage']['completion_tokens'] for x in selected]
            profiles.append(dict(model=model,provider=selected[0]['provider'],family=family,**h.counts(selected),
                intervals=h.bootstrap(selected,seed=20261021065),median_completion_tokens=float(np.median(tokens)),
                maximum_completion_tokens=max(tokens),median_elapsed_seconds=float(np.median([x['elapsed_seconds'] for x in selected]))))
    result=dict(created_at=r.p.now(),n_attempted=64,n_calibration_questions=16,n_fixed_templates=4,complete=True,
        recorded_cost_usd=str(cost),full_reserve_usd=m['maximum_cost_usd'],profiles=profiles,rows=rows,
        resource_items_excluded=True,advice_effect_measured=False,safety_metric_validated=False,original_study_remains_paused=True)
    r.p.save(OUT/'analysis.json',result)
    lines=['# Manageable numerical baseline calibration','','64 initial attempts; sixteen calibration items, two repeats per model, no advice.',
        f'Recorded calibration cost ${cost}; reserve ${m["maximum_cost_usd"]}. Resource items are excluded.','',
        '| Model/provider | Correct/recognized | Recognized/planned | Correct yield | Strict format/planned |','| --- | ---: | ---: | ---: | ---: |']
    for x in profiles:
        if x['family']=='all':lines.append(f'| {x["model"]}/{x["provider"]} | {x["n_correct"]}/{x["n_recognized"]} | {x["n_recognized"]}/{x["n_planned"]} | {x["correct_yield"]:.1%} | {x["n_strict_format"]}/{x["n_planned"]} |')
    lines+=['','| Model | Family | Correct/recognized | Recognized/planned |','| --- | --- | ---: | ---: |']
    for x in profiles:
        if x['family']!='all':lines.append(f'| {x["model"]} | {x["family"]} | {x["n_correct"]}/{x["n_recognized"]} | {x["n_recognized"]}/{x["n_planned"]} |')
    lines+=['','Development warnings (heuristics, not safety thresholds):']
    for x in profiles:
        if x['family']=='all':lines.append(f'- {x["model"]}: ceiling={x["ceiling_warning"]}, excessive difficulty={x["excessive_difficulty_warning"]}, >5% unrecognized={x["unavailable_warning"]}.')
    lines+=['','Full outcomes, costs, token/time summaries and 10,000-draw question-cluster bootstrap intervals are in analysis.json. Repeats stay together; families are fixed. Four shared templates, small item counts and possibly degenerate ceiling intervals prevent broad generalization. Answered-only accuracy can be selected. Provider effects are mixed with model differences. No advice effect, efficacy, equivalence, ranking or validated safety metric is established. The original study remains paused; no advice study starts automatically.']
    with (OUT/'REPORT.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    print(json.dumps({k:result[k] for k in ('complete','n_attempted','recorded_cost_usd','safety_metric_validated')},indent=2))


if __name__=='__main__':main()

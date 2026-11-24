"""Join saved first-pass labels to scores after masked annotation is complete."""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/deference/trust_planning/exploratory/trace_audit_20261019'
FIELDS = ['key_acknowledged','credibility_evaluation','task_interpretation','factual_key_conflict','explicit_key_rejection']


def main():
    review = {x['audit_id']:x for x in map(json.loads,(OUT/'masked_review.jsonl').read_text().splitlines())}
    annotations = pd.read_json(OUT/'masked_annotations.jsonl', lines=True)
    selected = pd.read_csv(OUT/'selection.csv')
    assert len(annotations) == len(selected) == 36
    assert not annotations.audit_id.duplicated().any()
    assert not selected.sample_id.duplicated().any()
    for row in annotations.to_dict('records'):
        text = review[row['audit_id']]['reasoning']+'\n'+review[row['audit_id']]['completion']
        for quote in row['evidence']:
            assert quote in text
        assert all(row[f] in ['yes','no','unclear'] for f in FIELDS)
    d = selected.merge(annotations, on='audit_id', validate='one_to_one')
    assert (d.groupby(['model','key_correct','correct']).size() == 3).all()
    d.to_csv(OUT/'annotations_with_scores.csv', index=False)
    counts = {f:d[f].value_counts().to_dict() for f in FIELDS}
    summary = dict(n=36,labels=counts,resolutions=d.resolution.value_counts().to_dict(),
                   ambiguous=int(d.ambiguous.sum()),option_fit_concern=int(d.option_fit_concern.sum()),
                   caution='Outcome-balanced selected sample; counts are not population prevalence. Single AI analyst, no inter-rater reliability.',
                   score_unmasking='After masked_annotations.jsonl and annotation_metadata.json were saved',
                   masked_annotations_sha256=hashlib.sha256((OUT/'masked_annotations.jsonl').read_bytes()).hexdigest())
    for group, filename in [('model','counts_by_model.csv'),('correct','counts_by_answer_correctness.csv')]:
        d.groupby([group,'resolution']).size().unstack(fill_value=0).to_csv(OUT/filename)
    (OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
    print(d[['audit_id','model','key_correct','correct','rate','wording','task_interpretation','resolution','ambiguous','option_fit_concern']].to_string(index=False))
    print('MODEL RESOLUTIONS\n',d.groupby(['model','resolution']).size().unstack(fill_value=0).to_string())


if __name__ == '__main__':
    main()

"""Select a fixed, metadata-masked qualitative sample without network access."""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/deference/trust_planning'
SNAPSHOT = BASE / 'exploratory/deep_20261019T210911Z'
OUT = BASE / 'exploratory/trace_audit_20261019'
SEED = 20261019


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert json.loads((BASE/'orchestration_state.json').read_text())['status'] == 'paused_by_user'
    assert not (BASE/'active_batch.json').exists()
    if OUT.exists():
        raise ValueError('Refusing to overwrite audit selection')
    d = pd.read_csv(SNAPSHOT/'snapshot.csv')
    assert len(d) == 623
    sources = json.loads((SNAPSHOT/'summary.json').read_text())['sources']
    lookup = {Path(s['path']).name.split('.attempt')[0]: s for s in sources}
    selected = []
    for _, group in d[(d.wording != 'control') & d.correct.notna()].groupby(['model','key_correct','correct']):
        candidates = group.to_dict('records')
        chosen = []
        for _ in range(3):
            def priority(row):
                same_rate = sum(x['rate'] == row['rate'] for x in chosen)
                same_word = sum(x['wording'] == row['wording'] for x in chosen)
                digest = hashlib.sha256(f"{SEED}:{row['sample_id']}".encode()).hexdigest()
                return same_rate + same_word, digest
            pick = min(candidates, key=priority)
            candidates.remove(pick)
            chosen.append(pick)
        selected.extend(chosen)
    selected.sort(key=lambda x: hashlib.sha256(f"mask:{SEED}:{x['sample_id']}".encode()).hexdigest())
    reviews = []
    for i, row in enumerate(selected, 1):
        src = lookup[row['sample_id']]
        assert sha(BASE/src['path']) == src['sha256']
        response = json.loads((BASE/src['path']).read_text())
        msg = response['choices'][0]['message']
        reasoning = msg.get('reasoning') or '\n'.join(x.get('text','') for x in msg.get('reasoning_details',[]) if x.get('type') == 'reasoning.text')
        row.update(audit_id=f'A{i:02d}', source=src['path'], source_sha256=src['sha256'])
        reviews.append(dict(audit_id=row['audit_id'], reasoning=reasoning, completion=msg.get('content') or ''))
    OUT.mkdir()
    pd.DataFrame(selected).to_csv(OUT/'selection.csv', index=False)
    (OUT/'masked_review.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in reviews))
    (OUT/'selection_metadata.json').write_text(json.dumps(dict(seed=SEED,n_selected=len(selected),
        rubric_sha256=sha(ROOT/'docs/TRACE_AUDIT_RUBRIC.md'),snapshot_sha256=sha(SNAPSHOT/'snapshot.csv'),
        sampling='3 per model x actual key correctness x answer correctness; prefer balanced rate and wording; hash ties',
        masking='review IDs hide scored correctness, actual key correctness, model and source ID; text is complete',
        prior_inspection='Earlier informal examples and interim effects were already inspected',
        reviewer='single AI analyst; no measured inter-rater reliability'),indent=2)+'\n')
    print('Selected',len(reviews),'traces; review characters',sum(len(x['reasoning']) for x in reviews))
    print('Output:',OUT)
    print(pd.DataFrame(selected).groupby(['model','key_correct','correct']).size().to_string())


if __name__ == '__main__':
    main()

"""Build a separate, offline GSM8K/BBH development packet, never collect.

Stage select hides official answers for initial analyst review. Later stages
must preserve a locked review before reconciling the downloaded source keys.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/research_directions/open_dataset_packet_20261020'
SEED = '20261020:open-dataset-review-v1'
GSM_COMMIT = '3101c7d5072418e28b9008a6636bde82a006892c'
BBH_COMMIT = '9ee07bd481feebf959a6b59d61ea57bdcf30964d'
BBH_TASKS = ['boolean_expressions', 'date_understanding', 'dyck_languages',
             'logical_deduction_five_objects', 'multistep_arithmetic_two',
             'navigate', 'object_counting', 'reasoning_about_colored_objects',
             'tracking_shuffled_objects_five_objects', 'word_sorting']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_new(path, data):
    with path.open('x') as f:
        f.write(json.dumps(data, indent=2) + '\n')


def rank(dataset, index):
    return hashlib.sha256(f'{SEED}:{dataset}:{index}'.encode()).hexdigest()


def select():
    if (OUT / 'selection_manifest.json').exists():
        raise ValueError('Refusing to overwrite selection')
    sources = OUT / 'sources'
    gsm = [json.loads(line) for line in (sources / 'gsm8k_test.jsonl').read_text().splitlines()]
    assert len(gsm) == 1319
    masked, sidecar = [], []
    # Index 0 and its key appeared in the discovery web preview: exclude it.
    indices = sorted(range(1, len(gsm)), key=lambda i: rank('gsm8k_test', i))[:10]
    for serial, index in enumerate(indices, 1):
        x = gsm[index]
        rid = f'G{serial:02d}'
        masked.append(dict(review_id=rid, dataset='GSM8K', task='math_word_problem',
                           question=x['question']))
        sidecar.append(dict(review_id=rid, source_index_zero_based=index,
                            official_solution=x['answer'], source_file='gsm8k_test.jsonl',
                            source_url=f'https://github.com/openai/grade-school-math/blob/{GSM_COMMIT}/grade_school_math/data/test.jsonl'))
    for serial, task in enumerate(BBH_TASKS, 1):
        source = json.loads((sources / f'{task}.json').read_text())
        examples = source['examples']
        index = min(range(len(examples)), key=lambda i: rank(task, i))
        x = examples[index]
        rid = f'B{serial:02d}'
        masked.append(dict(review_id=rid, dataset='BBH', task=task, question=x['input']))
        sidecar.append(dict(review_id=rid, source_index_zero_based=index,
                            official_target=x['target'], source_file=f'{task}.json',
                            source_url=f'https://github.com/suzgunmirac/BIG-Bench-Hard/blob/{BBH_COMMIT}/bbh/{task}.json'))
    assert len(masked) == len({x['question'] for x in masked}) == 20
    with (OUT / 'masked_source_questions.jsonl').open('x') as f:
        f.write(''.join(json.dumps(x) + '\n' for x in masked))
    save_new(OUT / 'official_keys_sidecar.json', sidecar)
    save_new(OUT / 'selection_manifest.json', dict(
        created_at=datetime.now(timezone.utc).isoformat(), seed=SEED,
        scope='20-item cross-domain development packet; not a confirmatory collection manifest',
        dataset_counts={'GSM8K': 10, 'BBH': 10}, bbh_tasks=BBH_TASKS,
        selection_rule='GSM: first ten SHA256 ranks, excluding index 0 exposed during discovery. BBH: minimum SHA256 rank per task. No evaluated-model outcomes used.',
        pinned_commits={'GSM8K': GSM_COMMIT, 'BBH': BBH_COMMIT},
        source_hashes={p.name: sha(p) for p in sorted(sources.iterdir()) if p.is_file()},
        licenses={'GSM8K': 'MIT; see sources/GSM8K_LICENSE', 'BBH': 'MIT; see sources/BBH_LICENSE'},
        bbh_canary='Preserved in original source files; data intended for evaluation, not model training.',
        masked_questions_sha256=sha(OUT / 'masked_source_questions.jsonl'),
        official_keys_sidecar_sha256=sha(OUT / 'official_keys_sidecar.json'),
        script_sha256=sha(Path(__file__)), collection_ready=False,
        independent_review_complete=False, model_calls_launched=0,
        limitations=['Public datasets may have appeared in model training.',
                     'Dataset source keys are proposals pending review.',
                     'This development set does not inherit the frozen cybersecurity design or power assumptions.',
                     'No human or separate fresh-context AI reviewer has reviewed this packet.']))
    print('Saved 20 masked questions and separate official-key sidecar; no model calls.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['select'], required=True)
    args = parser.parse_args()
    if args.stage == 'select':
        select()


if __name__ == '__main__':
    main()

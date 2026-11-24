"""Finalize a review-only packet; preserve version 1 and all initial judgments."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/research_directions/open_dataset_packet_20261020'
OUT = BASE / 'v2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    with path.open('x') as f:
        f.write(json.dumps(value, indent=2) + '\n')


def jsonl(path, values):
    with path.open('x') as f:
        f.write(''.join(json.dumps(x) + '\n' for x in values))


def main():
    if OUT.exists():
        raise ValueError('Refusing to overwrite finalized review packet')
    original = json.loads((BASE / 'binary_items_v1.json').read_text())
    prompts = [json.loads(x) for x in (BASE / 'draft_prompts.jsonl').read_text().splitlines()]
    summary = json.loads((BASE / 'packet_summary.json').read_text())
    checks = json.loads((BASE / 'derivation_checks.json').read_text())
    if checks['script_sha256'] != sha(ROOT / 'scripts/47_check_open_packet.py'):
        raise ValueError('Derivation script changed')
    if not json.loads((BASE / 'key_reconciliation.json').read_text())['all_agree']:
        raise ValueError('Unresolved source-key disagreement')
    items = json.loads(json.dumps(original))
    old = 'Ask for the total number of boxes'
    new = 'Report the total number of boxes'
    item = next(x for x in items if x['review_id'] == 'G05')
    if item['question'].count(old) != 1:
        raise ValueError('Unexpected editorial source')
    old_question = item['question']
    item['question'] = old_question.replace(old, new)
    item['clarification'] = item['clarification'].replace(old, new)
    changed = 0
    for prompt in prompts:
        prompt['question_version'] = 2
        if prompt['review_id'] == 'G05':
            text = prompt['messages'][0]['content']
            if text.count(old_question) != 1:
                raise ValueError('Unexpected G05 prompt')
            prompt['messages'][0]['content'] = text.replace(old_question, item['question'])
            changed += 1
    if changed != 6:
        raise ValueError('Editorial fix must affect exactly six G05 conditions')
    for item in items:
        item['version'] = 2
        item['source_variant'] = 'binary_items_v1.json'
    masked = [{k: x[k] for k in ['review_id', 'dataset', 'task', 'version', 'question', 'options']} for x in items]
    # Exact local nonuse check is limited to these prior question banks, not training data.
    prior = set()
    normalize = lambda s: ' '.join(s.casefold().split())
    banks = [ROOT / 'data/processed/two_choice.jsonl',
             ROOT / 'results/research_directions/ambiguity_review/revised_candidates/accepted_items.json']
    for bank in banks:
        data = [json.loads(s) for s in bank.read_text().splitlines()] if bank.suffix == '.jsonl' else json.loads(bank.read_text())
        for row in data:
            for key in ['question', 'original_question']:
                if key in row:
                    prior.add(normalize(row[key]))
    overlap = [x['review_id'] for x in items if normalize(x['original_question']) in prior]
    if overlap:
        raise ValueError(f'Prior local question overlap: {overlap}')
    OUT.mkdir()
    dump(OUT / 'binary_items.json', items)
    jsonl(OUT / 'masked_binary_items.jsonl', masked)
    jsonl(OUT / 'draft_prompts.jsonl', prompts)
    dump(OUT / 'editorial_addendum.json', dict(
        change='G05 clarification says Report rather than Ask for, so the evaluation prompt asks for an answer.',
        old_text=old, new_text=new, answer_changed=False, n_prompts_changed=changed,
        version_1_preserved=True, source_items_sha256=sha(BASE / 'binary_items_v1.json'),
        source_prompts_sha256=sha(BASE / 'draft_prompts.jsonl')))
    summary.update(version=2, finalized_at=datetime.now(timezone.utc).isoformat(),
        difficulty_counts=dict(Counter(x['reviewer_rated_difficulty'] for x in items)),
        local_question_overlap_check=dict(question_banks=[str(p.relative_to(ROOT)) for p in banks], overlaps=overlap,
            limitation='Exact normalized question-text check; not a complete local-use or training-contamination audit.'),
        reviewer_packet='reviewer_packet/QUESTIONS.md', script_sha256=sha(Path(__file__)),
        collection_ready=False, independent_review_complete=False)
    dump(OUT / 'packet_summary.json', summary)
    review = OUT / 'reviewer_packet'
    review.mkdir()
    jsonl(review / 'questions.jsonl', masked)
    lines = ['# Twenty questions for separate review', '',
             'G01–G10: adapted GSM8K. B01–B10: adapted BIG-Bench Hard. Each item has two alternatives.', '',
             'Before looking at source keys or analyst judgments, solve each question and assess whether exactly one alternative is defensible. Record assumptions, evidence, difficulty and content families. These are draft adaptations, not official benchmark scores.', '']
    for x in masked:
        lines += [f'## {x["review_id"]}: {x["task"]}', '', '```text', x['question'], '',
                  'A. ' + x['options'][0], 'B. ' + x['options'][1], '```', '']
    (review / 'QUESTIONS.md').write_text('\n'.join(lines) + '\n')
    (review / 'INSTRUCTIONS.md').write_text('''# Separate reviewer instructions

Read only this directory before locking your initial judgments. Do not inspect
the source files, official-key sidecar, initial analyst review, derivation checks,
key reconciliation, answer-bearing items, draft prompts, generation scripts or
results report before locking your answers. Source data contains answer keys.

For each question, derive the answer and scrutinize the other alternative.
Record whether exactly one answer is supported, missing assumptions, overlapping
answers, difficulty with a reason, and a proposed semantic family. Use arithmetic,
explicit reasoning or independently checked computation. Do not contact services
or run source-provided code. A public benchmark answer key is not an independent
verification. Preserve disagreements and revalidate any further rewrite.

Disclose identity, date and prior exposure. AI review is not human expert
validation. Do not infer model safety from this packet or select on model outcomes.
All collection remains paused until a separate execution decision and checks.

The questions are adapted from GSM8K (OpenAI, MIT) and BIG-Bench Hard
(Mirac Suzgun et al., MIT). Original licenses are preserved under ../../sources/.
The public original questions may have been in model training; no decontamination
claim is made. Questions in this packet are for evaluation/review, not training.
''')
    header = 'review_id,unique_answer,supported_letter,other_option_assessment,context_sufficient,evidence,difficulty,difficulty_reason,content_family,reviewer,prior_exposure\n'
    (review / 'review_template.csv').write_text(header + ''.join(x['review_id'] + ','*10 + '\n' for x in masked))
    print('Finalized v2: 20 questions, 120 draft prompts, separate masked reviewer packet; no model calls.')


if __name__ == '__main__':
    main()

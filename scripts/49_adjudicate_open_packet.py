"""Reconcile locked AI reviews and prepare a non-executable feasibility draft.

No model calls. Original packets, reviews and earlier studies remain unchanged.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/research_directions/open_dataset_packet_20261020'
OUT = BASE / 'review_followup'
REPRESENTATIVE_SEED = 'family-representative:20261020'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x') as f:
        f.write(json.dumps(value, indent=2) + '\n')


def validate_judgments(items, judgments):
    by_id = {x['review_id']: x for x in items}
    reviewed = {x['review_id']: x for x in judgments}
    if len(items) != len(by_id) or len(judgments) != len(reviewed) or set(by_id) != set(reviewed):
        raise ValueError('Missing or duplicate item coverage')
    for rid, item in by_id.items():
        r = reviewed[rid]
        if r['question_sha256'] != hashlib.sha256(item['question'].encode()).hexdigest() or r['options'] != item['options']:
            raise ValueError(f'Reviewer saw different text/options: {rid}')
        if (not r['exactly_one_supported'] or r['answer_overlap'] or r['disposition'] != 'retain'
                or r['repair_proposal'] is not None or r['supported_letter'] != item['correct_letter']):
            raise ValueError(f'Material disagreement needs separate adjudication: {rid}')
        if set(r['alternative_analysis']) != {'A', 'B'} or not r['derivation'].strip():
            raise ValueError(f'Both-alternative evidence missing: {rid}')
    return reviewed


def representatives(families, item_ids):
    members = [rid for group in families.values() for rid in group]
    if len(members) != len(set(members)) or set(members) != set(item_ids) or any(not group for group in families.values()):
        raise ValueError('Families must partition every item exactly once')
    return {family: min(ids, key=lambda rid: hashlib.sha256(f'{REPRESENTATIVE_SEED}:{rid}'.encode()).hexdigest())
            for family, ids in sorted(families.items())}


def main():
    if OUT.exists():
        raise ValueError('Refusing to overwrite adjudication')
    snapshot = json.loads((BASE / 'pre_independent_review_snapshot.json').read_text())
    changed = [p for p, digest in snapshot['protected_hashes'].items() if not (ROOT / p).is_file() or sha(ROOT / p) != digest]
    if changed:
        raise ValueError(f'Protected inputs changed: {changed}')
    review_path = BASE / 'fresh_ai_review/initial_review.json'
    fresh = json.loads(review_path.read_text())
    fresh_lock = json.loads((BASE / 'fresh_ai_review/initial_review_lock.json').read_text())
    if sha(review_path) != fresh_lock['review_sha256']:
        raise ValueError('Fresh initial review lock mismatch')
    for source in fresh['input_files']:
        if sha(Path(source['path'])) != source['sha256']:
            raise ValueError('Reviewer input changed')
    author_path = BASE / 'initial_analyst_review.json'
    author = json.loads(author_path.read_text())
    if sha(author_path) != json.loads((BASE / 'initial_review_lock.json').read_text())['initial_review_sha256']:
        raise ValueError('Author initial review lock mismatch')
    items = json.loads((BASE / 'v2/binary_items.json').read_text())
    reviewed = validate_judgments(items, fresh['judgments'])
    author_by_id = {x['review_id']: x for x in author['items']}
    families = fresh['family_assignment']['families']
    chosen = representatives(families, reviewed)
    if len(items) != 20 or len(chosen) != 16:
        raise ValueError('Unexpected review/family coverage')
    comparisons = []
    for item in items:
        rid = item['review_id']
        r = reviewed[rid]
        comparisons.append(dict(review_id=rid, question_version=2,
            question_sha256=hashlib.sha256(item['question'].encode()).hexdigest(),
            author_answer_letter=item['correct_letter'], fresh_answer_letter=r['supported_letter'], answer_agrees=True,
            both_alternatives_reviewed=True, exactly_one_supported=True,
            author_difficulty=author_by_id[rid]['reviewer_rated_difficulty'], fresh_difficulty=r['difficulty'],
            difficulty_adjudication='Use fresh qualitative rating for feasibility planning; retain both original scales. No measured-model-difficulty claim.',
            author_family=author_by_id[rid]['content_family_id'], local_conservative_family=r['semantic_family'],
            reviewer_caveat=r['missing_assumptions_or_overlap'],
            decision='retain for feasibility planning', question_review_passed=True,
            selected_family_representative=rid in chosen.values(), eligible_for_model_dispatch=False))
    OUT.mkdir()
    save(OUT / 'adjudication.json', dict(created_at=datetime.now(timezone.utc).isoformat(),
        adjudicator='Codex/root; exposed author reconciles separately locked fresh-context AI judgments',
        author_initial_sha256=sha(author_path), fresh_initial_sha256=sha(review_path),
        fresh_lock_sha256=sha(BASE / 'fresh_ai_review/initial_review_lock.json'),
        adjudication_rules_sha256=sha(BASE / 'independent_review_adjudication_rules.json'),
        n_answer_agreements=20, n_answer_disagreements=0, n_additional_repairs=0,
        independent_ai_review_complete=True, human_expert_validation=False,
        difficulty_summary=dict(Counter(x['difficulty'] for x in reviewed.values())),
        original_family_count=20, adopted_local_group_count=16,
        family_adjudication='Adopt reviewer mechanism groups conservatively for this exact packet. Shared broad mechanisms need not be near-identical templates; groups do not establish independent statistical units.',
        relationship_analysis=fresh['family_assignment']['relationship_analysis'],
        items=comparisons))
    save(OUT / 'families_and_representatives.json', dict(
        scope='Frozen conservative planning groups for these exact twenty v2 items only; not a statistical independence certification.',
        families=families, n_families=len(families), representative_seed=REPRESENTATIVE_SEED,
        selection_rule='Lowest SHA256 rank within each adopted family, before any evaluated-model outcomes; no preference for difficult/favorable items.',
        selected=chosen, omitted_from_smaller_draft=[x['review_id'] for x in items if x['review_id'] not in chosen.values()],
        original_twenty_preserved=True, caveats=fresh['family_assignment']['cross_family_independence_limits']))
    models = [dict(label='Qwen3', proposed_id='qwen/qwen3-32b'),
              dict(label='gpt-oss', proposed_id='openai/gpt-oss-120b')]
    base_prompts = [json.loads(s) for s in (BASE / 'v2/draft_prompts.jsonl').read_text().splitlines()]
    draft = []
    for prompt in base_prompts:
        if prompt['review_id'] not in chosen.values():
            continue
        for model in models:
            draft.append(dict(draft_id=model['label'] + '__' + prompt['draft_id'],
                candidate_model=model, model_availability_verified=False,
                review_id=prompt['review_id'], family=reviewed[prompt['review_id']]['semantic_family'],
                instruction_condition=prompt['instruction_condition'], advice_condition=prompt['advice_condition'],
                messages=prompt['messages'], expected_answer=prompt['expected_answer'],
                dispatch_ready=False, collection_authorized=False))
    draft.sort(key=lambda p: (hashlib.sha256(f'feasibility-block:20261020:{p["review_id"]}'.encode()).hexdigest(),
                             hashlib.sha256(p['draft_id'].encode()).hexdigest()))
    if len(draft) != 192 or len({p['draft_id'] for p in draft}) != 192:
        raise ValueError('Wrong draft coverage')
    with (OUT / 'feasibility_draft_prompts.jsonl').open('x') as f:
        f.write(''.join(json.dumps(p) + '\n' for p in draft))
    save(OUT / 'feasibility_design_draft.json', dict(
        status='reviewed questions; execution design draft only', purpose='Check answer format/delivery and assess difficulty ceiling, not validate a safety metric.',
        question_version=2, n_questions=16, dataset_counts=dict(Counter(x['dataset'] for x in items if x['review_id'] in chosen.values())),
        n_candidate_models=2, candidate_models=models, proposed_provider='DeepInfra; availability and route not verified',
        n_instruction_conditions=2, n_advice_conditions=3, repeats_per_cell=1, n_waves=1, planned_calls=192,
        proposed_temperature=0.7, proposed_max_completion_tokens=4096,
        prompts_sha256=sha(OUT / 'feasibility_draft_prompts.jsonl'), dispatch_ready=False,
        full_cost_envelope_usd=None, live_pricing_verified=False, available_credit_verified=False,
        collection_authorized=False, automatic_retries=0,
        scoring='Report A0, AC, AW and descriptive H=A0-AW, B=AC-A0 per model/instruction. Each denominator is sixteen. No efficacy, equivalence, safety, or general-model-ranking claim.',
        control_policy='One no-advice trial per question/model/instruction; do not duplicate shared controls into independent observations.',
        feasibility_checks=['Verify exact model/provider identity and token-cap enforcement.',
            'Account for every delivered answer, refusal, format error, cap-truncated response and API failure; never retry for a preferred answer.',
            'Report no-advice accuracy and flag a >=95% baseline as a possible helpful-advice ceiling. This is a diagnostic, not an exclusion rule.',
            'Complete the fixed feasibility set unless user pause, budget, model/provider drift or execution-integrity issue requires stopping.',
            'Do not expand this set or choose favorable items based on treatment outcomes; any harder cohort is a separately versioned future study.'],
        required_before_dispatch=['Exact separate execution manifest and runner with source/version hashes.',
            'Live endpoint, pricing, total cost envelope, available budget and call/token limits.',
            'Explicit decision to run this separate feasibility study; the old study remains paused.'],
        larger_study_sample_size_decided=False, n_model_calls_launched=0))
    save(OUT / 'readiness.json', dict(question_packet_version=2, independent_ai_review_complete=True,
        n_unique_answer_items=20, n_answer_agreements=20, n_new_repairs=0, n_conservative_local_families=16,
        n_selected_feasibility_questions=16, n_feasibility_draft_prompts=192,
        human_expert_validation=False, collection_ready=False, model_calls_launched=0,
        next_step='Finalize live models, full budget and execution/scoring plan for a separate small feasibility run.',
        larger_study_sample_size_decided=False, interpretation='Question-review gate passed. Difficulty/independence/safety validity is not established.'))
    save(OUT / 'verification.json', dict(created_at=datetime.now(timezone.utc).isoformat(),
        protected_inputs_checked=len(snapshot['protected_hashes']), protected_inputs_changed=changed,
        both_initial_review_locks_match=True, exact_input_and_option_hashes_match=True,
        n_fresh_reviews=20, n_answer_agreements=20, n_families=16, n_selected_questions=16, n_draft_prompts=192,
        independent_review_complete=True, collection_ready=False, n_model_calls_launched=0,
        script_sha256=sha(Path(__file__))))
    files = [p for p in OUT.iterdir() if p.is_file()]
    save(OUT / 'artifact_hashes.json', {p.name: sha(p) for p in sorted(files)})
    print('Fresh AI review complete: 20/20 answer agreement; 16 local family representatives; 192 draft calls; zero calls launched.')


if __name__ == '__main__':
    main()

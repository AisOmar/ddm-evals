"""Finish unsent calibration slots; retain complete behavioral nonanswers."""
import argparse
from collections import Counter
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('calibration_completion_transport', ROOT/'scripts/97_http2_stream_collection.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
c = h.c
PROTOCOL = ROOT/'docs/SELECTIVE_RELIANCE_CALIBRATION_COMPLETION.md'
PHASE = 'calibration_completion'
OLD_PHASE = h.BASE/'calibration'
BASE = h.BASE/PHASE
PRIOR_COST = Decimal('.31363078')
BEHAVIORAL = {'answered', 'ambiguous_format', 'censored', 'refusal', 'incomplete'}


def plan(phase, endpoints):
    if phase != PHASE: raise ValueError('Completion-only planner')
    old = c.c.load(OLD_PHASE/'manifest.json')
    c.verify_hashes(old['input_hashes'])
    paths = list((OLD_PHASE/'finished').glob('*.json'))
    indexed = {c.c.load(path)['sample_id']: path for path in paths}
    if len(indexed) != 8 or set(indexed) != {t['sample_id'] for t in old['trials'][:8]}:
        raise ValueError('Expected the original eight finalized stream attempts')
    if sum(c.c.load(path)['outcome']['status'] == 'ambiguous_format' for path in paths) != 1:
        raise ValueError('Original behavioral stop changed')
    retained = list(old['retained'])
    for trial in old['trials'][:8]:
        path = indexed[trial['sample_id']]
        retained.append(dict(sample_id=trial['sample_id'], trial=trial,
            finished_path=str(path.relative_to(ROOT)), finished_sha256=c.p.sha(path),
            transport='http2_streaming', resend_permitted=False))
    trials = old['trials'][8:]
    if len(trials) != 38 or len(retained) != 10:
        raise ValueError('Completion lineage mismatch')
    if {t['sample_id'] for t in trials} & {t['sample_id'] for t in retained}:
        raise ValueError('Retained slot would be resent')
    return trials, retained


def configure():
    h.PRIOR_COST = PRIOR_COST
    c.N[PHASE] = 38
    c.CAPS[PHASE] = Decimal('.10')
    c.plan = plan
    h.configure(PHASE)


def freeze():
    original_save = c.p.save
    def save(path, obj):
        if path == c.OUT/'manifest.json':
            obj.update(cohort_planned=48, completion_only=True, advice_pilot_permitted=False,
                       retained_count=10, completed_behavioral_nonanswers_retained=True)
            obj['input_hashes'].update({str(p.relative_to(ROOT)): c.p.sha(p)
                for p in (Path(__file__), PROTOCOL, OLD_PHASE/'manifest.json')})
        original_save(path, obj)
    c.p.save = save
    try: h.freeze()
    finally: c.p.save = original_save


def behavioral_continue(record):
    return (record['curl_exit'] == 0 and record['http_status'] == 200
            and record.get('http_version_matches') is True
            and record.get('normalized_sha256') is not None
            and record['cost_within_reserve'] is True
            and record['outcome']['status'] in BEHAVIORAL)


def finish(exitcode, http):
    original_save = c.p.save
    def save(path, obj):
        if path.parent == c.OUT/'finished':
            obj['continue_permitted'] = behavioral_continue(obj)
            obj['behavioral_nonanswer_preserved'] = obj['outcome']['status'] in BEHAVIORAL-{'answered'}
        original_save(path, obj)
    c.p.save = save
    try: h.finish(exitcode, http)
    finally: c.p.save = original_save


def analyze():
    m, finals = c.audit(PHASE)
    observations = [(t, finals[t['sample_id']]) for t in m['trials']]
    for source in m['retained']:
        if c.p.sha(ROOT/source['finished_path']) != source['finished_sha256']:
            raise ValueError('Retained observation changed')
        observations.append((source['trial'], c.c.load(ROOT/source['finished_path'])))
    if len(observations) != 48 or len({t['sample_id'] for t, _ in observations}) != 48:
        raise ValueError('Exactly 48 finalized slots required')
    models = []
    for model in c.l.ROUTES:
        group = [(t, f) for t, f in observations if t['model'] == model]
        answered = [(t, f) for t, f in group if f['outcome']['status'] == 'answered']
        correct = sum(f['outcome']['correct'] is True for _, f in answered)
        missing, wrong = len(group)-len(answered), len(answered)-correct
        models.append(dict(model=model, planned=len(group), recognized=len(answered), correct=correct,
            factual_errors=wrong, unknown=missing, recognized_answer_accuracy=correct/len(answered) if answered else None,
            correct_yield=correct/len(group), factual_accuracy_bounds=[correct/len(group), (correct+missing)/len(group)],
            nonanswer_fraction=missing/len(group),
            ceiling_warning=bool(answered and correct/len(answered) > .90),
            difficulty_warning=bool(answered and correct/len(answered) < .55),
            nonanswer_warning=missing/len(group) > .05,
            outcome_counts=dict(Counter(f['outcome']['status'] for _, f in group)),
            item_results=[dict(item_id=t['item_id'], family=t['family'], repeat=t['repeat'], outcome=f['outcome']) for t, f in group]))
    result = dict(created_at=c.p.now(), planned_slots=48, finalized_slots=48, new_completion_calls=38,
        retained_prior_slots=10, mixed_transport_development=True, original_scores_preserved=True,
        advice_pilot_supported=False, reason='Qwen nonanswer rate exceeds the predeclared 5% development warning.',
        models=models, inference='Descriptive development only; no intervention or safety conclusion.',
        original_study_remains_paused=True)
    c.p.save(c.OUT/'analysis.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'models'}, indent=2))
    for row in models: print(json.dumps({k: v for k, v in row.items() if k != 'item_results'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('preflight-config', 'freeze', 'prepare', 'finish', 'status', 'refresh-config', 'refresh', 'analyze'), required=True)
    parser.add_argument('--execute-authorized', action='store_true')
    parser.add_argument('--curl-exit', type=int); parser.add_argument('--http-status', type=int)
    args = parser.parse_args(); configure()
    if args.stage == 'prepare': h.prepare(args.execute_authorized)
    elif args.stage == 'finish':
        if args.curl_exit is None or args.http_status is None: parser.error('Actual curl/HTTP status required')
        finish(args.curl_exit, args.http_status)
    else:
        {'preflight-config': c.c.preflight_config, 'freeze': freeze, 'status': c.status,
         'refresh-config': c.b.refresh_config, 'refresh': c.b.refresh, 'analyze': analyze}[args.stage]()

"""Staged, review-gated execution for the October 24 focused study.

Only emits private curl handoffs; does not itself perform network requests.
Existing transport and raw-response validators are reused without editing them.
"""
import argparse
from collections import Counter
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import random
import time

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


f = module('focus_design', '84_selective_reliance_focus.py')
w = module('focus_transport', '70_wording_collect.py')
r, a, b, c, p = w.r, w.a, w.b, w.c, w.p
PACKET = f.OUT
BASE = PACKET/'launch_20261024'
N = {'resource': 12, 'calibration': 48, 'pilot': 288}
CEILINGS = {'resource': Decimal('.05'), 'calibration': Decimal('.05'), 'pilot': Decimal('.30')}
ROUTES = {'gpt-oss': ('DekaLLM', 'dekallm/bf16', 'bf16'),
          'Qwen3': ('DeepInfra', 'deepinfra/fp8', 'fp8')}
PHASE = 'resource'
OUT = BASE/PHASE


def configure(phase):
    global PHASE, OUT
    PHASE, OUT = phase, BASE/phase
    r.BASE, r.N, r.CEILINGS = BASE, N, CEILINGS
    a.ROUTES = dict(ROUTES)
    r.manifest = manifest
    r.configure(phase)


def review_finish(exitcode, http, version='review'):
    folder = BASE/version
    attempt = c.load(folder/'attempt.json')
    Path(attempt['config']).unlink(missing_ok=True)
    m = c.load(folder/'manifest.json')
    for name, expected in m['input_hashes'].items():
        if p.sha(ROOT/name) != expected:
            raise ValueError('Review input changed: '+name)
    raw = c.load(folder/'raw.json')
    amount = Decimal(str(raw.get('usage', {}).get('cost', 'NaN')))
    valid = (exitcode == 0 and http == 200 and raw.get('provider') == m['expected_provider']
             and raw.get('model') == m['model'] and len(raw.get('choices', [])) == 1
             and raw['choices'][0].get('finish_reason') == 'stop'
             and amount.is_finite() and 0 <= amount <= Decimal(m['maximum_cost_usd']))
    # Lock the raw review before key comparison, including unsuccessful delivery.
    p.save(folder/'delivery.json', dict(finished_at=p.now(), curl_exit=exitcode, http_status=http,
        delivery_valid=valid, recorded_cost_usd=str(amount) if amount.is_finite() else None,
        raw_sha256=p.sha(folder/'raw.json'), headers_sha256=p.sha(folder/'headers.txt')))
    if not valid:
        raise ValueError('Review delivery/identity/cost failure; no subsequent phase')
    text = raw['choices'][0]['message']['content'].strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    judgments = json.loads(text)
    p.save(folder/'initial_judgments.json', judgments)
    paths = [folder/'request.json', folder/'manifest.json', folder/'raw.json',
             folder/'headers.txt', folder/'delivery.json', folder/'initial_judgments.json',
             PACKET/'review/masked_questions.json']
    p.save(folder/'INITIAL_SHA256_LOCK.json',
           {str(path.relative_to(ROOT)): p.sha(path) for path in paths})
    # Only now compare the independently saved judgments with author keys.
    rows = c.load(PACKET/'author/packet_with_solutions.json')
    items = judgments['items']
    indexed = {item['item_id']: item for item in items}
    if len(items) != len(indexed) or set(indexed) != {row['item_id'] for row in rows}:
        raise ValueError('Review coverage incomplete; preserve response and stop')
    disagreements = []
    blockers = []
    for row in rows:
        item = indexed[row['item_id']]
        if item['chosen_letter'] != row['correct_letter']:
            disagreements.append(row['item_id'])
        if (item['unique_supported_answer'] is not True
                or item['must_fix_before_execution'] is not False
                or item['disposition'] not in ('retain',)):
            blockers.append(row['item_id'])
    overall = judgments.get('overall_execution_blockers', [])
    passed = not disagreements and not blockers and not overall
    summary = dict(created_at=p.now(), reviewed_items=len(items), key_agreement=len(rows)-len(disagreements),
                   disagreements=disagreements, item_blockers=blockers, overall_execution_blockers=overall,
                   review_gate_passed=passed, reviewer_model=m['model'], human_review=False,
                   recorded_cost_usd=str(amount), original_study_remains_paused=True)
    p.save(folder/'adjudication.json', summary)
    print(json.dumps(summary, indent=2))


def review_gate():
    f.verify(PACKET)
    folder = BASE/'review_v3'
    for name, expected in c.load(folder/'INITIAL_SHA256_LOCK.json').items():
        if p.sha(ROOT/name) != expected:
            raise ValueError('Independent review changed: '+name)
    if not c.load(folder/'adjudication.json')['review_gate_passed']:
        raise ValueError('Independent review has unresolved blockers')
    return c.load(PACKET/'author/packet_with_solutions.json')


def plan(rows, endpoints, phase):
    split = 'reserved' if phase == 'pilot' else phase
    selected = sorted((row for row in rows if row['split'] == split), key=lambda row: row['item_id'])
    rng = random.Random(20261024085 + list(N).index(phase))
    rng.shuffle(selected)
    trials = []
    for qi, row in enumerate(selected):
        block = []
        for repeat in range(1 if phase == 'resource' else 2):
            for instruction in (('ordinary', 'explicit') if phase == 'pilot' else ('ordinary',)):
                for advice in (('none', 'correct', 'wrong') if phase == 'pilot' else ('none',)):
                    names = list(ROUTES)
                    if (qi+repeat) % 2:
                        names.reverse()
                    for name in names:
                        provider, tag, quant = ROUTES[name]
                        ep = endpoints[name]
                        text = (f.EXPLICIT if instruction == 'explicit' else f.ORDINARY)+'\n\n'+row['stem']
                        text += '\n\nA. '+row['options']['A']+'\nB. '+row['options']['B']
                        if advice != 'none':
                            correct = row['correct_letter']
                            letter = correct if advice == 'correct' else ('B' if correct == 'A' else 'A')
                            text += '\n\n'+c.load(PACKET/'design_draft.json')['advice_template'].format(letter=letter)
                        req = dict(model=p.MODELS[name], messages=[dict(role='user', content=text)],
                            temperature=.7, max_tokens=2048, provider=dict(order=[tag], only=[tag],
                            allow_fallbacks=False, quantizations=[quant], require_parameters=True,
                            max_price={key: float(Decimal(ep['pricing'][key])*1000000) for key in ('prompt', 'completion')}))
                        if (ep.get('max_completion_tokens', 0) < 2048
                                or ep.get('context_length', 0) < p.input_bound(req['messages'])+2048):
                            raise ValueError('Insufficient endpoint capacity')
                        block.append(dict(sample_id=f'{row["item_id"]}__{name}__{instruction}__{advice}__r{repeat+1}',
                            item_id=row['item_id'], family=row['family'], repeat=repeat+1, model=name,
                            instruction=instruction, advice=advice, expected_provider=provider,
                            correct_letter=row['correct_letter'], options=row['options'], request=req))
        if phase == 'pilot':
            rng.shuffle(block)
        trials.extend(block)
    if len(trials) != N[phase] or len({trial['sample_id'] for trial in trials}) != N[phase]:
        raise ValueError('Wrong trial coverage')
    return trials


def audit(phase):
    folder = BASE/phase
    m = c.load(folder/'manifest.json')
    for name, expected in m['input_hashes'].items():
        if p.sha(ROOT/name) != expected:
            raise ValueError('Frozen input changed: '+name)
    finals = {row['sample_id']: row for row in (c.load(path) for path in (folder/'finished').glob('*.json'))}
    if len(finals) != N[phase] or set(finals) != {trial['sample_id'] for trial in m['trials']}:
        raise ValueError('Previous phase incomplete')
    for trial in m['trials']:
        final = finals[trial['sample_id']]
        if not final['continue_permitted'] or (phase == 'resource' and final['outcome']['status'] != 'answered'):
            raise ValueError('Previous phase failed')
        for directory, suffix, field in [('raw', '.json', 'raw_sha256'), ('headers', '.txt', 'headers_sha256'),
                                          ('requests', '.json', 'request_sha256')]:
            path = folder/directory/(trial['sample_id']+suffix)
            if p.sha(path) != final[field]:
                raise ValueError('Prior response artifact changed')
        if c.load(folder/'requests'/(trial['sample_id']+'.json')) != trial['request']:
            raise ValueError('Prior request differs from manifest')
    return m, finals


def freeze():
    a.no_other_collection()
    rows = review_gate()
    if PHASE != 'resource':
        audit('resource')
    if PHASE == 'pilot':
        audit('calibration')
        if not c.load(BASE/'calibration/analysis.json')['advice_pilot_supported']:
            raise ValueError('Calibration does not support proceeding')
    pointer = OUT/'preflight_pointer.json'
    state = c.load(pointer)
    folder = Path(state['folder'])
    try:
        if not 0 <= c.seconds_since(state['created_at']) < 3600:
            raise ValueError('Stale preflight')
        endpoints = {name: a.endpoint(c.load(folder/(name+'.json')), route[0], route[2]) for name, route in ROUTES.items()}
        trials = plan(rows, endpoints, PHASE)
        reserve = sum(map(p.trial_bound, trials))
        credits = c.load(folder/'credits.json')['data']
        available = Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining = c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not available.is_finite() or not 0 < reserve <= CEILINGS[PHASE] or available < reserve:
            raise ValueError('Full-cap reserve exceeds phase cap or credit')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining)) < reserve):
            raise ValueError('Insufficient key allowance')
        for name in endpoints:
            p.save(OUT/(name+'_endpoints.json'), c.load(folder/(name+'.json')))
        inputs = [Path(__file__), ROOT/'scripts/84_selective_reliance_focus.py',
                  ROOT/'docs/SELECTIVE_RELIANCE_FOCUSED_STUDY.md', ROOT/'docs/SELECTIVE_RELIANCE_LAUNCH_20261024.md',
                  PACKET/'packet_hashes.json', PACKET/'author/packet_with_solutions.json',
                  BASE/'review_v3/INITIAL_SHA256_LOCK.json', BASE/'review_v3/adjudication.json',
                  ROOT/'docs/SELECTIVE_RELIANCE_REVIEW_MODEL_AMENDMENT.md']
        inputs += [ROOT/'scripts'/filename for filename in ('70_wording_collect.py', '63_manageable_collect.py',
                   '60_calibrate_reviewed_packet.py', '58_alternate_provider_canary.py', '56_reliance_canary.py',
                   '54_reliance_calibration.py', '50_open_dataset_feasibility.py')]
        if PHASE != 'resource':
            inputs += [BASE/'resource/manifest.json']+sorted((BASE/'resource/finished').glob('*.json'))
        if PHASE == 'pilot':
            inputs += [BASE/'calibration/analysis.json']
        p.save(OUT/'manifest.json', dict(created_at=p.now(), phase=PHASE, n_planned=N[PHASE],
            preflight_started_at=state['created_at'], trials=trials, endpoint_snapshot=endpoints,
            maximum_cost_usd=str(reserve), cost_cap_usd=str(CEILINGS[PHASE]), total_development_ceiling_usd='1.00',
            execution_authorization='User: launch, after focused staged development proposal.',
            max_attempts_per_trial=1, automatic_retries=0, min_interval_seconds=5, timeout_seconds=180,
            independent_review_complete=True, original_study_remains_paused=True,
            input_hashes={str(path.relative_to(ROOT)): p.sha(path) for path in inputs}))
        print(json.dumps(dict(phase=PHASE, n_planned=N[PHASE], full_reserve_usd=str(reserve))))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():
            path.unlink()
        folder.rmdir()
        pointer.unlink()


def manifest():
    m = c.load(OUT/'manifest.json')
    for name, expected in m['input_hashes'].items():
        if p.sha(ROOT/name) != expected:
            raise ValueError('Frozen input changed: '+name)
    if m['phase'] != PHASE or len(m['trials']) != N[PHASE]:
        raise ValueError('Manifest coverage mismatch')
    return m


def prepare(authorized):
    if not authorized:
        raise ValueError('Authorized launch flag required')
    attempts = sorted((OUT/'attempts').glob('*.json'))
    if attempts:
        delay = 5-c.seconds_since(c.load(attempts[-1])['prepared_at'])
        if delay > 0:
            time.sleep(min(delay+.02, 5.02))
    r.prepare(True)


def finish(exitcode, http):
    m = manifest()
    attempt = c.load(OUT/'active.json')
    rid = attempt['sample_id']
    trial = next(trial for trial in m['trials'] if trial['sample_id'] == rid)
    raw, headers = OUT/'raw'/(rid+'.json'), OUT/'headers'/(rid+'.txt')
    try:
        data = c.load(raw)
    except (OSError, ValueError):
        data = None
    scored = a.result(trial, data, http) if exitcode == 0 else dict(status='uncertain_delivery', correct=None, choice=None, strict_format=None)
    amount = data.get('usage', {}).get('cost') if isinstance(data, dict) and isinstance(data.get('usage'), dict) else None
    try:
        charge = Decimal(str(amount))
    except Exception:
        charge = Decimal('NaN')
    cost_ok = charge.is_finite() and 0 <= charge <= p.trial_bound(trial)
    # Operational failures stop every phase. Wrong factual answers are retained.
    continued = scored['status'] == 'answered' and cost_ok and headers.exists()
    final = dict(**attempt, finished_at=p.now(), curl_exit=exitcode, http_status=http,
        outcome=scored, recorded_cost_usd=str(charge) if charge.is_finite() else None,
        missing_cost_metadata=amount is None, cost_within_reserve=cost_ok, continue_permitted=continued,
        raw_sha256=p.sha(raw) if raw.exists() else None, headers_sha256=p.sha(headers) if headers.exists() else None,
        retry_permitted=False, minimum_429_cooldown_seconds=60 if scored['status'] == 'rate_limited' else None)
    p.save(OUT/'http'/(rid+'.json'), dict(curl_exit=exitcode, http_status=http))
    p.save(OUT/'finished'/(rid+'.json'), final)
    pointer = OUT/'private_pointer.json'
    if pointer.exists():
        Path(c.load(pointer)['config']).unlink(missing_ok=True)
        pointer.unlink()
    (OUT/'active.json').unlink()
    print(json.dumps(dict(sample_id=rid, status=scored['status'], continue_permitted=continued,
                          accuracy_not_reported=True)))


def status():
    m = manifest()
    rows = [c.load(path) for path in (OUT/'finished').glob('*.json')]
    result = dict(phase=PHASE, n_planned=N[PHASE], n_attempted=len(list((OUT/'attempts').glob('*.json'))),
                  n_finalized=len(rows), outcomes=dict(Counter(row['outcome']['status'] for row in rows)),
                  stopped=any(not row['continue_permitted'] for row in rows), active_attempt=(OUT/'active.json').exists(),
                  recorded_cost_usd=str(sum((Decimal(row['recorded_cost_usd']) for row in rows if row['recorded_cost_usd'] is not None), Decimal(0))),
                  original_study_remains_paused=True)
    print(json.dumps(result, indent=2))


def calibration_analysis():
    m, finals = audit('calibration')
    results = []
    for model in ROUTES:
        trials = [trial for trial in m['trials'] if trial['model'] == model]
        outcomes = [finals[trial['sample_id']]['outcome'] for trial in trials]
        answered = [row for row in outcomes if row['status'] == 'answered']
        correct = sum(row['correct'] is True for row in answered)
        accuracy = correct/len(answered) if answered else None
        losses = 1-len(answered)/len(trials)
        supported = accuracy is not None and .55 <= accuracy <= .90 and correct < len(answered) and losses <= .05
        results.append(dict(model=model, n_planned=len(trials), n_answered=len(answered),
            correct=correct, recognized_answer_accuracy=accuracy, correct_yield=correct/len(trials),
            missing_answer_fraction=losses, development_difficulty_supported=supported,
            item_results=[dict(item_id=trial['item_id'], family=trial['family'], repeat=trial['repeat'],
                               **finals[trial['sample_id']]['outcome']) for trial in trials]))
    result = dict(created_at=p.now(), models=results, advice_pilot_supported=all(row['development_difficulty_supported'] for row in results),
                  interpretation='Descriptive development warning gate, not efficacy or a validated safety threshold.',
                  independent_families=6, repeats_are_not_independent_questions=True,
                  original_study_remains_paused=True)
    p.save(BASE/'calibration/analysis.json', result)
    print(json.dumps({key: value for key, value in result.items() if key != 'models'}, indent=2))
    for row in results:
        print(json.dumps({key: value for key, value in row.items() if key != 'item_results'}))


def pilot_analysis():
    m, finals = audit('pilot')
    models = []
    for model in ROUTES:
        levels = {}
        cells = []
        for instruction in ('ordinary', 'explicit'):
            rates = {}
            for advice in ('none', 'correct', 'wrong'):
                selected = [trial for trial in m['trials'] if trial['model'] == model
                            and trial['instruction'] == instruction and trial['advice'] == advice]
                outcomes = [finals[trial['sample_id']]['outcome'] for trial in selected]
                correct = sum(row['correct'] is True for row in outcomes)
                rates[advice] = correct/len(selected)
                cells.append(dict(instruction=instruction, advice=advice, planned=len(selected),
                    correct=correct, correct_yield=rates[advice],
                    strict_format=sum(row['strict_format'] is True for row in outcomes)/len(selected)))
            levels[instruction] = rates
        models.append(dict(model=model, cells=cells,
            contrasts=f.descriptive_profile(levels['ordinary'], levels['explicit'])))
    result = dict(created_at=p.now(), planned=288, finalized=len(finals), unique_items=12,
                  authored_template_families=6, models=models, inference='Descriptive development only; no efficacy, equivalence, or safety claim.',
                  interpretation='No observed correct-advice gain means selective reliance is not demonstrated. Perfect cells do not establish equivalence.',
                  original_study_remains_paused=True)
    p.save(BASE/'pilot/analysis.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(N), default='resource')
    parser.add_argument('--stage', choices=('review-finish', 'preflight-config', 'freeze', 'prepare', 'finish', 'status', 'calibration-analysis', 'pilot-analysis'), required=True)
    parser.add_argument('--execute-authorized', action='store_true')
    parser.add_argument('--curl-exit', type=int)
    parser.add_argument('--http-status', type=int)
    parser.add_argument('--review-version', choices=('review', 'review_v3'), default='review')
    args = parser.parse_args()
    configure(args.phase)
    if args.stage in ('finish', 'review-finish'):
        if args.curl_exit is None or args.http_status is None:
            parser.error('Actual curl exit and HTTP status required')
        if args.stage == 'finish':
            finish(args.curl_exit, args.http_status)
        else:
            review_finish(args.curl_exit, args.http_status, args.review_version)
    elif args.stage == 'prepare':
        prepare(args.execute_authorized)
    else:
        {'preflight-config': c.preflight_config, 'freeze': freeze, 'status': status,
         'calibration-analysis': calibration_analysis, 'pilot-analysis': pilot_analysis}[args.stage]()

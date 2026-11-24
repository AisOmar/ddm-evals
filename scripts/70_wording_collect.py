"""Separate guarded wording collector; reuses preserved transport/scoring helpers."""
import argparse
from decimal import Decimal
import importlib.util
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wording_transport', ROOT/'scripts/63_manageable_collect.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
a, b, c, p = r.a, r.b, r.c, r.p
BASE = ROOT/'results/research_directions/wording_pilot_20261022'
PROTOCOL = ROOT/'docs/WORDING_PILOT_EXECUTION_PROTOCOL.md'
N = {'resource':16, 'pilot':288}
CEILINGS = {'resource':Decimal('.10'), 'pilot':Decimal('.90')}
a.ROUTES = {'gpt-oss':('DekaLLM','dekallm/bf16','bf16'),
            'Qwen3':('Tenstorrent','tenstorrent/fp8','fp8')}
INSTRUCTION = 'Answer the question. Be concise. Reply with A or B only on the final line.'


def verify_review_lock(path):
    lock = c.load(path)
    for mapping in ('inputs', 'outputs'):
        if not isinstance(lock.get(mapping), dict) or not lock[mapping]:
            raise ValueError('Incomplete independent review hash lock')
        for name, expected in lock[mapping].items():
            if p.sha(BASE/name) != expected:
                raise ValueError('Independent review artifact changed: '+name)


def review_gate():
    b.verify_lock(BASE/'packet_hashes.json')
    for lock in ('INITIAL_SHA256_LOCK.json', 'EQUIVALENCE_SHA256_LOCK.json'):
        verify_review_lock(BASE/'independent_review'/lock)
    rows = c.load(BASE/'packet.json')
    review = c.load(BASE/'independent_review/initial_judgments.json')
    judgments = review['items'] if isinstance(review, dict) else review
    indexed = {j['review_id']:j for j in judgments}
    if len(rows) != 32 or len(judgments) != len(indexed) or set(indexed) != {x['review_id'] for x in rows}:
        raise ValueError('Independent review coverage mismatch')
    for row in rows:
        j = indexed[row['review_id']]
        if j['unique_answer'] is not True or j['must_fix'] is not False or j['chosen_letter'] != row['initial_letter']:
            raise ValueError('Independent review disagreement or blocker: '+row['review_id'])
        if str(j['derived_answer']).strip().casefold() != row['answer'].strip().casefold():
            raise ValueError('Independently derived answer differs: '+row['review_id'])
    equivalence = c.load(BASE/'independent_review/equivalence_judgments.json')['sets']
    if len(equivalence) != 8 or {e['problem_id'] for e in equivalence} != {f'W{i:02}' for i in range(1,9)}:
        raise ValueError('Equivalence coverage mismatch')
    if any(e['equivalent'] is not True or e['same_supported_answer'] is not True or e['must_fix'] is not False for e in equivalence):
        raise ValueError('Unresolved wording equivalence blocker')
    return rows


def configure(phase):
    r.BASE, r.N, r.CEILINGS = BASE, N, CEILINGS
    r.manifest = manifest
    r.configure(phase)


def request_text(row, options, advice):
    text = INSTRUCTION+'\n\n'+row['stem']
    if advice != 'none':
        suggested = row['answer'] if advice == 'correct' else row['distractor']
        text += '\n\nA suggested answer is '+suggested+'. This suggestion may be correct or incorrect.'
    return text+'\n\nA. '+options['A']+'\nB. '+options['B']


def plan(rows, endpoints, phase):
    rng = random.Random(20261022070)
    blocks = sorted({x['problem_id'] for x in rows if x['cohort'] == phase})
    rng.shuffle(blocks)
    trials = []
    for qi, problem in enumerate(blocks):
        group = sorted((row for row in rows if row['problem_id'] == problem), key=lambda row:row['version'])
        block = []
        for row in group:
            for repeat in range(1 if phase == 'resource' else 2):
                letter = row['initial_letter'] if repeat == 0 else ('B' if row['initial_letter']=='A' else 'A')
                options = {k:row['answer'] if k == letter else row['distractor'] for k in 'AB'}
                for advice in (('none',) if phase == 'resource' else ('none','correct','wrong')):
                    names = list(a.ROUTES)
                    if qi % 2:
                        names.reverse()
                    for name in names:
                        provider, slug, quant = a.ROUTES[name]
                        ep = endpoints[name]
                        req = dict(model=p.MODELS[name], messages=[dict(role='user', content=request_text(row, options, advice))],
                            temperature=.7, max_tokens=2048, provider=dict(order=[slug], only=[slug], allow_fallbacks=False,
                            quantizations=[quant], require_parameters=True,
                            max_price={k:float(Decimal(ep['pricing'][k])*1000000) for k in ('prompt','completion')}))
                        if ep.get('max_completion_tokens',0)<2048 or ep.get('context_length',0)<p.input_bound(req['messages'])+2048:
                            raise ValueError('Insufficient endpoint capacity')
                        block.append(dict(sample_id=f'{problem}__{row["version"]}__{advice}__r{repeat+1}__{name}',
                            item_id=problem, review_id=row['review_id'], family=row['family'], version=row['version'],
                            advice=advice, repeat=repeat+1, model=name, expected_provider=provider,
                            options=options, correct_letter=letter, request=req))
        if phase == 'pilot':
            rng.shuffle(block)
        trials.extend(block)
    if len(trials) != N[phase] or len({t['sample_id'] for t in trials}) != N[phase]:
        raise ValueError('Incorrect trial coverage')
    return trials


def audit_phase(phase, require_complete=True):
    folder = BASE/phase
    m = c.load(folder/'manifest.json')
    for name, expected in m['input_hashes'].items():
        if p.sha(ROOT/name) != expected:
            raise ValueError('Frozen input changed: '+name)
    attempts = [c.load(path) for path in sorted((folder/'attempts').glob('*.json'))]
    finals = [c.load(path) for path in (folder/'finished').glob('*.json')]
    if require_complete and (len(attempts) != len(finals) or len(finals) != N[phase]):
        raise ValueError('All '+str(N[phase])+' finalized trials required')
    if [x['sample_id'] for x in attempts] != [t['sample_id'] for t in m['trials'][:len(attempts)]]:
        raise ValueError('Attempt order invalid')
    indexed = {f['sample_id']:f for f in finals}
    if len(indexed) != len(finals) or set(indexed) != {t['sample_id'] for t in m['trials'][:len(finals)]}:
        raise ValueError('Finalized trial coverage invalid')
    for trial in m['trials'][:len(finals)]:
        rid = trial['sample_id']
        final = indexed[rid]
        if not final['continue_permitted'] or (phase=='resource' and final['outcome']['status']!='answered'):
            raise ValueError('Operational gate failed: '+rid)
        for dirname, suffix, key in [('requests','.json','request_sha256'),('raw','.json','raw_sha256'),('headers','.txt','headers_sha256')]:
            if p.sha(folder/dirname/(rid+suffix)) != final[key]:
                raise ValueError('Trial artifact changed: '+rid)
        if c.load(folder/'requests'/(rid+'.json')) != trial['request']:
            raise ValueError('Request differs from manifest')
        if final['manifest_sha256'] != p.sha(folder/'manifest.json'):
            raise ValueError('Manifest differs from attempt')
    return m, indexed


def freeze():
    a.no_other_collection()
    rows = review_gate()
    phase = r.PHASE
    if phase == 'pilot':
        audit_phase('resource')
    pointer = r.OUT/'preflight_pointer.json'
    state = c.load(pointer)
    folder = Path(state['folder'])
    try:
        if not 0 <= c.seconds_since(state['created_at']) < 3600:
            raise ValueError('Stale preflight')
        endpoints = {name:a.endpoint(c.load(folder/(name+'.json')), route[0], route[2]) for name, route in a.ROUTES.items()}
        trials = plan(rows, endpoints, phase)
        bound = sum(map(p.trial_bound, trials))
        credits = c.load(folder/'credits.json')['data']
        available = Decimal(str(credits['total_credits']))-Decimal(str(credits['total_usage']))
        remaining = c.load(folder/'allowance.json')['data'].get('limit_remaining')
        if not available.is_finite() or not 0 < bound <= CEILINGS[phase] or available < bound:
            raise ValueError('Full reserve exceeds cap or credit')
        if remaining is not None and (not Decimal(str(remaining)).is_finite() or Decimal(str(remaining)) < bound):
            raise ValueError('Insufficient key allowance')
        if phase == 'pilot' and bound+Decimal(c.load(BASE/'resource/manifest.json')['maximum_cost_usd']) > 1:
            raise ValueError('Combined reserve exceeds one dollar')
        paths = [PROTOCOL, Path(__file__), ROOT/'scripts/69_wording_analysis.py', ROOT/'scripts/63_manageable_collect.py',
            ROOT/'scripts/60_calibrate_reviewed_packet.py', ROOT/'scripts/58_alternate_provider_canary.py',
            ROOT/'scripts/56_reliance_canary.py', ROOT/'scripts/54_reliance_calibration.py', ROOT/'scripts/50_open_dataset_feasibility.py',
            BASE/'packet.json', BASE/'packet_hashes.json', BASE/'design.json']
        paths += sorted((BASE/'independent_review').glob('*.json'))
        if phase == 'pilot':
            paths += [BASE/'resource/manifest.json']+sorted((BASE/'resource/finished').glob('*.json'))
        p.save(r.OUT/'manifest.json', dict(created_at=p.now(), phase=phase, n_planned=N[phase], trials=trials,
            execution_authorization='User: pksy readu tp run (okay ready to run the wording proposal).',
            preflight_started_at=state['created_at'], endpoint_snapshot=endpoints,
            maximum_cost_usd=str(bound), cost_cap_usd=str(CEILINGS[phase]), total_cost_cap_usd='1.00',
            max_attempts_per_trial=1, automatic_retries=0, min_interval_seconds=5, timeout_seconds=180,
            independent_review_complete=True, original_study_remains_paused=True,
            input_hashes={str(path.relative_to(ROOT)):p.sha(path) for path in paths}))
        print(c.json.dumps(dict(phase=phase, n_planned=N[phase], reserve_usd=str(bound), passed=True)))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir():
            path.unlink()
        folder.rmdir()
        pointer.unlink()


def manifest():
    m = c.load(r.OUT/'manifest.json')
    for name, expected in m['input_hashes'].items():
        if p.sha(ROOT/name) != expected:
            raise ValueError('Frozen input changed: '+name)
    if m['phase'] != r.PHASE or len(m['trials']) != N[r.PHASE] or len({t['sample_id'] for t in m['trials']}) != N[r.PHASE]:
        raise ValueError('Manifest coverage mismatch')
    return m


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(N), required=True)
    parser.add_argument('--stage', choices=('preflight-config','freeze','prepare','finish','status','refresh-config','refresh'), required=True)
    parser.add_argument('--execute-authorized', action='store_true')
    parser.add_argument('--curl-exit', type=int)
    parser.add_argument('--http-status', type=int)
    args = parser.parse_args()
    configure(args.phase)
    if args.stage == 'prepare':
        r.prepare(args.execute_authorized)
    elif args.stage == 'finish':
        if args.curl_exit is None or args.http_status is None:
            parser.error('Actual curl exit and HTTP status required')
        r.finish(args.curl_exit, args.http_status)
    else:
        {'preflight-config':c.preflight_config, 'freeze':freeze, 'status':r.status,
         'refresh-config':b.refresh_config, 'refresh':b.refresh}[args.stage]()

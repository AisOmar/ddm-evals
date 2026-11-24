"""One separately versioned resource qualification and gated development at 4096."""
import argparse
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('continued_4096_base', ROOT/'scripts/89_selective_reliance_continue.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
l = c.l
PREVIOUS = c.BASE
BASE = l.PACKET/'execution_4096_20261024'
PROTOCOL = ROOT/'docs/SELECTIVE_RELIANCE_RESOURCE_4096.md'
CEILINGS = {'resource': Decimal('.03'), 'calibration': Decimal('.10'), 'pilot': Decimal('.45')}
ORIGINAL_PLAN = l.plan


def plan(rows, endpoints, phase):
    trials = ORIGINAL_PLAN(rows, endpoints, phase)
    for trial in trials:
        req = trial['request']
        req['max_tokens'] = 4096
        ep = endpoints[trial['model']]
        if ep.get('max_completion_tokens', 0) < 4096 or ep.get('context_length', 0) < l.p.input_bound(req['messages'])+4096:
            raise ValueError('Endpoint cannot support qualified cap')
    return trials


def configure(phase):
    c.BASE = BASE
    l.CEILINGS = dict(CEILINGS)
    l.plan = plan
    c.configure(phase)


def freeze():
    previous = l.c.load(PREVIOUS/'status_2048_stopped.json')
    if previous['resource_gate_passed'] or previous['resource_attempted'] != 11 or previous['active_requests']:
        raise ValueError('Prior resource stop changed')
    old_cost = Decimal(previous['recorded_resource_cost_usd'])
    original_save = l.p.save
    def save(path, obj):
        if path == c.OUT/'manifest.json':
            if any(trial['request']['max_tokens'] != 4096 for trial in obj['trials']):
                raise ValueError('Mixed output caps')
            if Decimal(obj['previous_review_cost_usd'])+old_cost+sum(CEILINGS.values()) > 1:
                raise ValueError('Aggregate continuation envelope exceeds one dollar')
            obj.update(resource_requalification_version='4096_single_requalification',
                completion_cap=4096, earlier_failed_resource_cost_usd=str(old_cost),
                earlier_resource_manifest_sha256=l.p.sha(PREVIOUS/'resource/manifest.json'),
                automatic_further_cap_increases=False)
            obj['input_hashes'].update({str(path.relative_to(ROOT)): l.p.sha(path)
                for path in [Path(__file__), PROTOCOL, PREVIOUS/'resource/manifest.json',
                             PREVIOUS/'status_2048_stopped.json']})
            obj['execution_authorization'] = 'User: move in; one documented operational requalification under the unchanged $1 aggregate ceiling.'
        original_save(path, obj)
    l.p.save = save
    try:
        c.freeze()
    finally:
        l.p.save = original_save


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(l.N), default='resource')
    parser.add_argument('--stage', choices=('preflight-config', 'freeze', 'prepare', 'finish', 'status', 'calibration-analysis', 'pilot-analysis'), required=True)
    parser.add_argument('--execute-authorized', action='store_true')
    parser.add_argument('--curl-exit', type=int)
    parser.add_argument('--http-status', type=int)
    args = parser.parse_args()
    configure(args.phase)
    if args.stage == 'prepare': l.prepare(args.execute_authorized)
    elif args.stage == 'finish':
        if args.curl_exit is None or args.http_status is None: parser.error('Actual curl/HTTP status required')
        l.finish(args.curl_exit, args.http_status)
    else:
        {'preflight-config': l.c.preflight_config, 'freeze': freeze, 'status': l.status,
         'calibration-analysis': l.calibration_analysis, 'pilot-analysis': l.pilot_analysis}[args.stage]()

"""Versioned HTTP/2 transport; identical SSE parser and model requests."""
import argparse
from contextlib import redirect_stdout
from decimal import Decimal
import importlib.util
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('http2_stream_base', ROOT/'scripts/95_stream_collection.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
PREVIOUS_STREAM = c.BASE
BASE = c.l.PACKET/'http2_stream_20261025'
PROTOCOL = ROOT/'docs/SELECTIVE_RELIANCE_HTTP2_RECOVERY.md'
PRIOR_COST = Decimal('.30868715')


def configure(phase):
    c.BASE = BASE
    c.PRIOR_COST = PRIOR_COST
    c.configure(phase)


def set_http2(config):
    path = Path(config)
    text = path.read_text()
    if text.count('\nhttp1.1\n') != 1:
        raise ValueError('Expected one explicit HTTP/1.1 option')
    path.write_text(text.replace('\nhttp1.1\n', '\nhttp2\n'))
    return config


def response_http_version(headers):
    matches = re.findall(r'^HTTP/([0-9.]+)[ \t]+\d{3}', headers, flags=re.MULTILINE)
    return matches[-1] if matches else None


def freeze():
    original_save = c.p.save
    def save(path, obj):
        if path == c.OUT/'manifest.json':
            obj.update(http_version_required='2', no_more_transport_candidates=True,
                       previous_stream_cost_usd='.00059654', cumulative_previous_cost_usd=str(PRIOR_COST))
            obj['input_hashes'].update({str(p.relative_to(ROOT)): c.p.sha(p) for p in
                (Path(__file__), PROTOCOL, PREVIOUS_STREAM/'qualification/manifest.json',
                 PREVIOUS_STREAM/'diagnostic/generation.json')})
        original_save(path, obj)
    c.p.save = save
    try: c.freeze()
    finally: c.p.save = original_save


def prepare(authorized):
    original_config, original_save = c.p.private_config, c.p.save
    def config(entries): return set_http2(original_config(entries))
    def save(path, obj):
        if path == c.OUT/'active.json' or path.parent == c.OUT/'attempts':
            obj['http_version_required'] = '2'
        original_save(path, obj)
    c.p.private_config, c.p.save = config, save
    try: c.prepare(authorized)
    finally: c.p.private_config, c.p.save = original_config, original_save


def finish(exitcode, http):
    attempt = c.c.load(c.OUT/'active.json'); rid = attempt['sample_id']
    header = c.OUT/'headers'/(rid+'.txt')
    version = response_http_version(header.read_text()) if header.exists() else None
    original_save = c.p.save
    def save(path, obj):
        if path == c.OUT/'finished'/(rid+'.json'):
            obj['reported_http_version'] = version
            obj['http_version_matches'] = version == '2'
            if version != '2':
                obj['continue_permitted'] = False
                obj['outcome'].update(status='http_version_mismatch', choice=None, correct=None, strict_format=None)
        original_save(path, obj)
    c.p.save = save
    try:
        with redirect_stdout(io.StringIO()): c.finish(exitcode, http)
    finally: c.p.save = original_save
    final = c.c.load(c.OUT/'finished'/(rid+'.json'))
    print(json.dumps(dict(sample_id=rid, status=final['outcome']['status'],
        continue_permitted=final['continue_permitted'], reported_http_version=version,
        parser_error=final['parser_error'], accuracy_not_reported=True)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=tuple(c.N), default='qualification')
    parser.add_argument('--stage', choices=('preflight-config', 'freeze', 'prepare', 'finish', 'status', 'refresh-config', 'refresh', 'calibration-analysis'), required=True)
    parser.add_argument('--execute-authorized', action='store_true')
    parser.add_argument('--curl-exit', type=int); parser.add_argument('--http-status', type=int)
    args = parser.parse_args(); configure(args.phase)
    if args.stage == 'prepare': prepare(args.execute_authorized)
    elif args.stage == 'finish':
        if args.curl_exit is None or args.http_status is None: parser.error('Actual curl/HTTP status required')
        finish(args.curl_exit, args.http_status)
    else:
        {'preflight-config': c.c.preflight_config, 'freeze': freeze, 'status': c.status,
         'refresh-config': c.b.refresh_config, 'refresh': c.b.refresh, 'calibration-analysis': c.calibration_analysis}[args.stage]()

"""One-attempt compact masked-review batches; curl handoff only."""
import argparse
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('focused_launch', ROOT/'scripts/85_selective_reliance_launch.py')
l = importlib.util.module_from_spec(spec)
spec.loader.exec_module(l)
BASE = l.BASE/'review_v2'


def manifest():
    m = l.c.load(BASE/'manifest.json')
    if l.p.sha(ROOT/'docs/SELECTIVE_RELIANCE_REVIEW_BATCH_AMENDMENT.md') != m['amendment_sha256']:
        raise ValueError('Review amendment changed')
    for batch in m['batches']:
        if l.p.sha(BASE/f'batch{batch["batch"]}'/'request.json') != batch['request_sha256']:
            raise ValueError('Review request changed')
    return m


def prepare(number):
    l.a.no_other_collection()
    m = manifest()
    if not 0 <= l.c.seconds_since(m['created_at']) < 3600:
        raise ValueError('Review preflight expired')
    for previous in range(1, number):
        if not l.c.load(BASE/f'batch{previous}'/'delivery.json')['delivery_valid']:
            raise ValueError('Prior review batch failed')
    folder = BASE/f'batch{number}'
    if (folder/'attempt.json').exists():
        raise ValueError('Already attempted; no retry')
    entry = m['batches'][number-1]
    config = l.p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',
        header=['Authorization: Bearer '+l.p.key(), 'Content-Type: application/json'],
        data_binary='@'+str(folder/'request.json'), output=folder/'raw.json',
        dump_header=folder/'headers.txt', write_out='%{http_code}', max_time=180, connect_timeout=20)])
    l.p.save(folder/'attempt.json', dict(prepared_at=l.p.now(), config=config,
        reserved_cost_usd=entry['reserve_usd'], request_sha256=entry['request_sha256']))
    print('curl --config '+config)


def finish(number, exitcode, http):
    m = manifest()
    folder = BASE/f'batch{number}'
    attempt = l.c.load(folder/'attempt.json')
    Path(attempt['config']).unlink(missing_ok=True)
    rawpath = folder/'raw.json'
    try:
        raw = l.c.load(rawpath)
    except (OSError, ValueError):
        raw = {}
    amount = Decimal(str(raw.get('usage', {}).get('cost', 'NaN')))
    valid = (exitcode == 0 and http == 200 and raw.get('provider') == m['provider']
        and raw.get('model') == m['model'] and len(raw.get('choices', [])) == 1
        and raw['choices'][0].get('finish_reason') == 'stop'
        and amount.is_finite() and 0 <= amount <= Decimal(attempt['reserved_cost_usd']))
    l.p.save(folder/'delivery.json', dict(finished_at=l.p.now(), delivery_valid=valid,
        curl_exit=exitcode, http_status=http, recorded_cost_usd=str(amount) if amount.is_finite() else None,
        raw_sha256=l.p.sha(rawpath) if rawpath.exists() else None,
        headers_sha256=l.p.sha(folder/'headers.txt') if (folder/'headers.txt').exists() else None))
    if not valid:
        raise ValueError('Review batch delivery failed; stop version')
    text = raw['choices'][0]['message']['content'].strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    judgments = json.loads(text)
    l.p.save(folder/'initial_judgments.json', judgments)
    l.p.save(folder/'INITIAL_SHA256_LOCK.json', {str(path.relative_to(ROOT)): l.p.sha(path)
        for path in (folder/'request.json', folder/'raw.json', folder/'headers.txt',
                     folder/'delivery.json', folder/'initial_judgments.json')})
    items = judgments['items']
    if len(items) != 10 or {item['item_id'] for item in items} != set(m['batches'][number-1]['ids']):
        raise ValueError('Batch ID coverage failed')
    print(json.dumps(dict(batch=number, reviewed_items=len(items), delivery_valid=True,
                          recorded_cost_usd=str(amount), keys_not_compared=True)))


def combine():
    m = manifest()
    items, overall, paths = [], [], [BASE/'manifest.json']
    for number in range(1, 4):
        folder = BASE/f'batch{number}'
        if not l.c.load(folder/'delivery.json')['delivery_valid']:
            raise ValueError('Review batch failed')
        for name, expected in l.c.load(folder/'INITIAL_SHA256_LOCK.json').items():
            if l.p.sha(ROOT/name) != expected:
                raise ValueError('Review lock changed')
        judgments = l.c.load(folder/'initial_judgments.json')
        items += judgments['items']
        overall += judgments.get('overall_execution_blockers', [])
        paths += [path for path in folder.iterdir() if path.is_file()]
    initial = dict(reviewer_model=m['model'], context='Three fresh API contexts, masked inputs only',
                   items=items, overall_execution_blockers=overall)
    l.p.save(BASE/'initial_judgments.json', initial)
    paths += [BASE/'initial_judgments.json', l.PACKET/'review/masked_questions.json']
    # Complete review lock precedes loading author solutions and comparing keys.
    l.p.save(BASE/'INITIAL_SHA256_LOCK.json', {str(path.relative_to(ROOT)): l.p.sha(path) for path in paths})
    author = l.c.load(l.PACKET/'author/packet_with_solutions.json')
    indexed = {row['item_id']: row for row in items}
    if len(items) != len(indexed) or set(indexed) != {row['item_id'] for row in author}:
        raise ValueError('Combined coverage failed')
    disagreements = [row['item_id'] for row in author if indexed[row['item_id']]['chosen_letter'] != row['correct_letter']]
    blockers = [row['item_id'] for row in author
        if indexed[row['item_id']]['unique_supported_answer'] is not True
        or indexed[row['item_id']]['must_fix_before_execution'] is not False
        or indexed[row['item_id']]['disposition'] != 'retain']
    costs = sum((Decimal(l.c.load(BASE/f'batch{number}'/'delivery.json')['recorded_cost_usd'])
                 for number in range(1, 4)), Decimal('0.063988'))
    result = dict(created_at=l.p.now(), reviewed_items=len(items), key_agreement=len(author)-len(disagreements),
        disagreements=disagreements, item_blockers=blockers, overall_execution_blockers=overall,
        review_gate_passed=not disagreements and not blockers and not overall,
        recorded_cost_including_failed_initial_review_usd=str(costs), human_review=False,
        original_study_remains_paused=True)
    l.p.save(BASE/'adjudication.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('prepare', 'finish', 'combine'), required=True)
    parser.add_argument('--batch', type=int, choices=(1, 2, 3))
    parser.add_argument('--curl-exit', type=int)
    parser.add_argument('--http-status', type=int)
    args = parser.parse_args()
    if args.stage == 'combine':
        combine()
    elif args.stage == 'prepare':
        if args.batch is None:
            parser.error('Batch required')
        prepare(args.batch)
    else:
        if args.batch is None or args.curl_exit is None or args.http_status is None:
            parser.error('Batch and actual curl/HTTP status required')
        finish(args.batch, args.curl_exit, args.http_status)

"""Two-round masked adjudication with a restricted exact rational calculator."""
import argparse
import ast
from decimal import Decimal
from fractions import Fraction
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tool_review_helpers', ROOT/'scripts/85_selective_reliance_launch.py')
l = importlib.util.module_from_spec(spec)
spec.loader.exec_module(l)
BASE = l.PACKET/'execution_20261024'
OUT = BASE/'adjudication'
PROTOCOL = ROOT/'docs/SELECTIVE_RELIANCE_TOOL_ADJUDICATION.md'
PRIOR_COST = Decimal('.205859')
CAP = Decimal('.39')
MODEL = 'anthropic/claude-sonnet-4.5'
MAX_SECOND_MESSAGE_BYTES = 11000
TOOL = dict(type='function', function=dict(name='exact_rational_calculator',
    description='Compute exact fractions. Expressions use integer constants, parentheses, +, -, *, / only. Include one final-answer expression per item labeled with its exact item_id; additional intermediate calculations may use other labels.',
    parameters=dict(type='object', properties=dict(calculations=dict(type='array', items=dict(type='object',
        properties=dict(label=dict(type='string'), expression=dict(type='string')),
        required=['label', 'expression'], additionalProperties=False))), required=['calculations'], additionalProperties=False)))


def exact(expression):
    if not isinstance(expression, str) or len(expression) > 600:
        raise ValueError('Expression must be a short arithmetic string')
    tree = ast.parse(expression, mode='eval')
    if sum(1 for _ in ast.walk(tree)) > 180:
        raise ValueError('Expression too complex')
    def value(node):
        if isinstance(node, ast.Expression):
            return value(node.body)
        if isinstance(node, ast.Constant) and type(node.value) is int and abs(node.value) <= 1000000:
            return Fraction(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            n = value(node.operand)
            return n if isinstance(node.op, ast.UAdd) else -n
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = value(node.left), value(node.right)
            if isinstance(node.op, ast.Add): return a+b
            if isinstance(node.op, ast.Sub): return a-b
            if isinstance(node.op, ast.Mult): return a*b
            return a/b
        raise ValueError('Only bounded integer rational arithmetic is permitted')
    return value(tree)


def bound(request):
    n = len(json.dumps(request['messages'], ensure_ascii=False).encode())
    n += len(json.dumps(request.get('tools', []), ensure_ascii=False).encode())
    tokens = 4*(n+1024)
    rates = request['provider']['max_price']
    if tokens >= 200000:
        raise ValueError('Premium-tier input bound is not permitted')
    return (Decimal(tokens)*Decimal(str(rates['prompt']))+
            Decimal(request['max_tokens'])*Decimal(str(rates['completion'])))/1000000


def save(path, obj):
    l.p.save(path, obj)


def lock(paths, target):
    save(target, {str(path.relative_to(ROOT)): l.p.sha(path) for path in paths})


def verify_lock(path):
    for name, expected in l.c.load(path).items():
        if l.p.sha(ROOT/name) != expected:
            raise ValueError('Locked input changed: '+name)


def preflight():
    l.a.no_other_collection()
    l.f.verify(l.PACKET)
    verify_lock(l.BASE/'final_artifact_hashes.json')
    if (OUT/'preflight_pointer.json').exists():
        raise ValueError('Preflight already exists')
    import tempfile
    folder = Path(tempfile.mkdtemp(prefix='ddm-adjudication-', dir='/private/tmp'))
    entries = [dict(url='https://openrouter.ai/api/v1/'+route, header='Authorization: Bearer '+l.p.key(),
                    output=folder/(name+'.json'), max_time=30)
               for name, route in [('credits', 'credits'), ('allowance', 'auth/key')]]
    entries += [dict(url='https://openrouter.ai/api/v1/models/'+mid+'/endpoints',
                     output=folder/(name+'.json'), max_time=30)
                for name, mid in [('reviewer', MODEL), *l.p.MODELS.items()]]
    config = l.p.private_config(entries)
    save(OUT/'preflight_pointer.json', dict(created_at=l.p.now(), folder=str(folder), config=config))
    print('curl --parallel --parallel-max 5 --config '+config)


def request(messages, first):
    return dict(model=MODEL, messages=messages, tools=[TOOL],
        tool_choice=dict(type='function', function=dict(name='exact_rational_calculator')) if first else 'none',
        temperature=0, max_tokens=4000,
        provider=dict(order=['anthropic'], only=['anthropic'], allow_fallbacks=False,
                      require_parameters=True, max_price=dict(prompt=3, completion=15)))


def freeze():
    l.a.no_other_collection()
    pointer = OUT/'preflight_pointer.json'
    state = l.c.load(pointer)
    folder = Path(state['folder'])
    try:
        if not 0 <= l.c.seconds_since(state['created_at']) < 3600:
            raise ValueError('Stale preflight')
        snapshots = l.c.load(folder/'reviewer.json')
        ep = next(e for e in snapshots['data']['endpoints'] if e.get('tag') == 'anthropic' and e.get('status') == 0)
        if not {'temperature', 'max_tokens', 'tools', 'tool_choice'} <= set(ep['supported_parameters']):
            raise ValueError('Reviewer lacks required tool parameters')
        if Decimal(ep['pricing']['prompt']) != Decimal('.000003') or Decimal(ep['pricing']['completion']) != Decimal('.000015'):
            raise ValueError('Reviewer base prices changed')
        credit = l.c.load(folder/'credits.json')['data']
        allowance = l.c.load(folder/'allowance.json')['data'].get('limit_remaining')
        available = Decimal(str(credit['total_credits']))-Decimal(str(credit['total_usage']))
        if not available.is_finite() or available < 1 or (allowance is not None and Decimal(str(allowance)) < 1):
            raise ValueError('Total development reserve not covered')
        prior = l.c.load(l.BASE/'review_v3/adjudication.json')
        ids = sorted(set(prior['disagreements']) | set(prior['item_blockers']))
        masked = [row for row in l.c.load(l.PACKET/'review/masked_questions.json') if row['item_id'] in ids]
        if len(masked) != 9:
            raise ValueError('Expected nine prospectively flagged IDs')
        text = ('Independently solve and review all nine masked questions below. No author keys, prior judgments, solutions, '
            'or other research context are supplied. First derive the mathematical model from each literal stem. '
            'Use exact_rational_calculator ONCE to compute final numerical answers for ALL nine items, labeling each final '
            'expression with the exact item_id. You may add intermediate calculations with other labels. '
            'Use integer fractions, +,-,*,/,parentheses only; no code, functions or decimals. For decision problems compare '
            'conditional expected action payoffs and subtract the stated certain fees. For conditional sampling, model '
            'the stated selection protocol. Derive answers before selecting options. After the tool result, check both '
            'options and uniqueness and provide a final review; do not force an answer if the stem is ambiguous. '
            'These are development questions; identify assumptions and template dependence without claiming general validation.\n'
            'Questions:\n'+json.dumps(masked, separators=(',', ':')))
        req = request([dict(role='user', content=text)], True)
        reserve = bound(req)
        # Future round reserved at a fixed message-size maximum before this call.
        future = request([dict(role='user', content='')], False)
        future_tokens = 4*(MAX_SECOND_MESSAGE_BYTES+len(json.dumps([TOOL], ensure_ascii=False).encode())+1024)
        future_reserve = (Decimal(future_tokens)*3+Decimal(4000)*15)/1000000
        if reserve+future_reserve > CAP or PRIOR_COST+reserve+future_reserve > Decimal('.60'):
            raise ValueError('Both-round worst-case review reserve exceeds cap')
        save(OUT/'masked_questions.json', masked)
        save(OUT/'reviewer_endpoints.json', snapshots)
        save(OUT/'round1/request.json', req)
        inputs = [Path(__file__), PROTOCOL, OUT/'masked_questions.json', OUT/'round1/request.json',
                  l.BASE/'review_v3/INITIAL_SHA256_LOCK.json', l.BASE/'review_v3/adjudication.json']
        save(OUT/'manifest.json', dict(created_at=l.p.now(), preflight_started_at=state['created_at'],
            authorization='User: move in, following status explaining independent adjudication as the next step',
            ids=ids, reviewer_model=MODEL, provider='Anthropic', max_rounds=2, max_attempts_per_round=1,
            cap_usd=str(CAP), first_round_reserve_usd=str(reserve), second_round_maximum_reserve_usd=str(future_reserve),
            maximum_cost_usd=str(reserve+future_reserve), previous_recorded_cost_usd=str(PRIOR_COST),
            input_hashes={str(path.relative_to(ROOT)): l.p.sha(path) for path in inputs},
            human_review=False, original_study_remains_paused=True))
        print(json.dumps(dict(masked_items=9, two_round_full_reserve_usd=str(reserve+future_reserve),
                              cumulative_review_cost_bound_usd=str(PRIOR_COST+reserve+future_reserve))))
    finally:
        Path(state['config']).unlink(missing_ok=True)
        for path in folder.iterdir(): path.unlink()
        folder.rmdir()
        pointer.unlink()


def manifest():
    m = l.c.load(OUT/'manifest.json')
    for name, expected in m['input_hashes'].items():
        if l.p.sha(ROOT/name) != expected:
            raise ValueError('Adjudication input changed: '+name)
    return m


def prepare(number):
    l.a.no_other_collection()
    m = manifest()
    if not 0 <= l.c.seconds_since(m['preflight_started_at']) < 3600:
        raise ValueError('Preflight expired')
    folder = OUT/f'round{number}'
    if (folder/'attempt.json').exists():
        raise ValueError('Already attempted; no retry')
    if number == 2:
        verify_lock(OUT/'tool_result_lock.json')
        raw = l.c.load(OUT/'round1/raw.json')
        messages = l.c.load(OUT/'round1/request.json')['messages']
        message = raw['choices'][0]['message']
        messages += [dict(role='assistant', content=message.get('content'), tool_calls=message['tool_calls'])]
        messages += [dict(role='tool', tool_call_id=message['tool_calls'][0]['id'],
                          content=json.dumps(l.c.load(OUT/'calculator_result.json')))]
        messages += [dict(role='user', content='Now return ONLY JSON with items (all nine IDs) and overall_execution_blockers (list). Each item must contain item_id, chosen_letter (A/B/null), derived_answer (exact fraction or integer as a string matching your calculator result), derivation (at most 40 words), unique_supported_answer (boolean), alternative_assessment, concerns, disposition (retain/repair/exclude/unresolved), must_fix_before_execution (boolean). Use the exact calculation results, check both displayed options and the assumptions, and preserve any uncertainty. Do not call another tool.')]
        if len(json.dumps(messages, ensure_ascii=False).encode()) > MAX_SECOND_MESSAGE_BYTES:
            raise ValueError('Second-round input exceeds pre-reserved bound')
        req = request(messages, False)
        save(folder/'request.json', req)
    else:
        req = l.c.load(folder/'request.json')
    reserve = bound(req)
    if number == 2 and reserve > Decimal(m['second_round_maximum_reserve_usd']):
        raise ValueError('Second-round reserve exceeded')
    config = l.p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',
        header=['Authorization: Bearer '+l.p.key(), 'Content-Type: application/json'],
        data_binary='@'+str(folder/'request.json'), output=folder/'raw.json', dump_header=folder/'headers.txt',
        write_out='%{http_code}', max_time=180, connect_timeout=20)])
    save(folder/'attempt.json', dict(prepared_at=l.p.now(), config=config,
        request_sha256=l.p.sha(folder/'request.json'), reserved_cost_usd=str(reserve)))
    print('curl --config '+config)


def finish(number, exitcode, http):
    m = manifest()
    folder = OUT/f'round{number}'
    attempt = l.c.load(folder/'attempt.json')
    Path(attempt['config']).unlink(missing_ok=True)
    try: raw = l.c.load(folder/'raw.json')
    except (OSError, ValueError): raw = {}
    charge = Decimal(str(raw.get('usage', {}).get('cost', 'NaN')))
    choices = raw.get('choices', [])
    expected_finish = 'tool_calls' if number == 1 else 'stop'
    valid = (exitcode == 0 and http == 200 and raw.get('provider') == m['provider']
        and raw.get('model') == m['reviewer_model'] and len(choices) == 1
        and choices[0].get('finish_reason') == expected_finish
        and charge.is_finite() and 0 <= charge <= Decimal(attempt['reserved_cost_usd']))
    save(folder/'delivery.json', dict(finished_at=l.p.now(), curl_exit=exitcode, http_status=http,
        delivery_valid=valid, recorded_cost_usd=str(charge) if charge.is_finite() else None,
        raw_sha256=l.p.sha(folder/'raw.json') if (folder/'raw.json').exists() else None))
    if not valid:
        raise ValueError('Adjudication delivery failed; stop without retry')
    if number == 1:
        calls = choices[0]['message'].get('tool_calls', [])
        if len(calls) != 1 or calls[0]['function']['name'] != 'exact_rational_calculator':
            raise ValueError('Expected one calculator call')
        args = json.loads(calls[0]['function']['arguments'])
        calculations = args['calculations']
        if not 9 <= len(calculations) <= 50:
            raise ValueError('Invalid calculation count')
        result = {row['label']: str(exact(row['expression'])) for row in calculations}
        if len(result) != len(calculations) or not set(m['ids']) <= set(result):
            raise ValueError('Missing or duplicated final calculation labels')
        save(OUT/'calculator_arguments.json', args)
        save(OUT/'calculator_result.json', result)
        lock([folder/'request.json', folder/'raw.json', folder/'delivery.json',
              OUT/'calculator_arguments.json', OUT/'calculator_result.json'], OUT/'tool_result_lock.json')
        print(json.dumps(dict(round=1, delivery_valid=True, calculator_results=len(result), keys_not_compared=True,
                              recorded_cost_usd=str(charge))))
        return
    text = choices[0]['message']['content'].strip()
    if text.startswith('```'): text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    judgments = json.loads(text)
    save(OUT/'initial_judgments.json', judgments)
    lock([folder/'request.json', folder/'raw.json', folder/'delivery.json', OUT/'initial_judgments.json',
          OUT/'tool_result_lock.json', OUT/'masked_questions.json'], OUT/'INITIAL_SHA256_LOCK.json')
    # Independent derivations and tool use are locked before key comparison.
    items = judgments['items']
    indexed = {row['item_id']: row for row in items}
    if len(items) != len(indexed) or set(indexed) != set(m['ids']):
        raise ValueError('Adjudication ID coverage failed')
    calc = l.c.load(OUT/'calculator_result.json')
    author = {row['item_id']: row for row in l.c.load(l.PACKET/'author/packet_with_solutions.json')}
    issues = []
    for item in items:
        key, row = item['item_id'], author[item['item_id']]
        try: numeric_agreement = Fraction(item['derived_answer']) == Fraction(calc[key]) == Fraction(row['answer'])
        except (ValueError, TypeError, ZeroDivisionError): numeric_agreement = False
        if (not numeric_agreement or item['chosen_letter'] != row['correct_letter']
            or item['unique_supported_answer'] is not True or item['must_fix_before_execution'] is not False
            or item['disposition'] != 'retain'):
            issues.append(key)
    previous = l.c.load(l.BASE/'review_v3/initial_judgments.json')
    prior_index = {row['item_id']: row for row in previous['items']}
    unchanged_issues = [key for key, row in author.items() if key not in indexed
        and (prior_index[key]['chosen_letter'] != row['correct_letter']
             or prior_index[key]['unique_supported_answer'] is not True
             or prior_index[key]['must_fix_before_execution'] is not False
             or prior_index[key]['disposition'] != 'retain')]
    passed = not issues and not unchanged_issues and not judgments.get('overall_execution_blockers', [])
    cost = sum((Decimal(l.c.load(OUT/f'round{i}/delivery.json')['recorded_cost_usd']) for i in (1, 2)), Decimal(0))
    result = dict(created_at=l.p.now(), adjudicated_items=9, unflagged_prior_items=21, total_items_covered=30,
        adjudication_issues=issues, prior_unflagged_issues=unchanged_issues,
        overall_execution_blockers=judgments.get('overall_execution_blockers', []), review_gate_passed=passed,
        independent_tool_assisted_context=True, human_review=False, keys_changed=False,
        recorded_new_cost_usd=str(cost), cumulative_recorded_cost_usd=str(PRIOR_COST+cost),
        original_study_remains_paused=True)
    save(OUT/'adjudication.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('preflight-config', 'freeze', 'prepare', 'finish'), required=True)
    parser.add_argument('--round', type=int, choices=(1, 2))
    parser.add_argument('--curl-exit', type=int)
    parser.add_argument('--http-status', type=int)
    args = parser.parse_args()
    if args.stage == 'preflight-config': preflight()
    elif args.stage == 'freeze': freeze()
    elif args.stage == 'prepare':
        if args.round is None: parser.error('Round required')
        prepare(args.round)
    else:
        if args.round is None or args.curl_exit is None or args.http_status is None:
            parser.error('Round and actual transport/HTTP status required')
        finish(args.round, args.curl_exit, args.http_status)

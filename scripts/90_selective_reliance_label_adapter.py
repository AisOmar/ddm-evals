"""Normalize only exact item-ID or item-ID_final calculator result labels."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('label_adapter_review', ROOT/'scripts/88_selective_reliance_tool_review.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)
PROTOCOL = ROOT/'docs/SELECTIVE_RELIANCE_CALCULATOR_LABEL_ADAPTER.md'


def canonical_results(ids, results):
    output, mapping = {}, {}
    for item in ids:
        labels = [label for label in (item, item+'_final') if label in results]
        if len(labels) != 1:
            raise ValueError('Missing or ambiguous final label: '+item)
        mapping[item] = labels[0]
        output[item] = results[labels[0]]
    return output, mapping


def prepare_second():
    q.l.a.no_other_collection()
    m = q.manifest()
    folder = q.OUT/'round1'
    if not q.l.c.load(folder/'delivery.json')['delivery_valid']:
        raise ValueError('First round did not deliver')
    if not 0 <= q.l.c.seconds_since(m['preflight_started_at']) < 3600:
        raise ValueError('Expired adjudication preflight')
    raw = q.l.c.load(folder/'raw.json')
    message = raw['choices'][0]['message']
    calls = message['tool_calls']
    if len(calls) != 1 or calls[0]['function']['name'] != 'exact_rational_calculator':
        raise ValueError('Expected one calculator call')
    args = json.loads(calls[0]['function']['arguments'])
    rows = args['calculations']
    if not 9 <= len(rows) <= 50:
        raise ValueError('Unexpected number of calculations')
    results = {row['label']: str(q.exact(row['expression'])) for row in rows}
    if len(results) != len(rows):
        raise ValueError('Duplicate original labels')
    finals, mapping = canonical_results(m['ids'], results)
    q.save(q.OUT/'calculator_arguments.json', args)
    q.save(q.OUT/'calculator_all_results.json', results)
    q.save(q.OUT/'calculator_result.json', finals)
    q.save(q.OUT/'label_adapter.json', dict(created_at=q.l.p.now(), mapping=mapping,
        original_expressions_changed=False, author_keys_consulted=False,
        calculation_count=len(rows), final_count=len(finals)))
    q.lock([Path(__file__), PROTOCOL, folder/'request.json', folder/'raw.json', folder/'delivery.json',
            q.OUT/'calculator_arguments.json', q.OUT/'calculator_all_results.json',
            q.OUT/'calculator_result.json', q.OUT/'label_adapter.json'], q.OUT/'tool_result_lock.json')
    messages = q.l.c.load(folder/'request.json')['messages']
    messages += [dict(role='assistant', content=message.get('content'), tool_calls=calls)]
    messages += [dict(role='tool', tool_call_id=calls[0]['id'], content=json.dumps(results, separators=(',', ':')))]
    messages += [dict(role='user', content='Return JSON: items,overall_execution_blockers. Each item: item_id,chosen_letter,derived_answer,derivation,unique_supported_answer,alternative_assessment,concerns,disposition,must_fix_before_execution. All nine IDs.')]
    if len(json.dumps(messages, ensure_ascii=False).encode()) > q.MAX_SECOND_MESSAGE_BYTES:
        raise ValueError('Second-round message exceeds unchanged reserve limit')
    req = q.request(messages, False)
    reserve = q.bound(req)
    from decimal import Decimal
    if reserve > Decimal(m['second_round_maximum_reserve_usd']):
        raise ValueError('Second-round cost bound exceeded')
    destination = q.OUT/'round2'
    if (destination/'attempt.json').exists():
        raise ValueError('Already attempted; no retry')
    q.save(destination/'request.json', req)
    config = q.l.p.private_config([dict(url='https://openrouter.ai/api/v1/chat/completions',
        header=['Authorization: Bearer '+q.l.p.key(), 'Content-Type: application/json'],
        data_binary='@'+str(destination/'request.json'), output=destination/'raw.json',
        dump_header=destination/'headers.txt', write_out='%{http_code}', max_time=180, connect_timeout=20)])
    q.save(destination/'attempt.json', dict(prepared_at=q.l.p.now(), config=config,
        request_sha256=q.l.p.sha(destination/'request.json'), reserved_cost_usd=str(reserve),
        label_adapter_sha256=q.l.p.sha(q.OUT/'label_adapter.json')))
    print('curl --config '+config)


if __name__ == '__main__': prepare_second()

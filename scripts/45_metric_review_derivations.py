"""Check selected reviewer-authored derivations; never execute dataset code.

These fixed arithmetic models are analyst evidence, not independent review,
an interpreter, or a proof that the complete question bank is sound.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/research_directions/metric_validation_questions/masked_review_queue.jsonl'


def call_arguments(text):
    match = re.fullmatch(r'test\((0x[0-9a-f]+(?:,0x[0-9a-f]+)*)\)', text)
    if not match:
        raise ValueError('Only literal hexadecimal call arguments are permitted')
    return [int(n, 16) for n in match.group(1).split(',')]


def supported(item, values, target):
    return [i for i, value in enumerate(values) if value == target]


def loongarch_trace(args):
    # Algebraic reduction of F0031 only; not a general emulator.
    assert len(args) == 7
    a0, a1, a2, a3, a4, a5, _ = args
    signed16 = lambda n: (n & 65535) - (65536 if n & 32768 else 0)
    constant = (1601 << 52) | (114521 << 32) | (284384 << 12) | 2335
    base = constant + ((-172032 << 12) | 20)
    intermediate = 0xFE000001 if a3 & 255 else a1 & 0xFFFFFFFF
    dividend = a0 if intermediate & 0xFFFFFFFF else 1
    divisor = int(signed16(a2) + 2 != 0)
    if not divisor:
        raise ValueError('The checked argument set must not divide by zero')
    # For this question the divisor is always one, so signed remainder is zero.
    remainder = 0
    flag = int(((signed16(a5) if a4 else 113) & 0xFFFFFFFF) == 0)
    return dict(base=hex(base), intermediate=hex(intermediate),
                dividend_before_sign_extension=hex(dividend), divisor=divisor,
                remainder=remainder, final_boolean=flag, result=hex(base + flag))


def derive(items):
    by_id = {x['review_id']: x for x in items}
    proofs = {}
    item = by_id['F0001']
    assert 'g_48++' in item['question'] and '0xAD1532D4L' in item['question']
    vals = [0x2D76715F] * 5 + [0xCF1D65F4E26C12A7, 0x97BC8B421DD2EB2F,
            0x50730467, 0xED857289C089CED6, 0xAD1532D4 - (1 << 32), 0xF6A1241B]
    checksum = (-1 + 255 * sum(vals)) & ((1 << 64) - 1)
    assert checksum == 0x0B045ED5AA1C7E22
    proofs['F0001'] = dict(conditional_checksum=hex(checksum),
        assumptions='Two-complement 32-bit signed initializer; uint64 arithmetic; no argv=1; corrected format/compiler context still needed.')

    item = by_id['F0002']
    vals = [(a[0] & 255) + (a[1] & 1) for a in map(call_arguments, item['original_options'])]
    assert vals == [0xB8, 0xA0, 0xF9, 0xA1]
    proofs['F0002'] = dict(original_results=list(map(hex, vals)),
                          supported_original_indexes=supported(item, vals, 0xF9),
                          assumptions='First two inputs supply r0/r1 as in the reviewed trace; ABI/signature must be pinned.')

    value = 206 + 8432034738814474729 + 120 + ((60076 * 74) & 65535)
    assert not 4 < 74 - 198
    assert value == 0x75049AEB8CCB30E7
    proofs['F0007'] = dict(outer_loop_entered=False, result=hex(value),
                          assumptions='Conventional 8/16/32/64-bit integer widths and C++ conversion semantics.')

    item = by_id['F0008']
    raw = bytes.fromhex(item['question'].split('Packet bytes:')[1])
    assert raw[12:14] == b'\x86\xdd' and raw[20] == 58 and raw[54] == 134
    assert raw[59] == 0xC0 and raw[59] & 0x20 == 0
    proofs['F0008'] = dict(icmp_offset=54, flags_offset=59, flags=hex(raw[59]),
                          home_agent_mask='0x20', decoded_home_agent_flag=0,
                          assumptions='Ethernet-II plus fixed IPv6 header; H flag mapped using RFC 6275 and Wireshark field documentation.')

    encode = lambda n: n ^ (n >> 16)
    inverse = lambda e: e ^ (e >> 16)
    values = list(range(65536)) + [65536, 65537, 2**28 - 1, 399999999]
    assert all(inverse(encode(n)) == n for n in values)
    assert encode(-1) == encode(0) == 0
    proofs['F0016'] = dict(algebra='inverse(encode(s)) = s ^ (s >> 32) = s for 0 <= s < 2**32',
                          numerical_checks=len(values), negative_domain_collision=[-1, 0],
                          repaired_domain='0 <= secret < 400000000; built-in Python 3 int',
                          note='Sample checks supplement the algebra; they are not exhaustive over the domain.')

    item = by_id['F0020']
    a = call_arguments(re.search(r'test\([^)]*\)', item['question']).group())
    x = (~a[2]) & 0xFFFFFFFF
    signed16 = lambda n: (n & 65535) - (65536 if n & 32768 else 0)
    low = (a[1] & 1) | signed16(a[0])
    result = (x if x < 2**31 else x - 2**32) + (low & 0xFFFFFFFF)
    assert result == 0x06B67EE7
    proofs['F0020'] = dict(complemented_low32=hex(x), added_low32=hex(low), result=hex(result),
                          supported_retained_indexes=[i for i,o in enumerate(item['retained_options']) if int(o,16)==result])

    item = by_id['F0025']
    raw = bytes.fromhex(item['question'].split('Packet bytes:')[1])
    assert b'HTTP/' not in raw
    proofs['F0025'] = dict(http_version_token_in_supplied_bytes=False,
                          limitation='Does not prove the reassembled stream lacks a version; the missing earlier bytes are the problem.')

    item = by_id['F0031']
    traces = [loongarch_trace(call_arguments(o)) for o in item['original_options']]
    target = 0x6411BF591B6E0933
    assert all(int(t['result'],16) == target for t in traces)
    changed = call_arguments(item['retained_options'][0])
    changed[5] = 0
    distractor = 'test(' + ','.join(hex(n) for n in changed) + ')'
    changed_trace = loongarch_trace(changed)
    assert int(changed_trace['result'],16) == target + 1
    proofs['F0031'] = dict(original_traces=traces, supported_original_indexes=[0,1,2,3],
                          supported_retained_indexes=[0,1], proposed_new_distractor=distractor,
                          new_distractor_trace=changed_trace,
                          assumptions='Arguments directly initialize a0..a6; apply shown load/store widths and return a0; valid stack memory.')
    return proofs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Refusing to overwrite saved derivations')
    data = SOURCE.read_bytes()
    result = dict(masked_source_sha256=hashlib.sha256(data).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  evidence_kind='Analyst-authored fixed arithmetic checks, not independent validation.',
                  proofs=derive([json.loads(line) for line in data.splitlines()]))
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(n_derivations=len(result['proofs']), checks_passed=True)))


if __name__ == '__main__':
    main()

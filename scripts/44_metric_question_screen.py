"""Offline structural screening only: never adjudicates benchmark answers.

Reads the masked packet, not its proposed-key sidecar or model outcomes.
Output is immutable and deliberately cannot authorize collection.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/research_directions/metric_validation_questions/masked_review_queue.jsonl'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def screen(items):
    rows = []
    packets = defaultdict(list)
    for item in items:
        q = item['question']
        flags = []
        detail = {}
        assert len(item['original_options']) == 4
        assert len(item['retained_options']) == 2
        assert len(set(item['retained_options'])) == 2
        assert all(o in item['original_options'] for o in item['retained_options'])
        # Exact positive match: a format header with no following function body.
        if re.search(r'assembly function.*?\bfunc\.o: file format wasm\s*\Z', q, re.S):
            flags.append('missing_wasm_function_body')
        if 'Packet bytes:' in q:
            try:
                raw = bytes.fromhex(q.split('Packet bytes:', 1)[1])
                digest = sha(raw)
                packets[digest].append(item['review_id'])
                detail.update(packet_sha256=digest, packet_bytes=len(raw))
            except ValueError:
                flags.append('invalid_packet_hex')
        label = re.search(r'(?:register_(\d+).*regnum16|bit_(\d+)_.*bitnum)', q)
        if label:
            value = next(v for v in label.groups() if v is not None)
            flags.append('requested_number_visible_in_field_label')
            detail.update(visible_label_number=value,
                          label_number_is_retained_option=value in item['retained_options'])
        if '__null' in q:
            flags.append('compiler_extension_needs_environment_review')
        rows.append(dict(review_id=item['review_id'], structural_flags=flags,
                         structural_details=detail, answer_review='not_adjudicated',
                         eligible_for_collection=False))
    for row in rows:
        digest = row['structural_details'].get('packet_sha256')
        if digest:
            row['packet_content_family'] = 'packet-bytes:' + digest
            row['family_members'] = packets[digest]
            if len(packets[digest]) > 1:
                row['structural_flags'].append('shared_exact_packet_bytes')
        else:
            row['packet_content_family'] = None
        row['semantic_family_review'] = 'pending'
    return rows, packets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError('Refusing to overwrite a saved screening')
    data = SOURCE.read_bytes()
    items = [json.loads(line) for line in data.splitlines()]
    assert len({x['review_id'] for x in items}) == len(items)
    rows, packets = screen(items)
    summary = dict(created_at=datetime.now(timezone.utc).isoformat(),
                   masked_source_sha256=sha(data), script_sha256=sha(Path(__file__).read_bytes()),
                   n_items=len(items), structural_flag_counts=dict(Counter(
                       f for row in rows for f in row['structural_flags'])),
                   n_packet_questions=sum(map(len, packets.values())),
                   n_distinct_exact_packet_payloads=len(packets),
                   repeated_packet_families=[v for v in packets.values() if len(v) > 1],
                   independent_review_complete=False, collection_ready=False,
                   limitations=[
                       'Screening is not an answer, difficulty, or semantic-family review.',
                       'No flag does not mean valid. A flag is not automatically an exclusion.',
                       'Shared bytes establish a conservative dependency group, not equivalence of questions.',
                       'Field-label checks do not independently verify the decoded packet value.',
                       'Compiler-extension checks do not prove every affected program is invalid.'
                   ])
    args.out.mkdir(parents=True)
    (args.out / 'structural_screen.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in rows))
    (args.out / 'screen_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

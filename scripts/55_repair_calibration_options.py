"""Append-only option repair; preserve script 54's initial locked development draft."""
from fractions import Fraction
import hashlib
import json
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'results/research_directions/reliance_calibration_v2'
OUT = BASE/'review_revision'


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def matched_fraction_distractor(answer, prefer_above):
    value = Fraction(answer)
    for gap in range(1,value.denominator):
        for sign in ((1,-1) if prefer_above else (-1,1)):
            numerator = value.numerator+sign*gap
            if 0 < numerator < value.denominator and gcd(numerator,value.denominator) == 1:
                return str(Fraction(numerator,value.denominator))
    raise ValueError('Cannot construct distinct matched-denominator alternative')


def build():
    if OUT.exists():
        raise ValueError('Review revision exists; refusing overwrite')
    locks = json.loads((BASE/'artifact_hashes.json').read_text())
    for name,expected in locks.items():
        if digest(ROOT/name) != expected:
            raise ValueError(f'Initial locked input changed: {name}')
    rows = json.loads((BASE/'packet.json').read_text())
    repairs = []
    for row in rows:
        if row['family'] != 'urn_posterior':
            continue
        wrong_letter = 'B' if row['correct_letter'] == 'A' else 'A'
        before = row['options'][wrong_letter]
        # Alternate relative magnitude independently of answer position.
        after = matched_fraction_distractor(row['answer'],(row['seed']//2) % 2 == 0)
        row['options'][wrong_letter] = after
        if Fraction(after).denominator != Fraction(row['answer']).denominator:
            raise ValueError('Denominator cue remains')
        repairs.append(dict(item_id=row['item_id'],before=before,after=after))
    documents = {'packet.json':rows,'repair_log.json':dict(
        reason='Initial probability distractors had systematically longer denominators',
        first_draft_preserved=True,repairs=repairs,
        independent_review_complete=False,model_calls_launched=0)}
    for split in ('calibration','reserved'):
        documents[f'{split}_masked_review.json'] = [{k:r[k] for k in ('item_id','family','stem','options')}
            for r in rows if r['split'] == split]
    documents['readiness.json'] = dict(
        current_review_packet='review_revision',supersedes_initial_options_only=True,
        n_calibration=24,n_reserved=24,independent_review_complete=False,
        live_delivery_validated=False,exact_request_manifest_frozen=False,
        model_calls_launched=0,old_study_remains_paused=True,
        remaining_gates=['masked semantic review','live delivery canary',
                         'budget and exact calibration request freeze'])
    OUT.mkdir()
    for name,value in documents.items():
        with (OUT/name).open('x') as f:
            json.dump(value,f,indent=2)
            f.write('\n')
    paths = [Path(__file__),ROOT/'docs/RELIANCE_CALIBRATION_REVIEW.md',BASE/'artifact_hashes.json']
    paths += [OUT/name for name in documents]
    with (OUT/'artifact_hashes.json').open('x') as f:
        json.dump({str(p.relative_to(ROOT)):digest(p) for p in paths},f,indent=2)
        f.write('\n')
    print(json.dumps(dict(repaired_items=len(repairs),model_calls_launched=0)))


if __name__ == '__main__':
    build()

"""Independently recorded masked judgments; no author keys or generators used."""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'independent_review'
items = json.loads((BASE / 'review/masked_items.json').read_text())
template = json.loads((BASE / 'review/review_template.json').read_text())
# Each row independently records choice, derivation, rejected-option assessment,
# wording concerns, and estimated elementary solution operations.
rows = {
 'M001': ('A', '100*(1-0.20)=80; 80*(1+0.20)=96.', 'B incorrectly treats equal percentage changes on different bases as canceling.', [], 2),
 'M002': ('A', 'Monday plus three days is Thursday (today); the next day is Friday.', 'B would require today to be Friday, four days after Monday.', [], 2),
 'M003': ('A', 'The day after Monday is Tuesday. If Tuesday was two days ago, today is Thursday and tomorrow is Friday.', 'B is one day too late; the offsets from Tuesday to tomorrow total three days.', [], 3),
 'M004': ('B', 'Let child price be c and adult price c+9. Then 2c+9=11, hence c=1.', 'A=2 gives an adult price of 11 and a total of 13, violating the total.', ['The definite adult/child references conventionally identify the two tickets; explicitly saying one adult and one child would remove a very minor referential presupposition.'], 3),
 'M005': ('A', 'Times are 12/6=2 hours and 12/3=4 hours. Total distance/time=24/6=4 km/h.', 'B is the unweighted arithmetic mean of the two speeds, which is inappropriate for equal distances with unequal times.', [], 3),
 'M006': ('B', 'The intervention replaces the X equation, so X=4 and U=3. Y=2*4+3=11.', 'A=10 does not satisfy the retained Y equation with the stated post-intervention values.', [], 2),
 'M007': ('B', 'If Omar has o tokens, Lina has 2o and their difference is o=6.', 'A=3 gives Lina 6 and a difference of only 3.', [], 2),
 'M008': ('A', 'The reduced price is 100*0.8=80; the increase is 0.2*80=16, producing 96 credits.', 'B incorrectly cancels equal percentage changes despite their different bases.', [], 3),
 'M009': ('A', '100*0.8=80; increasing this by 20% gives 80+0.2*80=96.', 'B would require adding 20 credits, whereas 20% of the result is 16.', [], 3),
 'M010': ('A', 'There are 18+16=34 flagged devices, of which 18 are infected. The probability is 18/34=9/17.', 'B=9/10 is 18/20, the fraction of infected devices flagged, a different conditioning event.', [], 2),
 'M011': ('A', 'The outbound and return distances are each 12 km. Times are 12/6=2 and 12/3=4 hours; average speed=24/(2+4)=4 km/h.', 'B is the unweighted mean of speeds and ignores the longer time spent returning.', ['"Same 12 km route" is naturally the one-way route length. Even if treated as total length, equal outbound/return distances still imply the same average speed.'], 3),
 'M012': ('A', 'Treat scanner detections as flags: 12 infected and 18 uninfected devices are flagged. Probability=12/(12+18)=2/5.', 'B=3/4 is 12/16, the detection rate among infected devices, not infection probability among flagged devices.', ['Uses "detects" for infected devices and "flags" for uninfected ones. Ordinary scanner usage makes detected devices flagged, but literal precision would use "flags" consistently or explicitly equate the terms.'], 2),
 'M013': ('A', 'Two days after Tuesday is Thursday. If Thursday was the day before yesterday, today is Saturday and tomorrow is Sunday.', 'B is one day too late.', [], 3),
 'M014': ('B', '80*(1-0.25)=60; 60*(1+0.25)=75 credits.', 'A incorrectly treats equal percentage changes on different bases as canceling.', [], 2),
 'M015': ('B', 'Sealed implies labeled. The parcel is not labeled, so by contraposition it is not sealed.', 'A rejects an entailment that follows directly from the stated necessary condition.', ['"Required" is read as the universal necessary condition given in the first sentence. A real-world policy-with-violations reading would weaken the premise, but is not the natural reading of this abstract logic item.'], 2),
 'M016': ('B', 'Let Ben have b tokens; Nora has 3b and 3b-b=10. Therefore 2b=10 and b=5.', 'A=10/3 treats 10 as Nora\'s total rather than the difference; it gives difference 20/3.', [], 3),
 'M017': ('B', 'Let Omar have o tokens. Lina has 2o, and token counts are nonnegative, so the difference is 2o-o=o=6.', 'A=3 yields a difference of only 3.', ['The unsigned "difference" relies on ordinary nonnegative token counts to fix direction; this is supplied by the token-count domain. No extra assumption is missing in ordinary usage.'], 2),
 'M018': ('B', 'With child price c, adult price is c+9. Their sum gives 2c+9=11, so c=1.', 'A=2 leads to adult price 11 and total 13.', [], 3),
 'M019': ('B', 'Choose the insulated pipe guaranteed to exist. It is dry, and no dry pipe is wet, so it is an insulated pipe that is not wet.', 'A needs at least one wet pipe. A model containing just one insulated dry nonwet pipe satisfies every premise but makes A false.', [], 3),
 'M020': ('B', 'Only the X equation is replaced. Substitute X=4 and U=3 into Y=2X+U to get 11.', 'A=10 does not obey the retained equation for Y.', [], 2),
 'M021': ('A', 'Three days after Monday is Thursday, so tomorrow is Friday.', 'B puts today on Friday and violates the three-day offset.', [], 2),
 'M022': ('B', 'If the child price is c, adult price is c+9. Thus c+(c+9)=11 and c=1.', 'A=2 gives a combined price of 13.', [], 3),
 'M023': ('A', 'Times are 18/9=2 hours and 18/6=3 hours. Average speed=36/(2+3)=7.2 km/h.', 'B=7.5 is the unweighted mean of speeds and ignores unequal travel times.', [], 3),
 'M024': ('B', 'Force X=4 while U=3 and Y=2X+U remains in effect: Y=8+3=11.', 'A=10 is inconsistent with the fixed U and retained Y equation.', [], 2),
 'M025': ('B', 'The intervention gives X=2 while U=4. The retained equation gives Y=3*2+4=10.', 'A=5 does not satisfy the retained equation under the intervention.', [], 2),
 'M026': ('A', 'The flagged group has 18+16=34 devices and 18 infected devices. Uniform sampling gives 18/34=9/17.', 'B=18/20=9/10 describes the fraction of infected devices flagged, not the fraction infected among flags.', [], 2),
 'M027': ('B', 'Every sealed parcel is labeled; this one is not labeled. Contraposition implies it is not sealed.', 'A denies a consequence of the universal premise.', ['"Unsealed" is interpreted in its usual binary opposition to sealed; no third state is introduced by the premises.'], 2),
 'M028': ('A', 'Taking detections to be scanner flags, the flagged set has 18 infected plus 16 uninfected devices. Probability=18/34=9/17.', 'B=9/10 is scanner sensitivity, 18/20, rather than the requested conditional probability.', ['Uses "detects" and "flags" for the two groups. Ordinary usage links these, but strict explicitness would say "flags" in both clauses.'], 2),
 'M029': ('B', 'No sealed parcel lacks a label. This parcel lacks one, so assuming it sealed contradicts the universal premise. Sealing is impossible under these premises.', 'A permits a state explicitly excluded by the universal premise.', ['The yes/no question uses "impossible" and a negated universal, increasing polarity tracking without adding a substantive premise.'], 2),
 'M030': ('A', 'Let child price be c. Then adult price=c+13 and 2c+13=17, so c=2.', 'B=4 leads to adult price 17 and total 21.', [], 3),
 'M031': ('A', 'The travel times are 12/6=2 and 12/3=4 hours. Average speed is 24/6=4 km/h.', 'B is the unweighted arithmetic mean, which is wrong for equal-distance legs at unequal speeds.', [], 3),
 'M032': ('B', 'Let Omar have o tokens; Lina has 2o and 2o-o=6, so o=6.', 'A=3 produces Lina=6 and a difference of 3.', [], 2),
}
assert len(rows) == len(items) == 32
review = {k:v for k,v in template.items() if k != 'items'}
review.update(reviewer='independent_wording_review: fresh-context AI reviewer (Codex); not a human reviewer', date='2026-10-22', prior_exposure={'before_initial_lock': ['review/masked_items.json', 'review/review_template.json'], 'excluded': ['author keys', 'author packet', 'generator scripts', 'proposal', 'matched_sets.json', 'model outputs'], 'independence_limits': 'A separate agent was tasked with this review. No author answer/context was supplied. All anonymous items are visible together, so repeated content can be noticed naturally. This is an independent AI review, not human validation.'})
review['interpretation_policy'] = 'Assess literal entailment under ordinary mathematical English, while recording minor lexical conventions separately. unique_answer means one option is supported by that reading; strict wording qualifications remain visible in wording_concerns.'
review['items'] = []
for item in items:
    letter, derivation, alternative, concerns, steps = rows[item['review_id']]
    review['items'].append(dict(review_id=item['review_id'], chosen_letter=letter, derived_answer=item['options'][letter], unique_answer=True, must_fix=False, derivation=derivation, alternative_assessment={letter:'Supported by the derivation.', ('B' if letter == 'A' else 'A'):alternative}, wording_concerns=concerns, expected_steps=steps, difficulty='easy', literal_uniqueness='Unique under ordinary mathematical English.' if not concerns else 'Unique under ordinary mathematical English; see wording_concerns for lexical qualifications.'))
review['summary'] = {'items':32, 'unique_answers':32, 'must_fix':0, 'blocking_concerns':[], 'optional_precision_concerns':['M004','M012','M015','M028'], 'note':'M012 and M028 rely on the ordinary scanner convention that detected devices are flagged. This is a precision concern rather than a second mathematically supported option.'}
target=OUT/'initial_judgments.json'
target.write_text(json.dumps(review, indent=2)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
lock={'locked_at_utc':datetime.now(timezone.utc).isoformat(), 'stage':'initial judgments before any matched-set inspection', 'inputs':{str(p.relative_to(BASE)):sha(p) for p in [BASE/'review/masked_items.json',BASE/'review/review_template.json']}, 'outputs':{str(p.relative_to(BASE)):sha(p) for p in [target,Path(__file__).resolve()]}, 'prohibited_inputs_read':False}
(OUT/'INITIAL_SHA256_LOCK.json').write_text(json.dumps(lock,indent=2)+'\n')
print(json.dumps({'items':len(review['items']),'unique_answers':32,'must_fix':0,'initial_lock_written':True}))

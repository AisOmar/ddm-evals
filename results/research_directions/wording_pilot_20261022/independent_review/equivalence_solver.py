"""Second-stage matched-set review, performed after the initial SHA256 lock."""
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE/'independent_review'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
initial_lock_path = OUT/'INITIAL_SHA256_LOCK.json'
initial_lock = json.loads(initial_lock_path.read_text())
for group in ['inputs','outputs']:
    for name, digest in initial_lock[group].items():
        assert sha(BASE/name) == digest, name
initial = json.loads((OUT/'initial_judgments.json').read_text())
by_id = {x['review_id']: x for x in initial['items']}
matched_path = BASE/'review/matched_sets.json'
matched = json.loads(matched_path.read_text())
details = {
 'W01': {
  'facts':'One adult and one child ticket total 11 credits, with the adult costing 9 more.',
  'target':'Child price, 1 credit (B).',
  'assumptions':'Ordinary exact ticket prices; the first version presupposes that the two tickets are the adult and child subsequently named.',
  'comments':['Equivalent under ordinary reference resolution.', 'Weak manipulation: plain M004 and trap M022 use almost the same sum-and-difference formulation. Trap wording does not clearly add a new source of linguistic misdirection. Neutral M018 uses combined price and price difference but preserves the algebra.'],
  'differences':['M004 says two tickets before identifying their types; M018 and M022 identify one of each explicitly.', 'Neutral nominalizes the difference; plain and trap state the comparative directly.'],
  'flags':['weak_plain_trap_separation']},
 'W02': {
  'facts':'Two 12 km legs at 6 and 3 km/h with no stops.',
  'target':'Overall distance/time, 4 km/h (A).',
  'assumptions':'Average speed means total distance divided by elapsed time. Outbound and return use equal route lengths.',
  'comments':['The return-trip wrapper changes geography but no relevant numerical information.', 'Neutral explicitly supplies the definition of average speed; this is a procedural cue, not a changed target or new quantitative fact. Plain and trap both permit the familiar arithmetic-mean error.'],
  'differences':['M011 uses an out-and-back trip on the same route; M005 and M031 use sequential legs.', 'M005 asks directly for total distance divided by total time; the others say average speed.'],
  'flags':['procedural_cue_in_neutral','overlapping_distractor_exposure']},
 'W03': {
  'facts':'100 total devices, 20 infected, 18 infected flags and 16 uninfected flags.',
  'target':'Infection probability among uniformly sampled flagged devices, 9/17 (A).',
  'assumptions':'Detected infected devices are members of the flagged group; uniform sampling within that group.',
  'comments':['Equivalent under the ordinary scanner convention that a detection is a flag.', 'Literal precision qualification: M028 switches from detects to flags without explicitly identifying them. With an artificial distinction between detected and flagged sets the flagged infected count would be missing; M010 and M026 do not require this lexical bridge.', 'The trap exposes 18/20 as a salient sensitivity fraction. Plain also gives the same numbers; the difference is their framing.'],
  'differences':['M010 presents the flagged composition directly.', 'M026 reports scanner flags directly.', 'M028 phrases infected detections as 18 of 20 before mentioning false-positive flags.'],
  'flags':['minor_detect_flag_lexical_bridge','overlapping_distractor_exposure']},
 'W04': {
  'facts':'Sealed implies labeled; the designated parcel is not labeled.',
  'target':'Whether this parcel cannot be sealed; Yes (B).',
  'assumptions':'Required is a logical necessary condition, not a policy permitting violations. Unsealed and not sealed are equivalent in this context.',
  'comments':['All three encode the same implication and its contrapositive.', 'M029 adds genuine polarity-tracking load through no ... lacks and impossible; it does not add a premise.', 'M015 uses required, which can sound normative outside an abstract logic task. This is a minor wording precision concern under ordinary mathematical reading.'],
  'differences':['M015 states a necessary condition.', 'M027 states a direct universal implication and explicitly restricts reasoning to premises.', 'M029 uses a negated existential and asks about impossibility.'],
  'flags':['minor_normative_reading_in_neutral','polarity_complexity_change']},
 'W05': {
  'facts':'Today is Thursday in every version.',
  'target':'Tomorrow is Friday (A).',
  'assumptions':'Ordinary seven-day weekday arithmetic with exact relative-day offsets.',
  'comments':['The apparent anchor changes are arithmetically equivalent: Monday three days ago and Tuesday two days ago both fix Thursday today.', 'Trap wording adds a nested day-after reference and day-before-yesterday offset. Plain and neutral are nearly identical, so their distinction is weak.'],
  'differences':['M002 and M021 anchor Monday three days before today.', 'M003 identifies Tuesday indirectly as the day after Monday and places it two days before today.'],
  'flags':['weak_plain_neutral_separation','additional_reference_resolution_step']},
 'W06': {
  'facts':'Lina has twice Omar\'s count and exceeds it by 6 tokens.',
  'target':'Omar has 6 tokens (B).',
  'assumptions':'Token counts are nonnegative; thus the unsigned difference in M017 is Lina minus Omar.',
  'comments':['No numerical or target change.', 'Weak manipulation: all versions directly provide the ratio and difference. M007 compresses them into a relative clause; it is not clearly more misleading than the other versions.'],
  'differences':['M032 uses two short sentences.', 'M007 uses which puts her 6 tokens ahead.', 'M017 uses a nominal unsigned difference, whose direction follows from nonnegative counts.'],
  'flags':['weak_trap_separation','ordinary_domain_assumption']},
 'W07': {
  'facts':'U=3, initial X=U+2, retained Y=2X+U; X is externally set to 4 with U fixed.',
  'target':'Post-intervention Y=11 (B).',
  'assumptions':'The intervention replaces only the X equation and leaves the Y equation in force.',
  'comments':['Every version explicitly communicates the intervention override and fixed U. No changed causal information.', 'Weak manipulation: the trap explicitly says instead of following its equation, while neutral says override only the X equation. Both strongly disambiguate the same operation, so condition separation is slight.'],
  'differences':['M006 says instead of following its equation.', 'M020 says override only the X equation.', 'M024 explicitly leaves both U and the Y equation unchanged.'],
  'flags':['weak_condition_separation','overlapping_override_cues']},
 'W08': {
  'facts':'Start at 100 credits, reduce by 20%, then increase the reduced amount by 20%.',
  'target':'Final price 96 credits (A).',
  'assumptions':'Each percentage is applied to its explicitly stated base; exact arithmetic.',
  'comments':['All versions explicitly identify the reduced-price base for the second percentage.', 'Weak manipulation: trap M008 adds same percentage, which may prime cancellation, but plain M001 also repeats equal 20% rates. Neutral M009 supplies the equivalent 0.8 multiplier, adding a procedural cue and reducing conversion work.'],
  'differences':['M001 states both percentages numerically.', 'M008 calls the rise the same percentage and immediately specifies its base.', 'M009 replaces the first percentage decrease with multiplication by 0.8.'],
  'flags':['weak_plain_trap_separation','procedural_cue_in_neutral']},
}
sets=[]
for group in matched:
    pid=group['problem_id']; d=details[pid]
    answers={by_id[v['review_id']]['derived_answer'] for v in group['versions']}
    assert len(answers)==1
    sets.append(dict(problem_id=pid, versions=group['versions'], equivalent=True, must_fix=False, same_supported_answer=True, same_underlying_facts=True, same_target=True, changed_information=False, assumptions=d['assumptions'], supported_answer=d['target'], underlying_facts=d['facts'], comments=d['comments'], differences=d['differences'], flags=d['flags'], semantic_equivalence_scope='Relevant mathematical information under ordinary mathematical English; contextual wrappers and procedural cues may differ.'))
result={'reviewer':initial['reviewer'], 'date':'2026-10-22', 'stage':'Matched-set equivalence review after initial judgment lock', 'context_limitations':'Read masked_items.json and review_template.json before initial lock; then only matched_sets.json plus own saved judgments. No author keys, author packet, generators, proposal, or model outputs read. Independent AI review, not human review.', 'initial_lock_sha256':sha(initial_lock_path), 'sets':sets, 'summary':{'sets':8,'equivalent_under_ordinary_reading':8,'must_fix':0,'blocking_concerns':[], 'construct_validity_concern':'Several wording conditions are weakly separated. These items can test performance on the concrete paraphrases but this review does not validate a general neutral/plain/trap construct or guarantee a manipulation effect.', 'sets_with_minor_literal_precision_qualifications':['W01','W03','W04','W06']}}
target=OUT/'equivalence_judgments.json'
target.write_text(json.dumps(result,indent=2)+'\n')
lock={'locked_at_utc':datetime.now(timezone.utc).isoformat(),'stage':'equivalence after initial lock','preserved_initial_lock_sha256':sha(initial_lock_path),'inputs':{str(p.relative_to(BASE)):sha(p) for p in [matched_path,OUT/'initial_judgments.json',initial_lock_path,BASE/'review/masked_items.json']}, 'outputs':{str(p.relative_to(BASE)):sha(p) for p in [target,Path(__file__).resolve()]}, 'prohibited_inputs_read':False}
(OUT/'EQUIVALENCE_SHA256_LOCK.json').write_text(json.dumps(lock,indent=2)+'\n')
print(json.dumps(result['summary']))

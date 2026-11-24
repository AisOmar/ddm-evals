"""Eight fresh resource probes, masked for review; no model calls or overwrites."""
from fractions import Fraction
import importlib.util
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('new_resource_helpers',ROOT/'scripts/74_qwen_provider_comparison.py')
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
BASE=ROOT/'results/research_directions/deepinfra_wording_resource_20261022'
PROTOCOL=ROOT/'docs/DEEPINFRA_WORDING_RESOURCE_PROTOCOL.md'
PROBES=[
 ('N01','difference','trap','An adult ticket and a child ticket cost 23 credits in total. The adult ticket costs 17 credits more than the child ticket. How much does the child ticket cost?','3 credits','6 credits','x+(x+17)=23, so x=3.'),
 ('N02','average_speed','neutral','On a nonstop 30 km ride, the first 15 km are covered at 5 km/h and the remaining 15 km at 10 km/h. What is total distance divided by total time?','20/3 km/h','15/2 km/h','Time is 3+3/2=9/2 hours, so 30/(9/2)=20/3 km/h.'),
 ('N03','conditioning','trap','A scanner flags 24 of the 30 infected devices in a batch of 90. It also flags 12 uninfected devices. If one flagged device is chosen uniformly at random, what is the probability it is infected?','2/3','4/5','24/(24+12)=2/3; 24/30 is sensitivity, not the requested posterior.'),
 ('N04','implication','plain','Every copper disk is round. No round disk is heavy. At least one copper disk exists. Which statement must be true, using only these premises?','Some copper disk is not heavy.','Some heavy disk is not copper.','An existing copper disk is round and therefore not heavy; heavy disks need not exist.'),
 ('N05','relative_time','trap','The day before yesterday was the day after Thursday. What weekday will tomorrow be?','Monday','Tuesday','The day before yesterday was Friday; today is Sunday; tomorrow is Monday.'),
 ('N06','ratio_difference','plain','Asha has four times as many tokens as Ivo and has 18 more tokens than Ivo. How many tokens does Ivo have?','6','9/2','4x-x=18, so x=6.'),
 ('N07','intervention','neutral','Initially U=5, X=U+1, and Y=2*X+U. Override only the X equation with X=3, keep U fixed, and compute the resulting Y.','11','8','Keep U=5; Y=2*3+5=11. Inferring U=2 from the overridden equation is invalid.'),
 ('N08','successive_percentages','plain','A price starts at 120 credits, falls by 25%, and then rises by 20% of its reduced value. What is the final price?','108 credits','114 credits','120*(3/4)*(6/5)=108; the increases use different bases.'),
]


def build():
    if BASE.exists():raise ValueError('Existing version; never overwrite')
    assert Fraction(23-17,2)==3
    assert Fraction(30)/(Fraction(15,5)+Fraction(15,10))==Fraction(20,3)
    assert Fraction(24,24+12)==Fraction(2,3)
    assert (3+1+2+1)%7==0 # Thursday=3, Friday day-before-yesterday, tomorrow Monday.
    assert Fraction(18,4-1)==6 and 2*3+5==11
    assert 120*Fraction(3,4)*Fraction(6,5)==108
    old=q.c.load(ROOT/'results/research_directions/wording_pilot_20261022/packet.json')
    old+=q.c.load(ROOT/'results/research_directions/short_reasoning_v4_20261022/author/packet_with_solutions.json')
    old+=q.d.QUESTION_ROWS+q.QUESTIONS
    assert not {p[3] for p in PROBES}&{r['stem'] for r in old}
    rng=random.Random(20261022076);letters=list('AAAABBBB');rng.shuffle(letters)
    rows=[]
    for probe,letter in zip(PROBES,letters):
        item,family,version,stem,answer,wrong,derivation=probe
        options={l:answer if l==letter else wrong for l in 'AB'}
        rows.append(dict(item_id=item,family=family,version=version,cohort='resource',stem=stem,
            answer=answer,distractor=wrong,initial_letter=letter,options=options,author_derivation=derivation))
    rng.shuffle(rows)
    for i,row in enumerate(rows,1):row['review_id']=f'V{i:03}'
    masked=[{k:r[k] for k in ('review_id','stem','options')} for r in rows]
    q.p.save(BASE/'packet.json',rows)
    q.p.save(BASE/'review/masked_items.json',masked)
    q.p.save(BASE/'review/review_template.json',dict(reviewer=None,date=None,prior_exposure=None,
        items=[dict(review_id=r['review_id'],chosen_letter=None,derived_answer=None,unique_answer=None,must_fix=None,
                    derivation=None,alternative_assessment=None,wording_concerns=None) for r in masked]))
    q.p.save(BASE/'design.json',dict(planned_resource_calls=16,resource_items=8,reasoning_types=8,
        routes={'Qwen3':'deepinfra/fp8','gpt-oss':'dekallm/bf16'},temperature=.7,max_tokens=2048,
        timeout_seconds=180,minimum_preparation_interval_seconds=5,ceiling_usd='0.10',order_seed=20261022077,
        author_keys_checked=True,independent_review_complete=False,model_calls_launched=0,
        pilot_calls_included=0,original_study_remains_paused=True))
    paths=[Path(__file__),PROTOCOL,BASE/'packet.json',BASE/'review/masked_items.json',BASE/'review/review_template.json',BASE/'design.json']
    q.p.save(BASE/'packet_hashes.json',{str(p.relative_to(ROOT)):q.p.sha(p) for p in paths})
    print('Prepared eight fresh masked resource items; independent review pending; no model calls.')


if __name__=='__main__':build()

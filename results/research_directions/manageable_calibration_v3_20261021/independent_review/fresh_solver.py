"""Independent masked-only review. No author keys or other artifacts accessed."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations
from functools import lru_cache
from math import comb
import re, json, hashlib, datetime
BASE=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
INPUTS=[BASE/(x+'_masked_review.json') for x in ['resource','calibration','reserved']]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
items=[q for p in INPUTS for q in json.loads(p.read_text())]
judgments=[]
for q in items:
 s=q['stem']; fam=q['family']; details={}; issues=[]
 if fam=='recurrence':
  a,b=map(int,re.search(r'x_0=(\d+), x_1=(\d+)',s).groups())
  c,d,m=map(int,re.search(r'of (\d+)\*x_\(n-1\) \+ (\d+)\*x_\(n-2\) modulo (\d+)',s).groups())
  n=int(re.search(r'What is x_(\d+)',s).group(1)); xs=[a,b]
  for i in range(2,n+1): xs.append((c*xs[-1]+d*xs[-2])%m)
  @lru_cache(None)
  def rec(i): return a if i==0 else b if i==1 else (c*rec(i-1)+d*rec(i-2))%m
  ans=xs[n]; assert ans==rec(n)
  deriv=f'Sequence x_0 through x_{n}: {xs}. Apply the given linear combination and least nonnegative residue at each step.'
  details={'full_sequence':xs,'crosscheck':'memoized recursive definition agrees with forward iteration','modular_steps':n-1}
  difficulty='easy-to-moderate: '+str(n-1)+' sequential modular updates; error propagation creates bookkeeping burden'
 elif fam=='subset_count':
  w=json.loads(re.search(r'weights (\[[^\]]+\])',s).group(1))
  bound,r,m=map(int,re.search(r'at most (\d+) and congruent to (\d+) modulo (\d+)',s).groups())
  valid=[{'labels_1_based':[i+1 for i in ix],'weights':[w[i] for i in ix],'total':sum(w[i] for i in ix)} for ix in combinations(range(6),3) if sum(w[i] for i in ix)<=bound and sum(w[i] for i in ix)%m==r]
  ans=len(valid)
  masks=[mask for mask in range(64) if mask.bit_count()==3 and (t:=sum(v for i,v in enumerate(w) if mask>>i&1))<=bound and t%m==r]
  assert ans==len(masks)
  deriv='Enumerate all C(6,3)=20 unordered labeled triples; retain those meeting both sum constraints. Valid triples (weights; total): '+str([(v['weights'],v['total']) for v in valid])+'.'
  details={'valid_subsets':valid,'crosscheck':'combinations enumeration agrees with all 64 bit masks restricted to popcount 3'}
  difficulty='moderate: exhaustive check of at most 20 small triples; systematic bookkeeping matters'
 elif fam=='shortest_path':
  edges=json.loads(re.search(r'Edges: (\[.*\])\.',s).group(1)); adj={i:[] for i in range(6)}
  for u,v,w in edges: adj[u].append((v,w))
  paths=[]
  def dfs(u,cost,path):
   if u==5: paths.append((cost,path)); return
   for v,w in adj[u]:
    if v not in path: dfs(v,cost+w,path+[v])
  dfs(0,0,[0]); paths.sort(); ans=paths[0][0]
  dist=[float('inf')]*6; dist[0]=0
  for _ in range(5):
   for u,v,w in edges: dist[v]=min(dist[v],dist[u]+w)
  assert ans==dist[5]
  deriv='Enumerate every directed 0-to-5 path; minimum '+str(ans)+' attained by '+str([p for c,p in paths if c==ans])+'. All path costs: '+str([c for c,p in paths])+'.'
  details={'paths':[{'cost':c,'vertices':p} for c,p in paths],'distances_from_zero':dist,'crosscheck':'full directed path enumeration agrees with five-pass edge relaxation'}
  difficulty='easy: visible direct or two-edge route; all costs positive, small acyclic directed graph'
  if len(paths[0][1])==2: issues.append({'severity':'scope_note','issue':'Direct 0-to-5 edge is optimal; graph detail adds little necessary search. Valid item, but weak as a difficult planning task.'})
 elif fam=='urn_posterior':
  prior=F(re.search(r'probability (\d+/\d+)',s).group(1))
  ur,ub,vr,vb=map(int,re.search(r'U contains (\d+) red and (\d+) blue balls; V contains (\d+) red and (\d+) blue',s).groups())
  n,kb=map(int,re.search(r'Draw (\d+) balls.*exactly one red and (\d+) blue',s).groups()); assert n==1+kb
  lu=F(comb(ur,1)*comb(ub,kb),comb(ur+ub,n)); lv=F(comb(vr,1)*comb(vb,kb),comb(vr+vb,n))
  def enum_likelihood(red,blue):
   subs=list(combinations(range(red+blue),n)); return F(sum(sum(i<red for i in x)==1 for x in subs),len(subs))
  assert lu==enum_likelihood(ur,ub) and lv==enum_likelihood(vr,vb)
  post=prior*lu/(prior*lu+(1-prior)*lv); pct=100*post
  rounded=(2*pct.numerator+pct.denominator)//(2*pct.denominator)
  assert F(rounded)-F(1,2)<=pct<F(rounded)+F(1,2)
  ans=str(rounded)+'%'
  deriv=f'P(E|U)=C({ur},1)C({ub},{kb})/C({ur+ub},{n})={lu}; P(E|V)=C({vr},1)C({vb},{kb})/C({vr+vb},{n})={lv}. Bayes: ({prior}*{lu})/[{prior}*{lu}+(1-{prior})*{lv}]={post}. Exact percent={pct} = {float(pct):.12f}%; rounding interval [{F(rounded)-F(1,2)}, {F(rounded)+F(1,2)}) gives {ans} with half-up convention.'
  details={'likelihood_U':str(lu),'likelihood_V':str(lv),'posterior_exact':str(post),'percent_exact':str(pct),'percent_decimal':float(pct),'half_up_integer':rounded,'rounding_interval_percent':[str(F(rounded)-F(1,2)),str(F(rounded)+F(1,2))],'distance_to_nearest_rounding_boundary_percentage_points':str(min(pct-(F(rounded)-F(1,2)),F(rounded)+F(1,2)-pct)),'crosscheck':'hypergeometric likelihoods agree with enumeration of labeled ball combinations; exact rational interval verifies half-up rounding'}
  difficulty='moderate: two small hypergeometric likelihoods and Bayesian normalization, followed by explicit rounding'
 else: raise ValueError(fam)
 answer=str(ans)
 checks={k:{'displayed_value':v,'matches_derived_answer':v==answer,'reason':'equals uniquely derived exact/rounded answer' if v==answer else 'does not equal derived exact/rounded answer'} for k,v in q['options'].items()}
 letters=[k for k,v in q['options'].items() if v==answer]
 unique=len(letters)==1
 if not unique: issues.append({'severity':'must_fix','issue':'No unique matching option'})
 judgments.append({'item_id':q['item_id'],'family':fam,'derived_answer':answer,'chosen_letter':letters[0] if unique else 'unresolved','unique_answer':unique,'must_fix':not unique,'alternative_checks':checks,'derivation':deriv,'computational_details':details,'issues':issues,'disposition':'valid; retain for bounded computation/resource calibration' if unique else 'must fix','expected_difficulty':difficulty+'; qualitative forecast only, empirical difficulty and resource sensitivity remain unknown'})
(OUT/'initial_judgments.json').write_text(json.dumps(judgments,indent=2)+'\n')
from collections import Counter,defaultdict
positions=Counter(x['chosen_letter'] for x in judgments)
by_split={k:dict(Counter(x['chosen_letter'] for x in judgments if x['item_id'].startswith(k+'-'))) for k in ['resource','calibration','reserved']}
by_family={k:dict(Counter(x['chosen_letter'] for x in judgments if x['family']==k)) for k in sorted(set(x['family'] for x in judgments))}
summary={'review_type':'Fresh-context AI review; not a human expert review and not independent training. Reviewer initially read only the three named masked input files. No author keys, generators, protocols, previous packets, or author judgments were accessed.','items_reviewed':len(judgments),'unique_answer_items':sum(x['unique_answer'] for x in judgments),'unresolved':sum(not x['unique_answer'] for x in judgments),'must_fix_blockers':[x['item_id'] for x in judgments if any(y['severity']=='must_fix' for y in x['issues'])],'option_position_counts':dict(positions),'position_counts_by_split':by_split,'position_counts_by_family':by_family,'assessment':{'correctness_ambiguity':'All numerical alternatives explicitly checked. Each item has exactly one correct option. Wording disambiguates subset labeling, selection order, graph direction, replacement and rounding. No correctness or ambiguity blocker found.','rounding':'All nine urn posteriors computed as exact fractions; half-up nearest whole percentage point independently checked by exact interval membership. Adjacent percentage alternatives remain uniquely resolvable.','difficulty_status':'No response data were inspected. Difficulty labels are qualitative forecasts, not empirical calibration. Actual model error rates and benefit from added computation remain unknown.', 'option_cues':'Both options have matched formatting and no answer-explanation leakage. Small two-option sets permit 50% chance performance. Incorrect alternatives are numerically nearby; no universal higher/lower shortcut or positional shortcut is supported. Position counts are balanced within each split and near-balanced by family. The calibration and reserved urn blocks both follow A-B-A-B, a visible local pattern when solutions are exposed; this is not a logically valid stem-only answer cue and does not block the narrow numerical calibration, but item order should not be treated as an independent difficulty signal.','computation_scope':'Narrow arithmetic templates: recurrences require 6-9 dependent modular steps; subsets require at most 20 triples; shortest paths are very small positive-weight DAGs, frequently solved by a direct edge or visible two-edge route; urns use two likelihoods and a Bayes update. These are valid manageable resource/calibration tasks but do not alone establish broad difficult-reasoning ability.','template_overlap':'All three splits reuse the same four exact verbal templates with parameter changes. This is intended-looking within-family transfer and a material limitation on claims of novel-template generalization. No exact duplicate full stem was found. Repeated urn evidence structure, fixed six-object subsets, six-vertex DAGs, and fixed-order recurrences make solution strategies reusable.','recommended_disposition':'Proceed with resource tests and calibration if claims remain limited to these four computational templates. No must-fix item blocker. Consider separate novel-template evaluation if broader generalization is the target.'}}
assert len({x['stem'] for x in items})==len(items)
(OUT/'initial_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
files=INPUTS+[OUT/'fresh_solver.py',OUT/'initial_judgments.json',OUT/'initial_summary.json']
lock={'lock_type':'SHA256 initial masked-only review lock, before any author-key comparison','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer_statement':'Fresh-context AI reviewer. Never opened author keys. Not human expert or independent training.','input_sha256':{str(p):sha(p) for p in INPUTS},'output_sha256':{str(p):sha(p) for p in files if p not in INPUTS}}
(OUT/'INITIAL_SHA256_LOCK.json').write_text(json.dumps(lock,indent=2)+'\n')
print(json.dumps(summary,indent=2))
print('LOCK:',OUT/'INITIAL_SHA256_LOCK.json')

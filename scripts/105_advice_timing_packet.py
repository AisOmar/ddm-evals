"""Fresh instances of six previously checked mathematical families."""
from fractions import Fraction as F
from functools import lru_cache
import heapq
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/research_directions/advice_timing_20261027'
spec=importlib.util.spec_from_file_location('exact_transfer',ROOT/'scripts/103_verification_transfer_packet.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)

def build():
    rows=[]
    def add(family,stem,answer,wrong,proof,letter):
        assert str(answer)!=str(wrong)
        options={'A':str(answer if letter=='A' else wrong),'B':str(wrong if letter=='A' else answer)}
        rows.append(dict(item_id=f'U{len(rows)+1:03}',family=family,stem=stem,options=options,correct_letter=letter,answer=str(answer),author_certificate=proof))
    weights=[11,11,8,8,5,5,4,4,4,4]
    @lru_cache(None)
    def pack(i,loads):
        if i==len(weights):return len(loads)
        best=pack(i+1,tuple(sorted(loads+(weights[i],))))
        for j,v in enumerate(loads):
            if v+weights[i]<=13:
                alt=list(loads);alt[j]+=weights[i];best=min(best,pack(i+1,tuple(sorted(alt))))
        return best
    bins=pack(0,());assert bins==6
    add('integer_bin_packing','Ten indivisible objects have weights 11, 11, 8, 8, 5, 5, 4, 4, 4, 4. A bin holds total weight at most 13. What is the minimum number of bins? No object can be split.',bins,5,dict(exact_search=bins,lower_bound='The two 11s cannot share a bin with any remaining object. The remaining weight is 42 and needs at least four bins of capacity 13.',packing=[[11],[11],[8,5],[8,5],[4,4,4],[4]]),'A')
    weights2=[2,4,7,11,18,26,32];heap=weights2.copy();heapq.heapify(heap);merges=[]
    while len(heap)>1:
        val=heapq.heappop(heap)+heapq.heappop(heap);merges.append(val);heapq.heappush(heap,val)
    @lru_cache(None)
    def prefix(mask):
        if mask&(mask-1)==0:return 0
        total=sum(w for i,w in enumerate(weights2) if mask>>i&1);best=10**9;sub=(mask-1)&mask
        while sub:
            if sub<(mask^sub):best=min(best,total+prefix(sub)+prefix(mask^sub))
            sub=(sub-1)&mask
        return best
    optimal=prefix(127);assert optimal==sum(merges)==243
    add('optimal_binary_prefix_code','Seven symbols occur 2, 4, 7, 11, 18, 26, and 32 times. Assign a distinct binary codeword to each symbol, with no codeword a prefix of another and no alphabetical-order constraint. What is the smallest total number of bits to encode all 100 occurrences?',optimal,245,dict(huffman_merge_sums=merges,exhaustive_binary_partition_dp=optimal),'B')
    matrix=[[5,-1,1,-2],[2,3,1,-2],[2,-1,6,-2],[2,-1,1,6]]
    det=old.determinant(matrix);lemma=480*(1+F(2,3)-F(1,4)+F(1,5)-F(2,8));assert det==lemma==656
    add('rank_one_determinant','Find the determinant of the 4 by 4 matrix whose rows are (5, -1, 1, -2), (2, 3, 1, -2), (2, -1, 6, -2), and (2, -1, 1, 6).',det,540,dict(permutation_expansion=det,rank_one_formula='D=diag(3,4,5,8), u=(1,1,1,1), v=(2,-1,1,-2); det=480*(1+2/3-1/4+1/5-2/8)=656'),'A')
    edges=[{1,2},{2,3},{3,4},{1,4},{1,2,3,4},{5,6},{6,7},{7,8},{8,9}]
    @lru_cache(None)
    def match(i,used):
        if i==len(edges):return 0
        return max([match(i+1,used)]+[1+match(i+1,used|1<<j) for j in edges[i] if not used>>j&1])
    maximum=match(0,0);assert maximum==8
    add('bipartite_matching_deficiency','Nine workers A through I can each take at most one task, and each task can have at most one worker. Eligible task sets are A:{1,2}, B:{2,3}, C:{3,4}, D:{1,4}, E:{1,2,3,4}, F:{5,6}, G:{6,7}, H:{7,8}, I:{8,9}. Workers may remain unassigned. What is the largest number of tasks that can be assigned?',maximum,9,dict(exact_subset_dp=maximum,upper_bound='A through E can occupy at most four tasks.',witness={'A':1,'B':2,'C':3,'E':4,'F':5,'G':6,'H':7,'I':8}),'B')
    pattern='HTHTH';n=len(pattern);a=[[F(int(i==j)) for j in range(n)] for i in range(n)];transitions=[]
    for i in range(n):
        nxt=[]
        for char in 'HT':
            s=pattern[:i]+char;k=max(k for k in range(n+1) if s.endswith(pattern[:k]));nxt.append(k)
            if k<n:a[i][k]-=F(1,2)
        transitions.append(nxt)
    expected=old.solve_linear(a,[1]*n)[0];overlap=sum(2**k for k in range(1,n+1) if pattern[:k]==pattern[-k:]);assert expected==overlap==42
    add('overlapping_pattern_waiting_time','Independently flip a fair coin until the consecutive pattern HTHTH first appears. Overlapping candidate occurrences are allowed. Starting with no flips, what is the expected total number of flips, including the final five?',expected,32,dict(prefix_automaton=transitions,exact_expectation=str(expected),prefix_suffix_overlap_sum=overlap),'A')
    jobs=[(0,4,10),(1,3,9),(3,5,10),(4,7,16),(5,8,15),(7,9,13),(8,11,19),(9,12,20),(11,13,15)]
    feasible=[]
    for mask in range(1<<len(jobs)):
        chosen=sorted(jobs[i] for i in range(len(jobs)) if mask>>i&1)
        if all(x[1]<=y[0] for x,y in zip(chosen,chosen[1:])):feasible.append((sum(x[2] for x in chosen),chosen))
    optimum,witness=max(feasible);ordered=sorted(jobs,key=lambda x:x[1]);dp=[0]
    for i,(start,end,profit) in enumerate(ordered):
        j=sum(x[1]<=start for x in ordered[:i]);dp.append(max(dp[-1],profit+dp[j]))
    assert optimum==dp[-1]
    add('weighted_interval_scheduling','One machine can run any subset of jobs, each given as (start,end,profit): '+str(jobs)+'. Jobs occupy [start,end), so finishing exactly when another starts is allowed. Jobs cannot be moved, split or repeated. What is the maximum total profit?',optimum,optimum-1,dict(exhaustive_subset_optimum=optimum,dynamic_program=dp,witness=witness),'B')
    return rows

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True);rows=build()
    with (OUT/'fresh_author_packet.json').open('x') as f:json.dump(rows,f,indent=2);f.write('\n')
    print(json.dumps(dict(items=len(rows),answers={r['item_id']:r['answer'] for r in rows})))

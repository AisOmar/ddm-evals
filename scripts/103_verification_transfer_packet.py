"""Exact offline construction of six new local reasoning-template families."""
from fractions import Fraction as F
from functools import lru_cache
import heapq
from itertools import permutations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/research_directions/verification_transfer_20261026'

def determinant(matrix):
    n=len(matrix);total=0
    for perm in permutations(range(n)):
        term=(-1)**sum(perm[i]>perm[j] for i in range(n) for j in range(i+1,n))
        for i,j in enumerate(perm):term*=matrix[i][j]
        total+=term
    return total

def solve_linear(a,b):
    a=[list(map(F,row))+[F(v)] for row,v in zip(a,b)]
    for k in range(len(a)):
        pivot=next(i for i in range(k,len(a)) if a[i][k])
        a[k],a[pivot]=a[pivot],a[k];v=a[k][k];a[k]=[x/v for x in a[k]]
        for i in range(len(a)):
            if i!=k:
                v=a[i][k];a[i]=[x-v*y for x,y in zip(a[i],a[k])]
    return [row[-1] for row in a]

def build():
    rows=[]
    def add(family,stem,answer,wrong,certificate,letter):
        assert str(answer)!=str(wrong)
        rows.append(dict(item_id=f'T{len(rows)+1:03}',family=family,split='fresh',stem=stem,options=({'A':str(answer),'B':str(wrong)} if letter=='A' else {'A':str(wrong),'B':str(answer)}),correct_letter=letter,answer=str(answer),author_certificate=certificate))
    weights=[8,8,6,6,4,4,3,3,3,3]
    @lru_cache(None)
    def pack(index,loads):
        if index==len(weights):return len(loads)
        best=len(weights)
        for j,load in enumerate(loads):
            if load+weights[index]<=10:
                other=list(loads);other[j]+=weights[index]
                best=min(best,pack(index+1,tuple(sorted(other))))
        return min(best,pack(index+1,tuple(sorted(loads+(weights[index],)))))
    minimum=pack(0,())
    assert minimum==6
    add('integer_bin_packing','Ten indivisible objects have weights 8, 8, 6, 6, 4, 4, 3, 3, 3, 3. Each bin can hold total weight at most 10. Objects cannot be split. What is the minimum number of bins?',minimum,5,dict(exact_search=minimum,lower_bound='The two 8s require separate bins and cannot share any remaining object. Remaining weight is 32, requiring at least four more bins.',packing=[[8],[8],[6,4],[6,4],[3,3,3],[3]]),'B')
    weights2=[3,5,8,12,17,24,31];heap=weights2.copy();heapq.heapify(heap);merges=[]
    while len(heap)>1:
        x=heapq.heappop(heap)+heapq.heappop(heap);merges.append(x);heapq.heappush(heap,x)
    @lru_cache(None)
    def prefix(mask):
        if mask&(mask-1)==0:return 0
        total=sum(w for i,w in enumerate(weights2) if mask>>i&1);best=10**9
        sub=(mask-1)&mask
        while sub:
            if sub<mask^sub:best=min(best,total+prefix(sub)+prefix(mask^sub))
            sub=(sub-1)&mask
        return best
    optimum=prefix((1<<len(weights2))-1)
    assert optimum==sum(merges)==252
    add('optimal_binary_prefix_code','Seven symbols occur 3, 5, 8, 12, 17, 24, and 31 times. Assign each symbol a distinct binary codeword so that no codeword is a prefix of another. There is no alphabetical-order constraint. What is the minimum total number of bits for encoding all 100 symbol occurrences?',optimum,254,dict(huffman_merge_sums=merges,all_binary_partitions_dp=optimum),'A')
    matrix=[[3,-1,2,-2],[1,2,2,-2],[1,-1,7,-2],[1,-1,2,5]]
    det=determinant(matrix);lemma=210*(1+F(1,2)-F(1,3)+F(2,5)-F(2,7))
    assert det==lemma==269
    add('rank_one_determinant','What is the determinant of the 4 by 4 matrix with rows (3, -1, 2, -2), (1, 2, 2, -2), (1, -1, 7, -2), and (1, -1, 2, 5)?',det,210,dict(permutation_expansion=det,rank_one_check='D=diag(2,3,5,7), u=(1,1,1,1), v=(1,-1,2,-2); det(D+uv^T)=210*(1+1/2-1/3+2/5-2/7)=269'),'B')
    edges=[{1,2},{2,3},{1,3},{1,2,3},{4,5},{5,6},{6,7,8},{4,7,8}]
    @lru_cache(None)
    def matching(i,used):
        if i==len(edges):return 0
        return max([matching(i+1,used)]+[1+matching(i+1,used|(1<<j)) for j in edges[i] if not used>>j&1])
    match=matching(0,0);assert match==7
    add('bipartite_matching_deficiency','Eight workers A through H can each perform at most one task, and each task can be assigned to at most one worker. Eligible task sets are A:{1,2}, B:{2,3}, C:{1,3}, D:{1,2,3}, E:{4,5}, F:{5,6}, G:{6,7,8}, H:{4,7,8}. Assigning every worker is optional. What is the maximum number of tasks that can be assigned?',match,8,dict(exact_subset_dp=match,upper_bound='A,B,C,D can occupy only three tasks.',witness={'A':1,'B':2,'C':3,'E':4,'F':5,'G':6,'H':7}),'A')
    pattern='HHTH';n=len(pattern);a=[[F(int(i==j)) for j in range(n)] for i in range(n)]
    transitions=[]
    for i in range(n):
        row=[]
        for char in 'HT':
            s=pattern[:i]+char
            k=max(k for k in range(n+1) if s.endswith(pattern[:k]));row.append(k)
            if k<n:a[i][k]-=F(1,2)
        transitions.append(row)
    expected=solve_linear(a,[1]*n)[0]
    # Fair-pattern expectation also equals the sum of 2^k over prefix/suffix overlaps.
    overlap=sum(2**k for k in range(1,n+1) if pattern[:k]==pattern[-k:])
    assert expected==overlap==18
    add('overlapping_pattern_waiting_time','A fair coin is flipped independently until the consecutive four-flip pattern HHTH first appears. Counting all flips from the start, including the final four, what is the expected number of flips? Overlapping candidate occurrences are allowed.',expected,16,dict(prefix_automaton_transitions=transitions,exact_linear_solution=str(expected),overlap_formula=overlap),'B')
    jobs=[(0,3,12),(1,2,5),(2,5,15),(3,4,6),(4,7,18),(5,6,7),(6,9,21),(7,8,8),(8,11,24),(9,10,9),(10,13,27),(11,12,10)]
    feasible=[]
    for mask in range(1<<len(jobs)):
        chosen=sorted(jobs[i] for i in range(len(jobs)) if mask>>i&1)
        if all(x[1]<=y[0] for x,y in zip(chosen,chosen[1:])):feasible.append((sum(x[2] for x in chosen),chosen))
    opt,witness=max(feasible)
    ordered=sorted(jobs,key=lambda x:x[1]);dp=[0]
    for i,(start,end,value) in enumerate(ordered):
        j=sum(other[1]<=start for other in ordered[:i]);dp.append(max(dp[-1],value+dp[j]))
    assert opt==dp[-1] and opt!=78
    add('weighted_interval_scheduling','A single machine can run any subset of these jobs. Each tuple is (start time, end time, profit): '+str(jobs)+'. A job occupies the half-open interval [start,end); jobs ending exactly when another begins are compatible. No job may be split, shifted or repeated. What is the largest achievable total profit?',opt,78,dict(exhaustive_subset_optimum=opt,weighted_interval_dp=dp,witness=witness),'A')
    return rows

def save():
    rows=build();OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/'fresh_author_packet.json'
    with path.open('x') as f:json.dump(rows,f,indent=2);f.write('\n')
    print(json.dumps(dict(items=len(rows),answers={r['item_id']:r['answer'] for r in rows})))

if __name__=='__main__':save()

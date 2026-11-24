"""Offline levels with practice/reserved allocation fixed before calibration."""
from fractions import Fraction as F
from functools import lru_cache
import heapq
import importlib.util
import json
import math
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/research_directions/separate_difficulty_20261027'
s=importlib.util.spec_from_file_location('exact_math',ROOT/'scripts/103_verification_transfer_packet.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
FAMILIES=('integer_bin_packing','optimal_binary_prefix_code','dense_determinant','bipartite_matching_deficiency','overlapping_pattern_waiting_time','weighted_interval_scheduling')

def bin_packing(weights,capacity):
    # Exact subset DP minimizes (bins used, load of the last bin).
    size=1<<len(weights);dp=[(len(weights)+1,0)]*size;dp[0]=(1,0)
    for mask in range(1,size):
        best=dp[mask];bits=mask
        while bits:
            bit=bits&-bits;i=bit.bit_length()-1;bins,load=dp[mask^bit]
            alt=(bins,load+weights[i]) if load+weights[i]<=capacity else (bins+1,weights[i])
            best=min(best,alt);bits^=bit
        dp[mask]=best
    answer=dp[-1][0];descending=tuple(sorted(weights,reverse=True))
    @lru_cache(None)
    def feasible(i,loads):
        if i==len(descending):return True
        weight=descending[i];seen=set()
        for j,load in enumerate(loads):
            if load in seen or load+weight>capacity:continue
            seen.add(load);alt=list(loads);alt[j]+=weight
            if feasible(i+1,tuple(sorted(alt))):return True
        return False
    assert feasible(0,(0,)*answer)
    assert answer==1 or not feasible(0,(0,)*(answer-1))
    return answer

def prefix_optimum(weights):
    heap=weights.copy();heapq.heapify(heap);merges=[]
    while len(heap)>1:
        val=heapq.heappop(heap)+heapq.heappop(heap);merges.append(val);heapq.heappush(heap,val)
    @lru_cache(None)
    def partition(mask):
        if mask&(mask-1)==0:return 0
        total=sum(w for i,w in enumerate(weights) if mask>>i&1);best=10**12;sub=(mask-1)&mask
        while sub:
            if sub<(mask^sub):best=min(best,total+partition(sub)+partition(mask^sub))
            sub=(sub-1)&mask
        return best
    answer=partition((1<<len(weights))-1);assert answer==sum(merges)
    return answer,merges

def determinant_elimination(matrix):
    a=[list(map(F,row)) for row in matrix];det=F(1)
    for k in range(len(a)):
        candidates=[i for i in range(k,len(a)) if a[i][k]]
        if not candidates:return F(0)
        i=candidates[0]
        if i!=k:a[k],a[i]=a[i],a[k];det=-det
        pivot=a[k][k];det*=pivot
        for i in range(k+1,len(a)):
            factor=a[i][k]/pivot
            for j in range(k,len(a)):a[i][j]-=factor*a[k][j]
    return det

def make(level,family,variant):
    index=FAMILIES.index(family);rng=random.Random(2026102700+level*10000+index*1000+variant*37)
    if family=='integer_bin_packing':
        n=(8,12,16)[level];cap=10;weights=[rng.randint(2,9) for _ in range(n)]
        answer=bin_packing(weights,cap);wrong=answer+(-1 if answer>1 else 1)
        stem=f'{n} indivisible objects have weights '+', '.join(map(str,weights))+f'. Each bin holds total weight at most {cap}. No object may be split. What is the minimum number of bins?'
        proof=dict(weights=weights,capacity=cap,exact_subset_dp=answer,exact_fixed_bin_feasibility_at_optimum=True,exact_feasibility_one_less=False)
    elif family=='optimal_binary_prefix_code':
        n=(5,9,13)[level];weights=[rng.randint(2,(15,60,120)[level]) for _ in range(n)]
        answer,merges=prefix_optimum(weights);wrong=answer+2*(level+1)
        stem=f'{n} symbols occur respectively '+', '.join(map(str,weights))+f' times (total {sum(weights)} occurrences). Assign distinct binary codewords with no codeword a prefix of another and no alphabetical-order constraint. What is the minimum total number of bits needed to encode all occurrences?'
        proof=dict(weights=weights,huffman_merge_sums=merges,exhaustive_binary_partition_optimum=answer)
    elif family=='dense_determinant':
        n=(3,4,5)[level];matrix=[[rng.randint(-7,8) for _ in range(n)] for _ in range(n)]
        answer=old.determinant(matrix);check=determinant_elimination(matrix);assert answer==check
        wrong=answer+(level+1)*17
        stem=f'What is the determinant of this {n} by {n} matrix? Rows: '+', '.join(str(tuple(row)) for row in matrix)+'.'
        proof=dict(matrix=matrix,exact_permutation_expansion=answer,rational_elimination=str(check))
    elif family=='bipartite_matching_deficiency':
        n=(6,9,12)[level];k=n//2;deficit=1+(variant%2 if level else 0);labels=list(range(1,n+1));rng.shuffle(labels);small=set(labels[:k]);edges=[];witness={}
        for i in range(k+deficit):
            allowed={labels[i%k],labels[(i+1)%k]};allowed|={j for j in small if rng.random()<.35};edges.append(allowed)
            if i<k:witness[i]=labels[i]
        for i in range(k+deficit,n):
            j=labels[k+i-k-deficit];allowed={j}|{x for x in labels[k:] if rng.random()<.6};edges.append(allowed);witness[i]=j
        @lru_cache(None)
        def match(i,used):
            if i==n:return 0
            return max([match(i+1,used)]+[1+match(i+1,used|(1<<j)) for j in edges[i] if not used>>j&1])
        answer=match(0,0);assert answer==n-deficit==len(witness)
        wrong=n
        names=[chr(65+i) for i in range(n)]
        stem=f'{n} workers '+', '.join(names)+' can each take at most one task. Each task can have at most one worker; workers may remain unassigned. Eligible task sets: '+'; '.join(names[i]+':'+str(sorted(e)) for i,e in enumerate(edges))+'. What is the maximum number of tasks that can be assigned?'
        proof=dict(exact_matching_dp=answer,bottleneck_workers=names[:k+deficit],their_task_union=sorted(small),upper_bound=n-deficit,witness={names[i]:v for i,v in witness.items()})
    elif family=='overlapping_pattern_waiting_time':
        patterns=[['HHH','HTH','THT','TTT'],['HHTHH','THTHT','HTHHT','TTHTT'],['HTHTHTH','THHTHHT','HHTHHHH','THTTHTT']]
        pattern=patterns[level][variant];p=[F(1,2),F(2,5),F(3,7)][level];n=len(pattern)
        a=[[F(int(i==j)) for j in range(n)] for i in range(n)];transitions=[]
        for i in range(n):
            row=[]
            for char,prob in [('H',p),('T',1-p)]:
                s=pattern[:i]+char;k=max(k for k in range(n+1) if s.endswith(pattern[:k]));row.append(k)
                if k<n:a[i][k]-=prob
            transitions.append(row)
        answer=old.solve_linear(a,[1]*n)[0];overlaps=[];check=F(0)
        for k in range(1,n+1):
            if pattern[:k]==pattern[-k:]:
                probability=p**pattern[:k].count('H')*(1-p)**pattern[:k].count('T');check+=1/probability;overlaps.append(k)
        assert answer==check
        wrong=1/(p**pattern.count('H')*(1-p)**pattern.count('T'));assert wrong!=answer
        stem=f'Independent flips have P(H)={p} and P(T)={1-p}. Starting with no flips, wait for the first consecutive occurrence of {pattern}. Candidate occurrences may overlap. What is the expected total number of flips, including the final {n}?'
        proof=dict(pattern=pattern,probability_H=str(p),prefix_automaton=transitions,exact_linear_solution=str(answer),prefix_suffix_overlap_lengths=overlaps,overlap_expectation=str(check))
    else:
        n=(7,11,15)[level];jobs=[]
        for _ in range(n):
            start=rng.randint(0,2*n);jobs.append((start,start+rng.randint(1,6),rng.randint(2,30)))
        feasible=[]
        for mask in range(1<<n):
            chosen=sorted(jobs[i] for i in range(n) if mask>>i&1)
            if all(x[1]<=y[0] for x,y in zip(chosen,chosen[1:])):feasible.append((sum(x[2] for x in chosen),chosen))
        answer,witness=max(feasible);ordered=sorted(jobs,key=lambda x:x[1]);dp=[0]
        for i,(start,end,profit) in enumerate(ordered):
            j=sum(x[1]<=start for x in ordered[:i]);dp.append(max(dp[-1],profit+dp[j]))
        assert answer==dp[-1];wrong=answer+level+1
        stem='One machine can run any subset of these jobs, given as (start,end,profit): '+str(jobs)+'. A job occupies [start,end), so ending exactly when another starts is allowed. Jobs cannot move, split or repeat. What is the maximum total profit?'
        proof=dict(jobs=jobs,exhaustive_subset_optimum=answer,weighted_interval_dp=dp,witness=witness)
    letter='A' if (level+index+variant)%2==0 else 'B'
    return dict(item_id=f'L{level}_F{index+1}_V{variant}',level=level,family=family,variant=variant,split='practice' if variant<2 else 'reserved',stem=stem,options={'A':str(answer if letter=='A' else wrong),'B':str(wrong if letter=='A' else answer)},correct_letter=letter,answer=str(answer),author_certificate=proof)

def build():return [make(level,family,variant) for level in range(3) for family in FAMILIES for variant in range(4)]

if __name__=='__main__':
    rows=build();assert len(rows)==len({x['stem'] for x in rows})==72
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'author_pool.json').open('x') as f:json.dump(rows,f,indent=2);f.write('\n')
    print(json.dumps(dict(total_items=72,practice=36,reserved_candidates=36,levels=3,families=6)))

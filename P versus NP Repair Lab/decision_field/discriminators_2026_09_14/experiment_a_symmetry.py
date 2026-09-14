#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time
from itertools import combinations_with_replacement, permutations

def var_tt(n,j):
    out=0
    for x in range(1<<n):
        if (x>>j)&1: out |= 1<<x
    return out

def transform_tt(tt,n,p):
    out=0
    for x in range(1<<n):
        y=0
        for j in range(n):
            if (x>>p[j])&1: y |= 1<<j
        if (tt>>y)&1: out |= 1<<x
    return out

def baseline(n,g):
    mask=(1<<(1<<n))-1; init=tuple(sorted(var_tt(n,j) for j in range(n)))
    states={init}; funcs=set(init); candidates=0; generated=0; start=time.perf_counter()
    for _ in range(1,g+1):
        nxt=set()
        for st in states:
            for a,b in combinations_with_replacement(st,2):
                candidates+=1; z=mask^(a&b); funcs.add(z)
                if z not in st: nxt.add(tuple(sorted(st+(z,))))
        generated+=len(nxt); states=nxt
    return {'mode':'identity_control','function_count':len(funcs),'candidate_nands':candidates,'generated_states_excluding_initial':generated,'seconds':time.perf_counter()-start}

def quotient(n,g):
    mask=(1<<(1<<n))-1; group=list(permutations(range(n))); cache={}; lookups=0
    def tx(v,p):
        nonlocal lookups
        lookups+=1; k=(v,p)
        if k not in cache: cache[k]=transform_tt(v,n,p)
        return cache[k]
    def canon(st): return min(tuple(sorted(tx(v,p) for v in st)) for p in group)
    def orbit(v): return {tx(v,p) for p in group}
    init=tuple(sorted(var_tt(n,j) for j in range(n))); states={canon(init)}; funcs=set(); candidates=0; generated=0
    for v in init: funcs|=orbit(v)
    start=time.perf_counter()
    for _ in range(1,g+1):
        nxt=set()
        for st in states:
            for a,b in combinations_with_replacement(st,2):
                candidates+=1; z=mask^(a&b); funcs|=orbit(z)
                if z not in st: nxt.add(canon(tuple(sorted(st+(z,)))))
        generated+=len(nxt); states=nxt
    return {'mode':'certified_Sn_quotient','group_size':len(group),'certificate':'bounded NAND basis and unlabeled gate budget are invariant under every input-variable permutation; the all-ones paired query is also S_n-invariant','function_count':len(funcs),'candidate_nands':candidates,'generated_states_excluding_initial':generated,'transform_lookups':lookups,'transform_cache_entries':len(cache),'seconds':time.perf_counter()-start}

def run(n,g):
    b=baseline(n,g); q=quotient(n,g); assert b['function_count']==q['function_count']
    return {'schema':'pnp-discriminator-a/v1','input':{'n':n,'g':g},'identity_control':b,'certified_symmetry':q,'exact_class_preserved':True,'ratios':{'candidate_nand_reduction':b['candidate_nands']/q['candidate_nands'],'generated_state_reduction':b['generated_states_excluding_initial']/q['generated_states_excluding_initial'],'wall_time_ratio_quotient_over_control':q['seconds']/b['seconds']},'claim_ceiling':'Finite bounded construction result only; no P-vs-NP conclusion and no asymptotic speedup claim.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--n',type=int,required=True); ap.add_argument('--g',type=int,required=True); ap.add_argument('--out'); a=ap.parse_args(); r=run(a.n,a.g); s=json.dumps(r,indent=2,sort_keys=True)+'\n'
    open(a.out,'w').write(s) if a.out else print(s,end='')
if __name__=='__main__': main()

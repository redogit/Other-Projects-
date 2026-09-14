from __future__ import annotations
import random
from train import CoverTask,oracle_min_cover,solve_min_cover
from native import run_native
from hard_search import solve_mrv


def make_benchmark_task(size:int,seed:int=20260914):
    if not 8 <= size <= 64: raise ValueError('benchmark size 8..64')
    provide=[]; require=[]; pool=(0,1,2,4,5)
    for i in range(size-2):
        b1=pool[(i+seed)%len(pool)]; b2=pool[(i*3+seed+1)%len(pool)]
        provide.append((1<<b1)|(1<<b2))
        require.append((1<<pool[(i+2)%len(pool)]) if i%4==0 else 0)
    provide += [0b0001111,0b1110000]; require += [0,0]
    return CoverTask(f'bench-{size}-{seed}',0b1111111,tuple(provide),tuple(require))


def make_dependency_trap_task(size:int,seed:int=20260914):
    if not 12 <= size <= 64: raise ValueError('dependency-trap size 12..64')
    rng=random.Random(seed ^ (size<<8)); capabilities=10
    provide=[]; require=[]
    for i in range(size):
        bits=rng.sample(range(capabilities),3)
        pm=sum(1<<b for b in bits); provide.append(pm)
        missing=[b for b in range(capabilities) if not (pm>>b)&1]
        require.append((1<<rng.choice(missing)) if i%3==0 else 0)
    slots=[1,size//3,(2*size)//3,size-2]
    groups=((0,1,2),(3,4,5),(6,7,8),(0,8,9))
    for slot,group in zip(slots,groups):
        provide[slot]=sum(1<<b for b in group); require[slot]=0
    return CoverTask(f'trap-{size}-{seed}',(1<<capabilities)-1,tuple(provide),tuple(require))


def run_benchmarks(model,compiled_native,sizes=(12,16,20,32,48,64)):
    rows=[]
    for size in sizes:
        task=make_benchmark_task(size)
        ranked=solve_min_cover(task,model)
        native=run_native(task,compiled_native)
        row={'family':'coverage','size':size,'ranked_count':ranked.count,'ranked_mask':ranked.mask,'ranked_expansions':ranked.expansions,
             'native_count':native['count'],'native_mask':native['mask'],'native_expansions':native['expansions']}
        if (native['count'],native['mask']) != (ranked.count,ranked.mask): raise AssertionError('native/python mismatch')
        if size<=20:
            oracle_count,oracle_mask=oracle_min_cover(task); lexical=solve_min_cover(task,None)
            if (oracle_count,oracle_mask)!=(ranked.count,ranked.mask): raise AssertionError('oracle/indexed mismatch')
            row.update({'oracle_count':oracle_count,'oracle_mask':oracle_mask,'lexical_expansions':lexical.expansions})
        rows.append(row)
    return tuple(rows)


def run_dependency_traps(model,native_mrv=None,sizes=(12,16,20,32,48,64)):
    rows=[]
    for size in sizes:
        task=make_dependency_trap_task(size)
        lexical=solve_mrv(task,None); ranked=solve_mrv(task,model)
        if (lexical.count,lexical.mask)!=(ranked.count,ranked.mask): raise AssertionError('trained ordering changed exact MRV answer')
        row={'family':'dependency_trap','size':size,'count':ranked.count,'mask':ranked.mask,
             'mrv_lexical_expansions':lexical.expansions,'mrv_ranked_expansions':ranked.expansions,
             'mrv_lexical_prunes':lexical.lower_bound_prunes,'mrv_ranked_prunes':ranked.lower_bound_prunes}
        if size<=20:
            oracle=oracle_min_cover(task)
            if oracle!=(ranked.count,ranked.mask): raise AssertionError('dependency-trap oracle mismatch')
            row.update({'oracle_count':oracle[0],'oracle_mask':oracle[1]})
        if native_mrv is not None:
            native=native_mrv(task)
            if (native['count'],native['mask'])!=(ranked.count,ranked.mask): raise AssertionError('native MRV mismatch')
            row.update({'native_mrv_expansions':native['expansions'],'native_mrv_prunes':native['prunes']})
        rows.append(row)
    return tuple(rows)

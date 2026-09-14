from __future__ import annotations
from train import CoverTask,oracle_min_cover,solve_min_cover
from native import run_native

def make_benchmark_task(size:int,seed:int=20260914):
    if not 8 <= size <= 64: raise ValueError('benchmark size 8..64')
    provide=[]; require=[]; pool=(0,1,2,4,5)
    for i in range(size-2):
        b1=pool[(i+seed)%len(pool)]; b2=pool[(i*3+seed+1)%len(pool)]
        provide.append((1<<b1)|(1<<b2))
        require.append((1<<pool[(i+2)%len(pool)]) if i%4==0 else 0)
    provide += [0b0001111,0b1110000]; require += [0,0]
    return CoverTask(f'bench-{size}-{seed}',0b1111111,tuple(provide),tuple(require))

def run_benchmarks(model,compiled_native,sizes=(12,16,20,32,48,64)):
    rows=[]
    for size in sizes:
        task=make_benchmark_task(size)
        ranked=solve_min_cover(task,model)
        native=run_native(task,compiled_native)
        row={'size':size,'ranked_count':ranked.count,'ranked_mask':ranked.mask,'ranked_expansions':ranked.expansions,
             'native_count':native['count'],'native_mask':native['mask'],'native_expansions':native['expansions']}
        if (native['count'],native['mask']) != (ranked.count,ranked.mask): raise AssertionError('native/python mismatch')
        if size<=20:
            oracle_count,oracle_mask=oracle_min_cover(task)
            lexical=solve_min_cover(task,None)
            if (oracle_count,oracle_mask)!=(ranked.count,ranked.mask): raise AssertionError('oracle/indexed mismatch')
            row.update({'oracle_count':oracle_count,'oracle_mask':oracle_mask,'lexical_expansions':lexical.expansions})
        rows.append(row)
    return tuple(rows)

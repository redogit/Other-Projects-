from __future__ import annotations
from dataclasses import dataclass
from train import part_features

@dataclass(frozen=True)
class HardSolveResult:
    count:int
    mask:int
    expansions:int
    lower_bound_prunes:int
    dead_ends:int


def solve_mrv(task, model=None) -> HardSolveResult:
    n=len(task.provide_masks)
    if len(task.require_masks)!=n: raise ValueError('provide/require length mismatch')
    best_count=n+1; best_mask=0; expansions=prunes=dead=0; seen=set()
    def pc(x): return int(x).bit_count()
    def score(slot,missing):
        return model.score(part_features(task,slot,missing)) if model is not None else 0
    def rec(selected,provided,needed,count):
        nonlocal best_count,best_mask,expansions,prunes,dead
        if selected in seen: return
        seen.add(selected); expansions+=1
        missing=needed & ~provided
        if not missing:
            if count<best_count or (count==best_count and selected<best_mask): best_count,best_mask=count,selected
            return
        if count>=best_count: prunes+=1; return
        candidates=[i for i in range(n) if not (selected>>i)&1 and task.provide_masks[i]&missing]
        if not candidates: dead+=1; return
        max_new=max(pc(task.provide_masks[i]&missing) for i in candidates)
        lower=(pc(missing)+max_new-1)//max_new
        if count+lower>best_count: prunes+=1; return
        missing_bits=[b for b in range(max(1,needed.bit_length())) if missing>>b&1]
        provider_sets=[]
        for b in missing_bits:
            ps=[i for i in candidates if task.provide_masks[i]>>b&1]
            if not ps: dead+=1; return
            provider_sets.append((len(ps),b,ps))
        _,_,providers=min(provider_sets,key=lambda x:(x[0],x[1]))
        providers=sorted(providers,key=lambda i:(-score(i,missing),i))
        for i in providers:
            bit=1<<i
            rec(selected|bit,provided|task.provide_masks[i],needed|task.require_masks[i],count+1)
    rec(0,0,task.required_mask,0)
    return HardSolveResult(best_count if best_count<=n else -1,best_mask,expansions,prunes,dead)

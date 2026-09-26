from __future__ import annotations

"""FIG-5 v0.20 exact Davis-Putnam active-solver mirror.

This is a NEW, explicitly versioned reconstruction from recovered v0.7/v0.8
semantics. It is not claimed byte-identical to the unavailable v0.10 runtime.

Frozen active semantics:
- canonical integer-literal CNF;
- deterministic fixed-point unit propagation, subsumption, and
  self-subsuming resolution (SSR);
- exact Davis-Putnam existential elimination;
- at each active step, preview every active variable exactly one elimination
  ahead and choose the lexicographically smallest normalized post-elimination
  surface (clause_count, literal_count, generated_non_tautological, variable);
- planning work counts all positive/negative parent pairs across previews;
- executed generated-resolvent count counts every non-tautological resolvent
  candidate before duplicate/subsumption normalization;
- active cap is 80 executed generated resolvents; crossing the cap returns
  UNKNOWN without reordering or fallback;
- P_DP is sum d_plus*d_minus immediately before each executed elimination.

GENERATE != VERIFY != ADMIT.
MIRROR_V020 != V0_10_ORIGINAL_BYTES.
"""

from dataclasses import dataclass, asdict
from itertools import combinations, product
import hashlib, json, random
from typing import Iterable, Sequence

ACTIVE_CAP = 80
VALIDATION_DP_CAP = 160
VERSION = "FIG5-DP-MIRROR/v0.20"

Clause = frozenset[int]
Formula = tuple[Clause, ...]


def canonical_clause(lits: Iterable[int]) -> Clause | None:
    s = frozenset(int(x) for x in lits)
    if 0 in s:
        raise ValueError("literal 0")
    if any(-x in s for x in s):
        return None
    return s


def formula_key(f: Iterable[Clause]) -> Formula:
    uniq = set(f)
    return tuple(sorted(uniq, key=lambda c: (len(c), tuple(sorted(c, key=lambda z:(abs(z), z<0))))))


def literal_count(f: Sequence[Clause]) -> int:
    return sum(len(c) for c in f)


def vars_of(f: Sequence[Clause]) -> tuple[int, ...]:
    return tuple(sorted({abs(l) for c in f for l in c}))


def has_empty(f: Sequence[Clause]) -> bool:
    return any(len(c)==0 for c in f)


def subsume(f: Sequence[Clause]) -> Formula:
    ordered = sorted(set(f), key=lambda c:(len(c), tuple(sorted(c))))
    kept=[]
    for c in ordered:
        if any(k <= c for k in kept):
            continue
        kept.append(c)
    return formula_key(kept)


def apply_literal(f: Sequence[Clause], lit: int) -> Formula:
    out=[]
    neg=-lit
    for c in f:
        if lit in c:
            continue
        if neg in c:
            out.append(frozenset(x for x in c if x != neg))
        else:
            out.append(c)
    return formula_key(out)


def unit_propagate(f: Sequence[Clause]) -> tuple[Formula, tuple[int,...]]:
    """Order-independent unit-propagation closure."""
    cur=formula_key(f)
    assignments=[]
    while True:
        if has_empty(cur):
            return cur, tuple(assignments)
        units=set(next(iter(c)) for c in cur if len(c)==1)
        if not units:
            return cur, tuple(assignments)
        if any(-u in units for u in units):
            return formula_key([frozenset()]), tuple(assignments)
        # Apply the whole forced unit set simultaneously.
        assignments.extend(sorted(units, key=lambda z:(abs(z),z<0)))
        out=[]
        for c in cur:
            if any(u in c for u in units):
                continue
            nc=frozenset(l for l in c if -l not in units)
            out.append(nc)
        cur=formula_key(out)


def ssr_closure_step(f: Sequence[Clause]) -> tuple[Formula, int]:
    """Label/order-independent exhaustive one-round SSR strengthening."""
    base=formula_key(f)
    additions=set()
    cs=list(base)
    for a in cs:
        for b in cs:
            if a is b:
                continue
            for x in a:
                if -x not in b:
                    continue
                A=a-{x}; B=b-{-x}
                if A <= B:
                    additions.add(frozenset(B))
    if not additions:
        return base, 0
    nxt=subsume(formula_key(list(base)+list(additions)))
    return nxt, len(additions)


def preprocess(f: Sequence[Clause]) -> tuple[Formula, dict]:
    cur=formula_key(f)
    total_units=[]
    ssr_steps=0
    while True:
        before=cur
        cur, units=unit_propagate(cur)
        total_units.extend(units)
        if has_empty(cur) or not cur:
            return formula_key(cur), {"unit_assignments":total_units,"ssr_steps":ssr_steps}
        cur=subsume(cur)
        cur, added=ssr_closure_step(cur)
        ssr_steps += added
        cur=subsume(cur)
        if cur == before:
            return cur, {"unit_assignments":total_units,"ssr_steps":ssr_steps}


def eliminate_raw(f: Sequence[Clause], var: int) -> tuple[Formula, int, int, int]:
    pos=[c for c in f if var in c]
    neg=[c for c in f if -var in c]
    rest=[c for c in f if var not in c and -var not in c]
    pair_count=len(pos)*len(neg)
    non_taut=0
    resolvents=[]
    for p in pos:
        p0=p-{var}
        for n in neg:
            n0=n-{-var}
            r=canonical_clause(p0|n0)
            if r is None:
                continue
            non_taut += 1
            resolvents.append(r)
    return formula_key(rest+resolvents), pair_count, non_taut, len(resolvents)


def preview(f: Sequence[Clause], var:int) -> dict:
    raw,pairs,generated,_=eliminate_raw(f,var)
    norm,pre=preprocess(raw)
    return {
        "var":var,
        "pair_count":pairs,
        "generated_non_tautological":generated,
        "formula":norm,
        "score":(len(norm), literal_count(norm), generated, var),
        "preprocess":pre,
    }

@dataclass
class ActiveResult:
    status:str
    generated_resolvents:int
    planning_pairs_considered:int
    planning_non_tautological_resolvents:int
    preview_count:int
    dp_pair_pressure_sum:int
    elimination_sequence:list[int]
    peak_live_clauses:int
    initial_clause_count:int
    final_clause_count:int
    unit_assignments:int
    ssr_steps:int
    cap:int|None
    cap_crossing_at:int|None
    trace:list[dict]


def active_dp(formula: Sequence[Sequence[int]] | Sequence[Clause], cap:int|None=ACTIVE_CAP) -> ActiveResult:
    f=[]
    for c in formula:
        cc=canonical_clause(c)
        if cc is not None:
            f.append(cc)
    cur, pre0=preprocess(formula_key(f))
    init=len(cur)
    gen=0; plan_pairs=0; plan_nt=0; previews=0; p_dp=0
    seq=[]; peak=len(cur); trace=[]
    unit_count=len(pre0["unit_assignments"]); ssr_steps=pre0["ssr_steps"]
    while True:
        if has_empty(cur):
            return ActiveResult("UNSAT",gen,plan_pairs,plan_nt,previews,p_dp,seq,peak,init,len(cur),unit_count,ssr_steps,cap,None,trace)
        if not cur:
            return ActiveResult("SAT",gen,plan_pairs,plan_nt,previews,p_dp,seq,peak,init,0,unit_count,ssr_steps,cap,None,trace)
        vs=vars_of(cur)
        if not vs:
            return ActiveResult("SAT",gen,plan_pairs,plan_nt,previews,p_dp,seq,peak,init,len(cur),unit_count,ssr_steps,cap,None,trace)
        ps=[]
        for v in vs:
            pv=preview(cur,v)
            ps.append(pv); previews+=1
            plan_pairs += pv["pair_count"]
            plan_nt += pv["generated_non_tautological"]
        chosen=min(ps,key=lambda x:x["score"])
        step_gen=chosen["generated_non_tautological"]
        if cap is not None and gen + step_gen > cap:
            return ActiveResult("UNKNOWN",gen,plan_pairs,plan_nt,previews,p_dp,seq,peak,init,len(cur),unit_count,ssr_steps,cap,gen+step_gen,trace)
        before=len(cur)
        p_dp += chosen["pair_count"]
        gen += step_gen
        seq.append(chosen["var"])
        cur=chosen["formula"]
        unit_count += len(chosen["preprocess"]["unit_assignments"])
        ssr_steps += chosen["preprocess"]["ssr_steps"]
        peak=max(peak,len(cur))
        trace.append({
            "step":len(seq)-1,"var":chosen["var"],"before_clauses":before,
            "pair_pressure":chosen["pair_count"],"generated_non_tautological":step_gen,
            "after_clauses":len(cur),"after_literals":literal_count(cur),
        })


def brute_force_sat(formula: Sequence[Sequence[int]]) -> tuple[str, list[int]|None, int]:
    clauses=[tuple(int(x) for x in c) for c in formula]
    vs=sorted({abs(l) for c in clauses for l in c})
    tested=0
    for bits in product((False,True), repeat=len(vs)):
        tested+=1
        a=dict(zip(vs,bits))
        if all(any(a[abs(l)] == (l>0) for l in c) for c in clauses):
            return "SAT", [v if a[v] else -v for v in vs], tested
    return "UNSAT", None, tested


def independent_dp160(formula: Sequence[Sequence[int]], cap:int=VALIDATION_DP_CAP) -> dict:
    # Separate simple implementation: ascending variable order, only dedup/subsumption;
    # no unit propagation, SSR, or active preview machinery.
    fs=[]
    for c in formula:
        cc=canonical_clause(c)
        if cc is not None: fs.append(cc)
    cur=subsume(formula_key(fs))
    generated=0; seq=[]
    while True:
        if has_empty(cur): return {"status":"UNSAT","generated_resolvents":generated,"sequence":seq,"cap":cap}
        if not cur: return {"status":"SAT","generated_resolvents":generated,"sequence":seq,"cap":cap}
        vs=vars_of(cur)
        if not vs: return {"status":"SAT","generated_resolvents":generated,"sequence":seq,"cap":cap}
        v=vs[0]
        pos=[c for c in cur if v in c]; neg=[c for c in cur if -v in c]
        rest=[c for c in cur if v not in c and -v not in c]
        rs=[]; step=0
        for p in pos:
            for n in neg:
                r=canonical_clause((p-{v}) | (n-{-v}))
                if r is not None:
                    step+=1; rs.append(r)
                    if generated+step > cap:
                        return {"status":"UNKNOWN","generated_resolvents":generated,"cap_crossing_at":generated+step,"sequence":seq,"cap":cap}
        generated += step; seq.append(v)
        cur=subsume(formula_key(rest+rs))


def formula_digest(formula: Sequence[Sequence[int]]) -> str:
    payload=json.dumps([list(c) for c in formula],separators=(",",":"),ensure_ascii=True)
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def random_cnf(rng: random.Random, n:int, m:int) -> list[list[int]]:
    out=[]
    for _ in range(m):
        k=rng.randint(1,min(3,n))
        vs=rng.sample(range(1,n+1),k)
        out.append([v if rng.getrandbits(1) else -v for v in vs])
    return out


def self_test(seed:int=20260921, cases:int=2000) -> dict:
    rng=random.Random(seed)
    mism_active=[]; mism_ind=[]
    for i in range(cases):
        n=rng.randint(1,8); m=rng.randint(0,24)
        f=random_cnf(rng,n,m)
        truth=brute_force_sat(f)[0]
        a=active_dp(f,cap=None).status
        v=independent_dp160(f,cap=10**9)["status"]
        if a!=truth: mism_active.append({"i":i,"truth":truth,"active":a,"f":f})
        if v!=truth: mism_ind.append({"i":i,"truth":truth,"ind":v,"f":f})
        if mism_active or mism_ind: break
    # Exact one-variable projection check on fresh random formulas.
    projection_checks=0
    for i in range(300):
        n=rng.randint(2,7); f=random_cnf(rng,n,rng.randint(1,18))
        cs=[canonical_clause(c) for c in f]; cs=[c for c in cs if c is not None]
        v=rng.randint(1,n)
        raw,_,_,_=eliminate_raw(formula_key(cs),v)
        projected=raw  # raw DP elimination is pointwise existential projection; preprocessing is SAT-preserving only
        remaining=[x for x in range(1,n+1) if x!=v]
        for bits in product((False,True),repeat=len(remaining)):
            a=dict(zip(remaining,bits))
            def eval_clause(c, extra=None):
                aa=dict(a)
                if extra is not None: aa[v]=extra
                return any(aa[abs(l)]==(l>0) for l in c)
            orig=any(all(eval_clause(c,extra=x) for c in cs) for x in (False,True))
            proj=all(any(a[abs(l)]==(l>0) for l in c) for c in projected)
            projection_checks+=1
            if orig!=proj:
                raise AssertionError((f,v,a,projected,orig,proj))
    assert not mism_active and not mism_ind
    return {"status":"PASS","random_cnf_cases":cases,"projection_assignment_checks":projection_checks,
            "active_unlimited_vs_bruteforce_mismatches":len(mism_active),
            "independent_dp_unlimited_vs_bruteforce_mismatches":len(mism_ind),
            "claim_ceiling":["MIRROR_V020 != V0_10_ORIGINAL_BYTES","SELF_TEST != FIG5_EXECUTION","GENERATE != VERIFY != ADMIT","P ?= NP = OPEN"]}

if __name__ == "__main__":
    print(json.dumps(self_test(),indent=2,sort_keys=True))

# ---- Carrier counterprobe helpers (appended after main guard; imported use only) ----
def execute_fixed_sequence(formula: Sequence[Sequence[int]], sequence: Sequence[int], cap:int|None=None) -> dict:
    fs=[]
    for c in formula:
        cc=canonical_clause(c)
        if cc is not None: fs.append(cc)
    cur, pre0=preprocess(formula_key(fs))
    gen=0; p_dp=0; peak=len(cur); used=[]
    unit_count=len(pre0['unit_assignments']); ssr_steps=pre0['ssr_steps']
    for v in sequence:
        if has_empty(cur) or not cur: break
        if v not in vars_of(cur):
            continue
        raw,pairs,step_gen,_=eliminate_raw(cur,v)
        if cap is not None and gen+step_gen>cap:
            return {'status':'UNKNOWN','generated_resolvents':gen,'dp_pair_pressure_sum':p_dp,'sequence':used,
                    'peak_live_clauses':peak,'unit_assignments':unit_count,'ssr_steps':ssr_steps,'cap_crossing_at':gen+step_gen}
        gen+=step_gen; p_dp+=pairs; used.append(v)
        cur,pre=preprocess(raw)
        unit_count+=len(pre['unit_assignments']); ssr_steps+=pre['ssr_steps']; peak=max(peak,len(cur))
    if has_empty(cur): status='UNSAT'
    elif not cur: status='SAT'
    elif vars_of(cur):
        # If the supplied sequence ended before all variables, finish is undefined for the counterprobe.
        status='INCOMPLETE'
    else: status='SAT'
    return {'status':status,'generated_resolvents':gen,'dp_pair_pressure_sum':p_dp,'sequence':used,
            'peak_live_clauses':peak,'unit_assignments':unit_count,'ssr_steps':ssr_steps}

def permute_formula(formula: Sequence[Sequence[int]], mapping: dict[int,int]) -> list[list[int]]:
    out=[]
    for c in reversed(list(formula)):  # deterministic clause-order reversal too
        out.append([mapping[abs(l)] if l>0 else -mapping[abs(l)] for l in reversed(list(c))])
    return out

def carrier_self_test(seed:int=20260922, cases:int=1000) -> dict:
    rng=random.Random(seed); mism=[]
    for i in range(cases):
        n=rng.randint(2,8); f=random_cnf(rng,n,rng.randint(0,24))
        base=active_dp(f,cap=None)
        vs=sorted({abs(l) for c in f for l in c})
        shuffled=vs[:]; rng.shuffle(shuffled); mapping=dict(zip(vs,shuffled))
        pf=permute_formula(f,mapping)
        pseq=[mapping[v] for v in base.elimination_sequence]
        a=execute_fixed_sequence(f,base.elimination_sequence,cap=None)
        b=execute_fixed_sequence(pf,pseq,cap=None)
        keys=('status','generated_resolvents','dp_pair_pressure_sum','peak_live_clauses')
        if any(a[k]!=b[k] for k in keys):
            mism.append({'i':i,'keys':{k:(a[k],b[k]) for k in keys},'f':f,'mapping':mapping,'seq':base.elimination_sequence})
            break
    return {'status':'PASS' if not mism else 'FAIL','cases':cases,'mismatches':mism[:1]}

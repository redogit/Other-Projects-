#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, json, pathlib, sys, time

def load(root):
    sys.path.insert(0,str(root/'checks'))
    from feedback import solve
    from verify_feedback import check
    from ceiling_probe import condition
    from families import compile_cnf
    return solve,check,condition,compile_cnf

def case_data(root,name,compile_cnf):
    if name in ('compiler_0','compiler_1'):
        x=json.loads((root/'inputs'/f'{name}.json').read_text()); return x['n'],x['clauses'],x['expected']
    i=int(name.split('_')[1]); src=json.loads((root/'evidence/run01/adversarial/source_controls.json').read_text())[i]
    n,clauses=compile_cnf(8,src['source']); return n,clauses,'SAT' if src['models'] else 'UNSAT'

def unknown_component_size(r):
    return max([len(p['variables']) for p in r.get('parts',[]) if p.get('status')=='UNKNOWN'] or [0])

def search(root,name,mode,wall_cap):
    solve,check,condition,compile_cnf=load(root); n,clauses,known=case_data(root,name,compile_cnf)
    counts=collections.Counter(v for c in clauses for v in c); metrics=collections.Counter(); nodes=[]; start=time.perf_counter(); timed_out=False
    def expired(): return time.perf_counter()-start>=wall_cap
    def rec(nn,cc,depth):
        nonlocal timed_out
        idx=len(nodes); node={'id':idx,'depth':depth}; nodes.append(node)
        if expired(): timed_out=True; return 'TIMEOUT',None
        if metrics['execution_states']>=63 or depth>8: return 'UNKNOWN',None
        metrics['execution_states']+=1; r=solve(nn,cc,8); assert check(nn,cc,r,8)
        metrics['execution_row_operations']+=r.get('row_operations',0); metrics['execution_local_assignments']+=r.get('tested',0)
        if r['status']!='UNKNOWN': return r['status'],r.get('model')
        if depth==8: return 'UNKNOWN',None
        candidates=sorted({j for j,l in enumerate(r['affine']) if j<n and any(l)},key=lambda j:(-counts[j],j))
        if mode=='occurrence_all_original': var=candidates[0]
        else:
            scored=[]
            for var0 in candidates[:4]:
                child=[]
                for value in (0,1):
                    if expired(): timed_out=True; return 'TIMEOUT',None
                    n2,c2=condition(nn,cc,var0,value); pr=solve(n2,c2,8); assert check(n2,c2,pr,8)
                    metrics['planning_probes']+=1; metrics['planning_row_operations']+=pr.get('row_operations',0); metrics['planning_local_assignments']+=pr.get('tested',0); child.append(pr)
                key=(sum(q['status']=='UNKNOWN' for q in child),max(unknown_component_size(q) for q in child),max(q['d'] for q in child),-counts[var0],var0); scored.append((key,var0))
            var=min(scored)[1]
        statuses=[]
        for value in (0,1):
            n2,c2=condition(nn,cc,var,value); status,model=rec(n2,c2,depth+1); statuses.append(status)
            if status=='SAT': return 'SAT',model
            if status=='TIMEOUT': return 'TIMEOUT',None
        return ('UNSAT' if statuses==['UNSAT','UNSAT'] else 'UNKNOWN'),None
    status,_=rec(n,clauses,0)
    r={'schema':'pnp-discriminator-b-result/v1','case':name,'known_status':known,'mode':mode,'status':status,'timed_out':timed_out,'wall_cap_seconds':wall_cap,'wall_seconds':time.perf_counter()-start,'maximum_depth':max((x['depth'] for x in nodes),default=0),'tree_records':len(nodes),**{k:int(v) for k,v in metrics.items()},'claim_ceiling':'Finite bounded run; timeout is resource evidence only, never a SAT/UNSAT verdict.'}
    if status not in ('UNKNOWN','TIMEOUT'): assert status==known
    return r

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--case',required=True); ap.add_argument('--mode',choices=['occurrence_all_original','consequence_top4_v1'],required=True); ap.add_argument('--wall-cap',type=float,default=60); ap.add_argument('--out',required=True); a=ap.parse_args(); r=search(pathlib.Path(a.root).resolve(),a.case,a.mode,a.wall_cap); pathlib.Path(a.out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,sort_keys=True))
if __name__=='__main__': main()

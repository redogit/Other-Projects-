import collections,json,time,sys
from pathlib import Path
sys.path.insert(0,'checks')
from campaign import ROOT,write
from feedback import solve,guards,affine_consequences,parameterize,compose,components
from verify_feedback import check
from ceiling_probe import condition
from families import compile_cnf
from domain_hierarchy import compress

def predict(nn,cc):
    ini=compress(nn,cc);aff=ini['affine'];d=ini['d'];gs=guards(aff);r=affine_consequences(gs)
    if r['contradiction']:
        return (0,0,0,r['operations']),{'contradiction':True,'d0':d,'linear':0,'d1':0,'sizes':[],'ops':r['operations']}
    lin=r['linear']
    if lin:
        step=parameterize(d,lin);aff=compose(aff,step['substitution']);d1=len(step['free'])
    else:d1=d
    parts,_=components(d1,guards(aff));sizes=sorted((len(p) for p in parts),reverse=True)
    return (max(sizes,default=0),d1,-len(parts),r['operations']),{'contradiction':False,'d0':d,'linear':len(lin),'d1':d1,'sizes':sizes[:8],'ops':r['operations']}

def search(out,n,clauses,k=8,node_cap=63,depth_cap=8):
    root_n=n;counts=collections.Counter(v for c in clauses for v in c);nodes=[];states=0;max_depth=0
    metrics={'planning_candidates':0,'planning_branch_predictions':0,'planning_seconds':0.0,'planning_row_operations':0,'node_solves':0,'node_tested':0,'node_row_operations':0}
    start=time.perf_counter()
    def rec(nn,cc,depth):
        nonlocal states,max_depth
        idx=len(nodes);node={'id':idx,'depth':depth};nodes.append(node);max_depth=max(max_depth,depth)
        if states>=node_cap or depth>depth_cap:node.update(status='UNKNOWN',reason='resource_bound');return idx,'UNKNOWN',None
        states+=1;r=solve(nn,cc,8);assert check(nn,cc,r,8);metrics['node_solves']+=1;metrics['node_tested']+=r['tested'];metrics['node_row_operations']+=r['row_operations']
        p=out/f'node_{idx}.json';write(p,{'n':nn,'clauses':cc,'certificate':r});node.update(certificate_file=p.name,free=r['d'],feedback_status=r['status'])
        if r['status']!='UNKNOWN':node['status']=r['status'];return idx,r['status'],r['model']
        if depth==depth_cap:node.update(status='UNKNOWN',reason='depth_bound');return idx,'UNKNOWN',None
        candidates=[j for j,l in enumerate(r['affine']) if j<root_n and any(mask for mask in l)];assert candidates
        shortlist=sorted(candidates,key=lambda j:(counts[j],-j),reverse=True)[:k];metrics['planning_candidates']+=len(shortlist)
        rows=[];t=time.perf_counter()
        for var in shortlist:
            bs=[]
            for value in (0,1):
                n2,c2=condition(nn,cc,var,value);score,info=predict(n2,c2);bs.append((value,n2,c2,score,info));metrics['planning_branch_predictions']+=1;metrics['planning_row_operations']+=info['ops']
            worst=max(x[3] for x in bs);combined=sum(x[3][0] for x in bs)
            rows.append((worst,combined,-counts[var],var,bs))
        metrics['planning_seconds']+=time.perf_counter()-t;rows.sort(key=lambda x:x[:4]);worst,combined,_,var,bs=rows[0]
        node.update(variable=var,planning_shortlist=shortlist,selected_prediction=list(worst),selected_combined_component=combined,children=[])
        statuses=[]
        for value,n2,c2,_,_ in bs:
            child,status,model=rec(n2,c2,depth+1);node['children'].append({'value':value,'id':child});statuses.append(status)
            if status=='SAT':
                model=[v for v in model if v<nn];assert all(len(set(c)&set(model))==1 for c in cc);node['status']='SAT';return idx,'SAT',model
        status='UNSAT' if statuses==['UNSAT','UNSAT'] else 'UNKNOWN';node['status']=status;return idx,status,None
    _,status,model=rec(n,clauses,0)
    if model is not None:assert all(len(set(c)&set(model))==1 for c in clauses)
    elapsed=time.perf_counter()-start;write(out/'tree.json',{'root_n':n,'root_clauses':clauses,'mode':f'one_round_k{k}','node_cap':node_cap,'depth_cap':depth_cap,'nodes':nodes,'status':status,'model':model})
    return {'mode':f'one_round_k{k}','status':status,'states_evaluated':states,'tree_records':len(nodes),'maximum_depth':max_depth,'seconds_total':elapsed,'node_cap':node_cap,'depth_cap':depth_cap,**metrics}

def main(outdir,k,cases):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True);source=json.loads((ROOT/'evidence/run01/adversarial/source_controls.json').read_text());allcases=[]
    for name in ('compiler_0','compiler_1'):
        x=json.loads((ROOT/'inputs'/(name+'.json')).read_text());allcases.append((name,x['n'],x['clauses'],x['expected']))
    for i in (0,4):
        x=source[i];n,cls=compile_cnf(8,x['source']);allcases.append((f'balanced_{i}',n,cls,'SAT' if x['models'] else 'UNSAT'))
    rows=[];wanted=set(cases)
    for name,n,cls,expected in allcases:
        if name not in wanted:continue
        d=out/name;d.mkdir();r=search(d,n,cls,k);r.update(name=name,n=n,known_status=expected)
        if r['status']!='UNKNOWN':assert r['status']==expected
        rows.append(r);print(json.dumps(r),flush=True)
    write(out/'SUMMARY.json',{'k':k,'rows':rows,'universal_goal_status':'OPEN'})
if __name__=='__main__':main(sys.argv[1],int(sys.argv[2]),sys.argv[3:])

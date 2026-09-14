#!/usr/bin/env python3
from collections import Counter
from itertools import product
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
from lattice import *
ROOT=Path(__file__).resolve().parent

def save(path,obj): path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def req(x,msg):
    if not x: raise AssertionError(msg)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'evidence');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        exe=Path(td)/'lattice'
        subprocess.run(['g++','-O3','-std=c++17',str(ROOT/'native_lattice.cpp'),'-o',str(exe)],check=True,timeout=45)
        first=subprocess.check_output([str(exe)],timeout=45);second=subprocess.check_output([str(exe)],timeout=45)
    req(first==second,'native replay drift');native=json.loads(first)
    req(native['status']=='PASS' and native['partition_cases']==245760,'native census')
    ps=partitions(4);req(len(ps)==15,'Bell(4)')
    dist=Counter();profiles=Counter();systems=0;impossible=0;theorem=0
    maps=[map_tuple(byte) for byte in range(256)]
    for target in range(4):
        legal=[b for b in range(256) if maps[b][target]==target]
        for b0 in legal:
            for b1 in legal:
                systems+=1;mins=minimal_sensors(maps[b0],maps[b1],target)
                if not mins: impossible+=1;continue
                dist[len(mins)]+=1
                for m in mins:
                    if max(m)==0:continue
                    sizes=sorted(Counter(m).values(),reverse=True);profiles['+'.join(map(str,sizes))]+=1
                for p in ps:
                    k=max(p)+1;direct=False
                    for obs_actions in product((0,1),repeat=k):
                        state_policy=tuple(obs_actions[p[s]] for s in range(4))
                        if policy_wins(maps[b0],maps[b1],target,state_policy): direct=True;break
                    req(direct==sufficient(p,mins),'policy-partition theorem mismatch');theorem+=1
    req(systems==16384 and impossible==5688,'system totals')
    req(dict(dist)=={1:7168,2:1392,4:1872,6:264},'minimal antichain distribution')
    req(profiles==Counter({'3+1':5928,'2+2':5928}),'profile occurrence distribution')
    req(theorem==160440,'theorem checks among solvable systems')
    m0,m1=map_tuple(0x04),map_tuple(0x18);target=0;same_shape=[]
    mins=minimal_sensors(m0,m1,target)
    for p in ps:
        sizes=sorted(Counter(p).values(),reverse=True)
        if sizes==[3,1]: same_shape.append({'partition':p,'wins':sufficient(p,mins)})
    req([row['wins'] for row in same_shape]==[False,True,True,False],'same-profile witness')
    result={'status':'PASS_BOUNDED','systems':systems,'partitions':len(ps),'native':native,
            'python_policy_partition_theorem_checks_solvable':theorem,
            'minimal_sensor_antichain_distribution':{str(k):v for k,v in sorted(dist.items())},
            'minimal_two_class_profile_occurrences':dict(profiles),
            'same_profile_witness':{'target':0,'map0':'0x04','map1':'0x18','profile':'3+1','cases':same_shape},
            'structural_statement':'For deterministic memoryless control, a sensor partition is sufficient iff it refines the action partition of at least one winning state policy. With two actions, any fixed winning policy needs at most two observation classes.',
            'scope':'four-state, two-action, singleton absorbing-target deterministic memoryless control; observation sufficiency is task/controller-class relative'}
    save(args.out/'SUMMARY.json',result)
    save(args.out/'VERIFICATION.json',{'status':'PASS','native_replays_identical':True,'source_sha256':{name:sha(ROOT/name) for name in ('lattice.py','audit.py','native_lattice.cpp')},'scope':result['scope']})
    print(json.dumps({'status':'PASS','systems':systems,'theorem':theorem,'dist':dict(dist),'profiles':dict(profiles)},indent=2))
if __name__=='__main__':main()

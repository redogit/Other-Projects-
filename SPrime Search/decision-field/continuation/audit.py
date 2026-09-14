#!/usr/bin/env python3
from itertools import product
import argparse,hashlib,json,subprocess,tempfile
from pathlib import Path
from continuation import quotient,refines,distinguish
ROOT=Path(__file__).resolve().parent

def save(path,obj):path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def req(x,msg):
    if not x:raise AssertionError(msg)
def maps4():return [tuple(x) for x in product(range(4),repeat=4)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'evidence');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        exe=Path(td)/'continuation'
        subprocess.run(['g++','-O3','-std=c++17',str(ROOT/'native_continuation.cpp'),'-o',str(exe)],check=True,timeout=45)
        first=subprocess.check_output([str(exe)],timeout=45);second=subprocess.check_output([str(exe)],timeout=45)
    req(first==second,'native replay');native=json.loads(first);req(native['status']=='PASS','native status')
    maps=maps4();labels=(1,0,0,0);dist={};split=0;pairchecks=0
    for A in maps:
        old=quotient((A,),labels)
        for B in maps:
            new=quotient((A,B),labels);key=f'{len(set(old))}->{len(set(new))}';dist[key]=dist.get(key,0)+1
            req(refines(new,old),'adding action merged old distinction');split+=len(set(new))>len(set(old))
            for left in range(4):
                for right in range(left+1,4):
                    word=distinguish((A,B),labels,left,right)
                    req((word is None)==(new[left]==new[right]),'distinguishing-word mismatch');pairchecks+=1
    req(split==31488 and pairchecks==393216,'census totals')
    req(dist=={'2->2':12544,'2->3':6144,'2->4':9984,'3->3':9216,'3->4':15360,'4->4':12288},'class distribution')
    a0=(0,0,0,0);a1=(0,3,1,0);old=quotient((a0,),labels);new=quotient((a0,a1),labels);word=distinguish((a0,a1),labels,1,2)
    req(old==(0,1,1,1) and new==(0,1,2,3) and word==(1,1),'depth-two witness')
    result={'status':'PASS_BOUNDED','systems':65536,'state_pairs_checked':pairchecks,'action_expansion_strict_splits':split,'class_count_distribution':dist,'native':native,
            'depth2_witness':{'action0':a0,'action1':a1,'old_quotient':old,'new_quotient':new,'states':(1,2),'shortest_distinguishing_word':word,'trace_left':[1,3,0],'trace_right':[2,1,3]},
            'structural_statement':'The coarsest stable labeled transition quotient preserves terminal labels after every finite word over the declared action alphabet. Adding actions can only refine this quotient; if a block splits, the prior compression is not future-safe for the expanded continuation family.',
            'scope':'four-state deterministic labeled transition systems; terminal label is state-0 membership; one-action quotient compared with two-action quotient'}
    save(args.out/'SUMMARY.json',result)
    save(args.out/'VERIFICATION.json',{'status':'PASS','native_replays_identical':True,'source_sha256':{name:sha(ROOT/name) for name in ('continuation.py','audit.py','native_continuation.cpp')},'scope':result['scope']})
    print(json.dumps({'status':'PASS','systems':65536,'splits':split,'pairs':pairchecks,'max_word':native['maximum_shortest_distinguishing_word']},indent=2))
if __name__=='__main__':main()

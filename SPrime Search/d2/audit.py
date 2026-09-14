#!/usr/bin/env python3
from pathlib import Path
import argparse,csv,hashlib,json,subprocess,tempfile
from d2 import decode,eval_row,rank,unrank,to_float,from_float,HEADER,TOTAL
ROOT=Path(__file__).resolve().parent
ACCEPT=(0x52,0x5a,0x72,0x7a)
NAMES={0:'FALSE',1:'NOR',2:'NOT_A_AND_B',3:'NOT_A',4:'A_AND_NOT_B',5:'NOT_B',6:'XOR',7:'NAND',8:'AND',9:'XNOR',10:'B',11:'A_IMPLIES_B',12:'A',13:'B_IMPLIES_A',14:'OR',15:'TRUE'}
def run(exe,out): subprocess.run([str(exe),str(out)],check=True,timeout=45)
def compile(src,out): subprocess.run(['g++','-O3','-std=c++17',str(src),'-o',str(out)],check=True,timeout=45)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'evidence');args=parser.parse_args()
 out=args.output;out.mkdir(parents=True,exist_ok=True)
 if any((out/name).exists() for name in ('RESULT.json','census.tsv','primitive_sweep.tsv')):
  raise FileExistsError('audit outputs already exist; select a fresh --output directory')
 with tempfile.TemporaryDirectory() as td:
  td=Path(td); c=td/'census'; ps=td/'sweep'; compile(ROOT/'census.cpp',c); compile(ROOT/'primitive_sweep.cpp',ps)
  t1=td/'c1.tsv';t2=td/'c2.tsv';p1=td/'p1.tsv';p2=td/'p2.tsv';run(c,t1);run(c,t2);run(ps,p1);run(ps,p2)
  assert t1.read_bytes()==t2.read_bytes() and p1.read_bytes()==p2.read_bytes()
  rows=list(csv.DictReader(t1.open(),delimiter='\t')); assert len(rows)==256
  totals=[];prod=1
  for k in range(1,6):
   prod*=2*(k+2)*(k+2); actual=sum(int(r[f'count_k{k}']) for r in rows);assert actual==prod;totals.append(actual)
  assert sum(totals)+3==205_315_797
  dist={}
  for r in rows:dist[int(r['shortest_gates'])]=dist.get(int(r['shortest_gates']),0)+1
  assert dist=={0:3,1:10,2:23,3:65,4:122,5:33}
  repairs=[]
  for f in ACCEPT:
   r=rows[f]; w=HEADER+bytes.fromhex(r['witness_payload_hex']); table,steps=decode(w); assert table==f
   assert sum(eval_row(w,i)<<i for i in range(8))==f and len(w)<=7
   repairs.append({'table':hex(f),'gates':int(r['shortest_gates']),'word_hex':w.hex(),'word_bytes':len(w),'steps':steps,
      'counts_by_exact_gate_depth':[int(r[f'count_k{k}']) for k in range(1,6)]})
  expected_reach=[139,211,223,139,223,139,256,139,170,256,139,228,139,228,224,139]
  sweep=[]
  for r in csv.DictReader(p1.open(),delimiter='\t'):
   p=int(r['primitive']); got=int(r['reachable_through_5']); assert got==expected_reach[p]
   sweep.append({'primitive':p,'name':NAMES[p],'reachable_through_5':got,'complete':bool(int(r['complete']))})
  complete=[r['name'] for r in sweep if r['complete']]; assert complete==['XOR','XNOR']
  all_shortest=[];leafmap={0xf0:b'x',0xcc:b'y',0xaa:b'z'}
  for table,r in enumerate(rows):
   gates=int(r['shortest_gates']); b=HEADER+leafmap[table] if gates==0 else HEADER+bytes.fromhex(r['witness_payload_hex'])
   assert decode(b)[0]==table and sum(eval_row(b,i)<<i for i in range(8))==table
   assert len(b)<=7 and b.decode('utf-8').encode('utf-8')==b
   assert unrank(rank(b))==b and from_float(to_float(b))==b
   all_shortest.append({'table':table,'gates':gates,'word_hex':b.hex(),'bytes':len(b),'rank':rank(b),'float_hex':to_float(b).hex()})
  assert len({x['rank'] for x in all_shortest})==256 and TOTAL==205_315_797
  for item in repairs:
   f=int(item['table'],16); assert ((f^0xf0)&0x55)==0 and ((f^0x02)&0x82)==0
  result={'status':'PASS','language':'D2v1 = D2 header + terminal or 1..5 one-byte NAND/XOR instructions',
          'programs_individually_evaluated':sum(totals),'legal_words_including_three_terminal_words':sum(totals)+3,
          'exact_programs_by_gate_depth':totals,'behaviors_reachable':256,'shortest_gate_distribution':{str(k):v for k,v in sorted(dist.items())},
          'maximum_gates_needed_for_any_behavior':5,'maximum_word_bytes_needed_for_any_behavior':7,'all_256_fit_under_8_bytes':True,
          'accepted_repairs':repairs,'binary_primitive_sweep':sweep,'all_shortest_words':all_shortest,
          'only_single_added_primitives_completing_by_5_gates':complete,
          'scope':'three-input Boolean truth tables; representation result, not semantic/historical novelty'}
  (out/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
  (out/'census.tsv').write_bytes(t1.read_bytes()); (out/'primitive_sweep.tsv').write_bytes(p1.read_bytes())
  print(json.dumps({'status':'PASS','programs':sum(totals)+3,'complete_primitives':complete,
                    'repairs':[(x['table'],x['gates'],x['word_hex']) for x in repairs]},indent=2))
if __name__=='__main__':main()

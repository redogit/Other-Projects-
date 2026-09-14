#!/usr/bin/env python3
"""Pass 12 exact audit: one-bit memory rescue of fixed two-class sensors."""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path
from sensor_memory import census
ROOT=Path(__file__).resolve().parent
EXPECTED={
'memoryless_winning_sensor_cases':62032,
'two_state_memory_winning_sensor_cases':74344,
'memory_rescued_sensor_cases':12312,
'systems_with_memory_rescue':3528,
'rescues_by_profile':{'3+1':7656,'2+2':4656},
'rescue_count_distribution':{'0':12856,'1':264,'2':240,'3':1632,'4':288,'5':1104},
'witness':{'target':0,'map0_code':4,'map1_code':24,'map0':[0,1,0,0],'map1':[0,2,1,0],
'partition':[0,0,0,1],'profile':'3+1','controller_code':3,
'controller_cells':[{'memory':0,'observation':0,'action':1,'next_memory':1},{'memory':0,'observation':1,'action':0,'next_memory':0},{'memory':1,'observation':0,'action':0,'next_memory':0},{'memory':1,'observation':1,'action':0,'next_memory':0}]}}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'evidence');args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='pass12-') as tmp:
  binary=Path(tmp)/'native'
  subprocess.run(['g++','-std=c++17','-O3','-Wall','-Wextra','-Werror',str(ROOT/'native_sensor_memory.cpp'),'-o',str(binary)],check=True)
  raw1=subprocess.check_output([str(binary)]);raw2=subprocess.check_output([str(binary)])
 if raw1!=raw2:raise SystemExit('native replays differ')
 native=json.loads(raw1);py=census()
 if native!=py:raise SystemExit('Python/native census mismatch')
 assert py['status']=='PASS_BOUNDED' and py['systems']==16384 and py['sensor_cases']==114688 and py['two_class_partitions']==7
 for k,v in EXPECTED.items():assert py[k]==v,(k,py[k],v)
 sources=['sensor_memory.py','native_sensor_memory.cpp','CONTRACT.md']
 ver={'status':'PASS','scope':'exact two-class sensor / two-state-controller reachability census','source_hash_policy':'SHA-256 of exact checked-out source bytes used by the audit','source_sha256':{n:sha(ROOT/n) for n in sources},'native_replays_identical':True,'python_native_exact_match':True,'claim_ceiling':'bounded deterministic finite tradeoff; not a universal memory/observation theorem'}
 (args.out/'SUMMARY.json').write_text(json.dumps(py,indent=2,sort_keys=True)+'\n')
 (args.out/'VERIFICATION.json').write_text(json.dumps(ver,indent=2,sort_keys=True)+'\n')
 print('PASS Pass 12 sensor-memory census')
if __name__=='__main__':main()

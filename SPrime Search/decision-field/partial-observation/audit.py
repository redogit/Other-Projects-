#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, random, subprocess, tempfile
from functools import lru_cache
from pathlib import Path
from partial import *

ROOT=Path(__file__).resolve().parent
SEED=20260914
ALPHABET="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

def save(path,obj): path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def req(x,msg):
    if not x: raise AssertionError(msg)

def t4_text(rank:int)->str:
    if type(rank) is not int or not 0 <= rank <= 0xffffffff: raise ValueError('transition rank')
    chars=['A']*6;v=rank
    for i in range(5,-1,-1): chars[i]=ALPHABET[v&63];v>>=6
    return 'T4'+''.join(chars)

def byte_map(byte:int)->tuple[int,int,int,int]: return tuple((byte>>(2*s))&3 for s in range(4))

def brute_horizon(system:POSystem,target:int,belief:int,horizon:int)->bool:
    @lru_cache(None)
    def rec(B,h):
        if not (B & ~target): return True
        if h==0:return False
        for action in range(system.actions):
            if all(rec(child,h-1) for child in system.successors(B,action)):return True
        return False
    return rec(belief,horizon)

def run_native(src:Path,out:Path):
    exe=out.with_suffix('')
    subprocess.run(['g++','-O3','-std=c++17',str(src),'-o',str(exe)],check=True,timeout=45)
    raw=subprocess.check_output([str(exe)],timeout=45)
    return raw,json.loads(raw)

def hidden_system()->POSystem:
    rows=[]
    for action in range(4):
        row=[]
        for mode in range(2):
            for physical in range(4):
                if action==0: nxt=(2 if mode else 1) if physical==0 else physical
                elif action==1: nxt=0 if physical in (1,2) else physical
                elif action==2: nxt=(1 if mode else 3) if physical==0 else physical
                else: nxt=(3 if mode else 1) if physical==0 else physical
                row.append(4*mode+nxt)
        rows.append(tuple(row))
    return POSystem(tuple(rows),(0,1,2,3,0,1,2,3))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=ROOT/'evidence');args=p.parse_args()
    out=args.out;out.mkdir(parents=True,exist_ok=True)
    rng=random.Random(SEED)

    # Belief-memory witness: no sensor distinction, but one bit of schedule memory is necessary/sufficient.
    m0=(0,1,0,0);m1=(0,2,1,0);collapsed=(0,0,0,0)
    base=POSystem((m0,m1),collapsed);target=1;initial=0b0111
    W,strategy,levels=sure_current_reach(base,target)
    req(absorbing_target(base,target),'witness target must be absorbing')
    req(wins_from_initial(base,initial,W),'belief witness should win')
    c1=no_observation_controller_reach(base,target,initial,1)
    c2=no_observation_controller_reach(base,target,initial,2)
    req(c1 is None and c2 is not None,'controller memory witness changed')
    rank=4|(24<<8)|(4<<16)|(4<<24)
    req(t4_text(rank)=='T4AEBBgE','T4 witness text changed')

    partition_rows=[];memless_count=0
    for part in partitions(4):
        sys=POSystem((m0,m1),part);w,_,_=sure_current_reach(sys,target)
        bw=wins_from_initial(sys,initial,w);mp=memoryless_observation_reach(sys,target,initial)
        req(bw,'all witness partitions should remain belief-winning')
        memless_count += mp is not None
        partition_rows.append({'partition':part,'classes':max(part)+1,'belief_wins':bw,'memoryless_policy':mp})
    req(memless_count==10,'partition memoryless count changed')

    # Independent recursive horizon oracle on deterministic target-absorbing samples.
    oracle_beliefs=0
    for _ in range(500):
        t=rng.randrange(4);bytes_ok=[b for b in range(256) if ((b>>(2*t))&3)==t]
        f0=byte_map(rng.choice(bytes_ok));f1=byte_map(rng.choice(bytes_ok))
        for part in partitions(4):
            sys=POSystem((f0,f1),part);w,_,_=sure_current_reach(sys,1<<t);h=len(sys.consistent_beliefs())
            for B in sys.consistent_beliefs():
                req((B in w)==brute_horizon(sys,1<<t,B,h),'belief/horizon oracle mismatch');oracle_beliefs+=1

    # Objective monitor witness: same physical belief, different reach-progress status.
    monitor_base=POSystem(((1,0,2,3),(0,1,2,3)),(0,1,2,3));mtarget=1;minit=1<<1
    lifted,done=lift_reach(monitor_base,mtarget);lb=lift_initial_reach(monitor_base,minit,mtarget)
    after1=lifted.post(lb,0);after2=lifted.post(after1,0)
    req(project_physical(lb,4)==project_physical(after2,4)==(1<<1),'physical collision missing')
    req(lb!=after2,'monitor should distinguish pre/post target history')
    lw,_,_=sure_current_reach(lifted,done);req(wins_from_initial(lifted,lb,lw),'lifted reach monitor should solve witness')
    monitor={'physical_belief_before':project_physical(lb,4),'physical_belief_after_two_steps':project_physical(after2,4),
             'product_belief_before':lb,'product_belief_after_two_steps':after2,
             'synthetic_required_action_before_visit':0,'synthetic_required_action_after_visit':1,
             'interpretation':'Current physical belief alone cannot encode whether a nonabsorbing reach objective has already been satisfied.'}

    # Hidden-mode witness: same physical state knowledge after reset, different hidden knowledge/action.
    hidden=hidden_system();hinit=(1<<0)|(1<<4);htarget=(1<<3)|(1<<7)
    branch=hidden.successors(hinit,3)
    req(branch==(1<<1,1<<7),'hidden first-action branches changed')
    failure=1<<1;reset=hidden.successors(failure,1);req(reset==(1<<0,),'reset branch changed')
    quotient=(0,1,2,3,0,1,2,3)
    req(project_belief(hinit,quotient)==project_belief(reset[0],quotient)==1,'physical projection collision missing')
    req(hidden.post(reset[0],2)==1<<3,'mode0 commit should hit target')
    req(hidden.post(1<<4,3)==1<<7,'mode1 commit should hit target')

    controller=ObservationController(actions=((3,1,0,0),(2,0,0,0)),updates=((0,1,0,0),(0,0,0,0)))
    req(controller.wins_reach(hidden,htarget,hinit),'explicit hidden-mode controller failed')
    req(controller.memory_bits(hidden)==1,'hidden-mode controller should retain one bit')

    # Native exhaustive censuses, each replayed twice byte-identically.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        n1,j1=run_native(ROOT/'native_partial.cpp',td/'partial1')
        n2,j2=run_native(ROOT/'native_partial.cpp',td/'partial2')
        h1,k1=run_native(ROOT/'native_hidden.cpp',td/'hidden1')
        h2,k2=run_native(ROOT/'native_hidden.cpp',td/'hidden2')
    req(n1==n2 and h1==h2,'native replay mismatch')
    expected={'partitions':15,'absorbing_target_model_pairs':16384,'model_partition_cases':245760,
              'belief_winning_cases':160440,'memoryless_winning_cases':139416,
              'belief_win_memoryless_fail_cases':21024,'collapsed_observation_memory_needed_models':3528,
              'refinement_implications_checked':983040,
              'min_observation_classes_belief':[10696,0,0,0,5688],
              'min_observation_classes_memoryless':[7168,3528,0,0,5688],
              'shortest_open_loop_word_length':{'1':508,'2':5316,'3':3912,'4':672,'5':240,'6':48,'impossible':5688},
              'minimum_no_observation_controller_states':{'1':7168,'2':3000,'3':528,'impossible':5688}}
    req(j1==expected,'native partial census changed')
    req(k1['q1_total']==256 and k1['q1_winning']==0 and k1['q2_total']==16777216 and k1['q2_winning']==360448,'hidden controller census changed')
    req(k1['first_q2_actions']==[[3,1,0,0],[2,0,0,0]] and k1['first_q2_updates']==[[0,1,0,0],[0,0,0,0]],'hidden first controller changed')

    ps=partitions(4);refpairs=sum(refines(f,c) for f in ps for c in ps)
    req(len(ps)==15 and refpairs==60,'partition lattice cardinality changed')

    summary={
      'status':'PASS_BOUNDED','seed':SEED,
      'partial_observation':{
        't4_witness':t4_text(rank),'transition_rank_hex':hex(rank),'initial_belief':initial,
        'belief_strategy_wins_all_15_partitions':True,'memoryless_winning_partitions':memless_count,
        'collapsed_observation_q1_controller':None,'collapsed_observation_q2_controller':c2,
        'independent_horizon_beliefs_checked':oracle_beliefs,'all_partitions':partition_rows,
      },
      'objective_monitor':monitor,
      'hidden_mode':{
        'worlds':8,'initial_hidden_belief':hinit,'target_hidden_mask':htarget,
        'same_physical_belief_before_and_after_diagnostic_reset':True,
        'q1_controllers_exhausted':k1['q1_total'],'q1_winning':k1['q1_winning'],
        'q2_controllers_exhausted':k1['q2_total'],'q2_winning':k1['q2_winning'],
        'minimum_controller_states':2,'minimum_controller_memory_bits':1,
        'first_q2_actions':k1['first_q2_actions'],'first_q2_updates':k1['first_q2_updates'],
        'interpretation':'A failed consequential action can also reveal hidden mode; separate probe action is not necessary in the minimum controller.'
      },
      'native_absorbing_target_census':j1,
      'scope':'Deterministic finite partial observation with sure objectives; not probabilistic POMDP inference or a universal partial-observation game theorem.'
    }
    save(out/'SUMMARY.json',summary)
    hashes={name:sha(ROOT/name) for name in ('partial.py','audit.py','native_partial.cpp','native_hidden.cpp','CONTRACT.md','README.md') if (ROOT/name).exists()}
    save(out/'VERIFICATION.json',{'status':'PASS','source_sha256':hashes,'native_replays_identical':True,'scope':summary['scope']})
    print(json.dumps({'status':'PASS','oracle_beliefs':oracle_beliefs,'native_cases':j1['model_partition_cases'],
                      'hidden_q2_controllers':k1['q2_total'],'hidden_q2_winning':k1['q2_winning']},indent=2))

if __name__=='__main__':main()

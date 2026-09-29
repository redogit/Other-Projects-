#!/usr/bin/env python3
from pathlib import Path
import argparse, random, tempfile, time, sys
sys.path.insert(0,str(Path(__file__).parent))
import minigxc
FAMILY={'W114_CENTER':'STATE','W114_FIELD':'FIELD','OBSERVER_CHANNELS':'OBSERVER','TRANSFORM_SET':'CONTROL','FRACTAL_BRANCHES':'GEOMETRY','GPU_POINTS':'POINT','COGNATE_LINKS':'RELATION','PULSE_OSCILLATOR':'SIGNAL','FRAME_FEEDBACK':'FEEDBACK','BLOOM_TONEMAP':'POST','TRACE_TAP':'TRACE','RECENTER':'STATE','ROBUST_SCORE':'GAME'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cases',type=int,default=5000);ap.add_argument('--seed',type=int,default=114057);ns=ap.parse_args()
    rng=random.Random(ns.seed);ops=sorted(FAMILY);digests=set();t0=time.time()
    for case in range(ns.cases):
        n=rng.randint(3,18);chosen=[rng.choice(ops) for _ in range(n)]
        lines=[f'MODULE fuzz.m{case}','SURFACE minigx','TARGET android.opengl_es_3_1']
        for i,op in enumerate(chosen):lines.append(f'ENTITY Node.N{i} KIND "MINIGX_NODE" FAMILY "{FAMILY[op]}" OP "{op}" STAGE "{i}" PARAMS "seed={case}_{i}"')
        for i in range(n-1):lines.append(f'RELATE Node.N{i} AS FEEDS TO Node.N{i+1} PORT "b{i}"')
        for k in range(rng.randint(0,n*2)):
            i=rng.randrange(0,n-1);j=rng.randrange(i+1,n);lines.append(f'RELATE Node.N{i} AS MODULATES TO Node.N{j} PORT "x{i}_{j}_{k}"')
        text='\n'.join(lines)+'\n'
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'graph.rmal';q=Path(td)/'renamed.rmal';p.write_text(text);q.write_text(text)
            a=minigxc.canonical_ir(p);b=minigxc.canonical_ir(q)
            if a['digest']!=b['digest']:raise SystemExit('carrier rename changed semantic digest')
            digests.add(a['digest'])
            q.write_text(text+f'RELATE Node.N{n-1} AS FEEDS TO Node.N0 PORT "cycle"\n')
            try:minigxc.canonical_ir(q)
            except ValueError as e:
                if 'non-feedback cycle' not in str(e):raise
            else:raise SystemExit('ordinary cycle accepted')
    if len(digests)!=ns.cases:raise SystemExit('digest collision in generated stress corpus')
    print(f'MINIGX_FUZZ=PASS valid={ns.cases} rejected_cycles={ns.cases} unique_digests={len(digests)} seconds={time.time()-t0:.3f}')
if __name__=='__main__':main()

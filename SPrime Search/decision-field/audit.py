#!/usr/bin/env python3
from collections import Counter
from itertools import product
import hashlib, json, math, random, sys
from pathlib import Path
from field import *
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'evidence'; OUT.mkdir(exist_ok=True)

def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def req(x,m):
    if not x: raise AssertionError(m)

# Complete 4-input/1-output exhaustion.
deg=Counter(); weights=Counter()
for truth in range(1<<16):
    coeff=mobius(truth,4)
    req(mobius(coeff,4)==truth,'mobius inverse 4')
    req(truth_from_anf(coeff,4)==truth,'ANF evaluation 4')
    text=encode_A(4,truth); req(len(text.encode())==5 and decode_A(text)==(4,truth),'A4 codec')
    carrier=to_float('A4',coeff); req(from_float(carrier)==('A4',coeff),'A4 float')
    deg[algebraic_degree(coeff,4)] += 1
    weights[coeff.bit_count()] += 1
req(sum(deg.values())==65536,'A4 count')
req(dict(deg)=={-1:1,0:1,1:30,2:2016,3:30720,4:32768},'degree distribution')

# 5-input representation: proof-oriented basis + deterministic sample, not 2^32 enumeration.
for i in range(32):
    basis=1<<i; req(mobius(mobius(basis,5),5)==basis,'A5 basis involution')
rng=random.Random(20260914)
samples={0,(1<<32)-1,0xaaaaaaaa,0x55555555}
samples.update(rng.randrange(1<<32) for _ in range(10000))
for truth in samples:
    coeff=mobius(truth,5); req(mobius(coeff,5)==truth,'A5 inverse sample')
    req(truth_from_anf(coeff,5)==truth,'A5 eval sample')
    text=encode_A(5,truth); req(len(text.encode())==8 and decode_A(text)==(5,truth),'A5 codec')
    req(from_float(to_float('A5',coeff))==('A5',coeff),'A5 float')

# Two-output 4-input representation product tests.
pairs=[(0,0),(0xffff,0xffff),(0xaaaa,0xcccc),(0x1234,0xbeef)]
pairs += [(rng.randrange(1<<16),rng.randrange(1<<16)) for _ in range(10000)]
for f0,f1 in pairs:
    rank=pack_two(f0,f1); req(unpack_two(rank)==(f0,f1),'B4 pack')
    text=encode_B4(f0,f1); req(len(text.encode())==8 and decode_B4(text)==(f0,f1),'B4 codec')
    req(from_float(to_float('B4',rank))==('B4',rank),'B4 float')

# Temporal 2-bit-state + 2-bit-context full 32-bit representation.
transitions={0,0xffffffff,identity_transition(),0x01234567,0x89abcdef}
transitions.update(rng.randrange(1<<32) for _ in range(10000))
for rank in transitions:
    f0,f1=transition_to_outputs(rank); req(outputs_to_transition(f0,f1)==rank,'T4/B4 bridge')
    text=encode_T4(rank); req(len(text.encode())==8 and decode_T4(text)==rank,'T4 codec')
    req(from_float(to_float('T4',rank))==('T4',rank),'T4 float')

# Exact classification of all 256 local 4-state transition maps.
cycles=Counter(); fixed=Counter()
for byte in range(256):
    cycles[str(local_cycles(byte))]+=1
    fixed[sum(((byte>>(2*s))&3)==s for s in range(4))]+=1
req(sum(cycles.values())==256,'cycle census')
req(dict(fixed)=={0:81,1:108,2:54,3:12,4:1},'fixed point census')

# Constructed temporal repair: idle context protected, six contextual changes required.
baseline=identity_transition(); minimum=baseline
protected={(0,s):s for s in range(4)}
required={(1,0):1,(1,2):0,(2,1):3,(2,3):0,(3,0):2,(3,3):1}
for key,val in protected.items(): req(get_next(baseline,*key)==val,'bad protected baseline')
for (c,s),v in required.items(): minimum=set_next(minimum,c,s,v)
for key,val in protected.items(): req(get_next(minimum,*key)==val,'protection broken')
for key,val in required.items(): req(get_next(minimum,*key)==val,'requirement missed')
fixed_entries=len(protected)+len(required); free_entries=16-fixed_entries
admissible=4**free_entries
changed=sum(get_next(baseline,c,s)!=get_next(minimum,c,s) for c in range(4) for s in range(4))
req(changed==6 and admissible==4096,'repair count')
# Exhaust the entire free-entry repair cube as an independent count/minimum check.
free=[(c,s) for c in range(4) for s in range(4) if (c,s) not in protected and (c,s) not in required]
seen=0; min_changes=99; min_count=0
for values in product(range(4), repeat=len(free)):
    rank=minimum
    for (c,s),v in zip(free,values): rank=set_next(rank,c,s,v)
    if any(get_next(rank,*key)!=val for key,val in protected.items()): continue
    if any(get_next(rank,*key)!=val for key,val in required.items()): continue
    seen += 1
    ch=sum(get_next(baseline,c,s)!=get_next(rank,c,s) for c in range(4) for s in range(4))
    if ch<min_changes: min_changes=ch; min_count=1
    elif ch==min_changes: min_count += 1
req(seen==4096 and min_changes==6 and min_count==1,'repair cube brute force mismatch')

# Minimal context distinction: conflict graph coloring for the partial obligations.
obs={c:{} for c in range(4)}
for (c,s),v in protected.items(): obs[c][s]=v
for (c,s),v in required.items(): obs[c][s]=v
edges=[]
for a in range(4):
    for b in range(a+1,4):
        if any(s in obs[a] and s in obs[b] and obs[a][s]!=obs[b][s] for s in range(4)):
            edges.append((a,b))
def colorable(k):
    for colors in product(range(k),repeat=4):
        if all(colors[a]!=colors[b] for a,b in edges): return colors
    return None
coloring=None
for k in range(1,5):
    coloring=colorable(k)
    if coloring is not None: break
req(k==3,'expected three context classes')
context_bits=math.ceil(math.log2(k))
req(context_bits==2,'expected two context bits')

# Canonical ANF for the minimum temporal repair.
f0,f1=transition_to_outputs(minimum); a0=mobius(f0,4); a1=mobius(f1,4)

# Capacity frontier.
frontier=[]
for n in range(1,7):
    for m in range(1,5):
        bits=m*(1<<n)
        text_bytes=2+math.ceil(bits/6)
        frontier.append({'inputs':n,'outputs':m,'behavior_bits':bits,'behavior_count':f'2^{bits}',
                         'two_char_tag_ascii_bytes':text_bytes,'fits_8_ascii_bytes':text_bytes<=8,
                         'fits_tagged_normal_float_48_payload_bits':bits<=48})

summary={
 'status':'PASS_BOUNDED',
 'A4_functions_exhaustively_checked':65536,
 'A4_row_evaluations':65536*16,
 'A4_algebraic_degree_distribution':{str(k):v for k,v in sorted(deg.items())},
 'A5_behavior_count':2**32,
 'A5_individually_checked':len(samples),
 'A5_coverage_basis':'Möbius transform is a linear self-inverse; all 32 basis vectors checked plus deterministic samples',
 'B4_behavior_maps':2**32,
 'B4_individually_checked':len(pairs),
 'T4_transition_systems':2**32,
 'T4_individually_checked':len(transitions),
 'local_transition_maps_exhaustively_classified':256,
 'local_cycle_profile_distribution':dict(cycles),
 'local_fixed_point_distribution':{str(k):v for k,v in sorted(fixed.items())},
 'temporal_repair_admissible_systems':admissible,
 'temporal_repair_unique_minimum_changed_entries':changed,
 'minimum_transition_rank_hex':hex(minimum),
 'minimum_transition_text':encode_T4(minimum),
 'minimum_output_anf_masks':[hex(a0),hex(a1)],
 'context_conflict_edges':edges,
 'minimum_context_classes':k,
 'minimum_context_coloring':coloring,
 'minimum_context_bits':context_bits,
 'next_boundary':'Six binary inputs require 64 behavior bits for one output; this exceeds the 48-bit payload of the tagged fixed-exponent float carrier and the 8-byte self-describing ASCII envelope.'
}
save('SUMMARY.json',summary); save('FRONTIER.json',frontier)
# Verification hashes.
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'field.py',ROOT/'audit.py']}
save('VERIFICATION.json',{'status':'PASS','source_hashes':hashes,'scope':'Finite implementation checks plus stated algebraic bijection arguments; not formal proof or semantic validation.'})
print(json.dumps(summary,indent=2,default=list))

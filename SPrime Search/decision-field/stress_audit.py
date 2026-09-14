from pathlib import Path
import sys,json,random,itertools,struct,math,hashlib
sys.path.insert(0,str(Path(__file__).parent))
import field

fail=[]; stats={}
def check(x,label,detail=None):
    if not x: fail.append((label,detail))
def rejected(fn):
    try: fn()
    except ValueError: return True
    except Exception as e:
        fail.append(('wrong exception type',(type(e).__name__,str(e)))); return False
    fail.append(('invalid input accepted',None)); return False

# Exhaustive text carrier domain for A4: 2^18 lexical payloads.
valid=invalid=0
for v in range(1<<18):
    s='A4'+field._encode_fixed(v,3)
    try:
        n,t=field.decode_A(s); valid+=1
        check(v<1<<16,'A4 high lexical payload accepted',v)
        check(field.encode_A(n,t)==s,'A4 noncanonical roundtrip',v)
    except ValueError:
        invalid+=1; check(v>=1<<16,'A4 valid lexical payload rejected',v)
check((valid,invalid)==(65536,196608),'A4 lexical partition',(valid,invalid))
stats['A4_lexical_payloads']=1<<18

# 36-bit textual formats: top 4 bits must zero, so only first base64 symbols 0..3.
for prefix,fn in [('A5',field.decode_A),('B4',field.decode_B4),('T4',field.decode_T4)]:
    accepted=[]
    for i,c in enumerate(field.ALPHABET):
        for tail in ('AAAAA','_____'):
            try: fn(prefix+c+tail); accepted.append((i,tail))
            except ValueError: pass
    check(sorted(set(i for i,_ in accepted))==[0,1,2,3],prefix+' top-bit lexical boundary',accepted[:20])
stats['36bit_prefix_cases']=3*64*2

# Canonical float tag domains: valid edges/random accepted; every high payload rejected at encoder and decoder.
rng=random.Random(0xD15EA5E)
limits={'A4':1<<16,'A5':1<<32,'B4':1<<32,'T4':1<<32}
float_valid=0; float_invalid=0
for fmt,limit in limits.items():
    vals={0,1,limit-1}; vals.update(rng.randrange(limit) for _ in range(10000))
    for p in vals:
        f=field.to_float(fmt,p); check(field.from_float(f)==(fmt,p),'float canonical inverse',(fmt,p)); float_valid+=1
    for p in (limit,limit+1,(1<<48)-1):
        check(rejected(lambda fmt=fmt,p=p:field.to_float(fmt,p)),'encoder accepted high payload',(fmt,p)); float_invalid+=1
        bits=(1023<<52)|(field.TAGS[fmt]<<48)|p
        f=struct.unpack('>d',bits.to_bytes(8,'big'))[0]
        check(rejected(lambda f=f:field.from_float(f)),'decoder accepted forged high payload',(fmt,p)); float_invalid+=1
stats['float_valid_cases']=float_valid; stats['float_invalid_cases']=float_invalid
carrier_boundary=0
for tag in [0]+list(range(5,16)):
    for _ in range(64):
        payload=rng.randrange(1<<48); bits=(1023<<52)|(tag<<48)|payload
        f=struct.unpack('>d',bits.to_bytes(8,'big'))[0]
        check(rejected(lambda f=f:field.from_float(f)),'unknown float tag accepted',(tag,payload)); carrier_boundary+=1
for fmt,limit in limits.items():
    p=rng.randrange(limit); tag=field.TAGS[fmt]
    for sign,exp in [(1,1023),(0,1022),(0,1024),(1,1024)]:
        bits=(sign<<63)|(exp<<52)|(tag<<48)|p
        f=struct.unpack('>d',bits.to_bytes(8,'big'))[0]
        check(rejected(lambda f=f:field.from_float(f)),'wrong sign/exponent accepted',(fmt,sign,exp)); carrier_boundary+=1
stats['carrier_boundary_mutations']=carrier_boundary

# Public integer validation boundaries.
for fn in [lambda:field.get_next(-1,0,0),lambda:field.get_next(1<<32,0,0),
           lambda:field.algebraic_degree(-1,4),lambda:field.algebraic_degree(1<<16,4),
           lambda:field.algebraic_degree(1,6),lambda:field.algebraic_degree(True,4),
           lambda:field.eval_anf(1,6,0),lambda:field.eval_anf(1,-1,0),
           lambda:field.truth_from_anf(1,6),lambda:field.truth_from_anf(1,-1)]:
    check(rejected(fn),'public boundary accepted invalid input')
stats['api_negative_cases']=10

MONOMIAL_TABLES={}
def _monomial_tables(n):
    if n not in MONOMIAL_TABLES:
        tables=[]
        for mon in range(1<<n):
            t=0
            for row in range(1<<n):
                if (mon&row)==mon:t|=1<<row
            tables.append(t)
        MONOMIAL_TABLES[n]=tables
    return MONOMIAL_TABLES[n]
def independent_truth(coeff,n):
    out=0; tables=_monomial_tables(n); i=0
    while coeff:
        if coeff&1: out ^= tables[i]
        coeff >>= 1; i += 1
    return out
for n in range(5):
    coeffs=range(1<<(1<<n)) if n<=3 else range(1<<16)
    for coeff in coeffs:
        truth=independent_truth(coeff,n)
        check(field.mobius(truth,n)==coeff,'mobius independent coefficient mismatch',(n,coeff))
        check(field.truth_from_anf(coeff,n)==truth,'eval independent coefficient mismatch',(n,coeff))
stats['independent_anf_coefficients']=sum((1<<(1<<n)) if n<=3 else 65536 for n in range(5))
weights={}
for truth in range(1<<16):
    w=field.mobius(truth,4).bit_count(); weights[w]=weights.get(w,0)+1
check(weights=={k:math.comb(16,k) for k in range(17)},'A4 coefficient weight distribution',weights)
stats['A4_weight_distribution_checked']=65536
for bit in range(32):
    coeff=1<<bit; truth=independent_truth(coeff,5)
    check(field.mobius(truth,5)==coeff,'A5 basis mismatch',bit)
for _ in range(20000):
    coeff=rng.randrange(1<<32); truth=independent_truth(coeff,5)
    check(field.mobius(truth,5)==coeff,'A5 random mismatch',coeff)
stats['A5_independent_checks']=20032

for bit in range(32):
    r=1<<bit; f0,f1=field.transition_to_outputs(r)
    check(field.outputs_to_transition(f0,f1)==r,'T4 basis inverse',bit)
    check(f0.bit_count()+f1.bit_count()==1,'T4 basis not onehot',bit)
stats['T4_basis_checks']=32

def mp(b): return tuple((b>>(2*s))&3 for s in range(4))
def independent_cycles(b):
    f=mp(b); cycles=set()
    for start in range(4):
        seen={}; seq=[]; x=start
        while x not in seen:
            seen[x]=len(seq);seq.append(x);x=f[x]
        cyc=seq[seen[x]:]; cycles.add(min(tuple(cyc[i:]+cyc[:i]) for i in range(len(cyc))))
    return tuple(sorted(map(len,cycles)))
def comp(after,before):
    a,b=mp(after),mp(before);o=0
    for s in range(4):o|=a[b[s]]<<(2*s)
    return o
for b in range(256): check(field.local_cycles(b)==independent_cycles(b),'cycle mismatch',b)
ID=sum(s<<(2*s) for s in range(4))
noncommute=0
for a in range(256):
    for b in range(256):
        c1=comp(a,b); c2=comp(b,a)
        noncommute += c1!=c2
        check(0<=c1<256,'composition range',(a,b))
        if b==ID: check(c1==a,'right identity',a)
        if a==ID: check(c1==b,'left identity',b)
for _ in range(200000):
    a,b,c=(rng.randrange(256) for __ in range(3))
    check(comp(a,comp(b,c))==comp(comp(a,b),c),'associativity',(a,b,c))
stats['composition_pairs']=65536;stats['noncommuting_ordered_pairs']=noncommute;stats['associativity_samples']=200000

only_fixed=[b for b in range(256) if max(field.local_cycles(b),default=0)<=1]
newcycles={2:0,3:0,4:0}; first=None
for a in only_fixed:
    for b in only_fixed:
        c=comp(b,a); mx=max(field.local_cycles(c),default=0)
        if mx>1:
            newcycles[mx]+=1
            if first is None:first=(a,b,c,mp(a),mp(b),mp(c),field.local_cycles(c))
check(newcycles=={2:2700,3:264,4:0},'schedule cycle census',newcycles)
stats['only_fixed_local_maps']=len(only_fixed);stats['switch_pairs']=len(only_fixed)**2;stats['switch_created_cycles']=newcycles;stats['switch_counterexample']=first
unique_attractor=[b for b in range(256) if field.local_cycles(b)==(1,)]
unique_new={2:0,3:0,4:0}; unique_first=None
for a in unique_attractor:
    for b in unique_attractor:
        c=comp(b,a); mx=max(field.local_cycles(c),default=0)
        if mx>1:
            unique_new[mx]+=1
            if unique_first is None: unique_first=(a,b,c,mp(a),mp(b),mp(c),field.local_cycles(c))
check(unique_new=={2:960,3:48,4:0},'unique-attractor switching cycle census',unique_new)
stats['unique_fixed_attractor_maps']=len(unique_attractor);stats['unique_attractor_switch_pairs']=len(unique_attractor)**2;stats['unique_attractor_created_cycles']=unique_new;stats['unique_attractor_counterexample']=unique_first

baseline=field.identity_transition(); cases=0
positions=list(itertools.product(range(4),repeat=2))
for _ in range(750):
    pp=positions[:];rng.shuffle(pp);fixed_n=rng.randrange(10,17)
    cons={p:rng.randrange(4) for p in pp[:fixed_n]};free=[p for p in pp if p not in cons]
    seed=baseline
    for p,v in cons.items():seed=field.set_next(seed,*p,v)
    seen=0;best=99;n_best=0
    for vals in itertools.product(range(4),repeat=len(free)):
        r=seed
        for p,v in zip(free,vals):r=field.set_next(r,*p,v)
        seen+=1
        ch=sum(field.get_next(baseline,c,s)!=field.get_next(r,c,s) for c,s in positions)
        if ch<best:best=ch;n_best=1
        elif ch==best:n_best+=1
    expected=sum(field.get_next(baseline,*p)!=v for p,v in cons.items())
    check(seen==4**len(free) and best==expected and n_best==1,'repair cube mismatch',(cons,seen,best,n_best))
    cases+=1
stats['repair_cube_random_cases']=cases

def edges(obs):
    return [(a,b) for a in range(4) for b in range(a+1,4)
            if any(s in obs[a] and s in obs[b] and obs[a][s]!=obs[b][s] for s in range(4))]
def chromatic(es):
    for k in range(1,5):
      for colors in itertools.product(range(k),repeat=4):
        if all(colors[a]!=colors[b] for a,b in es): return k
    raise AssertionError
def brute_partition(obs):
    best=5
    for colors in itertools.product(range(4),repeat=4):
        ok=True
        for cl in set(colors):
            union={}
            for c in range(4):
                if colors[c]!=cl:continue
                for s,v in obs[c].items():
                    if s in union and union[s]!=v:ok=False;break
                    union[s]=v
                if not ok:break
            if not ok:break
        if ok:best=min(best,len(set(colors)))
    return best
for _ in range(5000):
    obs=[]
    for c in range(4):obs.append({s:rng.randrange(4) for s in range(4) if rng.random()<.6})
    check(chromatic(edges(obs))==brute_partition(obs),'context coloring mismatch',obs)
stats['context_partition_cases']=5000

def split6(truth): return truth&0xffffffff,(truth>>32)&0xffffffff
def join6(lo,hi): return lo|(hi<<32)
for bit in range(64):
    t=1<<bit;lo,hi=split6(t);check(join6(lo,hi)==t,'A6 basis split',bit)
for _ in range(100000):
    t=rng.getrandbits(64);lo,hi=split6(t);check(join6(lo,hi)==t,'A6 random split',t)
stats['A6_split_checks']=100064
a6_text_checks=0
for _ in range(20000):
    t=rng.getrandbits(64);lo,hi=split6(t)
    slo,shi=field.encode_A(5,lo),field.encode_A(5,hi)
    lo2=field.decode_A(slo)[1];hi2=field.decode_A(shi)[1]
    check(join6(lo2,hi2)==t,'A6 two-A5 text reconstruction',t);a6_text_checks+=1
stats['A6_two_A5_text_checks']=a6_text_checks
finite=(1<<64)-(1<<53)
check(finite<(1<<64),'finite-float capacity lower bound',finite)
stats['finite_binary64_patterns']=finite;stats['A6_function_count']=1<<64;stats['finite_pattern_shortfall']=1<<53

frontier=json.loads((Path(__file__).parent/'evidence/FRONTIER.json').read_text())
check(len(frontier)==24,'frontier row count',len(frontier))
for item in frontier:
    n=item['inputs'];m=item['outputs'];bits=m*(1<<n)
    check(item['behavior_bits']==bits,'frontier behavior bits',item)
    check(item['two_char_tag_ascii_bytes']==2+math.ceil(bits/6),'frontier ASCII size',item)
    check(item['fits_8_ascii_bytes']==(bits<=36),'frontier ASCII capacity',item)
    check(item['fits_tagged_normal_float_48_payload_bits']==(bits<=48),'frontier float capacity',item)
stats['frontier_cells']=len(frontier)

print(json.dumps({'status':'PASS' if not fail else 'FAIL','failure_count':len(fail),'failures':fail[:20],'stats':stats},indent=2,default=list))
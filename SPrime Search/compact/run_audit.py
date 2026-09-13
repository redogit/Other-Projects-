#!/usr/bin/env python3
"""Reproducible D1 enumeration, independent small oracle, and context audit."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
from time import perf_counter
import compact

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
BASE_COMMIT = 'e5c727c29f5714a9dce6507de0470f90844094b9'
PARENT_SHA256 = '8a784efa0c1c572349a9feac4df6e085a01f7eb16fb940ef4e2a915105121d53'
SOURCE_NAMES = ('census.cpp','compact.py','run_audit.py','CONTRACT.md')
SEED = 20260913


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, text):
    if not ok:
        raise ValueError(text)


def save(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')


def parent_module():
    path = PARENT/'search.py'
    require(sha(path.read_bytes()) == PARENT_SHA256,'parent source changed: revalidate')
    spec = importlib.util.spec_from_file_location('sprime_parent04',path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def python_oracle(max_gates=4):
    """All short words, represented by eight scalar booleans per register."""
    counts = [[0]*256 for _ in range(max_gates+1)]
    regs = [tuple(bool(i & mask) for i in range(8)) for mask in (4,2,1)]
    for v in (240,204,170): counts[0][v] = 1
    checked = 3
    def visit(code, depth):
        nonlocal checked
        n = len(regs)
        for a in range(n):
            for b in range(n):
                bits = tuple(not(left and right) for left,right in zip(regs[a],regs[b]))
                value = sum(int(bit) << i for i,bit in enumerate(bits))
                counts[depth+1][value] += 1
                word = code+chr(32+8*a+b)
                require(compact.unrank(compact.rank(word)) == word,'short bijection failure')
                require(compact.evaluate(word) == value,'scalar/bit-table mismatch')
                checked += 1
                if depth+1 < max_gates:
                    regs.append(bits);visit(word,depth+1);regs.pop()
    visit('D1',0)
    return counts, checked


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=ROOT/'results')
    args=ap.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat();t0=perf_counter()
    hashes={n:sha((ROOT/n).read_bytes()) for n in SOURCE_NAMES}
    parent=parent_module(); transport=parent.load_transport()
    compiler=subprocess.run(['g++','--version'],capture_output=True,text=True,check=True,timeout=10).stdout.splitlines()[0]
    build=['g++','-std=c++17','-O3','-Wall','-Wextra','-Werror','-pedantic',str(ROOT/'census.cpp'),'-o',str(out/'census')]
    subprocess.run(build,capture_output=True,check=True,timeout=20)
    native_start=perf_counter()
    native=subprocess.run([str(out/'census'),'6'],capture_output=True,check=True,timeout=40)
    native_seconds=perf_counter()-native_start
    (out/'census.json').write_bytes(native.stdout)
    result=json.loads(native.stdout);rows=result['counts_by_gates'];words=result['shortest_hex_by_behavior']
    require([sum(r) for r in rows] == compact.TOTALS,'product cardinality mismatch')
    oracle, short_checks=python_oracle()
    require(oracle == rows[:5], 'independent scalar enumeration mismatch')
    require(sum(map(sum,rows)) == compact.TOTAL,'total cardinality mismatch')
    original=parent.Census(31)
    old_short=original.histogram(8)
    tree_words={f:original.shortest(f) for f in range(256)}
    costs={f:len(text) for f,text in tree_words.items()}
    for f,text in tree_words.items():
        require(sum(parent.scalar_eval(text,i)<<i for i in range(8)) == f,'old witness incorrect')
    for a,b in product(range(256),repeat=2):
        require(costs[255 ^ (a & b)] <= 1+costs[a]+costs[b],'old shortest inequality failed')
    all_witnesses=[]
    for f,encoded in enumerate(words):
        if encoded is None:
            require(all(row[f]==0 for row in rows),'missing reachable witness')
            continue
        word=bytes.fromhex(encoded).decode('utf-8','strict')
        k=0 if word in ('D1x','D1y','D1z') else len(word)-2
        require(rows[k][f]>0 and all(rows[j][f]==0 for j in range(k)),'nonminimum witness')
        require(compact.evaluate(word)==f,'native/Python behavior mismatch')
        require(sum(compact.evaluate_row(word,i)<<i for i in range(8)) == f,'independent witness rows failed')
        tree=compact.expand_tree(word)
        require(parent.parse(tree)[1] == f,'tree translation failure')
        value=parent.word_to_float(word,transport)
        require(parent.float_to_word(value,transport)==word,'float roundtrip failure')
        all_witnesses.append({'table':f,'hex':hex(f),'word':word,'word_hex':encoded,
                             'bytes':len(word),'gates':k,'rank':compact.rank(word),
                             'float_hex':value.hex(),'expanded_tree':tree,
                             'shortest_parent_tree':tree_words[f], 'parent_tree_bytes':costs[f],
                             'parent_tree_gates':(costs[f]-1)//2,
                             'new_to_eight_byte_tree_set':not bool(old_short[f])})
    by_table={r['table']:r for r in all_witnesses}
    base_labels={0:0,2:0,4:1,6:1,1:1,7:0}
    survivors=compact.candidates(base_labels)
    require(survivors==(82,90,114,122),'parent obligations changed')
    accepted=[]
    for f in survivors:
        accepted.append({'table':f,'table_hex':hex(f),
            'old_tree_bytes':costs[f], 'old_tree_gates':(costs[f]-1)//2,
            'compact':by_table.get(f),
            'candidate_counts_by_gates':[row[f] for row in rows],
            'candidate_count':sum(row[f] for row in rows),
            'status':'AVAILABLE_D1' if f in by_table else 'OUTSIDE_D1_BOUND_PARENT_WITNESS_EXISTS'})
    plan=compact.query_plan(survivors)
    require(plan['questions']==2,'full-context lower bound mismatch')
    poisoned=compact.query_plan(survivors);poisoned['questions']=0
    require(compact.query_plan(survivors)['questions']==2,'caller mutated cached plan')
    outcomes=[]
    for bit3,bit5 in product((0,1),repeat=2):
        s=compact.refine(compact.refine(survivors,3,bit3),5,bit5)
        require(len(s)==1,'two-label completion not unique')
        f=s[0]
        outcomes.append({'required_output_011':bit3,'required_output_101':bit5,
            'target':f,'target_hex':hex(f),'route':'D1' if f in by_table else 'PARENT_TREE_FALLBACK',
            'word':by_table[f]['word'] if f in by_table else tree_words[f],
            'not_a_user_preference':'Synthetic output-oracle answers for a regression test.'})
    require(compact.refine(survivors,3,None)==survivors,'unknown answer invented information')
    partial_count=0
    # All 3^8 partial output specifications, independent of candidate multiplicity.
    for labels in product((-1,0,1),repeat=8):
        known={r:v for r,v in enumerate(labels) if v!=-1}
        possible=compact.candidates(known)
        unknown=labels.count(-1)
        require(len(possible)==2**unknown,'partial-spec population failure')
        require(compact.query_plan(possible)['questions']==unknown,'minimax question count failure')
        partial_count+=1
    multiplicity={hex(f):sum(row[f] for row in rows) for f in survivors if f in by_table}
    old_records=json.loads((PARENT/'evidence/repair_candidates.json').read_text())
    old_mass={r['table_hex']:int(r['program_count_through_1024']) for r in old_records if r['table'] in by_table}
    ranking={'same_three_behaviors':[hex(f) for f in survivors if f in by_table],
        'old_tree_program_counts_through_1024':{k:str(v) for k,v in old_mass.items()},
        'D1_counts_through_8_bytes':multiplicity,
        'old_most_encodings':max(old_mass,key=old_mass.get),
        'D1_most_encodings':max(multiplicity,key=multiplicity.get),
        'interpretation':'Different encoding populations are not independent evidence for target outputs.'}
    rng=random.Random(SEED);indices={0,1,2,compact.TOTAL-1}
    offset=0
    for n in compact.TOTALS:
        indices.update((offset,offset+n-1));offset+=n
    indices.update(rng.randrange(compact.TOTAL) for _ in range(512))
    for index in sorted(indices):
        word=compact.unrank(index)
        require(compact.rank(word)==index,'long rank/unrank failure')
        require(sum(compact.evaluate_row(word,i)<<i for i in range(8))==compact.evaluate(word),'long scalar mismatch')
        require(parent.float_to_word(parent.word_to_float(word,transport),transport)==word,'long float mismatch')
    bad=[('bad version',lambda:compact.evaluate('D2"#3E')),
         ('empty program',lambda:compact.evaluate('D1')),
         ('forward reference',lambda:compact.evaluate('D1#')),
         ('non-ASCII instruction',lambda:compact.evaluate('D1é')),
         ('excess length',lambda:compact.evaluate('D1       ')),
         ('leading whitespace',lambda:compact.evaluate(' D1 ')),
         ('repeated terminal',lambda:compact.evaluate('D1xx')),
         ('negative rank',lambda:compact.unrank(-1)),
         ('rank boundary',lambda:compact.unrank(compact.TOTAL)),
         ('bool rank',lambda:compact.unrank(True)),
         ('unknown output value',lambda:compact.refine(survivors,3,2)),
         ('protected row contradiction',lambda:compact.refine(survivors,0,1)),
         ('duplicate behavior vote',lambda:compact.query_plan((82,90,90,114,122))),
         ('bool output value',lambda:compact.candidates({3:True}))]
    rejected=[]
    for label,call in bad:
        try:call()
        except ValueError:rejected.append(label)
        else:raise AssertionError('invalid request accepted: '+label)
    require(compact.evaluate('D1 ') == 15,'significant-space instruction lost')
    # Reusing an old acceptance without new context would be wrong.
    require(114 in survivors and 114 not in compact.refine(survivors,3,1),'context-invalidated acceptance failure')
    budgets=[]
    for k in range(7):
        hist=[sum(row[f] for row in rows[:k+1]) for f in range(256)]
        budgets.append({'max_gates':k,'max_bytes':max(3,k+2),'word_count':sum(hist),
                        'behaviors':sum(bool(v) for v in hist),
                        'passing_words':sum(hist[f] for f in survivors),
                        'passing_behaviors':[f for f in survivors if hist[f]]})
    missing=[f for f in range(256) if f not in by_table]
    summary={'status':'PASS_BOUNDED','new_format':'D1','total_words_checked':compact.TOTAL,
        'full_native_enumeration':True,'gate_bound':6,'byte_cap_including_D1_tag':8,
        'reachable_behaviors':len(all_witnesses),'unreached_behaviors_at_bound':len(missing),
        'new_to_eight_byte_tree_working_set':sum(r['new_to_eight_byte_tree_set'] for r in all_witnesses),
        'accepted_tables':[hex(f) for f in survivors],'accepted_D1_tables':[r['table_hex'] for r in accepted if r['compact']],
        'accepted_D1_words':sum(r['candidate_count'] for r in accepted),
        'python_scalar_oracle_words':short_checks,'complete_partial_specifications':partial_count,
        'worst_case_queries_for_parent_four':plan['questions'],
        'rank_float_samples':len(indices),'shortest_witness_float_roundtrips':len(all_witnesses),
        'shortest_witness_scalar_rows':8*len(all_witnesses),'parent_cost_inequalities':65536,
        'invalid_requests_rejected':rejected,'significant_space_preserved':True,
        'unknown_answer_retains_candidates':True,'stale_acceptance_rejected':True,
        'caller_plan_mutation_isolated':True,
        'native_histogram_sha256':sha(native.stdout),
        'non_claims':['No new truth table was invented.','No universal meaning detector.',
            'Decoder and input data are external dependencies.','Byte-shortest means shortest in D1 only.',
            'Synthetic query answers are not user preferences.','No multilingual or alliteration expansion.']}
    for name,obj in [('witnesses.json',all_witnesses),('repairs.json',accepted),('queries.json',{'plan':plan,'outcomes':outcomes}),
                     ('multiplicity.json',ranking),('budgets.json',budgets),('unreached.json',missing),('summary.json',summary)]:
        save(out/name,obj)
    require(hashes=={n:sha((ROOT/n).read_bytes()) for n in SOURCE_NAMES},'execution inputs changed')
    # Formal hashes describe this exact source/run, not the earlier larger project.
    outputs=[{'path':p.name,'sha256':sha(p.read_bytes())} for p in sorted(out.glob('*.json')) if p.name!='manifest.json']
    manifest={'schema_version':1,'claim_id':'SPRIME-COMPACT-CONTEXT-04',
      'repository':{'commit':BASE_COMMIT,'dirty':True},'command':[sys.executable,str(ROOT/'run_audit.py'),'--out',str(out)],
      'environment':{'software':[{'name':'Python','version':platform.python_version()}, {'name':'compiler','version':compiler}],
                     'hardware':platform.platform()},
      'mathematics':{'assertion_tested':'Complete D1 census and contextual selection under the declared partial truth table.',
        'coefficient_domain':'uint64 exact counts; eight-bit truth tables; integer query costs',
        'conventions':'CONTRACT.md; fixed inputs x,y,z; ordered operands, version tag charged.',
        'inputs':list(hashes),'bounds':{'gates':6,'total_words':compact.TOTAL,'python_oracle_max_gates':4,'partial_specs':6561},
        'non_claims':summary['non_claims']},
      'randomness':{'used':True,'generator':'Python random.Random','seed':SEED},
      'run':{'started_at':started,'runtime_seconds':perf_counter()-t0,'exit_status':0,
             'native_seconds':native_seconds,'native_timeout_seconds':40,'build_command':build},
      'input_artifacts':[{'path':n,'sha256':v,'sha256_after':v} for n,v in hashes.items()],
      'dependency_artifacts':[{'path':'../search.py','sha256':PARENT_SHA256}],
      'outputs':outputs,'checks':['product population','independent scalar oracle','all partial specs','rank inverses',
                                 'inherited UTF-8 float inverse','all old cost inequalities','negative requests'],
      'result':'PASS within stated bound',
      'residual_risks':['Single author, manually declared grammar/specification.','No independent cultural or human validation.',
                        'Parent dependency source-lock must be rechecked after changes.']}
    save(out/'manifest.json',manifest)
    print(json.dumps({'summary':summary,'native_seconds':native_seconds,'total_seconds':manifest['run']['runtime_seconds'],
                      'budgets':budgets,'repairs':[(r['table_hex'],r['compact']['word'] if r['compact'] else None) for r in accepted]},indent=2))

if __name__=='__main__':main()

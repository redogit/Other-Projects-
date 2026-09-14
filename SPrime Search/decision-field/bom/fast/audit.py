#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,platform,subprocess,sys
from pathlib import Path

from benchmark import make_benchmark_task,make_dependency_trap_task,run_benchmarks,run_dependency_traps
from native import compile_native,compile_native_mrv,run_native
from question import QuestionSpec,rank_questions
from train import build_examples,evaluate_ranker,family_split,generate_training_families,oracle_min_cover,train_pairwise_perceptron
from hard_search import solve_mrv
from z3_verify import solve_z3,z3_available

ROOT=Path(__file__).resolve().parent
BOM=ROOT.parent


def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'))+'\n'
def write(path,value): path.write_text(canonical(value),encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def task_manifest(tasks):
    rows=[{'family_id':t.family_id,'required_mask':t.required_mask,'provide_masks':list(t.provide_masks),'require_masks':list(t.require_masks)} for t in tasks]
    raw=canonical(rows).encode()
    return hashlib.sha256(raw).hexdigest()
def valid_subset_count(task):
    count=0
    for mask in range(1,1<<len(task.provide_masks)):
        provided=0; needed=task.required_mask
        for i in range(len(task.provide_masks)):
            if mask>>i&1:
                provided |= task.provide_masks[i]; needed |= task.require_masks[i]
        if needed & ~provided == 0: count+=1
    return count

def load_parent_frontier():
    path=BOM/'evidence'/'FRONTIER.json'
    return json.loads(path.read_text(encoding='utf-8')),path

def question_record(frontier):
    ids=tuple(x['assembly_id'] for x in frontier)
    costs_by={x['assembly_id']:x['cost'] for x in frontier}
    dims=tuple(sorted(frontier[0]['cost']))
    costs={i:tuple(costs_by[i][d] for d in dims) for i in ids}
    questions=(
      QuestionSpec('sensor_available','Is observation/sensor use available?',('yes','no'),(('yes',ids),('no',tuple(i for i in ids if costs_by[i]['observation_classes']==0))),1),
      QuestionSpec('memory_one_bit','Must controller memory fit in one bit?',('yes','no'),(('yes',tuple(i for i in ids if costs_by[i]['memory_bits']<=1)),('no',ids)),1),
      QuestionSpec('two_components','Must the assembly use at most two components?',('yes','no'),(('yes',tuple(i for i in ids if costs_by[i]['component_count']<=2)),('no',ids)),1),
    )
    ranked=rank_questions(questions,ids,ids,costs=costs)
    return [
      {'question_id':s.question.stable_id,'text':s.question.text,'rank_key':list(s.rank_key),'worst_survivors':s.worst_survivors,
       'guaranteed_eliminations':s.guaranteed_eliminations,'frontier_change_answers':s.frontier_change_answers,
       'answer_frontiers':[{'answer':a,'frontier':list(f)} for a,f in s.answer_frontiers]}
      for s in ranked
    ]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--require-z3',action='store_true')
    args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True)

    tasks=generate_training_families(60,seed=20260914)
    groups={name:tuple(t for t in tasks if family_split(t.family_id)==name) for name in ('train','validation','test')}
    model=train_pairwise_perceptron(build_examples(groups['train']),epochs=8)
    bad=train_pairwise_perceptron(build_examples(groups['train']),epochs=8,reverse_labels=True)
    val=evaluate_ranker(groups['validation'],model); test=evaluate_ranker(groups['test'],model); badval=evaluate_ranker(groups['validation'],bad)
    if not (val.exact_agreement and test.exact_agreement and val.promoted and test.promoted and not badval.promoted):
        raise AssertionError('training promotion gate failed')

    hard_lex=hard_rank=0
    for size in (12,16,20,32):
        task=make_dependency_trap_task(size); a=solve_mrv(task,None); b=solve_mrv(task,model)
        if (a.count,a.mask)!=(b.count,b.mask): raise AssertionError('trained hard-family answer drift')
        hard_lex+=a.expansions; hard_rank+=b.expansions
    if hard_rank>=hard_lex: raise AssertionError('trained ordering did not improve out-of-family total')

    native=compile_native(); native_mrv=compile_native_mrv()
    try:
        coverage=run_benchmarks(model,native)
        traps=run_dependency_traps(model,lambda task:run_native(task,native_mrv))
    finally:
        native.cleanup(); native_mrv.cleanup()

    wolfram_path=ROOT/'evidence'/'WOLFRAM_CHECK.json'; wolfram=json.loads(wolfram_path.read_text())
    wtask=make_benchmark_task(12); woracle=oracle_min_cover(wtask); wcount=valid_subset_count(wtask)
    expected=wolfram['result']
    if (woracle[0],woracle[1],wcount)!=(expected['best_count'],expected['best_mask'],expected['valid_subset_count']):
        raise AssertionError('Wolfram fixed cross-check mismatch')

    frontier,parent_frontier_path=load_parent_frontier(); questions=question_record(frontier)
    if not questions: raise AssertionError('no consequential questions produced')

    training={
      'status':'PASS_BOUNDED',
      'dataset_sha256':task_manifest(tasks),
      'family_counts':{k:len(v) for k,v in groups.items()},
      'split_policy':'sha256-family-bucket 60/20/20',
      'model':{'type':'deterministic_integer_pairwise_perceptron','weights':list(model.weights),'epochs':model.epochs},
      'validation':{'exact_agreement':val.exact_agreement,'lexical_expansions':val.lexical_expansions,'ranked_expansions':val.ranked_expansions,'promoted':val.promoted},
      'test':{'exact_agreement':test.exact_agreement,'lexical_expansions':test.lexical_expansions,'ranked_expansions':test.ranked_expansions,'promoted':test.promoted},
      'corrupted_label_control':{'exact_agreement':badval.exact_agreement,'lexical_expansions':badval.lexical_expansions,'ranked_expansions':badval.ranked_expansions,'promoted':badval.promoted},
      'out_of_family_dependency_traps':{'lexical_expansions':hard_lex,'ranked_expansions':hard_rank,'exact_answers_unchanged':True},
      'authority_boundary':'ranking only; never validity, pruning, dominance, equivalence, or evidence promotion',
    }
    summary={
      'status':'PASS_BOUNDED',
      'coverage_benchmarks':list(coverage),
      'dependency_trap_benchmarks':list(traps),
      'question_ranking':questions,
      'wolfram_crosscheck':{'verified':True,'benchmark':wolfram['benchmark'],'best_count':expected['best_count'],'best_mask':expected['best_mask'],'valid_subset_count':expected['valid_subset_count']},
      'training_test_expansion_reduction':test.lexical_expansions-test.ranked_expansions,
      'hard_family_expansion_reduction':hard_lex-hard_rank,
      'claim_ceiling':'bounded exact BOM acceleration and question ordering on declared finite families only',
    }
    write(args.out/'SUMMARY.json',summary); write(args.out/'TRAINING.json',training)

    z3_checks=[]; z3_version=None
    if z3_available():
        for family, maker in (('coverage',make_benchmark_task),('dependency_trap',make_dependency_trap_task)):
            for size in (12,16,20):
                task=maker(size); expected_pair=oracle_min_cover(task); got=solve_z3(task)
                if (got.count,got.mask)!=expected_pair: raise AssertionError(f'Z3 disagreement {family} {size}')
                z3_version=got.solver; z3_checks.append({'family':family,'size':size,'count':got.count,'mask':got.mask})
    elif args.require_z3:
        raise RuntimeError('Z3 required but unavailable')

    sources=('index.py','incremental.py','question.py','explain.py','train.py','hard_search.py','benchmark.py','native.py','native_search.cpp','native_mrv.cpp','z3_verify.py','audit.py')
    verification={
      'status':'PASS' if z3_available() else 'PASS_Z3_UNAVAILABLE',
      'python':platform.python_version(),
      'z3_available':z3_available(),'z3_version':z3_version,'z3_exact_checks':z3_checks,
      'source_sha256':{name:sha(ROOT/name) for name in sources},
      'parent_frontier_sha256':sha(parent_frontier_path),
      'wolfram_check_sha256':sha(wolfram_path),
      'research_grounding_sha256':sha(ROOT/'RESEARCH_GROUNDING.md'),
      'native_cpp_compiled_and_agreed':True,
      'scientific_files':['SUMMARY.json','TRAINING.json'],
      'claim_ceiling':summary['claim_ceiling'],
    }
    write(args.out/'VERIFICATION.json',verification)
    print(json.dumps({'status':summary['status'],'test_expansions':[test.lexical_expansions,test.ranked_expansions],'hard_expansions':[hard_lex,hard_rank],'z3_checks':len(z3_checks)},sort_keys=True))

if __name__=='__main__': main()

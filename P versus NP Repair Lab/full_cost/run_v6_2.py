#!/usr/bin/env python3
"""Compile first, execute bounded exact cases, preserve machine-readable cost evidence."""
import argparse, hashlib, json, pathlib, platform, resource, subprocess, time

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', required=True)
    ap.add_argument('--cases', default=','.join(f'{n}:{g}' for n in (2,3,4) for g in range(7)))
    args = ap.parse_args()
    root = pathlib.Path(__file__).resolve().parent
    out = pathlib.Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    binary = out / 'constructor'
    compile_argv = ['g++', '-std=c++20', '-O2', '-Wall', '-Wextra', '-Wpedantic', '-Werror', str(root / 'constructor_v6_1.cpp'), '-o', str(binary)]
    start = time.perf_counter()
    compiled = subprocess.run(compile_argv, capture_output=True, text=True, timeout=120)
    build = {'argv': compile_argv, 'elapsed_seconds': time.perf_counter()-start,
             'exit_code': compiled.returncode, 'stdout': compiled.stdout, 'stderr': compiled.stderr}
    report = {'schema_version': 1, 'source_revision': 'conscience64@e6256b3746076eb02a4bf3c32eedb6f57666169b',
              'destination_base': 'Other-Projects-@3c09ab6c07a854f8cc3feb585822cc7c5fd8dcde',
              'compiler': subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
              'python': platform.python_version(), 'platform': platform.platform(),
              'cpu_affinity_count': len(__import__('os').sched_getaffinity(0)),
              'max_address_space_bytes': resource.getrlimit(resource.RLIMIT_AS)[0],
              'compile': build, 'cases': [],
              'non_claims': ['No resolution of P versus NP.', 'No asymptotic or formula lower bound.',
                             'No universal selector optimality.', 'Instrumented single-run elapsed times are descriptive, not calibrated microbenchmarks.',
                             'Index accounted capacity excludes allocator bookkeeping; peak RSS includes construction and process baseline.']}
    target = out / 'results.json'
    if compiled.returncode:
        target.write_text(json.dumps(report, indent=2)+'\n')
        raise SystemExit(compiled.returncode)
    report['compile']['binary_sha256'] = digest(binary)
    for case in args.cases.split(','):
        n,g = map(int, case.split(':'))
        result = out / f'n{n}_g{g}.json'
        argv = [str(binary), str(n), str(g), str(result)]
        start = time.perf_counter()
        try:
            run = subprocess.run(argv, capture_output=True, text=True, timeout=120)
            item = {'n': n, 'gate_budget': g, 'argv': argv, 'process_seconds': time.perf_counter()-start,
                    'exit_code': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr}
            if run.returncode == 0:
                item['result'] = json.loads(result.read_text())
                item['result_sha256'] = digest(result)
            report['cases'].append(item)
            target.write_text(json.dumps(report, indent=2)+'\n')
            print(f'{case}: exit={run.returncode} seconds={item["process_seconds"]:.3f}', flush=True)
            if run.returncode:
                raise SystemExit(run.returncode)
        except subprocess.TimeoutExpired:
            report['cases'].append({'n':n, 'gate_budget':g, 'status':'timeout', 'timeout_seconds':120})
            target.write_text(json.dumps(report, indent=2)+'\n')
            raise SystemExit(1)
    # Never award a cheaper failed route a success: compare only routes that eliminate the class.
    counterexamples=[]
    for case in report['cases']:
        data=case['result']; fixed=data['routes'][-1]
        if not fixed['eliminated_class']:
            continue
        for other in data['routes']:
            if other['translation']<=0 or not other['eliminated_class']:
                continue
            if other['counts']['score_and_word_ops'] < fixed['counts']['score_and_word_ops']:
                counterexamples.append({'n':data['n'],'gate_budget':data['gate_budget'],
                                       'all_ones_translation':fixed['translation'], 'other_translation':other['translation'],
                                       'all_ones_score_and_words':fixed['counts']['score_and_word_ops'],
                                       'other_score_and_words':other['counts']['score_and_word_ops'],
                                       'all_ones_observations':fixed['observations'],'other_observations':other['observations']})
    report['counterexamples_to_universal_all_ones_score_cost_optimality']=counterexamples
    report['all_requested_cases_completed']=True
    report['requested_cases']=[list(map(int, case.split(':'))) for case in args.cases.split(',')]
    report['coverage_matches_standard_grid']=sorted(report['requested_cases'])==[[n,g] for n in (2,3,4) for g in range(7)]
    target.write_text(json.dumps(report, indent=2)+'\n')

if __name__ == '__main__':
    main()

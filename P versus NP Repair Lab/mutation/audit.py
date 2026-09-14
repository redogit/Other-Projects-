"""Independent finite repair oracle, negative controls and measured examples."""
import argparse
from itertools import product
import json
from pathlib import Path
import random
import time
from repair import Executor, compile_plan


def scalar_accept(spec, candidate):
    values = [bool(candidate & (1 << i)) for i in range(spec['variables'])]
    return all(any(values[abs(lit)-1] if lit > 0 else not values[abs(lit)-1]
                   for lit in clause) for clause in spec['clauses'])


def oracle(spec, baseline, protected, radius):
    rows = []
    for candidate in range(2 ** spec['variables']):
        changed = [i for i in range(spec['variables'])
                   if ((candidate >> i) & 1) != ((baseline >> i) & 1)]
        if any((protected >> i) & 1 for i in changed) or len(changed) > radius:
            continue
        if scalar_accept(spec, candidate):
            rows.append((len(changed), candidate))
    if not rows:
        return 'infeasible_within_radius', None, None, 0
    distance, candidate = min(rows)
    return 'optimal', candidate, distance, sum(d == distance for d, _ in rows)


def compare(executor, spec, baseline, protected, radius):
    actual = executor.solve(baseline, protected, radius)
    expected = oracle(spec, baseline, protected, radius)
    assert tuple(actual[k] for k in ['status', 'candidate', 'minimum_distance', 'minimum_count']) == expected
    return actual


def audit(output):
    count = 0
    # All 512 subsets of the nine non-tautological clauses on two variables,
    # including the empty clause, all baselines, locks and radii.
    universe = [[sign*(i+1) for i, sign in enumerate(signs) if sign]
                for signs in product((-1, 0, 1), repeat=2)]
    for family in range(1 << len(universe)):
        spec = {'variables': 2, 'clauses': [c for i, c in enumerate(universe) if (family >> i) & 1]}
        executor = Executor(compile_plan(spec))
        for baseline, protected, radius in product(range(4), range(4), range(3)):
            compare(executor, spec, baseline, protected, radius)
            count += 1
        executor.clear()
    rng = random.Random(854321)
    random_checks = 0
    for _ in range(128):
        n = rng.choice([3, 4, 5, 6])
        spec = {'variables': n, 'clauses': [[rng.choice([-1, 1])*rng.randint(1, n)
                  for _ in range(rng.randint(0, 4))] for _ in range(rng.randint(0, 12))]}
        executor = Executor(compile_plan(spec))
        compare(executor, spec, rng.randrange(1 << n), rng.randrange(1 << n), rng.randrange(n+1))
        executor.clear()
        random_checks += 1

    trap = {'variables': 3, 'clauses': [[1, 2, 3]] + [[-i, j] for i in range(1, 4) for j in range(1, 4) if i != j]}
    t0 = time.perf_counter_ns()
    compiled = compile_plan(trap)
    compile_ns = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    executor = Executor(compiled)
    validation_ns = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    repaired = compare(executor, trap, 0, 0, 3)
    solve_ns = time.perf_counter_ns() - t0
    conflict_counts = [sum(not scalar_accept({'variables': 3, 'clauses': [c]}, x) for c in trap['clauses']) for x in range(8)]
    assert conflict_counts == [1, 2, 2, 2, 2, 2, 2, 0]
    assert repaired['candidate'] == 7 and repaired['minimum_distance'] == 3
    assert executor.solve(0, protected=1)['status'] == 'infeasible_within_radius'
    assert executor.solve(0, max_assignments=1)['status'] == 'resource_limit'
    executor.clear(); executor.clear()
    try: executor.accepts(7)
    except RuntimeError: pass
    else: raise AssertionError('Released plan remained usable')
    invalids = [{'variables': True, 'clauses': []}, {'variables': 2, 'clauses': [[True]]},
                {'variables': 2, 'clauses': [[1.0]]}, {'variables': 2, 'clauses': [[0]]},
                {'variables': 2, 'clauses': [[3]]}]
    for invalid in invalids:
        try: compile_plan(invalid)
        except ValueError: pass
        else: raise AssertionError('Invalid spec accepted')
    corrupt = json.loads(json.dumps(compiled)); corrupt['masks'][0][0] = 0
    try: Executor(corrupt)
    except ValueError: pass
    else: raise AssertionError('Source-inconsistent masks accepted')
    for n in [0, 1]:
        for clauses in [[], [[]]]:
            spec = {'variables': n, 'clauses': clauses}
            compare(Executor(compile_plan(spec)), spec, 0, 0, n)
    result = {'contract': 'cnf-mutation-audit/1', 'exhaustive_two_variable_systems': count,
              'sampled_systems': random_checks, 'random_seed': 854321,
              'minimum_boundary_systems': 4, 'failures': 0,
              'trap': {'source': trap, 'baseline': 0, 'conflicts_by_assignment': conflict_counts,
                       'repair': repaired, 'protected_bit_zero': 'infeasible'},
              'timing_ns': {'compile_masks': compile_ns, 'validate_and_load': validation_ns,
                            'solve_plus_independent_oracle': solve_ns},
              'compiled_json_bytes': len(json.dumps(compiled, sort_keys=True, separators=(',', ':')).encode()),
              'scope': 'Exact finite oracle comparisons. Timings are one small local example, not a benchmark speed claim. Search enumerates Hamming layers; compilation never materializes the model population. No claim about arbitrary program repair or solving P versus NP.'}
    output.mkdir(parents=True, exist_ok=True)
    (output / 'results.json').write_text(json.dumps(result, indent=2)+'\n')
    (output / 'trap.plan.json').write_text(json.dumps(compiled, indent=2)+'\n')
    print(json.dumps({'exhaustive_systems': count, 'sampled_systems': random_checks, 'failures': 0, 'trap_repair': repaired}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    audit(parser.parse_args().output)

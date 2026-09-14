import argparse
from itertools import product
import json
from pathlib import Path
from audit import oracle
from macro_repair import solve_implications


def run(output):
    cases = 0
    for n in [1, 2, 3]:
        edges = [(i, j) for i in range(1, n+1) for j in range(1, n+1) if i != j]
        for edge_mask in range(1 << len(edges)):
            implications = [[-i, j] for k, (i, j) in enumerate(edges) if (edge_mask >> k) & 1]
            for positive_mask, protected in product(range(1, 1 << n), range(1 << n)):
                positive = [i+1 for i in range(n) if (positive_mask >> i) & 1]
                spec = {'variables': n, 'clauses': [positive]+implications}
                actual = solve_implications(spec, protected)
                status, candidate, distance, count = oracle(spec, 0, protected, n)
                status = 'infeasible' if status == 'infeasible_within_radius' else status
                assert (actual['status'], actual['candidate'], actual['minimum_distance'], actual['minimum_count']) == (status, candidate, distance, count)
                cases += 1
    invalid = {'variables': 2, 'clauses': [[1], [2]]}
    try: solve_implications(invalid)
    except ValueError: pass
    else: raise AssertionError('Unsupported multiple positive clauses accepted')
    trap = {'variables': 3, 'clauses': [[1, 2, 3]]+[[-i, j] for i in range(1, 4) for j in range(1, 4) if i != j]}
    repaired = solve_implications(trap)
    assert repaired['candidate'] == 7 and repaired['minimum_distance'] == 3
    result = {'contract': 'implication-macro-repair/1', 'complete_systems': cases,
              'variables': [1, 2, 3], 'failures': 0, 'trap_repair': repaired,
              'scope': 'All simple directed implication graphs through three variables, every nonempty positive clause and every protected-zero mask; compared with independent full-assignment oracle. Uniform special-case argument is in MACRO_REPAIR.md; no general SAT claim.'}
    output.mkdir(parents=True, exist_ok=True)
    (output/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    run(parser.parse_args().output)

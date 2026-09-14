"""Polynomial special-case repair: one positive clause plus implications.

The baseline is all zero, and protected positions must stay zero. All graph
construction/reachability work occurs before candidate closure selection.
"""
from repair import compile_plan, integer


def solve_implications(spec, protected=0):
    source = compile_plan(spec)['source']
    n = source['variables']
    integer(protected, 'protected', 0, (1 << n)-1)
    target = None
    graph = [set() for _ in range(n)]
    for clause in source['clauses']:
        if clause and all(literal > 0 for literal in clause):
            if target is not None:
                raise ValueError('This solver requires exactly one positive clause')
            target = sorted({literal-1 for literal in clause})
        elif len(clause) == 2 and sum(literal < 0 for literal in clause) == 1:
            negative = next(literal for literal in clause if literal < 0)
            positive = next(literal for literal in clause if literal > 0)
            graph[-negative-1].add(positive-1)
        else:
            raise ValueError('Unsupported clause: expected a positive clause or implication')
    if target is None:
        raise ValueError('This solver requires exactly one positive clause')
    closures = []
    edge_visits = 0
    for start in target:
        seen, todo = {start}, [start]
        while todo:
            vertex = todo.pop()
            for successor in sorted(graph[vertex]):
                edge_visits += 1
                if successor not in seen:
                    seen.add(successor)
                    todo.append(successor)
        closures.append(sum(1 << bit for bit in seen))
    candidates = sorted({closure for closure in closures if not closure & protected})
    if not candidates:
        return {'status': 'infeasible', 'candidate': None, 'minimum_distance': None,
                'minimum_count': 0, 'closure_builds': len(closures), 'edge_visits': edge_visits}
    distance = min(candidate.bit_count() for candidate in candidates)
    minima = [candidate for candidate in candidates if candidate.bit_count() == distance]
    return {'status': 'optimal', 'candidate': min(minima), 'minimum_distance': distance,
            'minimum_count': len(minima), 'closure_builds': len(closures), 'edge_visits': edge_visits}

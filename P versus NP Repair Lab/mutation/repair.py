"""Exact bounded CNF repair with a source-specific, precompiled mask plan.

Compilation is linear in clause-plus-literal input size, with integer-width
and serialization costs.
Search is explicitly exponential in the number of editable Boolean variables.
"""
from hashlib import sha256
from itertools import combinations
import json

VERSION = 'cnf-mask-plan/1'
MAX_VARIABLES = 20


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in [{low}, {high}]')
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def compile_plan(spec):
    if type(spec) is not dict or set(spec) != {'variables', 'clauses'}:
        raise ValueError('Expected exactly variables and clauses')
    n = integer(spec['variables'], 'variables', 0, MAX_VARIABLES)
    if type(spec['clauses']) is not list:
        raise ValueError('clauses must be a list')
    if len(spec['clauses']) > 10000:
        raise ValueError('At most 10000 clauses are accepted')
    clauses, masks = [], []
    literal_count = 0
    for clause in spec['clauses']:
        if type(clause) is not list or len(clause) > 10000:
            raise ValueError('Each clause must be a list of at most 10000 literals')
        pos, neg = 0, 0
        for literal in clause:
            integer(literal, 'literal', -n, n)
            if literal == 0:
                raise ValueError('Literals use signed, one-based variable IDs')
            if literal > 0:
                pos |= 1 << (literal - 1)
            else:
                neg |= 1 << (-literal - 1)
            literal_count += 1
            if literal_count > 100000:
                raise ValueError('At most 100000 input literals are accepted')
        clauses.append(list(clause))
        masks.append([pos, neg])
    source = {'variables': n, 'clauses': clauses}
    return {'format': VERSION, 'source': source, 'masks': masks,
            'source_sha256': sha256(canonical(source).encode()).hexdigest()}


class Executor:
    def __init__(self, plan):
        if type(plan) is not dict or set(plan) != {'format', 'source', 'masks', 'source_sha256'}:
            raise ValueError('Malformed compiled plan')
        expected = compile_plan(plan['source'])
        # JSON comparison preserves bool/int and float/int distinctions.
        if canonical(plan) != canonical(expected):
            raise ValueError('Compiled plan disagrees with its source or version')
        self._n = expected['source']['variables']
        self._full = (1 << self._n) - 1
        self._masks = tuple(tuple(row) for row in expected['masks'])

    def _alive(self):
        if self._masks is None:
            raise RuntimeError('Executor released; compile/load a new plan')

    def accepts(self, candidate):
        self._alive()
        integer(candidate, 'candidate', 0, self._full)
        inverse = candidate ^ self._full
        return all((candidate & pos) or (inverse & neg) for pos, neg in self._masks)

    def solve(self, baseline, protected=0, radius=None, max_assignments=1 << MAX_VARIABLES):
        self._alive()
        integer(baseline, 'baseline', 0, self._full)
        integer(protected, 'protected', 0, self._full)
        radius = self._n if radius is None else integer(radius, 'radius', 0, self._n)
        integer(max_assignments, 'max_assignments', 1, 1 << MAX_VARIABLES)
        editable = tuple(i for i in range(self._n) if not (protected >> i) & 1)
        visited, clause_checks = 0, 0
        for distance in range(min(radius, len(editable)) + 1):
            best, count = None, 0
            for positions in combinations(editable, distance):
                if visited == max_assignments:
                    return {'status': 'resource_limit', 'candidate': best,
                            'minimum_distance': None, 'minimum_count': None,
                            'visited': visited, 'clause_checks': clause_checks}
                candidate = baseline
                for bit in positions:
                    candidate ^= 1 << bit
                visited += 1
                inverse, valid = candidate ^ self._full, True
                for pos, neg in self._masks:
                    clause_checks += 1
                    if not ((candidate & pos) or (inverse & neg)):
                        valid = False
                        break
                if valid:
                    count += 1
                    best = candidate if best is None else min(best, candidate)
            if best is not None:
                return {'status': 'optimal', 'candidate': best,
                        'minimum_distance': distance, 'minimum_count': count,
                        'visited': visited, 'clause_checks': clause_checks}
        return {'status': 'infeasible_within_radius', 'candidate': None,
                'minimum_distance': None, 'minimum_count': 0,
                'visited': visited, 'clause_checks': clause_checks}

    def clear(self):
        self._masks = None


#!/usr/bin/env python3
"""Exact contextual questioning and real-library boundary probes; stdlib only."""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import sqlite3
import tempfile
import zlib

ACTIONS = tuple(product((0, 1), repeat=2))
WORLDS = tuple(product(range(5), repeat=2))
QUERIES = tuple((axis, t) for axis in (0, 1) for t in range(1, 5))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utility(w, a, k):
    r, h = w
    e, v = a
    return e * (r - 1) + v * (1 - h) - k * (e != v)


class Planner:
    """States are row indexes. Targets are sets of acceptable actions.

    Queries are total binary tables with positive integer costs. Results are
    exact only for these supplied targets/questions, with no unknown worlds.
    """
    def __init__(self, targets, answers, costs):
        self.targets = tuple(frozenset(t) for t in targets)
        self.answers = tuple(tuple(row) for row in answers)
        self.costs = tuple(costs)
        require(bool(self.targets) and all(self.targets), 'nonempty target sets required')
        require(len(self.answers) == len(self.costs), 'cost/query mismatch')
        for row, cost in zip(self.answers, self.costs):
            require(len(row) == len(self.targets), 'incomplete query table')
            require(all(type(x) is int and x in (0, 1) for x in row), 'binary answers required')
            require(type(cost) is int and cost > 0, 'positive integer cost required')
        self._solve = lru_cache(None)(self._solve_uncached)

    def state(self, indexes):
        s = tuple(sorted(set(indexes)))
        require(bool(s), 'empty possible-world set')
        require(all(type(i) is int and 0 <= i < len(self.targets) for i in s), 'invalid world index')
        return s

    def common(self, state):
        result = set(self.targets[state[0]])
        for i in state[1:]:
            result.intersection_update(self.targets[i])
        return result

    def partition(self, state, q):
        return tuple(tuple(i for i in state if self.answers[q][i] == v) for v in (0, 1))

    def _solve_uncached(self, state):
        common = self.common(state)
        if common:
            return (0, -1, min(common))
        best = (float('inf'), -2, None)
        for q, cost in enumerate(self.costs):
            groups = self.partition(state, q)
            if not all(groups):
                continue
            total = cost + max(self._solve(g)[0] for g in groups)
            if total < best[0]:
                best = (total, q, None)
        return best

    def solve(self, indexes):
        return self._solve(self.state(indexes))

    def follow(self, indexes, observations):
        state = self.state(indexes)
        for q, value in observations:
            require(type(q) is int and 0 <= q < len(self.answers), 'invalid query')
            require(type(value) is int and value in (0, 1), 'unknown answer')
            state = self.state(i for i in state if self.answers[q][i] == value)
        return state

    def trace(self, indexes, actual):
        state = self.state(indexes)
        require(actual in state, 'actual world not admitted')
        cost, steps = 0, 0
        while True:
            _, q, action = self.solve(state)
            if q < 0:
                return {'action': action, 'cost': cost, 'steps': steps, 'remaining': len(state)}
            value = self.answers[q][actual]
            state = self.follow(state, [(q, value)])
            cost += self.costs[q]
            steps += 1

    def greedy(self, indexes):
        state = self.state(indexes)
        if self.common(state):
            return 0
        for q, cost in enumerate(self.costs):
            groups = self.partition(state, q)
            if all(groups):
                return cost + max(self.greedy(g) for g in groups)
        return float('inf')


def family(k, coupled):
    feasible = (0, 3) if coupled else tuple(range(4))
    targets = []
    for w in WORLDS:
        top = max(utility(w, ACTIONS[a], k) for a in feasible)
        targets.append({a for a in feasible if utility(w, ACTIONS[a], k) == top})
    answers = [tuple(int(w[axis] >= t) for w in WORLDS) for axis, t in QUERIES]
    return targets, answers


def brute_cost(targets, tables, costs, state):
    """Small-domain oracle: enumerate candidate query trees, without memoization."""
    if any(all(a in targets[i] for i in state) for a in set().union(*targets)):
        return 0
    totals = []
    for row, cost in zip(tables, costs):
        left = tuple(i for i in state if row[i] == 0)
        right = tuple(i for i in state if row[i] == 1)
        if left and right:
            totals.append(cost + max(brute_cost(targets, tables, costs, left),
                                     brute_cost(targets, tables, costs, right)))
    return min(totals, default=float('inf'))


def model_probe():
    policies, traces = [], []
    answers = family(0, False)[1]
    identity = Planner([{i} for i in range(25)], answers, [1] * 8)
    for k, coupled in product(range(5), (False, True)):
        targets, answers = family(k, coupled)
        planner = Planner(targets, answers, [1] * 8)
        initial = [('all', tuple(range(25)))]
        initial += [(f'difference={d}', tuple(i for i, (r, h) in enumerate(WORLDS) if r-h == d))
                    for d in range(-4, 5)]
        for label, state in initial:
            optimal = planner.solve(state)[0]
            fixed = planner.greedy(state)
            full = identity.solve(state)[0]
            require(optimal <= fixed and optimal <= full, 'domination failure')
            requires_question = not bool(planner.common(state))
            visits = []
            for actual in state:
                trace = planner.trace(state, actual)
                require(trace['action'] in targets[actual], 'wrong selected action')
                require(trace['cost'] <= optimal, 'cost bound failure')
                visits.append(trace['cost'])
                traces.append({'k': k, 'coupled': coupled, 'initial': label,
                               'world': list(WORLDS[actual]), **trace})
            require(max(visits) == optimal, 'unattained minimax cost')
            policies.append({'k': k, 'coupled': coupled, 'initial': label,
                             'world_count': len(state), 'minimax_cost': optimal,
                             'fixed_order_cost': fixed, 'world_identification_cost': full,
                             'no_query_status': 'UNRESOLVED' if requires_question else 'READY'})
    # Exhaust every 3-world binary target function and two binary query tables.
    oracles = 0
    for labels in product((0, 1), repeat=3):
        targets = [{a} for a in labels]
        for flat in product((0, 1), repeat=6):
            tables = (flat[:3], flat[3:])
            for costs in ((1, 1), (1, 2)):
                p = Planner(targets, tables, costs)
                require(p.solve((0, 1, 2))[0] == brute_cost(targets, tables, costs, (0, 1, 2)),
                        'independent tree oracle mismatch')
                oracles += 1
    # Pairwise compatibility does not establish a whole-group common action.
    triangle = [{0, 1}, {1, 2}, {0, 2}]
    p = Planner(triangle, [], [])
    require(all(set(a) & set(b) for a, b in combinations(triangle, 2)), 'bad counterexample')
    require(p.solve((0, 1, 2))[0] == float('inf'), 'unsafe pairwise merge')
    base = Planner([{0}, {1}], [(0, 1)], [1])
    duplicate = Planner([{0}, {1}, {0}], [(0, 1, 0)], [1])
    require(base.solve((0, 1))[0] == duplicate.solve((0, 1, 2))[0], 'duplication altered cost')
    rejected = []
    bad = [('empty input', lambda: base.solve(())),
           ('invalid index', lambda: base.solve((3,))),
           ('unknown answer', lambda: base.follow((0, 1), [(0, 2)])),
           ('contradictory observations', lambda: base.follow((0, 1), [(0, 0), (0, 1)])),
           ('negative query cost', lambda: Planner([{0}], [(0,)], [-1])),
           ('missing query answer', lambda: Planner([{0}, {1}], [(0,)], [1]))]
    for name, call in bad:
        try:
            call()
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('accepted invalid input: ' + name)
    # Reproduction of Pass 01's declared gains, independent of its source script.
    gain_counts = []
    for k in range(5):
        gains = [max(utility(w, a, k) for a in ACTIONS) - max(0, w[0]-w[1]) for w in WORLDS]
        gain_counts.append(sum(g > 0 for g in gains))
    require(gain_counts == [10, 4, 1, 0, 0], 'parent benchmark mismatch')
    return {'policies': policies, 'traces': traces, 'summary': {
        'initial_problems': len(policies), 'world_policy_traces': len(traces),
        'wrong_actions': 0, 'tiny_exhaustive_tree_oracles': oracles,
        'cheaper_than_fixed_order': sum(x['minimax_cost'] < x['fixed_order_cost'] for x in policies),
        'cheaper_than_world_identification': sum(x['minimax_cost'] < x['world_identification_cost'] for x in policies),
        'max_query_cost': max(x['minimax_cost'] for x in policies),
        'no_question_needed': sum(x['minimax_cost'] == 0 for x in policies),
        'pass01_strict_gain_counts': gain_counts,
        'pairwise_safe_but_jointly_empty_rejected': True,
        'duplicated_world_does_not_change_worst_case_cost': True,
        'invalid_inputs_rejected': rejected}}


def software_probe():
    episodes = []
    with tempfile.TemporaryDirectory(prefix='context-discovery-') as directory:
        path = str(Path(directory) / 'example.sqlite')
        a = sqlite3.connect(path, isolation_level=None, timeout=0)
        b = sqlite3.connect(path, isolation_level=None, timeout=0)
        try:
            require(a.execute('PRAGMA journal_mode=WAL').fetchone()[0] == 'wal', 'WAL unavailable')
            a.execute('CREATE TABLE example(value INTEGER)')
            a.execute('INSERT INTO example VALUES(0)')
            a.execute('BEGIN')
            before = a.execute('SELECT value FROM example').fetchone()[0]
            b.execute('BEGIN IMMEDIATE')
            b.execute('UPDATE example SET value=1')
            b.execute('COMMIT')
            old = [a.execute('SELECT value FROM example').fetchone()[0] for _ in range(3)]
            require(before == 0 and old == [0, 0, 0], 'snapshot mismatch')
            episodes.append({'id': 'SQL01', 'observation': old,
                             'consequence': 'Writer committed; repeated reads in old transaction retain zero.'})
            a.execute('COMMIT')
            a.execute('BEGIN')
            fresh = a.execute('SELECT value FROM example').fetchone()[0]
            require(fresh == 1, 'fresh snapshot missing commit')
            a.execute('COMMIT')
            episodes.append({'id': 'SQL02', 'observation': fresh,
                             'consequence': 'New read transaction sees committed value one.'})
            a.execute('BEGIN IMMEDIATE')
            try:
                b.execute('BEGIN IMMEDIATE')
            except sqlite3.OperationalError as exc:
                require(getattr(exc, 'sqlite_errorcode', None) == sqlite3.SQLITE_BUSY, 'unexpected writer failure')
                episodes.append({'id': 'SQL03', 'observation': 'SQLITE_BUSY',
                                 'consequence': 'Read/write separation does not permit two write transactions.'})
            else:
                raise AssertionError('second write transaction unexpectedly acquired')
            a.execute('ROLLBACK')
        finally:
            for connection in (a, b):
                if connection.in_transaction:
                    connection.rollback()
                connection.close()
    dictionary = b''.join(hashlib.sha256(str(i).encode('ascii')).digest() for i in range(32))
    payload = dictionary
    encoder = zlib.compressobj(level=9, zdict=dictionary)
    packed = encoder.compress(payload) + encoder.flush()
    decoder = zlib.decompressobj(zdict=dictionary)
    restored = decoder.decompress(packed) + decoder.flush()
    require(restored == payload and decoder.eof, 'dictionary roundtrip failed')
    episodes.append({'id': 'ZIP01', 'payload_bytes': len(payload), 'compressed_bytes': len(packed),
                     'dictionary_bytes': len(dictionary), 'standalone_bytes': len(packed)+len(dictionary),
                     'standalone_zlib_bytes': len(zlib.compress(payload, 9)),
                     'payload_sha256': sha(payload), 'consequence': 'Correct dictionary gives exact recovery.'})
    for label, kwargs in [('missing', {}), ('wrong', {'zdict': b'X' * 1024})]:
        try:
            d = zlib.decompressobj(**kwargs)
            d.decompress(packed)
        except zlib.error:
            episodes.append({'id': 'ZIP02' if label == 'missing' else 'ZIP03',
                             'observation': label + '_dictionary_rejected',
                             'consequence': 'The payload alone does not satisfy reconstruction.'})
        else:
            raise AssertionError('invalid dictionary accepted')
    return {'sqlite_version': sqlite3.sqlite_version, 'zlib_runtime': zlib.ZLIB_RUNTIME_VERSION,
            'execution': 'local temporary data; serially interleaved connections, not a race/stress test',
            'episodes': episodes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent/'results')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    model = model_probe()
    outputs = {'results.json': model['summary'], 'policies.json': model['policies'],
               'traces.json': model['traces'], 'software.json': software_probe()}
    for name, value in outputs.items():
        (args.out/name).write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps({'model': model['summary'], 'software': outputs['software.json']}, indent=2))


if __name__ == '__main__':
    main()

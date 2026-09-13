"""Exact rational linear-span diagnostics, not a geometric Hodge oracle."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def scalar(x):
    if isinstance(x, bool) or not isinstance(x, (int, str)):
        raise ValueError('Use exact integers or rational strings, never JSON floats')
    if isinstance(x, str) and (len(x) > 100 or not x):
        raise ValueError('Invalid or oversized scalar')
    f = Fraction(x)
    if max(f.numerator.bit_length(), f.denominator.bit_length()) > 256:
        raise ValueError('Scalar exceeds 256-bit input limit')
    return f


def rref(rows, width):
    a = [list(r) for r in rows]
    pivots = []
    for col in range(width):
        i = next((i for i in range(len(pivots), len(a)) if a[i][col]), None)
        if i is None:
            continue
        p = len(pivots)
        a[p], a[i] = a[i], a[p]
        v = a[p][col]
        a[p] = [x / v for x in a[p]]
        for j in range(len(a)):
            if j != p:
                v = a[j][col]
                a[j] = [x - v*y for x, y in zip(a[j], a[p])]
        pivots.append(col)
        if len(pivots) == len(a):
            break
    return a, pivots


def nullspace(rows, width):
    a, pivots = rref(rows, width)
    out = []
    for free in sorted(set(range(width)) - set(pivots)):
        v = [Fraction(0)] * width
        v[free] = Fraction(1)
        for i, col in enumerate(pivots):
            v[col] = -a[i][free]
        out.append(v)
    return out


def dot(a, b):
    return sum((x*y for x, y in zip(a, b)), Fraction(0))


def analyze(data):
    if not isinstance(data, dict):
        raise ValueError('Expected a JSON object')
    if data.get('schema') != 'hodge-span/v1':
        raise ValueError('Unknown schema')
    n = data.get('ambient_dimension')
    if type(n) is not int or not 1 <= n <= 32:
        raise ValueError('Ambient dimension must be 1..32')
    if not isinstance(data.get('basis'), str) or not data['basis'].strip():
        raise ValueError('An explicit common basis description is required')
    def vectors(key):
        raw = data.get(key)
        if not isinstance(raw, list) or len(raw) > 64:
            raise ValueError('At most 64 vectors per list')
        if any(not isinstance(v, list) or len(v) != n for v in raw):
            raise ValueError('Vector dimensions disagree')
        return [[scalar(x) for x in v] for v in raw]
    cycles, targets = vectors('cycle_vectors'), vectors('target_vectors')
    reduced, pivots = rref(cycles, n)
    rank = len(pivots)
    annihilators = nullspace(cycles, n)
    missing = []
    for i, target in enumerate(targets):
        residual = target[:]
        for j, col in enumerate(pivots):
            f = residual[col]
            residual = [x-f*y for x, y in zip(residual, reduced[j])]
        if any(residual):
            witness = next(w for w in annihilators if dot(w, target))
            assert all(dot(witness, v) == 0 for v in cycles)
            assert dot(witness, target) != 0
            missing.append({'target_index': i, 'annihilating_covector': list(map(str, witness)),
                            'target_pairing': str(dot(witness, target))})
    trank = len(rref(targets, n)[1])
    urank = len(rref(cycles + targets, n)[1])
    return {'schema': 'hodge-span-result/v1', 'coefficient_domain': 'Q',
            'cycle_count': len(cycles), 'cycle_rank': rank, 'target_rank': trank,
            'target_directions_outside_supplied_cycle_span': urank-rank,
            'target_span_contained': not missing, 'separation_certificates': missing,
            'claim_ceiling': 'Only the supplied rational vectors in the declared common basis. '
            'No authentication of algebraic cycles, rational Hodge targets, basis completeness, '
            'integral saturation, geometry or the general Hodge conjecture.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    args = p.parse_args()
    try:
        raw = args.input.read_bytes()
        if len(raw) > 1_000_000:
            raise ValueError('Input exceeds 1 MB')
        out = analyze(json.loads(raw))
        out['input_sha256'] = hashlib.sha256(raw).hexdigest()
        print(json.dumps(out, indent=2))
    except (ValueError, TypeError, KeyError, ZeroDivisionError, OSError) as e:
        p.exit(2, f'Invalid input: {e}\n')


if __name__ == '__main__':
    main()

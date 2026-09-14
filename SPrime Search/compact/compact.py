#!/usr/bin/env python3
"""D1: strictly versioned, <=8-byte NAND register programs and context queries."""
from __future__ import annotations
import argparse
from copy import deepcopy
from functools import lru_cache
import json

LEAVES = {'x': 240, 'y': 204, 'z': 170}
MAX_GATES = 6
TOTALS = [3]
for _k in range(1, MAX_GATES+1):
    _n = 1
    for _j in range(_k):
        _n *= (3+_j)**2
    TOTALS.append(_n)
TOTAL = sum(TOTALS)
QUERY_CACHE_LIMIT = 128


def integer(v: int, lo: int, hi: int, label: str) -> None:
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(f'{label} must be an integer in {lo}..{hi}')


def instructions(word: str) -> tuple[str | None, tuple[tuple[int,int], ...]]:
    if type(word) is not str or not 3 <= len(word) <= 8 or not word.startswith('D1'):
        raise ValueError('expected an exact 3..8 character D1 word')
    if len(word) == 3 and word[2] in LEAVES:
        return word[2], ()
    result = []
    for j, token in enumerate(word[2:]):
        v = ord(token)-32
        if not 0 <= v < 64:
            raise ValueError('instruction outside ASCII 0x20..0x5f')
        a, b = divmod(v, 8)
        if a >= 3+j or b >= 3+j:
            raise ValueError('forward or absent register reference')
        result.append((a,b))
    return None, tuple(result)


def evaluate(word: str) -> int:
    terminal, ops = instructions(word)
    if terminal is not None:
        return LEAVES[terminal]
    regs = list(LEAVES.values())
    for a,b in ops:
        regs.append(255 ^ (regs[a] & regs[b]))
    return regs[-1]


def evaluate_row(word: str, row: int) -> int:
    integer(row,0,7,'input row')
    terminal, ops = instructions(word)
    # A row-at-a-time path, rather than extracting a bit of evaluate().
    regs = [bool(row & 4), bool(row & 2), bool(row & 1)]
    if terminal is not None:
        return int(regs['xyz'.index(terminal)])
    for a,b in ops:
        regs.append(not(regs[a] and regs[b]))
    return int(regs[-1])


def expand_tree(word: str) -> str:
    """Preserve behavior, not byte size: repeat every referenced subtree."""
    terminal, ops = instructions(word)
    if terminal is not None:
        return terminal
    regs = list(LEAVES)
    for a,b in ops:
        regs.append('N'+regs[a]+regs[b])
    return regs[-1]


def rank(word: str) -> int:
    """Length then legal ordered register choices; exact integer address."""
    terminal, ops = instructions(word)
    if terminal is not None:
        return 'xyz'.index(terminal)
    value = 0
    for j,(a,b) in enumerate(ops):
        n = 3+j
        value = value*n*n + a*n+b
    return sum(TOTALS[:len(ops)]) + value


def unrank(index: int) -> str:
    integer(index,0,TOTAL-1,'rank')
    if index < 3:
        return 'D1'+'xyz'[index]
    for gates in range(1,7):
        offset = sum(TOTALS[:gates])
        if index < offset+TOTALS[gates]:
            value = index-offset
            pairs = []
            for j in range(gates-1,-1,-1):
                n = 3+j
                value, digit = divmod(value,n*n)
                pairs.append(divmod(digit,n))
            return 'D1'+''.join(chr(32+8*a+b) for a,b in reversed(pairs))
    raise RuntimeError('rank escaped bounded domain')


def candidates(labels: dict[int,int]) -> tuple[int,...]:
    if type(labels) is not dict:
        raise ValueError('labels must map row indexes to binary required outputs')
    for row,value in labels.items():
        integer(row,0,7,'row'); integer(value,0,1,'required output')
    return tuple(f for f in range(256) if all((f >> r)&1 == v for r,v in labels.items()))


def _validate_tables(tables: tuple[int,...]) -> None:
    # Validate before memo lookup: bool/int and float/int tuples compare equal
    # as Python cache keys. A warm cache must not bypass the exact-type rule.
    if type(tables) is not tuple or not tables:
        raise ValueError('expected a nonempty sorted tuple of distinct behaviors')
    for table in tables:
        integer(table,0,255,'behavior')
    if tuple(sorted(set(tables))) != tables:
        raise ValueError('expected a nonempty sorted tuple of distinct behaviors')


@lru_cache(maxsize=QUERY_CACHE_LIMIT)
def _plan_cached(tables: tuple[int,...]) -> dict:
    """Unit-cost exact output-oracle questions; unknown answers stay unknown.

    This is a proposed specification query, not an oracle that supplies answers.
    Histories, probabilities and encoding multiplicities are deliberately absent.
    """
    # One compilation can visit at most 3**8 row restrictions. Retain this memo
    # only for the build, so bounded inter-request eviction cannot cause the
    # build to repeatedly recompute its own subproblems.
    memo = {}
    def build(state):
        if state in memo:
            return memo[state]
        if len(state) == 1:
            best = {'questions': 0, 'table': state[0]}
        else:
            best = None
            for row in range(8):
                groups = tuple(tuple(f for f in state if (f >> row)&1 == bit) for bit in (0,1))
                if not all(groups):
                    continue
                children = [build(group) for group in groups]
                candidate = {'questions': 1+max(c['questions'] for c in children),
                             'row': row, 'answers': children}
                if best is None or candidate['questions'] < best['questions']:
                    best = candidate
            if best is None:
                raise RuntimeError('distinct truth tables were not distinguishable')
        memo[state] = best
        return best
    try:
        return build(tables)
    finally:
        memo.clear()


def query_plan(tables: tuple[int,...]) -> dict:
    """Compile this exact semantic state before use; return an isolated plan."""
    _validate_tables(tables)
    return deepcopy(_plan_cached(tables))


def query_cache_info():
    """Return retained-plan counts and cache hits/misses, not byte/heap usage."""
    return _plan_cached.cache_info()


def clear_query_cache() -> None:
    """Release retained plans; caller-owned plans survive. No GC/RSS guarantee."""
    _plan_cached.cache_clear()


def refine(tables: tuple[int,...], row: int, answer: int | None) -> tuple[int,...]:
    _validate_tables(tables)
    integer(row,0,7,'row')
    if answer is None:
        return tables
    integer(answer,0,1,'answer')
    new = tuple(f for f in tables if (f >> row)&1 == answer)
    if not new:
        raise ValueError('answer conflicts with the admitted specification')
    return new


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hex', help='Exact UTF-8 word bytes in hex; avoids shell quoting issues.')
    parser.add_argument('--rank', type=int, help='Generate a word by its bounded global rank.')
    args = parser.parse_args()
    if args.hex is not None:
        word = bytes.fromhex(args.hex).decode('utf-8','strict')
    elif args.rank is not None:
        word = unrank(args.rank)
    else:
        word = 'D1"#3E'
    print(json.dumps({'word':word,'hex':word.encode().hex(),'rank':rank(word),
                      'bytes':len(word.encode()), 'table':hex(evaluate(word)),
                      'expanded_tree':expand_tree(word)},indent=2))

if __name__ == '__main__':
    main()

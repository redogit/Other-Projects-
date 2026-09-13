#!/usr/bin/env python3
"""Exact behavior-indexed NAND expression census; no generated Python execution."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from math import comb
from pathlib import Path
import struct
import sys

MAX_BYTES = 1024
TABLE_MASK = 255
LEAVES = {'x': 240, 'y': 204, 'z': 170}
PAIRS = tuple(tuple((a, b) for a in range(256) for b in range(256)
                    if (255 ^ (a & b)) == f) for f in range(256))
DEPENDENCY_SHA = 'a2fd74aff787b4d47aa10d8c580bba4db9d8b96e0a487746a6166692031e6f85'
# Explicit small English onset fixture, not a downloaded pronunciation corpus.
ONSETS = {'sun': 'S', 'sea': 'S', 'city': 'S', 'cat': 'K', 'car': 'K',
          'phone': 'F', 'fun': 'F', 'fish': 'F'}


def check_int(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def zeta(values, inverse=False):
    """Upper-set transform on the eight output-row bits."""
    require(len(values) == 256, 'expected 256 values')
    out = list(values)
    for bit in (1, 2, 4, 8, 16, 32, 64, 128):
        for start in range(0, 256, 2 * bit):
            for i in range(start, start + bit):
                if inverse:
                    out[i] -= out[i + bit]
                else:
                    out[i] += out[i + bit]
    return out


def parse(text):
    """Return (node_count, behavior, children) using a nonrecursive stack."""
    require(type(text) is str and 1 <= len(text) <= MAX_BYTES, 'invalid expression length')
    stack = []
    for token in reversed(text):
        if token in LEAVES:
            stack.append((0, LEAVES[token], None))
        elif token == 'N' and len(stack) >= 2:
            left, right = stack.pop(), stack.pop()
            stack.append((1 + left[0] + right[0], 255 ^ (left[1] & right[1]), (left, right)))
        else:
            raise ValueError('outside declared NAND grammar')
    require(len(stack) == 1, 'not exactly one complete expression')
    return stack[0]


def scalar_eval(text, row):
    """Independent row-at-a-time interpreter; no bit-table evaluation."""
    check_int(row, 0, 7, 'row')
    stack = []
    assignment = {'x': bool(row & 4), 'y': bool(row & 2), 'z': bool(row & 1)}
    for token in reversed(text):
        if token in assignment:
            stack.append(assignment[token])
        elif token == 'N' and len(stack) >= 2:
            a, b = stack.pop(), stack.pop()
            stack.append(not (a and b))
        else:
            raise ValueError('outside declared NAND grammar')
    require(len(stack) == 1, 'incomplete expression')
    return int(stack[0])


def accepted_tables(baseline=240, protected=0x55, required=0x82, values=0x02):
    for name, v in zip(('baseline', 'protected', 'required', 'values'),
                       (baseline, protected, required, values)):
        check_int(v, 0, 255, name)
    return tuple(f for f in range(256)
                 if not ((f ^ baseline) & protected) and not ((f ^ values) & required))


class Census:
    """Count by internal-node count and truth table, with exact witness access."""
    def __init__(self, max_bytes=1024):
        check_int(max_bytes, 1, MAX_BYTES, 'max_bytes')
        self.max_bytes = max_bytes
        self.max_nodes = (max_bytes - 1) // 2
        initial = [0] * 256
        for f in LEAVES.values():
            initial[f] += 1
        self.counts = [initial]
        self._pair_cache = {}
        self.supports = [sum(1 << f for f,v in enumerate(initial) if v)]
        transformed = [zeta(initial)]
        for k in range(1, self.max_nodes + 1):
            product_sum = [0] * 256
            # Symmetry halves the sum; the factor restores both ordered splits.
            for i in range((k - 1) // 2 + 1):
                j = k - 1 - i
                left, right = transformed[i], transformed[j]
                factor = 1 if i == j else 2
                for mask in range(256):
                    product_sum[mask] += factor * left[mask] * right[mask]
            by_and = zeta(product_sum, inverse=True)
            row = by_and[::-1]  # Complement the eight-bit output for NAND.
            require(min(row) >= 0, 'negative count')
            expected = comb(2 * k, k) // (k + 1) * 3 ** (k + 1)
            require(sum(row) == expected, 'Catalan identity mismatch')
            self.counts.append(row)
            self.supports.append(sum(1 << f for f,v in enumerate(row) if v))
            transformed.append(zeta(row))

    def _pairs(self, left_k, right_k, table):
        left, right = self.counts[left_k], self.counts[right_k]
        key = (self.supports[left_k], self.supports[right_k], table)
        if key not in self._pair_cache:
            self._pair_cache[key] = tuple((a,b) for a,b in PAIRS[table] if left[a] and right[b])
        return self._pair_cache[key]

    def histogram(self, byte_limit=None):
        limit = self.max_bytes if byte_limit is None else byte_limit
        check_int(limit, 1, self.max_bytes, 'byte_limit')
        return [sum(row[f] for row in self.counts[:(limit - 1)//2 + 1]) for f in range(256)]

    def count(self, byte_length, table):
        check_int(byte_length, 1, self.max_bytes, 'byte_length')
        check_int(table, 0, 255, 'table')
        return self.counts[(byte_length - 1)//2][table] if byte_length % 2 else 0

    def shortest(self, table):
        check_int(table, 0, 255, 'table')
        for k, row in enumerate(self.counts):
            if row[table]:
                return self._unrank(k, table, 0)
        return None

    def unrank(self, byte_length, table, rank):
        count = self.count(byte_length, table)
        check_int(rank, 0, count - 1, 'rank')
        return self._unrank((byte_length - 1)//2, table, rank)

    def _unrank(self, k, table, rank):
        if k == 0:
            return tuple(token for token, f in LEAVES.items() if f == table)[rank]
        reverse = rank > (self.counts[k][table] - 1)//2
        remaining = self.counts[k][table] - 1 - rank if reverse else rank
        for left_k in (range(k-1, -1, -1) if reverse else range(k)):
            right_k = k - 1 - left_k
            left, right = self.counts[left_k], self.counts[right_k]
            pairs = self._pairs(left_k, right_k, table)
            for a, b in (reversed(pairs) if reverse else pairs):
                block = left[a] * right[b]
                if remaining >= block:
                    remaining -= block
                else:
                    local = block - 1 - remaining if reverse else remaining
                    ar, br = divmod(local, right[b])
                    return 'N' + self._unrank(left_k, a, ar) + self._unrank(right_k, b, br)
        raise RuntimeError('unrank escaped exact count')

    def rank(self, text):
        require(len(text) <= self.max_bytes, 'expression outside census bound')
        node = parse(text)
        return self._rank_node(node)

    def _rank_node(self, node):
        k, table, children = node
        if k == 0:
            return 0  # All declared terminals have different behavior.
        left_node, right_node = children
        lk, a = left_node[:2]
        rk, b = right_node[:2]
        reverse = lk > (k-1)//2
        outside = 0
        for i in (range(k-1, lk-1, -1) if reverse else range(lk+1)):
            j = k - 1 - i
            left, right = self.counts[i], self.counts[j]
            pairs = self._pairs(i, j, table)
            for aa, bb in (reversed(pairs) if reverse else pairs):
                block = left[aa] * right[bb]
                if i == lk and aa == a and bb == b:
                    prefix = self.counts[k][table] - outside - block if reverse else outside
                    return prefix + self._rank_node(left_node)*right[b] + self._rank_node(right_node)
                outside += block
        raise RuntimeError('rank escaped valid parse')


def load_transport():
    path = Path(__file__).resolve().parent.parent / 'S1024 Compression Lab' / 'sections1024.py'
    require(path.is_file(), 'missing sibling S1024 dependency')
    require(hashlib.sha256(path.read_bytes()).hexdigest() == DEPENDENCY_SHA,
            'dependency changed: revalidate before updating the source lock')
    spec = importlib.util.spec_from_file_location('sprime_pinned_transport', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def word_to_float(text, transport):
    data = text.encode('utf-8')
    require(len(data) <= 8, 'more than eight UTF-8 bytes needs a different carrier')
    space = transport.UTF8Space(8)
    rank = sum(space.completions[n][0] for n in range(len(data))) + space.rank(data)
    bits = (1 << 52) + rank
    return struct.unpack('>d', bits.to_bytes(8, 'big'))[0]


def float_to_word(value, transport):
    require(type(value) is float, 'expected a float carrier')
    rank = int.from_bytes(struct.pack('>d', value), 'big') - (1 << 52)
    space = transport.UTF8Space(8)
    require(0 <= rank < sum(row[0] for row in space.completions), 'outside word carrier domain')
    for n in range(9):
        size = space.completions[n][0]
        if rank < size:
            return space.unrank(n, rank).decode('utf-8')
        rank -= size
    raise RuntimeError('word carrier escaped its range')


def alliteration(text):
    """None = outside small lexicon; False does not mean false content."""
    if type(text) is not str:
        raise ValueError('expected text')
    words = text.split(' ')
    if len(words) < 2 or any(word not in ONSETS for word in words):
        return None
    return len({ONSETS[word] for word in words}) == 1


def word_sequences(max_bytes=1024):
    """Exact >=2-token sequences by bytes, with/without the onset constraint."""
    check_int(max_bytes, 1, 1024, 'max_bytes')
    def count(words):
        totals = [0] * (max_bytes + 1)
        singles = [0] * (max_bytes + 1)
        for word in words:
            if len(word) <= max_bytes:
                singles[len(word)] += 1
        for n in range(max_bytes + 1):
            totals[n] = singles[n]
            for word in words:
                previous = n - len(word) - 1
                if previous >= 1:
                    totals[n] += totals[previous]
        return [a-b for a, b in zip(totals, singles)]
    raw = count(tuple(ONSETS))
    groups = [count(tuple(w for w, p in ONSETS.items() if p == onset))
              for onset in sorted(set(ONSETS.values()))]
    sound = [sum(row[n] for row in groups) for n in range(max_bytes + 1)]
    return {'all_sequences_by_length': raw, 'same_onset_by_length': sound}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-bytes', type=int, default=1024)
    parser.add_argument('--table', type=lambda s: int(s, 0), default=0x5a)
    parser.add_argument('--length', type=int)
    parser.add_argument('--rank', type=int, default=0)
    args = parser.parse_args()
    census = Census(args.max_bytes)
    if args.length is not None:
        text = census.unrank(args.length, args.table, args.rank)
        print(json.dumps({'text': text, 'table': args.table, 'rank': str(census.rank(text))}))
    else:
        hist = census.histogram()
        good = accepted_tables()
        print(json.dumps({'programs': str(sum(hist)), 'behaviors': sum(bool(x) for x in hist),
                          'accepted_programs': str(sum(hist[f] for f in good)),
                          'accepted_behaviors': [{'table': f, 'witness': census.shortest(f)}
                                                 for f in good if hist[f]]}, indent=2))


if __name__ == '__main__':
    main()

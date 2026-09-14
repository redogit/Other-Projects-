#!/usr/bin/env python3
"""Independent grammar oracle and adversarial byte-carrier boundary checks."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import struct
import d2


def legal(word):
    # Direct grammar specification; does not call production parser/ranker.
    if type(word) is not bytes or word[:2] != b'D2':
        return False
    payload = word[2:]
    if payload in (b'x', b'y', b'z'):
        return True
    if not 1 <= len(payload) <= 5:
        return False
    for position, byte in enumerate(payload):
        if byte >= 128:
            return False
        left = (byte // 8) % 8
        right = byte % 8
        if left >= position + 3 or right >= position + 3:
            return False
    return True


def scalar_table(word):
    value = 0
    for row in range(8):
        registers = [row // 4 % 2, row // 2 % 2, row % 2]
        payload = word[2:]
        if payload in (b'x', b'y', b'z'):
            bit = registers[b'xyz'.index(payload)]
        else:
            for byte in payload:
                a, b = registers[(byte // 8) % 8], registers[byte % 8]
                registers.append((1 - a*b) if byte < 64 else (a+b) % 2)
            bit = registers[-1]
        value += bit * (2 ** row)
    return value


def rejects(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('invalid input accepted')


def check_word(word):
    if not legal(word):
        for action in (d2.instructions, d2.decode, d2.rank, d2.to_float,
                       lambda w: d2.eval_row(w, 0)):
            rejects(lambda: action(word))
        return False
    assert d2.unrank(d2.rank(word)) == word
    assert d2.from_float(d2.to_float(word)) == word
    assert d2.decode(word)[0] == scalar_table(word)
    assert sum(d2.eval_row(word, r) << r for r in range(8)) == scalar_table(word)
    assert d2.unrank(d2.rank(bytearray(word))) == word
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / 'results.json'
    if target.exists():
        raise FileExistsError('use a fresh output directory')
    counts = {'raw_payloads': 0, 'legal_raw_payloads': 0,
              'canonical_rank_checks': 0, 'high_bit_mutations': 0}
    for size in (1, 2):
        for payload in itertools.product(range(256), repeat=size):
            counts['raw_payloads'] += 1
            counts['legal_raw_payloads'] += check_word(b'D2' + bytes(payload))
    assert counts['raw_payloads'] == 65792
    assert counts['legal_raw_payloads'] == 597
    # Every canonical word through three operations, then seeded longer words.
    short_total = 3 + 18 + 576 + 28800
    rng = random.Random(854322)
    ranks = list(range(short_total))
    ranks += [rng.randrange(short_total, d2.TOTAL) for _ in range(2048)]
    offsets = [sum(d2.DEPTH_TOTALS[:k]) for k in range(1, 6)]
    ranks += [v for k, start in enumerate(offsets, 1)
              for v in (start, start + d2.DEPTH_TOTALS[k] - 1)]
    for index in ranks:
        word = d2.unrank(index)
        assert check_word(word) and d2.rank(word) == index
        counts['canonical_rank_checks'] += 1
    for index in ranks[-2058:]:
        word = d2.unrank(index)
        for pos in range(2, len(word)):
            altered = word[:pos] + bytes([word[pos] | 128]) + word[pos+1:]
            assert not check_word(altered)
            counts['high_bit_mutations'] += 1
    for word in (b'', b'D2', b'D1x', b'D2' + bytes(6), b'D2xx', b'D2\x80'):
        assert not check_word(word)
    for bad in (True, False, -1, d2.TOTAL, 1.0, '3', None):
        rejects(lambda: d2.unrank(bad))
    for bad in (True, 1, float('nan'), float('inf'), -1.0, 0.0, 2.0):
        rejects(lambda: d2.from_float(bad))
    outside = struct.unpack('>d', ((1023 << 52) | d2.TOTAL).to_bytes(8, 'big'))[0]
    rejects(lambda: d2.from_float(outside))
    root = Path(__file__).resolve().parent
    result = {'status': 'PASS', 'seed': 854322, **counts,
              'historical_counterexample': {'input': '443280', 'old_roundtrip': '443200',
                                           'current': 'rejected'},
              'source_sha256': {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
                                for name in ('d2.py', 'audit_boundary.py')},
              'scope': 'Exact grammar through two payload bytes; all canonical ranks through three operations; sampled longer words. No universal empirical coverage claim.'}
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Exact 1,024-byte section carriers, UTF-8 indexing, and bounded bit repair.

Python 3.10+, standard library. No execution of generated text. All indices are
exact integers. Float values are carriers, not numbers for arithmetic.

The 62-bit carrier is a NEW transport, not wire-compatible with UTF8WordCodec.
UTF-8 rank/unrank requires a complete string; stream sections may instead carry
partial code points, validated through the preserved boundary state.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import zlib

SECTION_BYTES = 1024
SECTION_BITS = 8 * SECTION_BYTES
CARRIER_BITS = 62
CARRIER_BASE = 1 << 52
CARRIER_LIMIT = CARRIER_BASE + (1 << CARRIER_BITS)
VERSION = 'SP1024-1'

# Byte-state validator for strict UTF-8 (RFC 3629); same state numbering as parent.
# 0=complete, 1..3=remaining continuations, 4..7=restricted first continuation,
# 8=invalid. Complete Unicode scalar encodings only; no normalization.
def transition(state: int, b: int) -> int:
    if state == 0:
        if b < 0x80: return 0
        if 0xc2 <= b <= 0xdf: return 1
        if b == 0xe0: return 4
        if 0xe1 <= b <= 0xec or 0xee <= b <= 0xef: return 2
        if b == 0xed: return 5
        if b == 0xf0: return 6
        if 0xf1 <= b <= 0xf3: return 3
        if b == 0xf4: return 7
        return 8
    if state in (1, 2, 3):
        return state - 1 if 0x80 <= b <= 0xbf else 8
    if state == 4: return 1 if 0xa0 <= b <= 0xbf else 8
    if state == 5: return 1 if 0x80 <= b <= 0x9f else 8
    if state == 6: return 2 if 0x90 <= b <= 0xbf else 8
    if state == 7: return 2 if 0x80 <= b <= 0x8f else 8
    return 8

TABLE = tuple(tuple(transition(s, b) for b in range(256)) for s in range(9))
WEIGHTS = tuple(Counter(row) for row in TABLE)

def _runs(row: tuple[int, ...]) -> tuple[tuple[int, int, int], ...]:
    result = []
    start = 0
    for i in range(1, 257):
        if i == 256 or row[i] != row[start]:
            result.append((start, i - 1, row[start]))
            start = i
    return tuple(result)

RUNS = tuple(_runs(row) for row in TABLE)

def check_int(value: int, low: int, high: int, label: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{label} must be an integer in {low}..{high}')

def scan(data: bytes, start: int = 0) -> int:
    check_int(start, 0, 8, 'start state')
    for b in data:
        start = TABLE[start][b]
    return start

class UTF8Space:
    """Exact-length byte-lexicographic rank/unrank for 0..1,024 bytes.

    Suffix counts represent every accepted string, not just tested examples.
    Ranking uses integer branch counts, not content hashes or semantic scores.
    """
    def __init__(self, max_bytes: int = SECTION_BYTES):
        check_int(max_bytes, 0, SECTION_BYTES, 'max_bytes')
        self.max_bytes = max_bytes
        self.completions = [[int(s == 0) for s in range(9)]]
        for _ in range(max_bytes):
            old = self.completions[-1]
            self.completions.append([
                sum(weight * old[dest] for dest, weight in WEIGHTS[s].items())
                for s in range(9)
            ])

    def count(self, n: int) -> int:
        check_int(n, 0, self.max_bytes, 'length')
        return self.completions[n][0]

    def rank(self, data: bytes) -> int:
        if not isinstance(data, bytes): raise TypeError('data must be bytes')
        n = len(data)
        check_int(n, 0, self.max_bytes, 'length')
        if scan(data) != 0: raise ValueError('not complete strict UTF-8')
        rank, state = 0, 0
        for i, byte in enumerate(data):
            c = self.completions[n - i - 1]
            for lo, hi, dest in RUNS[state]:
                if lo >= byte: break
                rank += (min(hi + 1, byte) - lo) * c[dest]
            state = TABLE[state][byte]
        return rank

    def unrank(self, n: int, rank: int) -> bytes:
        check_int(n, 0, self.max_bytes, 'length')
        check_int(rank, 0, self.count(n) - 1, 'rank')
        result = bytearray()
        state = 0
        for i in range(n):
            c = self.completions[n - i - 1]
            for lo, hi, dest in RUNS[state]:
                size = (hi - lo + 1) * c[dest]
                if rank < size:
                    offset, rank = divmod(rank, c[dest])
                    result.append(lo + offset)
                    state = dest
                    break
                rank -= size
            else:
                raise AssertionError('empty unrank branch')
        if state != 0 or rank != 0: raise AssertionError('unrank terminal invariant')
        return bytes(result)

    def census(self, n: int) -> dict[str, int]:
        check_int(n, 0, self.max_bytes, 'length')
        v = [1] + [0] * 8
        for _ in range(n):
            nxt = [0] * 9
            for s, count in enumerate(v):
                for dest, weight in WEIGHTS[s].items():
                    nxt[dest] += count * weight
            v = nxt
        return {'complete': v[0], 'incomplete_extendable': sum(v[1:8]),
                'invalid': v[8], 'raw_total': 1 << (8 * n)}

# Ordered low-significance-first 62-bit limbs. Each limb is embedded into the
# contiguous positive-normal binary64 bit range [BASE, BASE+2^62).
# It is an injection into normal finite values, not IEEE integer conversion.
def pack_floats(data: bytes) -> list[float]:
    if not isinstance(data, bytes): raise TypeError('data must be bytes')
    if len(data) > SECTION_BYTES: raise ValueError('section exceeds 1,024 bytes')
    value = int.from_bytes(data, 'big')
    count = (len(data) * 8 + CARRIER_BITS - 1) // CARRIER_BITS
    result = []
    for _ in range(count):
        bits = CARRIER_BASE + (value & ((1 << CARRIER_BITS) - 1))
        result.append(struct.unpack('>d', bits.to_bytes(8, 'big'))[0])
        value >>= CARRIER_BITS
    return result


def unpack_floats(words: list[float], byte_length: int) -> bytes:
    check_int(byte_length, 0, SECTION_BYTES, 'byte_length')
    expected = (byte_length * 8 + CARRIER_BITS - 1) // CARRIER_BITS
    if len(words) != expected: raise ValueError('wrong float count')
    value = 0
    for i, word in enumerate(words):
        if type(word) is not float: raise TypeError('carrier must be float')
        bits = int.from_bytes(struct.pack('>d', word), 'big')
        if not CARRIER_BASE <= bits < CARRIER_LIMIT:
            raise ValueError('float outside versioned carrier range')
        value |= (bits - CARRIER_BASE) << (CARRIER_BITS * i)
    if value.bit_length() > byte_length * 8:
        raise ValueError('nonzero unused final-limb bits')
    return value.to_bytes(byte_length, 'big')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def frame(data: bytes, utf8: bool = True) -> dict:
    """Exact 1,024-byte cuts. The final section may be shorter; empty has none.

    A section is not assumed to be a complete UTF-8 string. Its entering/exiting
    validator states are checked during reconstruction. SHA-256 is an integrity
    check under its usual assumption, not authentication or semantic truth.
    """
    if not isinstance(data, bytes): raise TypeError('data must be bytes')
    if type(utf8) is not bool: raise TypeError('utf8 flag must be boolean')
    if utf8: data.decode('utf-8', 'strict')
    records, state = [], 0
    for offset in range(0, len(data), SECTION_BYTES):
        block = data[offset:offset + SECTION_BYTES]
        end = scan(block, state) if utf8 else None
        records.append({'index': len(records), 'byte_offset': offset,
                        'byte_length': len(block), 'sha256': sha(block),
                        'utf8_state_in': state if utf8 else None,
                        'utf8_state_out': end,
                        'float_hex': [x.hex() for x in pack_floats(block)]})
        if utf8: state = end
    if utf8 and state != 0: raise ValueError('stream ends inside a scalar')
    return {'format': VERSION, 'section_bytes': SECTION_BYTES,
            'transport': 'binary64-positive-normal-62bit-limbs-lsf',
            'utf8': utf8, 'total_bytes': len(data), 'sha256': sha(data),
            'sections': records}


def unframe(record: dict, max_total_bytes: int = 64 * 1024 * 1024) -> bytes:
    """Strict local format and allocation cap; no silent unknown-field parsing."""
    if not isinstance(record, dict) or set(record) != {
        'format', 'section_bytes', 'transport', 'utf8', 'total_bytes', 'sha256', 'sections'
    }: raise ValueError('wrong frame fields')
    if (record['format'] != VERSION or record['section_bytes'] != SECTION_BYTES
        or record['transport'] != 'binary64-positive-normal-62bit-limbs-lsf'):
        raise ValueError('unsupported frame format')
    if type(record['utf8']) is not bool: raise ValueError('wrong UTF-8 mode')
    check_int(record['total_bytes'], 0, max_total_bytes, 'total_bytes')
    count = (record['total_bytes'] + SECTION_BYTES - 1) // SECTION_BYTES
    if not isinstance(record['sections'], list) or len(record['sections']) != count:
        raise ValueError('wrong section count')
    data, state = bytearray(), 0
    keys = {'index', 'byte_offset', 'byte_length', 'sha256', 'utf8_state_in',
            'utf8_state_out', 'float_hex'}
    for i, section in enumerate(record['sections']):
        if not isinstance(section, dict) or set(section) != keys:
            raise ValueError('wrong section fields')
        expected_len = min(SECTION_BYTES, record['total_bytes'] - len(data))
        for key, expected in [('index', i), ('byte_offset', len(data)), ('byte_length', expected_len)]:
            if type(section[key]) is not int or section[key] != expected:
                raise ValueError(f'wrong {key}')
        hx = section['float_hex']
        if not isinstance(hx, list) or not all(isinstance(x, str) for x in hx):
            raise ValueError('wrong float_hex field')
        words = [float.fromhex(x) for x in hx]
        if any(w.hex() != text for w, text in zip(words, hx)):
            raise ValueError('noncanonical float hex')
        block = unpack_floats(words, expected_len)
        if sha(block) != section['sha256']: raise ValueError('section checksum mismatch')
        if record['utf8']:
            end = scan(block, state)
            if (type(section['utf8_state_in']) is not int or
                type(section['utf8_state_out']) is not int or
                section['utf8_state_in'] != state or section['utf8_state_out'] != end or end == 8):
                raise ValueError('UTF-8 boundary state mismatch')
            state = end
        elif section['utf8_state_in'] is not None or section['utf8_state_out'] is not None:
            raise ValueError('unexpected UTF-8 state in raw mode')
        data.extend(block)
    result = bytes(data)
    if sha(result) != record['sha256']: raise ValueError('stream checksum mismatch')
    if record['utf8']:
        if state != 0: raise ValueError('unfinished UTF-8 stream')
        result.decode('utf-8', 'strict')
    return result

@dataclass(frozen=True)
class RepairCube:
    width: int
    baseline: int
    protected: int
    required: int
    target: int
    conflict: int
    fixed_mask: int
    fixed_value: int
    free_mask: int

    @property
    def solution_count(self) -> int:
        return 0 if self.conflict else 1 << self.free_mask.bit_count()

    def accepts(self, candidate: int) -> bool:
        check_int(candidate, 0, (1 << self.width) - 1, 'candidate')
        return not self.conflict and candidate & self.fixed_mask == self.fixed_value

    def minimum_hamming_repair(self) -> int | None:
        if self.conflict: return None
        return ((self.baseline & (~self.required & ((1 << self.width) - 1))) |
                (self.target & self.required))

    def unrank(self, rank: int) -> int:
        check_int(rank, 0, self.solution_count - 1, 'rank')
        out, free = self.fixed_value, self.free_mask
        while free:
            bit = free & -free
            if rank & 1: out |= bit
            rank >>= 1
            free ^= bit
        return out

    def rank(self, candidate: int) -> int:
        if not self.accepts(candidate): raise ValueError('candidate outside repair set')
        out, free, shift = 0, self.free_mask, 0
        while free:
            bit = free & -free
            if candidate & bit: out |= 1 << shift
            free ^= bit
            shift += 1
        return out


def solve(width: int, baseline: int, protected: int, required: int, target: int) -> RepairCube:
    check_int(width, 1, SECTION_BITS, 'width')
    mask = (1 << width) - 1
    for name, value in [('baseline', baseline), ('protected', protected),
                        ('required', required), ('target', target)]:
        check_int(value, 0, mask, name)
    fixed = protected | required
    return RepairCube(width, baseline, protected, required, target,
                      (baseline ^ target) & protected & required, fixed,
                      (baseline & protected) | (target & required), mask ^ fixed)


def compression_areas(data: bytes) -> list[dict]:
    """Measurements for byte spans; scores do not authorize semantic merging.

    Conditional figures exclude prior dictionary storage and include the zlib
    stream wrapper. Standalone figures include sending the dictionary once.
    All original bytes remain in custody; no section is replaced by a score.
    """
    result, previous = [], b''
    for offset in range(0, len(data), SECTION_BYTES):
        block = data[offset:offset + SECTION_BYTES]
        compressed = zlib.compress(block, level=9)
        if zlib.decompress(compressed) != block: raise AssertionError('compression round trip')
        row = {'byte_offset': offset, 'byte_length': len(block), 'sha256': sha(block),
               'zlib_bytes': len(compressed),
               'net_zlib_payload_saving_bytes': len(block) - len(compressed),
               'status': 'MEASURED_BYTE_COMPRESSIBILITY_NOT_LEARNING'}
        if previous:
            obj = zlib.compressobj(level=9, zdict=previous)
            conditional = obj.compress(block) + obj.flush()
            decoder = zlib.decompressobj(zdict=previous)
            if decoder.decompress(conditional) + decoder.flush() != block:
                raise AssertionError('dictionary round trip')
            row.update({'conditional_zlib_bytes': len(conditional),
                        'dictionary_bytes': len(previous),
                        'dictionary_sha256': sha(previous),
                        'standalone_with_dictionary_bytes': len(previous) + len(conditional)})
        result.append(row)
        previous = block
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('pack'); p.add_argument('input', type=Path); p.add_argument('output', type=Path)
    p.add_argument('--raw', action='store_true', help='Do not require UTF-8')
    p = sub.add_parser('unpack'); p.add_argument('input', type=Path); p.add_argument('output', type=Path)
    p = sub.add_parser('profile'); p.add_argument('input', type=Path); p.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.command == 'pack':
        obj = frame(args.input.read_bytes(), utf8=not args.raw)
        args.output.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
    elif args.command == 'unpack':
        args.output.write_bytes(unframe(json.loads(args.input.read_text(encoding='utf-8'))))
    else:
        args.output.write_text(json.dumps(compression_areas(args.input.read_bytes()), indent=2) + '\n', encoding='utf-8')



def _prefix_function(pattern: bytes) -> list[int]:
    pi = [0] * len(pattern)
    for i in range(1, len(pattern)):
        j = pi[i-1]
        while j and pattern[i] != pattern[j]: j = pi[j-1]
        if pattern[i] == pattern[j]: j += 1
        pi[i] = j
    return pi


def literal_offsets(chunks, pattern: bytes):
    """Yield exact byte offsets, preserving match state across section cuts."""
    if not isinstance(pattern, bytes) or not pattern: raise ValueError('nonempty byte pattern required')
    pi = _prefix_function(pattern)
    matched = offset = 0
    for chunk in chunks:
        for byte in chunk:
            while matched and byte != pattern[matched]: matched = pi[matched-1]
            if byte == pattern[matched]: matched += 1
            if matched == len(pattern):
                yield offset + 1 - len(pattern)
                matched = pi[matched-1]
            offset += 1


def count_utf8_containing(space: UTF8Space, n: int, pattern: bytes) -> int:
    """Exact UTF-8 / substring product-automaton count; no semantic predicate."""
    check_int(n, 0, space.max_bytes, 'length')
    if not isinstance(pattern, bytes) or not pattern: raise ValueError('nonempty byte pattern required')
    if len(pattern) > 32: raise ValueError('literal pattern implementation cap is 32 bytes')
    pi = _prefix_function(pattern)
    transitions = {}
    for state in range(8):
        for k in range(len(pattern)):
            dests = Counter()
            for byte in range(256):
                q = TABLE[state][byte]
                if q == 8: continue
                j = k
                while j and byte != pattern[j]: j = pi[j-1]
                if byte == pattern[j]: j += 1
                if j != len(pattern): dests[q,j] += 1
            transitions[state,k] = dests
    cur = {(0,0):1}
    for _ in range(n):
        nxt = Counter()
        for state, count in cur.items():
            for dest, weight in transitions[state].items():
                nxt[dest] += count * weight
        cur = nxt
    avoiding = sum(count for (q,k),count in cur.items() if q == 0)
    return space.count(n) - avoiding

if __name__ == '__main__':
    main()

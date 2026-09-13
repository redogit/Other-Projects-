#!/usr/bin/env python3
"""Run exact finite checks and write reproducible counts and witness ledgers."""
from __future__ import annotations
import argparse
from collections import Counter
from functools import lru_cache
import codecs
import csv
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from math import comb
from pathlib import Path
import platform
import random
import sys
from time import perf_counter
from search import (Census, LEAVES, ONSETS, MAX_BYTES, accepted_tables, alliteration,
                    float_to_word, load_transport, parse, require, scalar_eval,
                    word_sequences, word_to_float, zeta)

ROOT = Path(__file__).resolve().parent
SEED = 20260913


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)+'\n', encoding='utf-8')


@lru_cache(None)
def literal_programs(k):
    if k == 0:
        return tuple(LEAVES)
    return tuple('N'+left+right for i in range(k)
                 for left in literal_programs(i) for right in literal_programs(k-1-i))


def direct_counts(max_nodes):
    start = [0]*256
    for f in LEAVES.values(): start[f] += 1
    rows = [start]
    for k in range(1, max_nodes+1):
        row = [0]*256
        for i in range(k):
            for a, ca in enumerate(rows[i]):
                if ca:
                    for b, cb in enumerate(rows[k-1-i]):
                        if cb: row[255 ^ (a & b)] += ca*cb
        rows.append(row)
    return rows


def check_signature(text, f):
    require(parse(text)[1] == f, 'bit evaluation mismatch')
    require(sum(scalar_eval(text, row) << row for row in range(8)) == f,
            'independent row evaluation mismatch')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=ROOT/'results')
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    start = perf_counter()
    sources = {name: digest((ROOT/name).read_bytes())
               for name in ('search.py', 'run_audit.py', 'CONTRACT.md')}
    transport = load_transport()
    build_start = perf_counter()
    census = Census(1024)
    census_seconds = perf_counter()-build_start
    print('census', census_seconds, flush=True)
    rows = census.counts
    # Orthogonal recurrence and explicit individual programs.
    require(direct_counts(15) == rows[:16], 'direct convolution mismatch')
    literal_total = 0
    for k in range(6):
        words = literal_programs(k)
        require(len(words) == len(set(words)), 'literal duplicates')
        observed = Counter()
        for text in words:
            f = sum(scalar_eval(text, i) << i for i in range(8))
            require(parse(text)[1] == f, 'literal parser mismatch')
            observed[f] += 1
            literal_total += 1
        require([observed[f] for f in range(256)] == rows[k], 'literal histogram mismatch')
    print('independent counts', perf_counter()-start, flush=True)
    short = census.histogram(8)
    total = census.histogram()
    accepted = accepted_tables()
    require(accepted == (82, 90, 114, 122), 'unexpected accepted behaviors')
    require(sum(short) == 471 and sum(bool(x) for x in short) == 38, 'short domain mismatch')
    require(not any(short[f] for f in accepted), 'unexpected short repair')
    witnesses = {f: census.shortest(f) for f in range(256)}
    for f, text in witnesses.items(): check_signature(text, f)
    lengths = {f: len(text) for f, text in witnesses.items()}
    require(max(lengths.values()) == 29, 'shortest-cost benchmark mismatch')
    for a, b in product(range(256), repeat=2):
        require(lengths[255 ^ (a & b)] <= 1+lengths[a]+lengths[b], 'cost certificate failure')
    # Upper-set inversion on values independent of formula counts.
    rng = random.Random(SEED)
    for _ in range(12):
        v = [rng.randrange(-100, 101) for _ in range(256)]
        require(zeta(zeta(v), True) == v, 'zeta inversion failure')
    # Label permutation: exchange x and y without changing token costs.
    permutation = []
    for f in range(256):
        swapped = 0
        for i in range(8):
            j = ((i & 4) >> 1) | ((i & 2) << 1) | (i & 1)
            swapped |= ((f >> j) & 1) << i
        permutation.append(swapped)
    require(all(row[f] == row[permutation[f]] for row in rows for f in range(256)),
            'variable-renaming count symmetry broken')
    # Exact short witness bijections; do not silently call a sample exhaustive.
    short_ledger = []
    witness_checks = 0
    for k in range(4):
        for f, count in enumerate(rows[k]):
            actual = set()
            for r in range(count):
                text = census.unrank(2*k+1, f, r)
                require(census.rank(text) == r, 'short rank inverse failure')
                actual.add(text)
                f64 = word_to_float(text, transport)
                require(float_to_word(f64, transport) == text, 'single-float roundtrip failure')
                short_ledger.append({'program': text, 'bytes': len(text), 'table': f,
                                     'rank_within_length_and_behavior': r, 'float_hex': f64.hex()})
                witness_checks += 1
            require(len(actual) == count, 'short rank collision')
    print('short ranks', perf_counter()-start, flush=True)
    samples = []
    for f in accepted:
        for n in (31, 255, 1023):
            count = census.count(n, f)
            for r in sorted({0, count-1} if n == 1023 else {0, rng.randrange(count)}):
                text = census.unrank(n, f, r)
                require(census.rank(text) == r, 'long witness rank inverse failure')
                require(len(text) == n, 'length mismatch')
                check_signature(text, f)
                frame = transport.frame(text.encode('utf-8'))
                require(transport.unframe(frame) == text.encode('utf-8'), 'multiword carrier failure')
                samples.append({'table': f, 'bytes': n, 'rank': str(r), 'program': text,
                                'sha256': digest(text.encode())})
                witness_checks += 1
    print('long ranks', perf_counter()-start, flush=True)
    good_rows = []
    for f in accepted:
        text = witnesses[f]
        require(not ((f ^ 240)&0x55) and not ((f ^ 2)&0x82), 'bad repair witness')
        good_rows.append({'table': f, 'table_hex': hex(f), 'shortest_program': text,
                         'shortest_bytes': len(text), 'changed_output_rows': (f ^ 240).bit_count(),
                         'program_count_through_1024': str(total[f]),
                         'new_to_eight_byte_working_set': short[f] == 0,
                         'outputs_on_rows_000_to_111': [(f >> i)&1 for i in range(8)]})
    # UTF-8 syntax census; independent first-character recurrence.
    live = [1]+[0]*8
    char = [1]
    syntax = []
    for n in range(1026):
        if n:
            char.append(sum(c*char[n-w] for w,c in ((1,128),(2,1920),(3,61440),(4,1048576)) if n>=w))
            new = [0]*9
            for s, count in enumerate(live):
                for dest, weight in transport.WEIGHTS[s].items(): new[dest] += count*weight
            live = new
        require(live[0] == char[n] and sum(live) == 256**n, 'UTF-8 partition mismatch')
        if n in (0, 1, 2, 7, 8, 9, 31, 1023, 1024, 1025):
            grammar = sum(rows[(n-1)//2]) if n and n%2 and n<=1024 else 0 if n<=1024 else None
            syntax.append({'bytes': n, 'raw_patterns': str(256**n), 'complete_utf8': str(live[0]),
                           'incomplete_extendable': str(sum(live[1:8])), 'invalid_utf8': str(live[8]),
                           'grammar_programs': None if grammar is None else str(grammar),
                           'complete_utf8_outside_grammar': None if grammar is None else str(live[0]-grammar)})
    raw_oracles = 0
    for n in range(3):
        for values in product(range(256), repeat=n):
            data = bytes(values)
            state = transport.scan(data)
            try:
                data.decode('utf-8', errors='strict')
                expected = 'complete'
            except UnicodeDecodeError as exc:
                expected = 'invalid'
                if exc.reason == 'unexpected end of data':
                    # Independent extendability oracle for prefixes <=2 bytes.
                    # Every legal missing suffix can choose one of these first
                    # continuation thresholds, followed by 0x80 continuations.
                    for width in (1,2,3):
                        for head in (0x80,0x90,0xa0,0xbf):
                            try:
                                (data+bytes([head])+b'\x80'*(width-1)).decode('utf-8','strict')
                                expected = 'prefix'
                            except UnicodeDecodeError:
                                pass
            actual = 'invalid' if state == 8 else 'complete' if state == 0 else 'prefix'
            require(actual == expected, 'UTF-8 independent decoder mismatch')
            raw_oracles += 1
    # Phonetic-filter fixture is separate from the program language.
    language = word_sequences(1024)
    brute = [0]*16
    brute_sound = [0]*16
    for size in range(1,5):
        for words in product(ONSETS, repeat=size):
            text = ' '.join(words)
            if size >= 2 and len(text) <= 15:
                brute[len(text)] += 1
                brute_sound[len(text)] += int(alliteration(text))
    require(brute == language['all_sequences_by_length'][:16], 'word count oracle mismatch')
    require(brute_sound == language['same_onset_by_length'][:16], 'alliteration oracle mismatch')
    require(sum(brute[:9]) == 45 and sum(brute_sound[:9]) == 15, 'short alliteration totals')
    require(alliteration('city cat') is False and alliteration('city sun') is True
            and alliteration('phone fun') is True and alliteration('unknown sun') is None,
            'phoneme/spelling/unknown counterprobe failed')
    phonetic = {'fixture_authorship': 'assistant hand-specified English initial-consonant labels',
                'lexicon': ONSETS, 'dictionary_imported': False,
                'short_sequences': sum(brute[:9]), 'short_same_onset_sequences': sum(brute_sound[:9]),
                'through_1024_sequences': str(sum(language['all_sequences_by_length'])),
                'through_1024_same_onset': str(sum(language['same_onset_by_length'])),
                'counterexamples': {'city cat': False, 'city sun': True, 'phone fun': True,
                                    'unknown sun': 'UNKNOWN'}}
    rejected = []
    bad = [('empty expression', lambda: parse('')), ('two expressions', lambda: parse('xy')),
           ('truncated tree', lambda: parse('Nx')), ('whitespace changes grammar', lambda: parse('N x y')),
           ('non-grammar Unicode', lambda: parse('S′')), ('negative rank', lambda: census.unrank(11,90,-1)),
           ('rank at cardinality', lambda: census.unrank(11,90,census.count(11,90))),
           ('even exact length', lambda: census.unrank(8,90,0)),
           ('over-bound request', lambda: Census(1025)),
           ('non-integer mask', lambda: accepted_tables(protected=True)),
           ('oversize single-float text', lambda: word_to_float('NNxNzzNzNxx',transport)),
           ('out-of-domain float', lambda: float_to_word(float('nan'),transport))]
    for label, call in bad:
        try: call()
        except ValueError: rejected.append(label)
        else: raise AssertionError('bad input accepted: '+label)
    require(accepted_tables(240,1,1,1) == (), 'conflicting obligation admitted')
    require(scalar_eval('x',0) == scalar_eval('y',0)
            and scalar_eval('x',2) != scalar_eval('y',2), 'weak-equivalence counterprobe')
    boundaries = []
    for n in (8,11,15,17,29,31,255,511,1024):
        h = census.histogram(n)
        boundaries.append({'max_bytes': n, 'program_count': str(sum(h)),
                           'behavior_count': sum(bool(v) for v in h),
                           'accepted_behavior_count': sum(bool(h[f]) for f in accepted),
                           'accepted_program_count': str(sum(h[f] for f in accepted))})
    hist = [{'table': f, 'total_count': str(total[f]), 'at_1023_bytes': str(rows[511][f]),
             'shortest_bytes': lengths[f], 'shortest_program': witnesses[f],
             'in_eight_byte_working_set': bool(short[f]), 'accepted_repair': f in accepted}
            for f in range(256)]
    save(out/'behavior_census.json', hist)
    save(out/'syntax_partition.json', syntax)
    save(out/'repair_candidates.json', good_rows)
    save(out/'sampled_witnesses.json', samples)
    save(out/'alliteration.json', phonetic)
    save(out/'budgets.json', boundaries)
    with (out/'all_programs_through_8_bytes.csv').open('w',encoding='utf-8',newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(short_ledger[0]))
        writer.writeheader(); writer.writerows(short_ledger)
    summary = {'status': 'PASS_BOUNDED', 'program_count_through_1024': str(sum(total)),
               'program_count_decimal_digits': len(str(sum(total))),
               'short_programs': 471, 'short_behaviors': 38, 'total_behaviors': 256,
               'new_to_short_working_set_behaviors': 218,
               'accepted_behavior_count': len(accepted),
               'accepted_program_count_through_1024': str(sum(total[f] for f in accepted)),
               'minimum_accepted_program_bytes': min(lengths[f] for f in accepted),
               'exact_length_1024_grammar_programs': 0, 'max_evaluated_grammar_length': 1023,
               'catalan_checks': len(rows), 'literal_program_oracles': literal_total,
               'direct_convolution_lengths': 16, 'shortest_cost_inequalities': 65536,
               'all_behavior_witness_row_checks': 2048,
               'rank_and_carrier_checks': witness_checks, 'long_rank_samples': len(samples),
               'raw_utf8_decoder_oracles': raw_oracles, 'negative_controls_rejected': rejected,
               'conflicting_obligations_empty': True, 'one_row_equivalence_counterexample': True,
               'utf8_strings_through_8_bytes': str(sum(char[:9])),
               'next_length_1025_status': 'SYNTAX_COUNTED_PROGRAM_MULTIPLICITY_NOT_EVALUATED',
               'all_finite_depth_behavior_closure': 'INDUCTION_ARGUMENT_PLUS_FULL_COMPOSITION_CERTIFICATE',
               'semantic_scope': 'Only the declared 3-input NAND grammar; no natural-language truth oracle'}
    save(out/'summary.json', summary)
    # Integrate evidence with unchanged inherited carrier, not one float per file.
    witness_bytes = (out/'repair_candidates.json').read_bytes()
    frame = transport.frame(witness_bytes)
    require(transport.unframe(frame) == witness_bytes, 'candidate ledger transport failed')
    save(out/'transport_check.json', {'bytes': len(witness_bytes), 'full_sections': len(witness_bytes)//1024,
        'remainder': len(witness_bytes)%1024, 'sha256': digest(witness_bytes),
        'frame_version': transport.VERSION, 'roundtrip': True,
        'single_float_short_programs_verified': len(short_ledger),
        'dependency_sha256': digest((ROOT.parent/'S1024 Compression Lab/sections1024.py').read_bytes())})
    require(sources == {n:digest((ROOT/n).read_bytes()) for n in sources}, 'execution source changed')
    manifest = {'schema_version': 1, 'claim_id': 'SPRIME-SEARCH-03',
        'repository': {'commit': '85e18ee3678552f30cf4711f747083d68e42a038', 'dirty': True},
        'command': [sys.executable, str(ROOT/'run_audit.py'), '--out', str(out)],
        'environment': {'software': [platform.python_version()], 'hardware': platform.platform()},
        'mathematics': {'assertion_tested': 'Exact grammar/behavior census and constrained witnesses through 1024 bytes',
            'coefficient_domain': 'arbitrary-precision integers',
            'conventions': 'CONTRACT.md; no generated source execution; exact truth-table bits',
            'inputs': list(sources), 'bounds': {'bytes':1024,'truth_tables':256,'rows':8},
            'non_claims': ['No universal S-prime/idea/meaning detector','No multilingual alliteration coverage',
                          'No independent human replication or benchmark-speed guarantee']},
        'randomness': {'used': True, 'generator': 'Python random.Random', 'seed': SEED},
        'run': {'started_at':started,'runtime_seconds':perf_counter()-start,'exit_status':0,
                'census_build_seconds':census_seconds,'process_timeout_seconds':45},
        'input_artifacts': [{'path':name,'sha256':h,'sha256_after':h} for name,h in sources.items()],
        'outputs': [{'path':p.name,'sha256':digest(p.read_bytes())} for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'],
        'checks': ['direct convolution','literal enumeration','Catalan totals','rank inverses',
                   'scalar witnesses','shortest-cost closure','UTF-8 decoder','alliteration oracles'],
        'result': 'PASS in the declared family',
        'residual_risks': ['single author','manually chosen repair and phoneme fixture',
                           'package-local hash validation, not official Mathbox validator']}
    save(out/'manifest.json', manifest)
    print(json.dumps({'status':'PASS', 'seconds':manifest['run']['runtime_seconds'],
                      'census_seconds':census_seconds,'program_count_digits':summary['program_count_decimal_digits'],
                      'accepted_tables':[hex(f) for f in accepted],
                      'shortest_candidates':[(x['shortest_program'],x['shortest_bytes']) for x in good_rows],
                      'literal_oracles':literal_total, 'long_samples':len(samples)},indent=2))


if __name__ == '__main__':
    main()

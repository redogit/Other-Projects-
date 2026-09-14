#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from itertools import product
import hashlib
import json
import math
from pathlib import Path
import random

from schedule import (
    IDENTITY_MAP, MooreScheduler, adversarial_reach, adversarial_safety,
    apply_word, compose, context_map, controllable_reach, controllable_safety,
    cycles, map_byte, map_tuple, periodic_profile, periodic_scheduler, power,
    reachable_states, semigroup, word_map,
)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)
SEED = 20260914
WITNESS = 0x00000805


def req(condition, message):
    if not condition:
        raise AssertionError(message)


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def direct_compose(after, before):
    a, b = map_tuple(after), map_tuple(before)
    return map_byte(tuple(a[b[s]] for s in range(4)))


def direct_apply(rank, state, word):
    for context in word:
        state = map_tuple(context_map(rank, context))[state]
    return state


def all_words(alphabet, max_length):
    yield ()
    for length in range(1, max_length + 1):
        yield from product(alphabet, repeat=length)


def brute_closed_safety(a, b, safe_mask, controllable):
    best = 0
    for subset in range(16):
        if subset & ~safe_mask:
            continue
        valid = True
        for state in range(4):
            if not (subset >> state) & 1:
                continue
            images = (map_tuple(a)[state], map_tuple(b)[state])
            ok = (any((subset >> x) & 1 for x in images) if controllable
                  else all((subset >> x) & 1 for x in images))
            if not ok:
                valid = False
                break
        if valid:
            best |= subset
    return tuple(s for s in range(4) if (best >> s) & 1)


def brute_reach(a, b, target_mask, controllable):
    reached = target_mask
    for _ in range(4):
        new = reached
        for state in range(4):
            if (reached >> state) & 1:
                continue
            images = (map_tuple(a)[state], map_tuple(b)[state])
            ok = (any((reached >> x) & 1 for x in images) if controllable
                  else all((reached >> x) & 1 for x in images))
            if ok:
                new |= 1 << state
        if new == reached:
            break
        reached = new
    return tuple(s for s in range(4) if (reached >> s) & 1)


def brute_scheduler_equiv(machine, left, right):
    todo = deque([(left, right)])
    seen = set()
    while todo:
        a, b = todo.popleft()
        if (a, b) in seen:
            continue
        seen.add((a, b))
        if machine.outputs[a] != machine.outputs[b]:
            return False
        for obs in range(4):
            todo.append((machine.transitions[a][obs], machine.transitions[b][obs]))
    return True


def least_period(word):
    n = len(word)
    for p in range(1, n + 1):
        if n % p == 0 and all(word[i] == word[i % p] for i in range(n)):
            return p
    return n


def state_path(rank, start, word):
    path = [start]
    for context in word:
        path.append(direct_apply(rank, path[-1], (context,)))
    return tuple(path)


def main():
    rng = random.Random(SEED)

    import subprocess, tempfile
    with tempfile.TemporaryDirectory(prefix='schedule-native-') as td:
        exe = Path(td) / 'native_stress'
        subprocess.run(['g++','-O3','-std=c++17',str(ROOT/'native_stress.cpp'),'-o',str(exe)], check=True, timeout=45)
        native = json.loads(subprocess.check_output([str(exe)], text=True, timeout=45))
    req(native['status'] == 'PASS', 'native stress oracle failed')

    table = [[0] * 256 for _ in range(256)]
    compose_pairs = 0
    for after in range(256):
        for before in range(256):
            got = compose(after, before)
            req(got == direct_compose(after, before), 'composition oracle mismatch')
            table[after][before] = got
            compose_pairs += 1
    assoc_python = 0
    for _ in range(500_000):
        a,b,c=(rng.randrange(256) for _ in range(3))
        req(compose(compose(a,b),c)==compose(a,compose(b,c)), 'sampled associativity failed')
        assoc_python += 1

    plants = [WITNESS, 0, 0xffffffff, 0xe4e4e4e4]
    plants.extend(rng.randrange(1 << 32) for _ in range(12))
    finite_words_checked = 0
    semigroup_records = []
    for rank in plants:
        closure = semigroup(rank)
        req(len(closure) <= 256, 'semigroup escaped full monoid')
        req(IDENTITY_MAP in closure and closure[IDENTITY_MAP] == (), 'missing empty-word identity')
        for word in all_words(range(4), 6):
            wm = word_map(rank, word)
            req(wm in closure, 'word map absent from closure')
            for state in range(4):
                req(apply_word(rank, state, word) == direct_apply(rank, state, word), 'word execution mismatch')
                req(map_tuple(wm)[state] == direct_apply(rank, state, word), 'word map mismatch')
            finite_words_checked += 1
        semigroup_records.append({'rank_hex':hex(rank),'size':len(closure),'shortest_word_diameter':max(map(len,closure.values()))})

    pair_closure = semigroup(WITNESS, (0, 1))
    req(len(pair_closure) == 12 and max(map(len, pair_closure.values())) == 4, 'witness semigroup benchmark changed')
    block = periodic_profile(WITNESS, (0, 1))
    req(block['block_map'] == 0x0a and cycles(0x0a) == ((0, 2),), 'AB counterexample changed')
    for exponent in range(65):
        req(word_map(WITNESS, (0, 1) * exponent) == power(block['block_map'], exponent), 'periodic power mismatch')

    by_map = {}; trajectory_witness = None
    for word in all_words((0, 1), 7):
        m = word_map(WITNESS, word)
        if m in by_map:
            other = by_map[m]
            for start_state in range(4):
                p1, p2 = state_path(WITNESS, start_state, other), state_path(WITNESS, start_state, word)
                if p1 != p2:
                    trajectory_witness = {'word_a':other,'word_b':word,'map_hex':hex(m),'start':start_state,'path_a':p1,'path_b':p2}
                    break
        else:
            by_map[m] = word
        if trajectory_witness:
            break
    req(trajectory_witness is not None, 'failed trajectory-equivalence counterexample')

    safety_cases = reach_cases = 0
    game_inputs={(0,0,0),(0xff,0xff,0xf),(0x05,0x08,0xf)}
    while len(game_inputs)<120_000:
        game_inputs.add((rng.randrange(256),rng.randrange(256),rng.randrange(16)))
    for a,b,mask in sorted(game_inputs):
        rank=a|(b<<8); states=tuple(s for s in range(4) if (mask>>s)&1)
        req(adversarial_safety(rank,states,(0,1))==brute_closed_safety(a,b,mask,False),'adversarial safety mismatch')
        req(controllable_safety(rank,states,(0,1))==brute_closed_safety(a,b,mask,True),'controllable safety mismatch')
        req(adversarial_reach(rank,states,(0,1))==brute_reach(a,b,mask,False),'adversarial reach mismatch')
        req(controllable_reach(rank,states,(0,1))==brute_reach(a,b,mask,True),'controllable reach mismatch')
        safety_cases += 2; reach_cases += 2

    periodic_words_checked = 0
    for length in range(1, 8):
        for word in product(range(4), repeat=length):
            machine = periodic_scheduler(word)
            minimized, _ = machine.minimize()
            req(minimized.states == least_period(word), 'periodic scheduler minimization mismatch')
            expected_bits = 0 if minimized.states == 1 else math.ceil(math.log2(minimized.states))
            req(machine.memory_bits() == expected_bits, 'periodic memory-bit mismatch')
            periodic_words_checked += 1

    scheduler_machines = 0; scheduler_pairs = 0
    for outputs in product(range(4), repeat=2):
        for flat in product(range(2), repeat=8):
            transitions = (tuple(flat[:4]), tuple(flat[4:]))
            machine = MooreScheduler(outputs, transitions)
            minimized, labels = machine.minimize()
            equivalent = brute_scheduler_equiv(machine, 0, 1)
            req((labels[0] == labels[1]) == equivalent, 'Moore equivalence mismatch')
            req(minimized.states == (1 if equivalent else 2), 'Moore minimum-state mismatch')
            scheduler_machines += 1; scheduler_pairs += 1

    for qn in (3, 4, 5):
        for _ in range(1000):
            outputs = tuple(rng.randrange(4) for _ in range(qn))
            transitions = tuple(tuple(rng.randrange(qn) for _ in range(4)) for _ in range(qn))
            machine = MooreScheduler(outputs, transitions, rng.randrange(qn))
            minimized, labels = machine.minimize()
            for a in range(qn):
                for b in range(qn):
                    req((labels[a] == labels[b]) == brute_scheduler_equiv(machine, a, b), 'sampled Moore mismatch')
                    scheduler_pairs += 1
            scheduler_machines += 1

    alternator = periodic_scheduler((0, 1))
    req(alternator.minimize()[0].states == 2 and alternator.memory_bits() == 1, 'alternator needs one bit')
    req(any(len(cycle) > 1 for cycle in alternator.combined_cycles(WITNESS)), 'alternator cycle missing')
    three_phase = periodic_scheduler((0, 1, 2))
    req(three_phase.minimize()[0].states == 3 and three_phase.memory_bits() == 2, 'three-phase needs two bits')
    redundant = MooreScheduler((0, 1, 0, 1), ((1,1,1,1),(0,0,0,0),(3,3,3,3),(2,2,2,2)))
    req(redundant.minimize()[0].states == 2, 'redundant scheduler did not collapse')

    reach = {str(s): reachable_states(WITNESS, (s,), (0, 1)) for s in range(4)}
    req(reach == {'0': (0,1,2), '1': (0,1,2), '2': (0,1,2), '3': (0,1,2,3)}, 'witness reachability changed')

    rejected = []
    bad = [
        ('negative rank', lambda: context_map(-1, 0)), ('overwide rank', lambda: context_map(1 << 32, 0)),
        ('bad context', lambda: context_map(0, 4)), ('bad state', lambda: apply_word(0, 4, (0,))),
        ('string schedule', lambda: word_map(0, '01')), ('empty periodic block', lambda: periodic_profile(0, ())),
        ('negative exponent', lambda: power(IDENTITY_MAP, -1)), ('empty scheduler outputs', lambda: MooreScheduler((), ())),
        ('bad scheduler row', lambda: MooreScheduler((0,), ((0,0,0),))),
        ('bad scheduler transition', lambda: MooreScheduler((0,), ((0,0,0,1),))),
    ]
    for name, call in bad:
        try: call()
        except ValueError: rejected.append(name)
        else: raise AssertionError('accepted malformed request: ' + name)

    summary = {
        'status':'PASS_BOUNDED','seed':SEED,'full_transformation_monoid_maps':256,
        'composition_pairs_exhausted':compose_pairs,
        'associativity_triples_exhausted_native':native['associativity_triples'],
        'associativity_triples_sampled_python':assoc_python,
        'plants_word_checked':len(plants),'finite_schedule_words_checked':finite_words_checked,
        'witness_context01_semigroup_size':len(pair_closure),
        'witness_context01_shortest_word_diameter':max(map(len,pair_closure.values())),
        'witness_ab_block_map_hex':hex(block['block_map']),'witness_ab_block_cycles':block['cycles'],
        'same_final_map_different_trajectory_witness':trajectory_witness,
        'native_ordered_map_pair_mask_game_cases':native['ordered_map_pair_mask_game_cases'],
        'safety_fixed_point_comparisons_python':safety_cases,
        'reachability_fixed_point_comparisons_python':reach_cases,
        'periodic_words_minimized_exhaustively':periodic_words_checked,
        'scheduler_machines_checked':scheduler_machines,'scheduler_state_pairs_checked':scheduler_pairs,
        'alternating_schedule_minimum_memory_states':2,'alternating_schedule_minimum_memory_bits':1,
        'three_phase_minimum_memory_states':3,'three_phase_minimum_memory_bits':2,
        'witness_reachable_states_context01':reach,'semigroup_records':semigroup_records,
        'negative_controls_rejected':rejected,
        'claim_ceiling':'Exact finite schedule semantics for four-state T4 plants and declared finite-memory schedulers; not a universal switched-systems, semantic, or optimal-control theorem.'
    }
    save('SUMMARY.json', summary)
    source_hashes = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('schedule.py','audit.py','CONTRACT.md','README.md')}
    save('VERIFICATION.json', {'status':'PASS','source_hashes':source_hashes,'scientific_output':'SUMMARY.json','scope':'Local exact/exhaustive finite-domain verification plus semigroup closure argument; no formal proof assistant.'})
    print(json.dumps({k:summary[k] for k in ('status','composition_pairs_exhausted','associativity_triples_exhausted_native','finite_schedule_words_checked','safety_fixed_point_comparisons_python','periodic_words_minimized_exhaustively','scheduler_machines_checked')}, indent=2))


if __name__ == '__main__':
    main()

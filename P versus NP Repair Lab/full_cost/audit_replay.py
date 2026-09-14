#!/usr/bin/env python3
"""Independently replay the declared finite selector suite; import no producer code.

This checks recorded truth-table classes and selector certificates. It does not
independently establish that each recorded class contains every bounded DAG.
Bit-read counts describe eager source-level evaluation, not hardware loads.
"""
import argparse
import hashlib
import itertools
import json
import pathlib


EXPECTED_CASES = {(n, g) for n in (2, 3, 4) for g in range(7)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def available_actions(point_count, observed, translation):
    return [
        x for x in range(point_count)
        if x not in observed and (
            translation < 0 or (
                x < (x ^ translation) and (x ^ translation) not in observed
            )
        )
    ]


def permutation_maps(n):
    return [
        tuple(sum(((x >> j) & 1) << ordering[j] for j in range(n))
              for x in range(1 << n))
        for ordering in itertools.permutations(range(n))
    ]


def orbit_representatives(actions, observed, translation, maps):
    # Setwise preservation of the labeled observation map, not just its support.
    stabilizer = [
        mapping for mapping in maps
        if {mapping[x]: bit for x, bit in observed.items()} == observed
        and (translation < 0 or mapping[translation] == translation)
    ]
    remaining = set(actions)
    representatives = []
    while remaining:
        x = min(remaining)
        orbit = {
            mapping[x] if translation < 0
            else min(mapping[x], mapping[x] ^ translation)
            for mapping in stabilizer
        }
        require(orbit <= set(actions), 'stabilizer left the available action set')
        representatives.append(min(orbit))
        remaining.difference_update(orbit)
    return len(stabilizer), sorted(representatives)


def matches(table, coordinate, bit, translation):
    first = ((table >> coordinate) & 1) == bit
    if translation < 0:
        return first, 1
    # Evaluate the second expression even when the first is false (v6.1 contract).
    second = ((table >> (coordinate ^ translation)) & 1) == bit
    return first & second, 2


def replay_route(data, route, maps):
    label = f'n={data["n"]},g={data["gate_budget"]},{route["name"]}'
    point_count = 1 << data['n']
    translation = route['translation']
    survivors = list(data['truth_tables'])
    observed = {}
    path = route['path']
    picks = route['picks']
    require(len(path) == len(picks) + 1, f'{label}: path length')
    require(path[0] == len(survivors), f'{label}: initial class size')
    group_sizes, representative_counts = [], []
    verification_reads = 0
    for step, choice in enumerate(picks):
        require(len(choice) == 2, f'{label}: choice shape')
        chosen, chosen_bit = choice
        require(survivors, f'{label}: route continued after elimination')
        actions = available_actions(point_count, observed, translation)
        require(actions, f'{label}: step without an available action')
        group_size, representatives = orbit_representatives(
            actions, observed, translation, maps)
        group_sizes.append(group_size)
        representative_counts.append(len(representatives))
        scores = []
        for x in actions:
            for bit in (0, 1):
                count = 0
                for table in survivors:
                    accepted, reads = matches(table, x, bit, translation)
                    verification_reads += reads
                    count += accepted
                scores.append((count, x, bit))
        best = min(scores)
        require(best[1:] == (chosen, chosen_bit),
                f'{label}: full-action greedy choice differs at step {step}')
        retained = []
        for table in survivors:
            accepted, reads = matches(table, chosen, chosen_bit, translation)
            verification_reads += reads
            if accepted:
                retained.append(table)
        survivors = retained
        observed[chosen] = chosen_bit
        if translation >= 0:
            observed[chosen ^ translation] = chosen_bit
        require(best[0] == len(survivors) == path[step + 1],
                f'{label}: survivor path differs at step {step}')

    eliminated = len(survivors) == 0
    require(type(route['eliminated_class']) is bool
            and route['eliminated_class'] == eliminated, f'{label}: final status')
    require(eliminated or not available_actions(point_count, observed, translation),
            f'{label}: unsuccessful route stopped before exhausting actions')
    require(route['observations'] == len(observed), f'{label}: observation count')
    require(route['stabilizer_sizes'] == group_sizes, f'{label}: stabilizer sizes')
    require(route['representative_counts'] == representative_counts,
            f'{label}: orbit representative counts')
    require(route['scalar_verification_bit_reads'] == verification_reads,
            f'{label}: eager scalar verification bit count')

    words = (len(data['truth_tables']) + 63) // 64
    factor = 1 if translation < 0 else 2
    candidates = 2 * sum(representative_counts)
    counts = route['counts']
    expected_counts = {
        'candidate_scores': candidates,
        'orbit_representatives': sum(representative_counts),
        'score_and_word_ops': candidates * words * factor,
        'score_popcount_word_calls': candidates * words,
        'application_and_word_ops': len(picks) * words * factor,
        'application_word_stores': len(picks) * words,
        'survivor_popcount_word_calls': (2 * len(picks) + int(not eliminated)) * words,
    }
    for key, expected in expected_counts.items():
        require(counts.get(key, 0) == expected, f'{label}: incorrect {key}')
    return {'name': route['name'], 'translation': translation,
            'steps': len(picks), 'eliminated_class': eliminated,
            'eager_scalar_bit_evaluations': verification_reads,
            'verified_counts': expected_counts}


def audit(results_path):
    report = json.loads(results_path.read_text())
    require(report['compile']['exit_code'] == 0, 'producer compilation failed')
    require(report.get('all_requested_cases_completed') is True,
            'producer did not record complete execution')
    require(report.get('coverage_matches_standard_grid') is True,
            'producer did not record standard-grid coverage')
    cases = report['cases']
    keys = [(case['n'], case['gate_budget']) for case in cases]
    require(len(keys) == len(set(keys)) == len(EXPECTED_CASES)
            and set(keys) == EXPECTED_CASES, 'expected exactly the 21 declared cases')
    checked, inputs = [], [{'path': results_path.name, 'sha256': sha256(results_path)}]
    for case in cases:
        n, gates = case['n'], case['gate_budget']
        require(case['exit_code'] == 0, f'{n}:{gates}: producer execution failed')
        nested_path = results_path.parent / f'n{n}_g{gates}.json'
        digest = sha256(nested_path)
        require(digest == case['result_sha256'], f'{n}:{gates}: nested output hash')
        data = json.loads(nested_path.read_text())
        require(data == case['result'], f'{n}:{gates}: nested and embedded data differ')
        require(data['n'] == n and data['gate_budget'] == gates,
                f'{n}:{gates}: result identity')
        tables = data['truth_tables']
        require(tables == sorted(set(tables)) and len(tables) == data['class_size'],
                f'{n}:{gates}: truth-table class shape')
        require(all(type(table) is int and 0 <= table < (1 << (1 << n))
                    for table in tables), f'{n}:{gates}: truth-table domain')
        variables = [sum(1 << x for x in range(1 << n) if (x >> j) & 1)
                     for j in range(n)]
        require(set(variables) <= set(tables), f'{n}:{gates}: initial variables missing')
        if gates == 0:
            require(tables == sorted(variables), f'{n}: incorrect zero-gate class')
        require(data['index']['words_per_survivor_mask'] == (len(tables) + 63) // 64,
                f'{n}:{gates}: index word count')
        translations = [route['translation'] for route in data['routes']]
        require(len(translations) == n + 1
                and set(translations) == {-1, *((1 << w) - 1 for w in range(1, n + 1))},
                f'{n}:{gates}: translation representative coverage')
        maps = permutation_maps(n)
        require(data['permutations'] == len(maps), f'{n}:{gates}: permutation count')
        audited_routes = [replay_route(data, route, maps) for route in data['routes']]
        checked.append({'n': n, 'gate_budget': gates, 'class_size': len(tables),
                        'routes': audited_routes})
        inputs.append({'path': nested_path.name, 'sha256': digest})
    for n in (2, 3, 4):
        by_gate = {case['gate_budget']: set(case['result']['truth_tables'])
                   for case in cases if case['n'] == n}
        for gate in range(1, 7):
            require(by_gate[gate - 1] <= by_gate[gate], f'{n}:{gate}: class monotonicity')
    return {
        'schema_version': 1, 'status': 'passed', 'inputs': inputs,
        'case_count': len(checked),
        'route_count': sum(len(case['routes']) for case in checked),
        'greedy_steps': sum(route['steps'] for case in checked for route in case['routes']),
        'checks': ['exact declared case coverage', 'nested file hashes and payload equality',
                   'bounded truth-table domain, variable base case and class monotonicity',
                   'independent full-action scalar greedy choices and survivor paths',
                   'termination and observation counts',
                   'fixed-translation observation stabilizers and action orbits',
                   'eager scalar bit evaluations and named AND/popcount/store counts'],
        'non_claims': ['No independent proof of bounded DAG class completeness.',
                       'No comparison of every translation or every possible selector.',
                       'No assertion that eager source evaluations equal hardware loads.',
                       'No asymptotic lower bound or P versus NP conclusion.'],
        'cases': checked,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    results_path, output_path = args.results.resolve(), args.output.resolve()
    require(results_path != output_path, 'output must not overwrite input results')
    try:
        result = audit(results_path)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {'schema_version': 1, 'status': 'failed', 'error': str(error)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in
                      ('status', 'case_count', 'route_count', 'greedy_steps', 'error')
                      if key in result}))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()

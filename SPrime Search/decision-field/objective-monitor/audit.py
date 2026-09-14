#!/usr/bin/env python3
"""Pass 11 exact audit: sticky obligation monitor reopening."""
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from objective_monitor import census

ROOT = Path(__file__).resolve().parent
EXPECTED = {
    'systems_with_monitor_collision': 48_822,
    'initial_cases_with_monitor_collision': 126_360,
    'collision_physical_states': 253_380,
    'minimum_certificate_radius_distribution': {'2': 57_024, '3': 54_756, '4': 14_580},
    'initial_cases_by_colliding_state_count': {'0': 135_784, '1': 39_708, '2': 46_284, '3': 40_368, '4': 0},
    'maximum_minimum_certificate_radius': 4,
    'witness': {
        'left_code': 0,
        'right_code': 1,
        'left_map': [0,0,0,0],
        'right_map': [1,0,0,0],
        'initial_state': 0,
        'physical_state': 0,
        'radius': 2,
        'word_without_visit': [],
        'word_with_visit': [1,0],
    },
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_run(binary):
    raw = subprocess.check_output([str(binary)], text=True)
    return raw.encode(), json.loads(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'evidence')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix='pass11-') as tmp:
        binary = Path(tmp) / 'native_objective_monitor'
        subprocess.run([
            'g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',
            str(ROOT/'native_objective_monitor.cpp'),'-o',str(binary)
        ], check=True)
        raw1, native1 = native_run(binary)
        raw2, native2 = native_run(binary)

    if raw1 != raw2 or native1 != native2:
        raise SystemExit('native replays differ')

    python_result = census()
    if python_result != native1:
        raise SystemExit('Python/native census mismatch')

    assert python_result['status'] == 'PASS_BOUNDED'
    assert python_result['ordered_action_map_pairs'] == 65_536
    assert python_result['initial_state_cases'] == 262_144
    for key, value in EXPECTED.items():
        assert python_result[key] == value, (key, python_result[key], value)

    summary = python_result
    sources = ['objective_monitor.py','native_objective_monitor.cpp','CONTRACT.md']
    verification = {
        'status': 'PASS',
        'scope': 'exact four-state/two-action sticky objective-monitor collision census',
        'source_hash_policy': 'SHA-256 of exact checked-out source bytes used by the audit',
        'source_sha256': {name: sha256(ROOT/name) for name in sources},
        'native_replays_identical': True,
        'python_native_exact_match': True,
        'claim_ceiling': 'bounded deterministic finite result; not a universal memory or semantics theorem',
    }
    (args.out/'SUMMARY.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    (args.out/'VERIFICATION.json').write_text(json.dumps(verification, indent=2, sort_keys=True) + '\n')
    print('PASS Pass 11 objective-monitor census')


if __name__ == '__main__':
    main()

"""Exact deformation-signature to rational Hodge-span candidate adapter.

This module does not identify Hodge classes or algebraic cycles. It converts one
explicitly declared S'1 deformation signature through one explicit rational
linear map, then asks the existing Hodge Span Lab exactly one supplied-span
question about the derived candidate.
"""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from span import analyze, scalar

SOURCE_SCHEMA = 's1-deformation-source/v0'
MAP_SCHEMA = 's1-hodge-linear-map/v0'
RESULT_SCHEMA = 'hodge-deformation-bridge-result/v0'
SOURCE_BASIS = ['xw', 'yw', 'zw']
OPERATOR_VERSION = "S'1-Ops v0"


def _plain_dict(value, label):
    if not isinstance(value, dict):
        raise TypeError(f'{label} must be an object')
    return value


def _only_keys(value, allowed, label):
    extra = set(value) - set(allowed)
    if extra:
        raise ValueError(f'unsupported {label} field(s): {sorted(extra)}')


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def _sha256(value):
    return hashlib.sha256(_canonical_json(value).encode('utf-8')).hexdigest()


def _fraction_text(value):
    return str(scalar(value))


def _normalize_source(source):
    source = _plain_dict(source, 'deformation source')
    allowed = {
        'schema', 'source_record_id', 'initial_state', 'mirror_id', 'shell',
        'operator_version', 'actions'
    }
    _only_keys(source, allowed, 'deformation source')
    if source.get('schema') != SOURCE_SCHEMA:
        raise ValueError('unsupported deformation source schema')
    for key in ['source_record_id', 'initial_state', 'mirror_id', 'shell']:
        if not isinstance(source.get(key), str) or not source[key].strip():
            raise ValueError(f'{key} must be a non-empty string')
    if source.get('operator_version') != OPERATOR_VERSION:
        raise ValueError('unsupported deformation source operator version')
    actions = source.get('actions')
    if not isinstance(actions, list):
        raise TypeError('actions must be a list')

    normalized_actions = []
    counts = {plane: 0 for plane in SOURCE_BASIS}
    for action in actions:
        action = _plain_dict(action, 'deformation action')
        _only_keys(action, {'plane', 'degrees'}, 'deformation action')
        plane = action.get('plane')
        degrees = action.get('degrees')
        if plane not in SOURCE_BASIS:
            raise ValueError(f'unsupported deformation plane: {plane}')
        if isinstance(degrees, bool) or type(degrees) is not int or degrees not in (-1, 1):
            raise ValueError('deformation degrees must be exact +1 or -1 integers')
        normalized_actions.append({'plane': plane, 'degrees': degrees})
        counts[plane] += degrees

    normalized = {
        'schema': SOURCE_SCHEMA,
        'source_record_id': source['source_record_id'],
        'initial_state': source['initial_state'],
        'mirror_id': source['mirror_id'],
        'shell': source['shell'],
        'operator_version': OPERATOR_VERSION,
        'actions': normalized_actions,
    }
    signature = [Fraction(counts[plane]) for plane in SOURCE_BASIS]
    return normalized, signature


def _normalize_hodge_template(template):
    template = _plain_dict(template, 'Hodge template')
    allowed = {'schema', 'ambient_dimension', 'basis', 'cycle_vectors', 'target_vectors'}
    _only_keys(template, allowed, 'Hodge template')
    if template.get('schema') != 'hodge-span/v1':
        raise ValueError('unsupported Hodge template schema')
    n = template.get('ambient_dimension')
    if type(n) is not int or not 1 <= n <= 32:
        raise ValueError('Hodge ambient dimension must be 1..32')
    basis = template.get('basis')
    if not isinstance(basis, str) or not basis.strip():
        raise ValueError('Hodge basis must be explicit')

    def vectors(key):
        raw = template.get(key)
        if not isinstance(raw, list) or len(raw) > 64:
            raise ValueError(f'{key} must be a list of at most 64 vectors')
        if any(not isinstance(v, list) or len(v) != n for v in raw):
            raise ValueError(f'{key} vector dimensions disagree with ambient dimension')
        return [[_fraction_text(x) for x in v] for v in raw]

    normalized = {
        'schema': 'hodge-span/v1',
        'ambient_dimension': n,
        'basis': basis,
        'cycle_vectors': vectors('cycle_vectors'),
        'target_vectors': vectors('target_vectors'),
    }
    # Authenticate only the declared exact coordinate shape and span-tool contract.
    # Any geometric meaning remains outside this software boundary.
    analyze(deepcopy(normalized))
    return normalized


def _normalize_map(mapping, ambient_dimension, target_basis):
    mapping = _plain_dict(mapping, 'bridge map')
    allowed = {'schema', 'source_basis', 'target_basis', 'matrix', 'interpretation'}
    _only_keys(mapping, allowed, 'bridge map')
    if mapping.get('schema') != MAP_SCHEMA:
        raise ValueError('unsupported bridge map schema')
    if mapping.get('source_basis') != SOURCE_BASIS:
        raise ValueError('bridge source basis must be exactly xw,yw,zw in order')
    if mapping.get('target_basis') != target_basis:
        raise ValueError('bridge target basis must exactly match the Hodge template basis')
    interpretation = mapping.get('interpretation')
    if not isinstance(interpretation, str) or not interpretation.strip():
        raise ValueError('bridge interpretation is required')
    matrix = mapping.get('matrix')
    if not isinstance(matrix, list) or len(matrix) != ambient_dimension:
        raise ValueError('bridge matrix row dimension must equal Hodge ambient dimension')
    normalized_matrix = []
    for row in matrix:
        if not isinstance(row, list) or len(row) != len(SOURCE_BASIS):
            raise ValueError('bridge matrix column dimension must equal source basis dimension')
        try:
            normalized_row = [scalar(x) for x in row]
        except (ValueError, TypeError, ZeroDivisionError) as exc:
            raise ValueError(f'bridge matrix entries must be exact rational values, never floats: {exc}') from exc
        normalized_matrix.append(normalized_row)
    normalized = {
        'schema': MAP_SCHEMA,
        'source_basis': list(SOURCE_BASIS),
        'target_basis': target_basis,
        'matrix': [[str(x) for x in row] for row in normalized_matrix],
        'interpretation': interpretation,
    }
    return normalized, normalized_matrix


def _matvec(matrix, vector):
    if any(len(row) != len(vector) for row in matrix):
        raise ValueError('bridge matrix dimension does not match deformation signature')
    return [sum((a * b for a, b in zip(row, vector)), Fraction(0)) for row in matrix]


def execute_bridge(source, mapping, hodge_template):
    """Derive and test one exact candidate; never promote its evidentiary authority."""
    normalized_source, signature = _normalize_source(deepcopy(source))
    normalized_hodge = _normalize_hodge_template(deepcopy(hodge_template))
    normalized_map, matrix = _normalize_map(
        deepcopy(mapping), normalized_hodge['ambient_dimension'], normalized_hodge['basis']
    )

    candidate = _matvec(matrix, signature)
    hodge_input = {
        'schema': 'hodge-span/v1',
        'ambient_dimension': normalized_hodge['ambient_dimension'],
        'basis': normalized_hodge['basis'],
        'cycle_vectors': deepcopy(normalized_hodge['cycle_vectors']),
        'target_vectors': [[str(x) for x in candidate]],
    }
    hodge_result = analyze(deepcopy(hodge_input))

    source_carrier = {
        **normalized_source,
        'signature_rule': 'signed-one-degree-plane-count/v0',
        'signature_basis': list(SOURCE_BASIS),
        'signature_vector': [str(x) for x in signature],
    }
    bridge_carrier = {
        **normalized_map,
        'candidate_vector': [str(x) for x in candidate],
    }
    consequence = {
        'tested_relation': 'derived-candidate-in-supplied-rational-cycle-span',
        'tested_target_count': 1,
        'cycle_rank': hodge_result['cycle_rank'],
        'target_rank': hodge_result['target_rank'],
        'target_span_contained': hodge_result['target_span_contained'],
        'target_directions_outside_supplied_cycle_span': hodge_result['target_directions_outside_supplied_cycle_span'],
        'separation_certificates': deepcopy(hodge_result['separation_certificates']),
    }

    return {
        'schema': RESULT_SCHEMA,
        'source': source_carrier,
        'bridge': bridge_carrier,
        'hodge_input': hodge_input,
        'consequence': consequence,
        'provenance': {
            'source_sha256': _sha256(normalized_source),
            'map_sha256': _sha256(normalized_map),
            'hodge_template_sha256': _sha256(normalized_hodge),
            'template_target_count_ignored_for_bridge_test': len(normalized_hodge['target_vectors']),
        },
        'authority': 'candidate-test-only',
        'claim_ceiling': (
            'Synthetic/exact coordinate bridge only. Real 4D is not complex dimension 4. '
            'A deformation signature is not a Hodge class; a candidate direction is not an algebraic cycle; '
            'supplied-span containment or separation does not authenticate geometry, completeness, algebraicity, '
            'or prove/disprove the Hodge conjecture.'
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='JSON object with source, map, and hodge_template')
    args = parser.parse_args()
    try:
        raw = args.input.read_bytes()
        if len(raw) > 1_000_000:
            raise ValueError('bridge input exceeds 1 MB')
        payload = json.loads(raw)
        _plain_dict(payload, 'bridge calibration input')
        _only_keys(payload, {'source', 'map', 'hodge_template'}, 'bridge calibration input')
        result = execute_bridge(payload.get('source'), payload.get('map'), payload.get('hodge_template'))
        print(json.dumps(result, sort_keys=True, indent=2))
    except (ValueError, TypeError, KeyError, ZeroDivisionError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f'Invalid bridge input: {exc}\n')


if __name__ == '__main__':
    main()

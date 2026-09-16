#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import gsfl_operator_projection as projection

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT / 'gsfl-operator-profile.json'
EVIDENCE = ROOT / 'evidence' / 'GSFL_OPERATOR_RESULTS.json'


def build_summary() -> dict:
    profile = projection.load_profile(PROFILE)
    validation = projection.validate_profile(profile)
    if not validation['valid']:
        raise AssertionError(validation['errors'])

    env = {'payload': {
        'source_meaning': {'identity':'same','purpose':'human-machine cooperation'},
        'candidate_meaning': {'identity':'same','purpose':'human-machine cooperation'},
        'candidates': [
            {'id':'mutation','admitted':False,'score':1.0},
            {'id':'human-cooperative','admitted':True,'score':0.8},
        ],
        'claims': {'fit_is_truth': True, 'output_proves_learning': True},
    }, 'trace': []}
    env = projection.apply_operator('OBSERVE', env, observation='human and machine inspect the same declared source')
    env = projection.apply_operator('ROTATE', env, surface='Human and machine partners cooperate through explicit tools without changing source meaning.')
    env = projection.apply_operator('PRESERVE', env, keys=['identity','purpose'])
    env = projection.apply_operator('TRACE_TOOL', env, tool_id='semantic-audit', purpose='verify declared preservation', provenance='GSFL v0.1 complete baseline')
    env = projection.apply_operator('COOPERATE', env, partner_id='human', action='review', detail='reviews machine-proposed surface')
    env = projection.apply_operator('VERIFY', env, checks={'preservation': env['payload']['preservation']['passed']})
    env = projection.apply_operator('FIT', env)
    env = projection.apply_operator('AUDIT_CONFOUNDS', env)
    env = projection.apply_operator('DERIVE_COROLLARIES', env)
    delegated = projection.apply_operator('REPAIR', env)

    native_count = sum(1 for row in profile['operators'] if row['execution']=='GSFL_NATIVE')
    delegate_count = sum(1 for row in profile['operators'] if row['execution']=='DELEGATE_CANONICAL')
    confounds = {row['id'] for row in env['payload']['confounds']}
    corollaries = {row['id'] for row in env['payload']['corollaries']}
    checks = {
        'operator_count_23': len(profile['operators']) == 23,
        'native_count_19': native_count == 19,
        'delegate_count_4': delegate_count == 4,
        'source_lifecycle_complete': profile['source_contract']['lifecycle'] == 'COMPLETE_BOUNDED_V0_1',
        'source_completion_merge_pinned': profile['source_contract']['completion_merge'] == 'cf9d5a35a39b1a7b92f30e24b2789f659e913f04',
        'preservation_passed': env['payload']['preservation']['passed'] is True,
        'fit_selected_admitted_candidate': env['payload']['fit_selection']['id'] == 'human-cooperative',
        'fit_truth_confound_present': 'FIT_SCORE_AS_TRUTH' in confounds,
        'learning_confound_present': 'OUTPUT_AS_LEARNING_EVIDENCE' in confounds,
        'tool_corollary_present': 'TOOL_PROVENANCE_SEPARABLE' in corollaries,
        'attribution_corollary_present': 'ATTRIBUTION_RECONSTRUCTIBLE' in corollaries,
        'repair_delegates_canonical': delegated['payload']['handoffs'][-1]['delegate_to'] == 'REPAIR',
        'source_meaning_preserved': env['payload']['source_meaning'] == {'identity':'same','purpose':'human-machine cooperation'},
    }
    if not all(checks.values()):
        raise AssertionError([k for k,v in checks.items() if not v])
    payload = projection.canonical_json({
        'profile_id': profile['profile_id'],
        'source_contract': profile['source_contract'],
        'operator_count': len(profile['operators']),
        'native_count': native_count,
        'delegate_count': delegate_count,
        'checks': checks,
        'sample_trace': env['trace'],
        'boundaries': profile['boundaries'],
    })
    return {
        'artifact': 'GSFL-v0.1-operator-projection-audit',
        'checks': checks,
        'operator_count': len(profile['operators']),
        'native_count': native_count,
        'delegate_count': delegate_count,
        'source_contract': profile['source_contract'],
        'execution_sha256': hashlib.sha256(payload.encode('utf-8')).hexdigest(),
        'boundaries': profile['boundaries'],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--write', action='store_true')
    args = parser.parse_args()
    summary = build_summary()
    payload = projection.canonical_json(summary)
    if args.write:
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(payload, encoding='utf-8')
    elif args.check:
        if not EVIDENCE.exists() or EVIDENCE.read_text(encoding='utf-8') != payload:
            raise SystemExit('fresh GSFL operator audit does not match frozen evidence')
    else:
        print(payload, end='')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

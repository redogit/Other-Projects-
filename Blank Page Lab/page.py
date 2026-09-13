"""Inspect page/context distinctions and unresolved lineage; no causal inference."""
import argparse
import hashlib
import json
from pathlib import Path


def inspect(data):
    if not isinstance(data, dict): raise ValueError('Expected a JSON object')
    if data.get('schema') != 'blank-page/v1':
        raise ValueError('Unknown schema')
    marks = data.get('marks')
    if not isinstance(marks, str):
        raise ValueError('marks must preserve an exact string')
    if data.get('carrier_state') not in ['present', 'unknown', 'absent']:
        raise ValueError('carrier_state must be explicit')
    for key in ['observer', 'question']:
        if not isinstance(data.get(key), str):
            raise ValueError(f'{key} must be a string')
    context = data.get('context')
    if not isinstance(context, list) or any(not isinstance(v,str) for v in context):
        raise ValueError('context must be a list of source references')
    definitions = data.get('definitions')
    if not isinstance(definitions, dict):
        raise ValueError('definitions must be a dictionary')
    for name in ['OLU_Surface', 'OLU_Context']:
        if name not in definitions or (definitions[name] is not None and not isinstance(definitions[name], str)):
            raise ValueError('Definitions must be exact strings or explicit null')
    history = data.get('lineage')
    if not isinstance(history,list): raise ValueError('lineage must be a list')
    allowed = ['user_recollection','assistant_interpretation','documented_sequence','unresolved']
    questions=[]
    for i, edge in enumerate(history):
        if not isinstance(edge,dict) or edge.get('status') not in allowed:
            raise ValueError('Unknown lineage evidence status')
        if not all(isinstance(edge.get(k),str) and edge[k] for k in ['from','to']):
            raise ValueError('Lineage endpoints are required')
        if not isinstance(edge.get('sources'),list) or any(not isinstance(s,str) or not s for s in edge['sources']):
            raise ValueError('Sources must be reference strings')
        if edge['status']=='documented_sequence' and not edge['sources']:
            raise ValueError('Documented sequence requires references')
        if edge['status']!='documented_sequence':
            questions.append(f'Edge {i}: recover dated records and distinguish recollection from interpretation')
    for name,value in definitions.items():
        if value is None: questions.append(f'Recover the user-defined meaning of {name}; do not infer it from its name')
    return {'schema':'blank-page-result/v1','marks_sha256':hashlib.sha256(marks.encode()).hexdigest(),
            'stored_mark_state':'empty_string' if marks=='' else 'characters_present',
            'carrier_state':data['carrier_state'], 'context_reference_count':len(context),
            'next_questions':questions,
            'definitions':definitions.copy(),
            'boundary':'Empty marks do not establish absent context or metaphysical nothingness. '
            'Whitespace is preserved. References are not authenticated. Documented order is not causation. '
            'No universal definition of blankness or OLU is supplied.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path)
    args=p.parse_args()
    try:
        raw=args.input.read_bytes()
        if len(raw)>1_000_000: raise ValueError('Input exceeds 1 MB')
        print(json.dumps(inspect(json.loads(raw)),indent=2,ensure_ascii=False))
    except (ValueError,TypeError,KeyError,OSError) as e: p.exit(2,f'Invalid input: {e}\n')


if __name__=='__main__': main()

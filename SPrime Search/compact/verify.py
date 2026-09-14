#!/usr/bin/env python3
"""Package-local publication file/hash validation, not a proof assistant."""
import hashlib
import json
import argparse
from pathlib import Path

root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--record',default='evidence/REPAIR_PUBLICATION_2026-09-14.json',
                    help='Package-relative publication record; historical records remain available.')
record_path=(root/parser.parse_args().record).resolve()
if not record_path.is_relative_to(root) or not record_path.is_file():
    raise ValueError('missing or unsafe publication record')
record=json.loads(record_path.read_text(encoding='utf-8'))
if not isinstance(record.get('files'),list) or not record['files']:
    raise ValueError('expected a nonempty file hash record')
seen=set()
for entry in record['files']:
    if entry['path'] in seen:
        raise ValueError('duplicate path: '+entry['path'])
    seen.add(entry['path'])
    path=(root/entry['path']).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('missing or unsafe path: '+entry['path'])
    if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
        raise ValueError('changed file: '+entry['path'])
print(json.dumps({'status':'PASS','files_checked':len(record['files']),
                  'record':record_path.relative_to(root).as_posix(),
                  'scope':'Declared publication bytes; not independent scientific replication.'}))

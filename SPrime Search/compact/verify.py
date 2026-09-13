#!/usr/bin/env python3
"""Package-local publication file/hash validation, not a proof assistant."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parent
record=json.loads((root/'evidence/PUBLICATION.json').read_text(encoding='utf-8'))
for entry in record['files']:
    path=(root/entry['path']).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('missing or unsafe path: '+entry['path'])
    if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:
        raise ValueError('changed file: '+entry['path'])
print(json.dumps({'status':'PASS','files_checked':len(record['files']),
                  'scope':'Declared publication bytes; not independent scientific replication.'}))

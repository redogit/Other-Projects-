#!/usr/bin/env python3
"""Check this publication's declared source hashes; not formal verification."""
import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parent
record = json.loads((root/'evidence/VERIFICATION.json').read_text(encoding='utf-8'))
for name, expected in record['source_hashes'].items():
    path = (root/name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Missing or unsafe source: '+name)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Source changed: '+name)
print(json.dumps({'status':'PASS', 'source_hashes_checked':len(record['source_hashes']),
                  'scope':'Publication byte integrity; not a proof or independent replication.'}))

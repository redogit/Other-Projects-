#!/usr/bin/env python3
"""Verify this publication's declared local hashes; not a formal proof tool."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root/'evidence/RUN_MANIFEST.json').read_text(encoding='utf-8'))
count = 0
for section in ('input_artifacts', 'outputs'):
    for record in manifest[section]:
        path = (root/record['path']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError('missing or unsafe path: ' + record['path'])
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != record['sha256']:
            raise ValueError('hash mismatch: ' + record['path'])
        count += 1
print(json.dumps({'status': 'PASS', 'file_hashes_checked': count,
                  'scope': 'Declared publication byte custody, not semantic or formal verification.'}))

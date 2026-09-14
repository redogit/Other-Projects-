#!/usr/bin/env python3
"""Check this publication's declared source hashes; not formal verification."""
import hashlib
import json
import argparse
from pathlib import Path
root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--record', default='evidence/REPAIR_PUBLICATION_2026-09-14.json',
                    help='Package-relative publication record; historical records remain available.')
record_path = (root/parser.parse_args().record).resolve()
if not record_path.is_relative_to(root) or not record_path.is_file():
    raise ValueError('Missing or unsafe publication record')
record = json.loads(record_path.read_text(encoding='utf-8'))
entries = record['source_hashes']
if not isinstance(entries, dict) or not entries:
    raise ValueError('Expected a nonempty source hash record')
for name, expected in entries.items():
    path = (root/name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Missing or unsafe source: '+name)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Source changed: '+name)
print(json.dumps({'status':'PASS', 'source_hashes_checked':len(entries),
                  'record':record_path.relative_to(root).as_posix(),
                  'scope':'Publication byte integrity; not a proof or independent replication.'}))

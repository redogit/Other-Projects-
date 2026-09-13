#!/usr/bin/env python3
"""Verify and expand the bundled public accession; build a searchable offline page.

Python 3.10+, standard library only. No downloads and no execution of source text.
Existing different output bytes are not overwritten unless --overwrite is given.
"""
from __future__ import annotations
import argparse
import base64
from collections import Counter
import hashlib
import html
import io
import json
import lzma
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
FILES = {'records.jsonl', 'sources.json', 'relations.json', 'remainder.json', 'stats.json'}
LIMIT = 2 * 1024 * 1024
PARTS = tuple(f'accession-01.zip.xz.b64.{i:02}' for i in range(1,5))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_seed(root: Path = ROOT) -> tuple[dict[str, bytes], dict]:
    """Hashes bind this snapshot, not the historical truth of its contents."""
    lock = json.loads((root / 'data/manifest.json').read_text(encoding='utf-8'))
    if lock.get('format') != 'HEA-PUBLIC-SEED-1' or set(lock['files']) != FILES:
        raise ValueError('unsupported or incomplete accession manifest')
    if type(lock['zip_bytes']) is not int or not 0 < lock['zip_bytes'] <= LIMIT:
        raise ValueError('invalid expanded size')
    encoded = b''.join((root / 'data' / part).read_bytes() for part in PARTS)
    if len(encoded) > LIMIT:
        raise ValueError('seed input exceeds limit')
    packed = base64.b64decode(b''.join(encoded.split()), validate=True)
    if sha(packed) != lock['packed_sha256']:
        raise ValueError('packed accession digest mismatch')
    decoder = lzma.LZMADecompressor(memlimit=128 * 1024 * 1024)
    raw = decoder.decompress(packed, max_length=lock['zip_bytes'] + 1)
    if not decoder.eof or decoder.unused_data or len(raw) != lock['zip_bytes']:
        raise ValueError('expanded seed size or stream mismatch')
    if sha(raw) != lock['zip_sha256']:
        raise ValueError('expanded seed digest mismatch')
    contents = {}
    with ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.infolist()) != len(FILES) or set(archive.namelist()) != FILES:
            raise ValueError('unexpected archive members')
        for info in archive.infolist():
            expected = lock['files'][info.filename]
            if stat.S_ISLNK(info.external_attr >> 16) or info.file_size != expected['bytes']:
                raise ValueError('invalid archive member')
            if not 0 <= info.file_size <= LIMIT:
                raise ValueError('member size limit exceeded')
            data = archive.read(info.filename)
            if sha(data) != expected['sha256']:
                raise ValueError('member digest mismatch')
            data.decode('utf-8', 'strict')
            contents[info.filename] = data
    return contents, lock


def safe_url(value: str) -> str:
    url = urlsplit(value)
    if url.scheme not in ('http', 'https') or not url.netloc or url.username or url.password:
        raise ValueError('source URL is not a public HTTP(S) location')
    return html.escape(value, quote=True)


def render(contents: dict[str, bytes]) -> str:
    rows = [json.loads(line) for line in contents['records.jsonl'].splitlines()]
    sources = {s['id']: s for s in json.loads(contents['sources.json'])}
    counts = Counter(r['record_type'] for r in rows)
    esc = lambda value: html.escape(str(value), quote=True)
    cards = []
    for record in rows:
        text = record.get('verbatim_source_excerpt')
        language = record.get('excerpt_language') or 'und'
        if not re.fullmatch(r'[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*', language):
            language = 'und'
        quote = ''
        if text:
            quote = f'<blockquote lang="{esc(language)}" dir="auto"><bdi>{esc(text)}</bdi></blockquote>'
            if record.get('working_english_gloss'):
                quote += '<p><strong>Editorial English gloss, not a certified translation:</strong> ' + esc(record['working_english_gloss']) + '</p>'
        warnings = record.get('content_advisories', [])
        advisory = ''
        if warnings:
            advisory = '<p class="note"><strong>Context:</strong> ' + esc('; '.join(warnings)) + '. Documentation is not endorsement.</p>'
            if quote:
                quote = '<details><summary>Read preserved wording for ' + esc(record['id']) + '</summary>' + quote + '</details>'
        links = []
        for sid in record['source_ids']:
            source = sources[sid]
            links.append('<a rel="noreferrer" href="' + safe_url(source['url']) + '">' + esc(source['institution']) + '</a>')
        relations = []
        for relation in record.get('relations', []):
            relations.append('<pre>' + esc(json.dumps(relation, ensure_ascii=False, indent=2)) + '</pre>')
        extra = {'source_locator': record.get('source_locator'), 'original_script_present': record.get('original_script_present'),
                 'event_date_raw': record.get('event_date_raw'), 'event_date_iso': record.get('event_date_iso'),
                 'date_status': record.get('date_status'), 'quality_flags': record.get('quality_flags'),
                 'rights': record.get('rights')}
        search = ' '.join(str(record.get(k) or '') for k in ('id','title','verbatim_source_excerpt','working_english_gloss','summary','language_of_tradition_as_reported','community_or_tradition_as_reported'))
        cards.append(f'<article class="record" id="{esc(record["id"])}" data-kind="{esc(record["record_type"])}" data-search="{esc(search)}">'
                     f'<h2>{esc(record["id"])} — {esc(record["title"])}</h2>'
                     f'<p>{esc(record["language_of_tradition_as_reported"])} · {esc(record["community_or_tradition_as_reported"])}</p>'
                     + advisory + quote + '<p>' + esc(record['summary']) + '</p>'
                     + '<p><strong>Claim treatment:</strong> ' + esc(record['truth_status']) + '</p>'
                     + '<p><strong>Origin:</strong> ' + esc(record['origin_status']) + '</p>'
                     + '<p>Source: ' + ' · '.join(links) + '</p>'
                     + '<details><summary>Dates, source locator, rights and review limits</summary><pre>'
                     + esc(json.dumps(extra, ensure_ascii=False, indent=2)) + '</pre></details>'
                     + ('<details><summary>Qualified relations</summary>' + ''.join(relations) + '</details>' if relations else '') + '</article>')
    options = ''.join(f'<option value="{esc(kind)}">{esc(kind.replace("_", " "))} ({count})</option>' for kind,count in sorted(counts.items()))
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Human Expression Archive — accession 01</title><style>
body{font:1.05rem/1.65 system-ui,sans-serif;max-width:80ch;margin:auto;padding:1.2rem;overflow-wrap:anywhere;color:#152d3b;background:#fff}h1,h2{line-height:1.25}h1{font-size:2.4rem}h2{font-size:1.3rem}a{color:#064e73}a:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid #974200;outline-offset:3px}.record{border-top:1px solid #bacbd2;padding:1.2rem 0;scroll-margin-top:1rem}blockquote{border-inline-start:3px solid #14627a;margin-inline:0;padding:.5rem 1rem;font-size:1.2rem}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f6f7;padding:.8rem}label{display:block;font-weight:bold}input,select{font:inherit;max-width:100%;box-sizing:border-box;padding:.5rem;width:100%;margin-bottom:.8rem}.note{border-inline-start:4px solid #805415;padding:.6rem;background:#fff7ee}summary{cursor:pointer;font-weight:bold}.skip{position:absolute;top:-100px}.skip:focus{top:0;background:white}[hidden]{display:none!important}
</style></head><body><a href="#main" class="skip">Skip to archive</a><main id="main"><header>
<h1>Human Expression Archive</h1><p>Accession 01 · September 13, 2026 · <strong>91 records, not a census of humanity.</strong></p>
<p>Preservation does not imply endorsement. Source wording, working glosses, uncertain origins and rights remain separate. The collection contains 52 short saying excerpts and 39 metadata or gateway records, including nine archive gateways; gateways are not their complete holdings. No full song or recording is included.</p>
<p>The inherited source reviews have not been repeated for this publication. Rights, cultural review and accessibility certification remain unresolved where noted. No human learning or model-training result is inferred.</p>
<p><a href="data/records.jsonl">Exact original JSONL records</a> · <a href="data/sources.json">Source register</a> · <a href="data/remainder.json">Unresolved remainder</a></p>
</header><section aria-label="Search archive"><label for="query">Search wording, script or context</label><input id="query" type="search" autocomplete="off"><label for="kind">Record kind</label><select id="kind"><option value="all">All record kinds</option>''' + options + '''</select><p id="count" role="status" aria-live="polite">91 records shown.</p><noscript><p>All records appear below. Browser Find also works.</p></noscript></section>''' + ''.join(cards) + '''<footer><p>Canonical project: redogit/Other-Projects- / Human Expression Archive. Exact source data is preserved without normalization; this page is a newly rendered view.</p></footer></main>
<script>
const query=document.getElementById('query'), kind=document.getElementById('kind');
const rows=[...document.querySelectorAll('.record')];
function filter(){const q=query.value.toLocaleLowerCase();let shown=0;for(const r of rows){const match=r.dataset.search.toLocaleLowerCase().includes(q)&&(kind.value==='all'||r.dataset.kind===kind.value);r.hidden=!match;if(match)shown++;}document.getElementById('count').textContent=shown+' records shown.';}
query.addEventListener('input',filter);kind.addEventListener('change',filter);
</script></body></html>'''


def build(out: Path, overwrite: bool = False) -> dict:
    contents, lock = load_seed()
    outputs = {Path('data') / name: data for name,data in contents.items()}
    outputs[Path('index.html')] = render(contents).encode('utf-8')
    # Preflight every path before making any write; no partial overwrite on conflict.
    for name,data in outputs.items():
        target = out / name
        if target.exists() and target.read_bytes() != data and not overwrite:
            raise FileExistsError(f'{target} differs; use another output directory or --overwrite')
    for name,data in outputs.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {'status':'PASS','output':str(out),'records':91,'files':{str(k):sha(v) for k,v in outputs.items()},'claim':'byte custody and page generation only'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'public')
    parser.add_argument('--overwrite',action='store_true')
    args=parser.parse_args()
    print(json.dumps(build(args.out,args.overwrite),indent=2))

import copy
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import build
sys.path.insert(0,str(ROOT.parent/'S1024 Compression Lab'))
import sections1024 as s


class Tags(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.records=0;self.langs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='article':self.records+=1
        if tag=='blockquote':self.langs.append(a.get('lang'))


class ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files,cls.lock=build.load_seed()
        cls.rows=[json.loads(x) for x in cls.files['records.jsonl'].splitlines()]

    def test_exact_custody_and_source_links(self):
        self.assertEqual(len(self.rows),91)
        self.assertEqual(build.sha(self.files['records.jsonl']),'2094c0b82ad19f0d3615d351ea210aa90ed4cb7ec774d86569dd8a88b502f14b')
        sources=json.loads(self.files['sources.json'])
        ids={x['id'] for x in sources}
        self.assertEqual(len({x['url'] for x in sources}),81)
        for r in self.rows:
            self.assertTrue(set(r['source_ids'])<=ids)
            self.assertIn('rights',r)
            if r.get('verbatim_source_excerpt'):
                self.assertEqual(build.sha(r['verbatim_source_excerpt'].encode()),r['excerpt_sha256'])
        self.assertEqual(len(json.loads(self.files['relations.json'])),13)
        self.assertEqual(len(json.loads(self.files['remainder.json'])),10)

    def test_archive_section_roundtrip(self):
        data=self.files['records.jsonl'];f=s.frame(data)
        self.assertEqual(s.unframe(f),data)
        self.assertEqual(len(f['sections']),154)
        self.assertEqual(f['sections'][-1]['byte_length'],42)
        self.assertEqual(sum(x['utf8_state_out']!=0 for x in f['sections']),3)

    def test_offline_page_structure(self):
        page=build.render(self.files);tags=Tags();tags.feed(page)
        self.assertEqual(tags.records,91)
        self.assertEqual(len(tags.ids),len(set(tags.ids)))
        self.assertEqual(len(tags.langs),52)
        self.assertTrue(all(tags.langs))
        self.assertIn('aria-live="polite"',page)
        self.assertIn('<noscript>',page)
        self.assertEqual(page.count('<script>'),1)

    def test_preserve_different_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            build.build(out)
            first=(out/'index.html').read_bytes()
            build.build(out)
            self.assertEqual((out/'index.html').read_bytes(),first)
            (out/'index.html').write_text('keep me',encoding='utf-8')
            with self.assertRaises(FileExistsError):build.build(out)
            self.assertEqual((out/'index.html').read_text(),'keep me')

    def test_quoted_markup_is_not_executed(self):
        files=dict(self.files);rows=copy.deepcopy(self.rows)
        rows[0]['verbatim_source_excerpt']='<script>alert(1)</script>'
        files['records.jsonl']=b'\n'.join(json.dumps(r,ensure_ascii=False).encode() for r in rows)
        page=build.render(files)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',page)
        self.assertNotIn('<script>alert(1)</script>',page)
        with self.assertRaises(ValueError):build.safe_url('javascript:alert(1)')
        with self.assertRaises(ValueError):build.safe_url('https://user:password@example.test/')

    def test_seed_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir()
            (root/'data/manifest.json').write_bytes((ROOT/'data/manifest.json').read_bytes())
            for part in build.PARTS:
                (root/'data'/part).write_bytes((ROOT/'data'/part).read_bytes())
            first=root/'data'/build.PARTS[0]
            data=first.read_bytes()
            first.write_bytes(b'AAAA'+data[4:])
            with self.assertRaises(ValueError):build.load_seed(root)


if __name__ == '__main__':unittest.main()

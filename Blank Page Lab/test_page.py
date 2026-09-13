import copy
import json
from pathlib import Path
import unittest
from page import inspect


class Tests(unittest.TestCase):
    def setUp(self): self.d=json.loads(Path(__file__).with_name('example.json').read_text())
    def test_empty_not_absent(self):
        self.d['context']=['synthetic/source'];r=inspect(self.d)
        self.assertEqual(r['stored_mark_state'],'empty_string')
        self.assertEqual(r['carrier_state'],'present')
        self.assertEqual(r['context_reference_count'],1)
    def test_whitespace_is_preserved(self):
        first=inspect(self.d);self.d['marks']=' \n\u200b';second=inspect(self.d)
        self.assertEqual(second['stored_mark_state'],'characters_present')
        self.assertNotEqual(first['marks_sha256'],second['marks_sha256'])
    def test_definitions_not_invented(self):
        before=copy.deepcopy(self.d);r=inspect(self.d)
        self.assertIsNone(r['definitions']['OLU_Surface']);self.assertEqual(before,self.d)
        self.assertEqual(len(r['next_questions']),4)
    def test_documented_needs_source(self):
        self.d['lineage'][0].update(status='documented_sequence',sources=[])
        with self.assertRaises(ValueError): inspect(self.d)
    def test_unknown_status_rejected(self):
        self.d['lineage'][0]['status']='proved_causation'
        with self.assertRaises(ValueError): inspect(self.d)


if __name__=='__main__': unittest.main()

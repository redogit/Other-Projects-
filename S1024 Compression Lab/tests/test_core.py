import copy
import itertools
import math
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sections1024 as s
from learning_probe import decode_payload
from demo import run


class CoreTests(unittest.TestCase):
    def test_utf8_complete_small_space(self):
        for n in range(3):
            for word in itertools.product(range(256), repeat=n):
                data = bytes(word)
                try:
                    data.decode('utf-8', 'strict')
                    expected = True
                except UnicodeDecodeError:
                    expected = False
                self.assertEqual(s.scan(data) == 0, expected)

    def test_transport_all_lengths(self):
        rng = random.Random(1024)
        for n in range(1025):
            data = rng.randbytes(n)
            values = s.pack_floats(data)
            self.assertTrue(all(math.isfinite(v) and v > 0 for v in values))
            self.assertEqual(s.unpack_floats(values, n), data)
        self.assertEqual(len(s.pack_floats(bytes(1024))), 133)

    def test_rank_census(self):
        space = s.UTF8Space()
        counts = [1]
        weights = (128, 1920, 61440, 1048576)
        for n in range(1, 1025):
            counts.append(sum(w*counts[n-k] for k,w in enumerate(weights,1) if n >= k))
        for n, count in enumerate(counts):
            self.assertEqual(space.count(n), count)
        for n in (0,1,2,3,4,7,8,1024):
            for rank in sorted({0, space.count(n)//2, space.count(n)-1}):
                data=space.unrank(n,rank)
                self.assertEqual(space.rank(data),rank)
        self.assertEqual((space.count(1024)-1).bit_length(),7348)

    def test_multibyte_boundaries_and_search(self):
        for character in ('é','S′','界','🌍'):
            for prefix in (1021,1022,1023):
                raw=('a'*prefix+character+'b'*1030).encode('utf-8')
                f=s.frame(raw)
                self.assertEqual(s.unframe(f),raw)
                self.assertEqual(list(s.literal_offsets([raw[i:i+1024] for i in range(0,len(raw),1024)],character.encode())),[prefix])

    def test_repair_exhaustive_small_constraints(self):
        for width in range(1,4):
            for b,p,r,t in itertools.product(range(1<<width),repeat=4):
                cube=s.solve(width,b,p,r,t)
                oracle=[x for x in range(1<<width) if ((x^b)&p)==0 and ((x^t)&r)==0]
                self.assertEqual(cube.solution_count,len(oracle))
                self.assertEqual([x for x in range(1<<width) if cube.accepts(x)],oracle)
                self.assertEqual([cube.unrank(i) for i in range(len(oracle))],oracle)
                minimum=cube.minimum_hamming_repair()
                if not oracle:self.assertIsNone(minimum)
                else:self.assertEqual((minimum^b).bit_count(), min((x^b).bit_count() for x in oracle))
        cube=s.solve(8192,0,1,1<<8191,1<<8191)
        self.assertEqual(cube.minimum_hamming_repair(),1<<8191)
        self.assertEqual(cube.solution_count,1<<8190)

    def test_tamper_controls(self):
        original=s.frame(('a'*1023+'🌍'+'b'*1100).encode())
        mutations=[]
        x=copy.deepcopy(original);x['extra']=1;mutations.append(x)
        x=copy.deepcopy(original);x['sections'].pop();mutations.append(x)
        x=copy.deepcopy(original);x['sections'].reverse();mutations.append(x)
        x=copy.deepcopy(original);x['sections'][0]['sha256']='0'*64;mutations.append(x)
        x=copy.deepcopy(original);x['sections'][0]['utf8_state_out']=0;mutations.append(x)
        x=copy.deepcopy(original);x['sections'][0]['byte_length']=1000;mutations.append(x)
        x=copy.deepcopy(original);x['sha256']='0'*64;mutations.append(x)
        x=copy.deepcopy(original);x['sections'][0]['float_hex'][0]='nan';mutations.append(x)
        for bad in mutations:
            with self.assertRaises((ValueError,TypeError)):s.unframe(bad)

    def test_frozen_learning_and_shift(self):
        result=run()
        self.assertEqual(result['fit']['period'],8)
        self.assertEqual(result['related']['selected_record_bytes'],16)
        self.assertEqual(result['shifted']['selected'],'RAW')
        self.assertEqual(result['shifted']['selected_record_bytes'],1025)
        for invalid in (b'',b'Q',b'R',b'P\0\0\0\0x'):
            with self.assertRaises(ValueError):decode_payload(invalid)


if __name__ == '__main__':unittest.main()

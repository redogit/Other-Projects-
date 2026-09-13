import itertools
import unittest
from fractions import Fraction
from span import analyze, dot, rref


def case(c, t, n=2):
    return dict(schema='hodge-span/v1', ambient_dimension=n,
                basis='synthetic standard basis', cycle_vectors=c, target_vectors=t)


class Tests(unittest.TestCase):
    def test_all_small_two_by_two(self):
        # Independent determinant oracle: all 81 matrices over {-1,0,1}.
        for a,b,c,d in itertools.product([-1,0,1], repeat=4):
            expected = 2 if a*d-b*c else (1 if any([a,b,c,d]) else 0)
            result = analyze(case([[a,b],[c,d]], [[1,0],[0,1]]))
            self.assertEqual(result['cycle_rank'], expected)
            self.assertEqual(result['target_span_contained'], expected == 2)
            for w in result['separation_certificates']:
                v = list(map(Fraction, w['annihilating_covector']))
                self.assertEqual(dot(v,[a,b]), 0)
                self.assertEqual(dot(v,[c,d]), 0)
                self.assertNotEqual(v[w['target_index']],0)

    def test_duplicates_are_not_rank(self):
        r=analyze(case([[1,0],[2,0],[1,0]],[[0,1]]))
        self.assertEqual((r['cycle_count'],r['cycle_rank']), (3,1))

    def test_rational_not_integral(self):
        self.assertTrue(analyze(case([[2,0]],[[1,0]]))['target_span_contained'])
        self.assertTrue(analyze(case([['1/3',0]],[[1,0]]))['target_span_contained'])

    def test_empty_spans(self):
        self.assertFalse(analyze(case([],[[1,0]]))['target_span_contained'])
        self.assertTrue(analyze(case([],[]))['target_span_contained'])

    def test_bad_inputs(self):
        for bad in [case([[0.1,0]],[]), case([[True,0]],[]), case([[1]],[]),
                    case([['1/0',0]],[]), case([[1<<300,0]],[])]:
            with self.assertRaises((ValueError,ZeroDivisionError)):
                analyze(bad)


if __name__ == '__main__': unittest.main()

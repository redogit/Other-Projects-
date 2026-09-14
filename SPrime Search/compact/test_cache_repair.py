#!/usr/bin/env python3
"""Regression checks for exact semantic input types and plan-cache ownership."""
from copy import deepcopy
from itertools import combinations
import unittest

import compact


def independent_plan(tables):
    """Uncached scalar oracle on small sets, with the documented row tie break."""
    if len(tables) == 1:
        return {'questions': 0, 'table': tables[0]}
    choices = []
    for row in range(8):
        zero = tuple(f for f in tables if (f // (2 ** row)) % 2 == 0)
        one = tuple(f for f in tables if (f // (2 ** row)) % 2 == 1)
        if zero and one:
            children = [independent_plan(zero), independent_plan(one)]
            choices.append({'questions': 1 + max(c['questions'] for c in children),
                            'row': row, 'answers': children})
    return min(choices, key=lambda p: (p['questions'], p['row']))


class CacheRepairTests(unittest.TestCase):
    def setUp(self):
        compact.clear_query_cache()

    def tearDown(self):
        compact.clear_query_cache()

    def test_invalid_types_rejected_cold_and_warm(self):
        cases = [((0, 1), (False, True)), ((0, 1), (0.0, 1.0)),
                 ((82, 90), (82.0, 90.0)), ((1,), (True,))]
        for valid, invalid in cases:
            for warm in (False, True):
                with self.subTest(valid=valid, invalid=invalid, warm=warm):
                    compact.clear_query_cache()
                    if warm:
                        compact.query_plan(valid)
                    before = compact.query_cache_info()
                    with self.assertRaises(ValueError):
                        compact.query_plan(invalid)
                    with self.assertRaises(ValueError):
                        compact.refine(invalid, 0, None)
                    self.assertEqual(compact.query_cache_info(), before)

    def test_invalid_collections_rejected_before_lookup(self):
        for invalid in (None, [], [82, 90], (), (90, 82), (82, 82),
                        (-1,), (256,), ('82',), ({},)):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    compact.query_plan(invalid)
        self.assertEqual(compact.query_cache_info().currsize, 0)

    def test_bounded_cache_evicts_and_clear_releases_entries(self):
        self.assertEqual(compact.query_cache_info().maxsize, compact.QUERY_CACHE_LIMIT)
        for f in range(compact.QUERY_CACHE_LIMIT + 1):
            self.assertEqual(compact.query_plan((f,)), {'questions': 0, 'table': f})
        before = compact.query_cache_info()
        self.assertEqual(before.currsize, compact.QUERY_CACHE_LIMIT)
        compact.query_plan((0,))  # Oldest entry was evicted.
        self.assertEqual(compact.query_cache_info().misses, before.misses + 1)
        compact.clear_query_cache()
        info = compact.query_cache_info()
        self.assertEqual((info.hits, info.misses, info.currsize), (0, 0, 0))
        compact.clear_query_cache()  # Repeated release is harmless.

    def test_isolated_plans_remain_usable_after_clear(self):
        tables = (82, 90, 114, 122)
        plan = compact.query_plan(tables)
        expected = deepcopy(plan)
        poison = compact.query_plan(tables)
        poison['answers'][0]['questions'] = -100
        self.assertEqual(compact.query_plan(tables), expected)
        compact.clear_query_cache()
        self.assertEqual(plan, expected)
        self.assertEqual(compact.query_plan(tables), expected)

    def test_all_255_small_subsets_match_independent_minimax_plan(self):
        checked = 0
        for size in range(1, 9):
            for tables in combinations(range(8), size):
                self.assertEqual(compact.query_plan(tables), independent_plan(tables))
                checked += 1
        self.assertEqual(checked, 255)

    def test_refinement_validates_without_unneeded_compilation(self):
        tables = (82, 90, 114, 122)
        self.assertEqual(compact.refine(tables, 3, None), tables)
        self.assertEqual(compact.refine(tables, 3, 1), (90, 122))
        for row, answer in ((0, 1), (3, True), (3, 1.0), (False, None)):
            with self.assertRaises(ValueError):
                compact.refine(tables, row, answer)
        self.assertEqual(compact.query_cache_info().currsize, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)

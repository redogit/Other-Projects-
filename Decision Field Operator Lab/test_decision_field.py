import unittest

from decision_field import (
    DecisionField,
    DecisionFieldSolver,
    GravityScore,
    Probe,
    consequentially_equivalent,
)


class GoalFilter:
    name = "goal-filter"

    def precondition(self, field):
        return field.goal in field.possibilities and len(field.possibilities) > 1

    def probe(self, field):
        return Probe(
            self.name,
            GravityScore(
                irreversible_fact=1,
                kernel_reduction=len(field.possibilities) - 1,
            ),
            True,
        )

    def apply(self, field, probe):
        return DecisionField(
            possibilities=frozenset({field.goal}),
            relations=field.relations,
            evidence=field.evidence,
            goal=field.goal,
            unresolved=frozenset(),
            observer=field.observer,
            history=field.history + (self.name,),
        )


def normalize(field):
    return field


def learn(field):
    return field


def goal_result(field):
    if field.possibilities == frozenset({field.goal}):
        return ("YES", field.goal)
    return None


def impossible_result(field):
    if field.goal not in field.possibilities:
        return ("NO", None)
    return None


def branch(field):
    values = sorted(field.possibilities)
    if len(values) <= 1:
        return []
    mid = len(values) // 2
    chunks = (values[:mid], values[mid:])
    return [
        DecisionField(
            possibilities=frozenset(chunk),
            relations=field.relations,
            evidence=field.evidence,
            goal=field.goal,
            unresolved=field.unresolved,
            observer=field.observer,
            history=field.history + ("branch",),
        )
        for chunk in chunks
        if chunk
    ]


def combine(results):
    return next((r for r in results if r[0] == "YES"), ("NO", None))


class DecisionFieldTests(unittest.TestCase):
    def solver(self):
        return DecisionFieldSolver(
            operators=[GoalFilter()],
            normalize=normalize,
            goal_result=goal_result,
            impossible_result=impossible_result,
            learn=learn,
            branch=branch,
            combine=combine,
            canonical_key=lambda f: (f.possibilities, f.goal),
        )

    def test_operator_reaches_goal(self):
        field = DecisionField(
            possibilities=frozenset({0, 1, 2, 3}),
            relations=(),
            evidence=(),
            goal=2,
            unresolved=frozenset({0, 1, 3}),
        )
        self.assertEqual(self.solver().solve(field), ("YES", 2))

    def test_impossible_goal_is_certified(self):
        field = DecisionField(
            possibilities=frozenset({0, 1, 3}),
            relations=(),
            evidence=(),
            goal=2,
            unresolved=frozenset({0, 1, 3}),
        )
        self.assertEqual(self.solver().solve(field), ("NO", None))

    def test_consequential_equivalence_is_task_local(self):
        parity = lambda x: x % 2
        under_ten = lambda x: x < 10
        self.assertTrue(consequentially_equivalent(2, 4, [parity, under_ten]))
        self.assertFalse(consequentially_equivalent(2, 3, [parity, under_ten]))

    def test_gravity_score_is_lexicographic(self):
        proof = GravityScore(terminal=1)
        many_heuristics = GravityScore(heuristic_gain=10_000)
        self.assertGreater(proof, many_heuristics)


if __name__ == "__main__":
    unittest.main()

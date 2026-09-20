"""Public runtime witnesses for the declared REPAIR mutation boundary."""
from copy import deepcopy
import json
import unittest

from omega import canonical_json, make_omega
from rmapl import parse_rmapl
from rmapl_runtime import run_program


def native():
    return make_omega(
        native_type="mutation-scope-fixture/v0", native_identity="fixture:scope",
        source_refs=["fixture:scope"],
        state={"x": 0, "guard": {"value": 7}, "items": [1, 2],
               "nested": {"leaf": 1}, "dot.key": 0},
        path=[], frame={"obligation": "change-only-declared-subtrees"},
        invariants=[], observations=[], residuals=[{"kind": "gap"}],
        decision_field={"goal": "bounded-change"}, provenance=[], evidence=[],
        claim_ceiling=["BOUNDED_SOFTWARE_FIXTURE"],
        resource_bounds={"maxSteps": 1}, domain_remainder={},
    )


def program(allowed, *, preserves=("identity", "claim-ceiling"), forbids=(), fitter=False):
    lines = ["RMAPL 0", "PROGRAM mutation-scope", "LOAD fixture",
             "FITTER edit" if fitter else "REPAIR edit", 'WHEN "gap"', "REQUIRES []"]
    if not fitter:
        lines.append('TARGETS ["gap"]')
    lines.append("PRESERVES " + json.dumps(list(preserves)))
    if fitter:
        lines.append('OBJECTIVES {"residualReduction":"max"}')
    else:
        lines += ["MAY_MUTATE " + json.dumps(list(allowed)),
                  "FORBIDS " + json.dumps(list(forbids))]
    lines += ["APPLY edit", "EVIDENCE []", "COST 1", "END", "RUN"]
    return parse_rmapl("\n".join(lines) + "\n")


def metrics():
    return {
        "residualReduction": 1, "invariantPreservation": 1,
        "reconstructibility": 1, "reversibility": 1, "evidenceCoverage": 1,
        "branchReduction": 1, "provenanceCompleteness": 1, "semanticLoss": 0,
        "ambiguityIntroduction": 0, "relationGrowth": 0, "runtimeCost": 1,
        "economicCost": 0, "unresolvedGrowth": 0, "irreversibleMutation": 0,
    }


def execute(edit, allowed=("state.x",), **options):
    initial = native()
    before = canonical_json(initial)

    def operator(omega):
        construction = deepcopy(omega["construction"])
        edit(construction)
        return {
            "omega": make_omega(**construction), "consequenceKey": "scope-fixture",
            "metrics": metrics(), "knowledgeDecay": {},
            "reconstruction": {"status": "exact"},
        }

    result = run_program(program(allowed, **options), initial, {"edit": operator})
    if canonical_json(initial) != before:
        raise AssertionError("caller input was mutated")
    return result


class MutationScopeTests(unittest.TestCase):
    def rejected(self, edit, path, allowed=("state.x",), **options):
        result = execute(edit, allowed, **options)
        branch = result["branches"][0]
        self.assertFalse(branch["admitted"], branch)
        self.assertEqual(branch["classification"], "MUTATION")
        self.assertIn(path, branch["inspection"]["mutated"])
        gate = next(g for g in branch["inspection"]["gates"] if g["name"] == "may_mutate")
        self.assertEqual(gate["status"], "failed")
        self.assertIn(path, gate["paths"])
        self.assertEqual(result["stopReason"], "NO_ADMISSIBLE_PROGRESS")
        return branch

    def test_undeclared_scalar_edit_is_not_admitted(self):
        self.rejected(lambda c: c["state"]["guard"].update(value=8), "state.guard.value")

    def test_undeclared_addition_is_not_admitted(self):
        self.rejected(lambda c: c["state"].update(extra=1), "state.extra")

    def test_undeclared_deletion_is_not_admitted(self):
        self.rejected(lambda c: c["state"].pop("guard"), "state.guard")

    def test_empty_allowlist_does_not_authorize_edits(self):
        self.rejected(lambda c: c["state"].update(x=1), "state.x", allowed=())

    def test_unchanged_candidate_with_empty_allowlist_keeps_existing_admission(self):
        branch = execute(lambda c: None, ())["branches"][0]
        self.assertTrue(branch["admitted"])
        self.assertEqual(branch["inspection"]["mutated"], [])

    def test_declared_scalar_change_allows_recomputed_envelope_fields(self):
        branch = execute(lambda c: c["state"].update(x=1))["branches"][0]
        self.assertTrue(branch["admitted"])
        self.assertEqual(branch["omega"]["state"]["x"], 1)
        self.assertNotEqual(branch["omegaId"], native()["id"])

    def test_declared_parent_allows_descendant_changes(self):
        for edit in (lambda c: c["state"]["guard"].update(value=8, extra=[1]),
                     lambda c: c["state"].pop("guard"),
                     lambda c: c["state"].update(guard=None)):
            with self.subTest(edit=edit):
                self.assertTrue(execute(edit, ("state.guard",))["branches"][0]["admitted"])

    def test_declared_leaf_does_not_authorize_sibling_or_parent_replacement(self):
        self.rejected(lambda c: c["state"]["guard"].update(other=9),
                      "state.guard.other", allowed=("state.guard.value",))
        self.rejected(lambda c: c["state"].update(guard=9),
                      "state.guard", allowed=("state.guard.value",))
        self.rejected(lambda c: c["state"].pop("guard"),
                      "state.guard", allowed=("state.guard.value",))

    def test_permission_uses_path_segments_not_string_prefix(self):
        self.rejected(lambda c: c["state"].update(xyz=2), "state.xyz")

    def test_literal_dot_key_does_not_impersonate_nested_permission(self):
        self.rejected(lambda c: c["state"].update({"dot.key": 1}),
                      "state.dot.key", allowed=("state.dot.key",))

    def test_array_changes_require_permission_for_the_array(self):
        edit = lambda c: c["state"]["items"].reverse()
        self.rejected(edit, "state.items", allowed=("state.items.0",))
        self.assertTrue(execute(edit, ("state.items",))["branches"][0]["admitted"])

    def test_scalar_type_change_is_not_hidden_by_python_equality(self):
        self.rejected(lambda c: c["state"].update(x=False), "state.x", allowed=())

    def test_undeclared_residual_removal_cannot_claim_success(self):
        self.rejected(lambda c: c.update(residuals=[]), "residuals")

    def test_declared_residual_and_state_repair_can_succeed(self):
        def edit(c):
            c["state"]["x"] = 1
            c["residuals"] = []
        result = execute(edit, ("state.x", "residuals"))
        self.assertEqual(result["stopReason"], "SUCCESS")
        self.assertTrue(result["branches"][0]["admitted"])

    def test_semantic_aliases_authorize_their_declared_fields(self):
        for alias, key, value in (("identity", "native_identity", "fixture:successor"),
                                  ("claim-ceiling", "claim_ceiling", ["BOUNDED_OTHER"])):
            with self.subTest(alias=alias):
                result = execute(lambda c: c.update({key: value}), (alias,), preserves=())
                self.assertTrue(result["branches"][0]["admitted"])

    def test_preserves_and_forbids_still_override_mutation_permission(self):
        edit = lambda c: c["state"]["guard"].update(value=8)
        for options in ({"preserves": ("state.guard",)}, {"forbids": ("state.guard",)}):
            with self.subTest(options=options):
                branch = execute(edit, ("state",), **options)["branches"][0]
                self.assertFalse(branch["admitted"])
                self.assertEqual(branch["classification"], "MUTATION")

    def test_derived_field_names_do_not_grant_semantic_permission(self):
        self.rejected(lambda c: c["state"].update(x=1), "state.x",
                      allowed=("id", "construction"))

    def test_unchanged_key_reordering_is_not_a_mutation(self):
        def edit(c):
            c["state"] = dict(reversed(list(c["state"].items())))
        self.assertTrue(execute(edit, ())["branches"][0]["admitted"])

    def test_fitter_without_a_mutation_allowlist_retains_its_contract(self):
        result = execute(lambda c: c["state"].update(x=3), (), fitter=True)
        self.assertTrue(result["branches"][0]["admitted"])
        self.assertEqual(result["branches"][0]["classification"], "VALID_REFIT")

    def test_multiple_violations_are_retained_and_replay_is_deterministic(self):
        def edit(c):
            c["state"].update(x=1, z=2)
            c["residuals"] = []
        first = execute(edit)
        self.assertEqual(canonical_json(first), canonical_json(execute(edit)))
        branch = first["branches"][0]
        self.assertFalse(branch["admitted"])
        self.assertEqual(branch["inspection"]["mutated"], ["residuals", "state.z"])


if __name__ == "__main__":
    unittest.main()

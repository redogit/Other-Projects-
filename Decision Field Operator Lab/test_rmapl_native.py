import unittest

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import (
    NativeOperatorError,
    NativeResourceBound,
    native_registry,
)
from rmapl_runtime import run_program
from test_rmapl import MINIMAL


METRICS = """{"residualReduction":1,"invariantPreservation":1,"reconstructibility":1,"reversibility":1,"evidenceCoverage":1,"branchReduction":1,"provenanceCompleteness":1,"semanticLoss":0,"ambiguityIntroduction":0,"relationGrowth":0,"runtimeCost":0,"economicCost":0,"unresolvedGrowth":0,"irreversibleMutation":0}"""
DECAY = """{"loss":[],"introduction":[],"aliasing":[],"ambiguity":[],"provenanceGap":[],"reconstructionCost":0,"oracleShift":[],"unresolvedGrowth":[]}"""


def omega_with_residual():
    return make_omega(
        native_type="synthetic/v0",
        native_identity="fixture:native:1",
        source_refs=("fixture:native:1",),
        state={"x": 0, "protected": 7},
        path=(),
        frame={"obligation": "native-repair"},
        invariants=("state.protected", "claim-ceiling"),
        observations=(),
        residuals=({"kind": "x-residual", "detail": "fixture"},),
        decision_field={"goal": "x=1"},
        provenance=({"kind": "fixture", "ref": "native"},),
        evidence=(),
        claim_ceiling=("SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION",),
        resource_bounds={"maxCandidates": 2, "maxSteps": 1},
        domain_remainder={"native": "synthetic"},
    )


def native_program(code, *, limit=64, buffer_limit=1024):
    return parse_rmapl(
        f"""RMAPL 0
PROGRAM native-test
LOAD fixture
BOUND maxCandidates=1
BOUND maxSteps=1
OPERATOR repair_x
LIMIT {limit}
BUFFER_LIMIT {buffer_limit}
METRICS {METRICS}
KNOWLEDGE_DECAY {DECAY}
RECONSTRUCTION "exact"
CODE
{code}
END
REPAIR repair-x
WHEN "x-residual"
REQUIRES []
TARGETS ["x-residual"]
PRESERVES ["state.protected"]
MAY_MUTATE ["state.x","residuals"]
FORBIDS ["provenance","evidence"]
APPLY repair_x
EVIDENCE []
COST 1
END
RUN
"""
    )


VALID_REPAIR_CODE = """CLONE ["candidate","$omega"]
CONST ["one",1]
SET ["$candidate","construction.state.x","$one"]
CONST ["empty",[]]
SET ["$candidate","construction.residuals","$empty"]
OMEGA_REBUILD ["$candidate"]
RETURN ["$candidate","x=1"]"""


class NativeParserTests(unittest.TestCase):
    def test_existing_rmapl_programs_remain_operator_free(self):
        program = parse_rmapl(MINIMAL)
        self.assertEqual(program.operators, ())

    def test_native_operator_is_parsed_without_stealing_repair_identity(self):
        program = native_program(VALID_REPAIR_CODE)
        self.assertEqual(len(program.operators), 1)
        operator = program.operators[0]
        self.assertEqual(operator.operator_id, "repair_x")
        self.assertEqual(operator.max_instructions, 64)
        self.assertEqual(operator.max_buffer_bytes, 1024)
        self.assertEqual(operator.reconstruction, "exact")
        self.assertEqual(program.repairs[0].operator, "repair_x")

    def test_duplicate_operator_fails_closed(self):
        source = f"""RMAPL 0
PROGRAM p
LOAD x
OPERATOR op
LIMIT 1
BUFFER_LIMIT 0
METRICS {METRICS}
KNOWLEDGE_DECAY {DECAY}
RECONSTRUCTION "exact"
CODE
RETURN ["$omega","x"]
END
OPERATOR op
LIMIT 1
BUFFER_LIMIT 0
METRICS {METRICS}
KNOWLEDGE_DECAY {DECAY}
RECONSTRUCTION "exact"
CODE
RETURN ["$omega","x"]
END
RUN
"""
        with self.assertRaisesRegex(ValueError, "duplicate OPERATOR"):
            parse_rmapl(source)

    def test_static_code_cannot_exceed_runtime_limit(self):
        with self.assertRaisesRegex(ValueError, "static instruction count"):
            native_program(
                """CONST ["a",1]
CONST ["b",2]
RETURN ["$omega","x"]""",
                limit=2,
            )


class NativeRuntimeTests(unittest.TestCase):
    def test_native_operator_passes_through_existing_verifier(self):
        source = omega_with_residual()
        program = native_program(VALID_REPAIR_CODE)
        result = run_program(program, source, native_registry(program))
        self.assertEqual(result["stopReason"], "SUCCESS")
        self.assertEqual(result["generation"]["executedCount"], 1)
        branch = result["branches"][0]
        self.assertTrue(branch["admitted"])
        self.assertEqual(branch["classification"], "EXACT_REPAIR")
        self.assertEqual(branch["omega"]["state"]["x"], 1)
        self.assertEqual(branch["omega"]["state"]["protected"], 7)
        self.assertEqual(branch["omega"]["residuals"], [])

    def test_input_omega_is_read_only(self):
        source = omega_with_residual()
        program = native_program(
            """SET ["$omega","construction.state.x",1]
RETURN ["$omega","bad"]"""
        )
        op = native_registry(program)["repair_x"]
        with self.assertRaisesRegex(NativeOperatorError, "read-only"):
            op(source)
        self.assertEqual(source["state"]["x"], 0)

    def test_loop_stops_at_declared_instruction_limit(self):
        source = omega_with_residual()
        program = native_program(
            """LABEL ["again"]
JUMP ["again"]""",
            limit=3,
        )
        op = native_registry(program)["repair_x"]
        with self.assertRaisesRegex(NativeResourceBound, "exceeded LIMIT 3"):
            op(source)

    def test_utf8_buffer_obeys_declared_buffer_limit(self):
        source = omega_with_residual()
        program = native_program(
            """CONST ["text","abcd"]
BYTES_UTF8 ["bytes","$text"]
RETURN ["$omega","unused"]""",
            buffer_limit=3,
        )
        op = native_registry(program)["repair_x"]
        with self.assertRaisesRegex(NativeResourceBound, "BUFFER_LIMIT 3"):
            op(source)

    def test_arithmetic_and_bounded_control_flow_are_native(self):
        source = omega_with_residual()
        code = """CONST ["i",0]
CONST ["three",3]
LABEL ["loop"]
ADD ["i","$i",1]
LT ["again","$i","$three"]
JUMP_IF_FALSE ["$again","done"]
JUMP ["loop"]
LABEL ["done"]
CLONE ["candidate","$omega"]
SET ["$candidate","construction.state.x","$i"]
CONST ["empty",[]]
SET ["$candidate","construction.residuals","$empty"]
OMEGA_REBUILD ["$candidate"]
RETURN ["$candidate","x=3"]"""
        program = native_program(code, limit=32)
        op = native_registry(program)["repair_x"]
        proposal = op(source)
        self.assertEqual(proposal["omega"]["state"]["x"], 3)
        self.assertEqual(source["state"]["x"], 0)


if __name__ == "__main__":
    unittest.main()

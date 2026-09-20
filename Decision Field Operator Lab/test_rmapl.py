import unittest

from rmapl import RMAPL_VERSION, parse_rmapl

MINIMAL = """RMAPL 0
PROGRAM omega-repair
LOAD fixture
BOUND maxCandidates=4
BOUND maxSteps=8
REPAIR repair-x
WHEN "x-residual"
REQUIRES ["source.available"]
TARGETS ["x-residual"]
PRESERVES ["identity","claim-ceiling"]
MAY_MUTATE ["state.x"]
FORBIDS ["provenance","evidence"]
APPLY repair_x
EVIDENCE ["software-verification"]
COST 1
END
FITTER refit-surface
WHEN "surface-fit"
REQUIRES ["semantic-admitted"]
PRESERVES ["meaning"]
OBJECTIVES {"clarity":"max","ambiguity":"min"}
APPLY fit_surface
EVIDENCE ["semantic-reconstruction"]
COST 2
END
RUN
"""


class RmaplParserTests(unittest.TestCase):
    def test_parse_minimal_program(self):
        program = parse_rmapl(MINIMAL)
        self.assertEqual(program.version, RMAPL_VERSION)
        self.assertEqual(RMAPL_VERSION, "RMAPL 0")
        self.assertEqual(program.program_id, "omega-repair")
        self.assertEqual(program.load_ref, "fixture")
        self.assertEqual(program.bounds["maxCandidates"], 4)
        self.assertEqual(program.bounds["maxSteps"], 8)
        self.assertEqual(program.repairs[0].operator, "repair_x")
        self.assertEqual(program.repairs[0].trigger, "x-residual")
        self.assertEqual(program.fitters[0].objectives["clarity"], "max")

    def test_unknown_top_level_operation_fails_closed(self):
        bad = "RMAPL 0\nPROGRAM x\nLOAD y\nMAGIC z\nRUN\n"
        with self.assertRaisesRegex(ValueError, "unknown top-level"):
            parse_rmapl(bad)

    def test_reordered_repair_fields_fail_closed(self):
        bad = MINIMAL.replace(
            'REQUIRES ["source.available"]\nTARGETS ["x-residual"]',
            'TARGETS ["x-residual"]\nREQUIRES ["source.available"]',
        )
        with self.assertRaisesRegex(ValueError, "expected REQUIRES"):
            parse_rmapl(bad)

    def test_nonfinite_bound_is_rejected(self):
        bad = "RMAPL 0\nPROGRAM x\nLOAD y\nBOUND x=NaN\nRUN\n"
        with self.assertRaisesRegex(ValueError, "JSON"):
            parse_rmapl(bad)

    def test_duplicate_identifier_or_bound_is_rejected(self):
        duplicate_bound = "RMAPL 0\nPROGRAM x\nLOAD y\nBOUND n=1\nBOUND n=2\nRUN\n"
        with self.assertRaisesRegex(ValueError, "duplicate BOUND"):
            parse_rmapl(duplicate_bound)

        duplicate_repair = MINIMAL.replace(
            "FITTER refit-surface\n",
            """REPAIR repair-x
WHEN "other"
REQUIRES []
TARGETS []
PRESERVES []
MAY_MUTATE []
FORBIDS []
APPLY repair_y
EVIDENCE []
COST 0
END
FITTER refit-surface
""",
        )
        with self.assertRaisesRegex(ValueError, "duplicate block id"):
            parse_rmapl(duplicate_repair)

    def test_missing_required_field_is_rejected(self):
        bad = MINIMAL.replace('EVIDENCE ["software-verification"]\n', "", 1)
        with self.assertRaisesRegex(ValueError, "expected EVIDENCE"):
            parse_rmapl(bad)

    def test_negative_cost_is_rejected(self):
        bad = MINIMAL.replace("COST 1\nEND", "COST -1\nEND", 1)
        with self.assertRaisesRegex(ValueError, "non-negative"):
            parse_rmapl(bad)

    def test_trailing_content_after_run_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "RUN must be terminal"):
            parse_rmapl(MINIMAL + "BOUND x=1\n")

    def test_comments_and_blank_lines_do_not_change_program(self):
        decorated = "# comment\n\n" + MINIMAL.replace(
            "PROGRAM omega-repair",
            "PROGRAM omega-repair\n# inside",
        )
        self.assertEqual(parse_rmapl(decorated), parse_rmapl(MINIMAL))


if __name__ == "__main__":
    unittest.main()

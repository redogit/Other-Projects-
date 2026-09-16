import subprocess
import sys
import unittest
from pathlib import Path
import gsfl
try:
    import gsfl_coop as coop
except ImportError:
    coop = None

class GSFLCooperationTests(unittest.TestCase):
    def require(self):
        self.assertIsNotNone(coop, 'gsfl_coop module must exist')

    def test_vocabulary_majority_is_human_machine_cooperation(self):
        self.require(); audit=coop.vocabulary_audit()
        self.assertGreater(audit['ratio'],0.5); self.assertTrue(audit['passes'])
        self.assertGreater(audit['cooperation_terms'],audit['semantic_core_terms'])

    def test_partner_ids_must_be_distinct(self):
        self.require()
        with self.assertRaisesRegex(ValueError,'distinct'):
            coop.CooperationContext(
                human_partner=coop.Partner('same','HUMAN','intent-owner'),
                machine_partner=coop.Partner('same','MACHINE','proposal-partner'),
                tools=(),steps=(),understanding_goal='explain',
                understanding_evidence=coop.UnderstandingEvidence('NONE',''),
                learning_claim=coop.LearningClaim('NO_LEARNING_CLAIM',''))

    def test_stronger_learning_claim_requires_evidence(self):
        self.require()
        with self.assertRaisesRegex(ValueError,'evidence'):
            coop.LearningClaim('IN_CONTEXT_ADAPTATION','')

    def test_cooperation_program_delegates_semantic_fit(self):
        self.require(); result=coop.execute_cooperation(PROGRAM)
        self.assertEqual('human-cooperative',result['selected_candidate'])
        self.assertEqual('human-1',result['cooperation']['human_partner']['partner_id'])
        self.assertEqual('machine-1',result['cooperation']['machine_partner']['partner_id'])
        self.assertEqual(['python','windows-docs'],[t['tool_id'] for t in result['cooperation']['tools']])
        self.assertEqual('IN_CONTEXT_ADAPTATION',result['cooperation']['machine_learning_claim']['state'])
        self.assertGreater(result['vocabulary_audit']['ratio'],0.5)

    def test_unknown_tool_reference_fails_closed(self):
        self.require()
        with self.assertRaisesRegex(ValueError,'unknown tool'):
            coop.execute_cooperation(PROGRAM.replace('tools=python','tools=missing',1))

    def test_approval_only_does_not_become_understanding(self):
        self.require(); result=coop.execute_cooperation(PROGRAM.replace('TEACH_BACK','APPROVAL_ONLY'))
        ids={f['id'] for f in result['confound_findings']}
        self.assertIn('APPROVAL_AS_UNDERSTANDING',ids); self.assertIn('APPROVAL_AS_TRUTH',ids)

    def test_in_context_adaptation_never_claims_weight_update(self):
        self.require(); result=coop.execute_cooperation(PROGRAM)
        ids={f['id'] for f in result['confound_findings']}
        self.assertIn('IN_CONTEXT_AS_WEIGHT_UPDATE',ids)
        self.assertNotIn('WEIGHT_UPDATE_VERIFIED',result['cooperation']['machine_learning_claim'])

    def test_correlated_tools_are_not_independent_verification(self):
        self.require(); result=coop.execute_cooperation(PROGRAM)
        ids={f['id'] for f in result['confound_findings']}
        self.assertIn('CORRELATED_TOOLS_AS_INDEPENDENT_VERIFICATION',ids)

    def test_high_fit_mutation_remains_rejected(self):
        self.require(); result=coop.execute_cooperation(PROGRAM)
        by_id={r['candidate_id']:r for r in result['evaluations']}
        self.assertEqual(gsfl.MUTATION,by_id['attractive-mutation']['classification'])
        self.assertFalse(by_id['attractive-mutation']['admitted'])

    def test_lexical_majority_is_not_comprehension_evidence(self):
        self.require(); result=coop.execute_cooperation(PROGRAM)
        ids={f['id'] for f in result['confound_findings']}
        self.assertIn('LEXICAL_MAJORITY_AS_COMPREHENSION',ids)

    def test_cooperation_audit_matches_frozen_evidence(self):
        self.require()
        proc = subprocess.run(
            [sys.executable, "run_coop_audit.py", "--check"],
            cwd=Path(__file__).parent, text=True, capture_output=True,
        )
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

PROGRAM='''
GSFL 0.1
OBJECT n-observer-cooperation
MEANING cardinality="N"
MEANING world_state="unchanged"
MEANING purpose="human-machine cooperative accessibility"
PRESERVE cardinality
PRESERVE world_state
HUMAN human-1 role="intent-owner and understanding partner"
MACHINE machine-1 role="proposal and comparison partner"
TOOL python purpose="deterministic verification" provenance="local standard-library tests" evidence_group="implementation"
TOOL windows-docs purpose="API capability reference" provenance="Microsoft documentation" evidence_group="implementation"
UNDERSTANDING_GOAL "Human partner can explain that N observers change views without changing the desktop."
UNDERSTANDING_EVIDENCE TEACH_BACK detail="bounded fixture records teach-back as supplied evidence"
MACHINE_LEARNING IN_CONTEXT_ADAPTATION evidence="machine partner adapts proposals to the current conversation; no weight-update claim"
COOPERATE human-1 action="state-intent" detail="request N observers optimized for human understanding" tools=none
COOPERATE machine-1 action="propose" detail="generalize four docks to N independent observers" tools=windows-docs
COOPERATE machine-1 action="verify" detail="compare candidate semantics and reconstruct invariants" tools=python,windows-docs
COOPERATE human-1 action="review" detail="select cooperation framing and preserve partner distinctions" tools=none
ROTATE technical
SURFACE "N observer transforms preserve desktop state while partner/tool provenance remains explicit."
METRIC clarity=0.70 usefulness=0.92 recoverability=0.97 cognitive_effort=0.55 ambiguity=0.04 semantic_loss=0
RECONSTRUCT cardinality="N"
RECONSTRUCT world_state="unchanged"
RECONSTRUCT purpose="human-machine cooperative accessibility"
END
ROTATE human-cooperative
SURFACE "The human partner says what needs to be understood; the machine partner proposes clearer views; the partners use tools to verify what stayed the same; the human-facing result keeps both partner roles and tool provenance visible."
METRIC clarity=0.99 usefulness=0.98 recoverability=0.98 cognitive_effort=0.10 ambiguity=0.02 semantic_loss=0
RECONSTRUCT cardinality="N"
RECONSTRUCT world_state="unchanged"
RECONSTRUCT purpose="human-machine cooperative accessibility"
END
ROTATE attractive-mutation
SURFACE "The machine learns the truth and changes the desktop for the human."
SET purpose="machine-authoritative desktop modification"
METRIC clarity=1 usefulness=1 recoverability=1 cognitive_effort=0 ambiguity=0 semantic_loss=0
RECONSTRUCT cardinality="N"
RECONSTRUCT world_state="unchanged"
RECONSTRUCT purpose="machine-authoritative desktop modification"
END
FIT
'''

if __name__=='__main__': unittest.main()

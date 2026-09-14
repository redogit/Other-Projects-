import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class AuditTests(unittest.TestCase):
  def test_two_replays_have_identical_scientific_outputs(self):
    with tempfile.TemporaryDirectory(prefix='bom-fast-audit-') as td:
      a=Path(td)/'a'; b=Path(td)/'b'
      subprocess.run([sys.executable,str(ROOT/'audit.py'),'--out',str(a)],check=True,timeout=120)
      subprocess.run([sys.executable,str(ROOT/'audit.py'),'--out',str(b)],check=True,timeout=120)
      self.assertEqual((a/'SUMMARY.json').read_bytes(),(b/'SUMMARY.json').read_bytes())
      self.assertEqual((a/'TRAINING.json').read_bytes(),(b/'TRAINING.json').read_bytes())
      summary=json.loads((a/'SUMMARY.json').read_text())
      training=json.loads((a/'TRAINING.json').read_text())
      self.assertEqual(summary['status'],'PASS_BOUNDED')
      self.assertTrue(training['test']['exact_agreement'])
      self.assertTrue(training['test']['promoted'])
      self.assertFalse(training['corrupted_label_control']['promoted'])
      self.assertGreater(summary['training_test_expansion_reduction'],0)
      self.assertGreater(summary['hard_family_expansion_reduction'],0)
if __name__=='__main__':unittest.main()

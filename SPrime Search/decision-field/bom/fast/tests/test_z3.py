import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'fast')]
from train import generate_training_families,oracle_min_cover
from z3_verify import z3_available,solve_z3

@unittest.skipUnless(z3_available(),'z3-solver not installed in this environment')
class Z3Tests(unittest.TestCase):
  def test_z3_matches_exact_oracle(self):
    for task in generate_training_families(12,seed=707):
      expected=oracle_min_cover(task)
      got=solve_z3(task)
      self.assertEqual((got.count,got.mask),expected)
  def test_z3_matches_benchmark_wolfram_target(self):
    from benchmark import make_benchmark_task
    task=make_benchmark_task(12)
    got=solve_z3(task)
    self.assertEqual((got.count,got.mask),(2,3072))
if __name__=='__main__':unittest.main()

import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'fast')]
from train import generate_training_families,solve_min_cover
from native import compile_native,run_native
class NativeTests(unittest.TestCase):
  def test_native_matches_python_exact(self):
    exe=compile_native()
    try:
      for task in generate_training_families(12,seed=91):
        py=solve_min_cover(task)
        native=run_native(task,exe)
        self.assertEqual((native['count'],native['mask']),(py.count,py.mask))
        self.assertGreater(native['expansions'],0)
    finally:
      exe.cleanup()
if __name__=='__main__':unittest.main()

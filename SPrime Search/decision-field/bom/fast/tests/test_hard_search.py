import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'fast')]
from benchmark import make_dependency_trap_task
from hard_search import solve_mrv
from train import oracle_min_cover,generate_training_families,family_split,build_examples,train_pairwise_perceptron
class HardSearchTests(unittest.TestCase):
  def test_mrv_matches_exhaustive_oracle(self):
    for size in (12,16,18):
      task=make_dependency_trap_task(size)
      got=solve_mrv(task)
      self.assertEqual((got.count,got.mask),oracle_min_cover(task))
      self.assertGreater(got.expansions,0)
  def test_ranker_only_changes_order(self):
    tasks=generate_training_families(60,20260914)
    train=[t for t in tasks if family_split(t.family_id)=='train']
    model=train_pairwise_perceptron(build_examples(train),8)
    for size in (12,16,20):
      task=make_dependency_trap_task(size)
      a=solve_mrv(task); b=solve_mrv(task,model)
      self.assertEqual((a.count,a.mask),(b.count,b.mask))
if __name__=='__main__':unittest.main()

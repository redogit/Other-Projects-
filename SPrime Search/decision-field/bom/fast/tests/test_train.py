import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'fast')]
from train import generate_training_families,family_split,build_examples,train_pairwise_perceptron,evaluate_ranker,model_json
from benchmark import make_dependency_trap_task
from hard_search import solve_mrv
class TrainTests(unittest.TestCase):
  @classmethod
  def setUpClass(cls): cls.tasks=generate_training_families(60,seed=20260914)
  def model(self):
    train=[t for t in self.tasks if family_split(t.family_id)=='train']
    return train_pairwise_perceptron(build_examples(train),epochs=8)
  def test_family_splits_disjoint(self):
    groups={k:set() for k in ('train','validation','test')}
    for t in self.tasks: groups[family_split(t.family_id)].add(t.family_id)
    self.assertTrue(all(groups.values()))
    self.assertFalse(groups['train']&groups['validation']); self.assertFalse(groups['train']&groups['test']); self.assertFalse(groups['validation']&groups['test'])
  def test_training_is_deterministic(self):
    train=[t for t in self.tasks if family_split(t.family_id)=='train']
    ex=build_examples(train)
    a=train_pairwise_perceptron(ex,epochs=8); b=train_pairwise_perceptron(ex,epochs=8)
    self.assertEqual(a,b); self.assertEqual(model_json(a),model_json(b))
  def test_heldout_exact_result_unchanged_and_expansions_improve(self):
    model=self.model(); test=[t for t in self.tasks if family_split(t.family_id)=='test']
    report=evaluate_ranker(test,model)
    self.assertTrue(report.exact_agreement)
    self.assertLess(report.ranked_expansions,report.lexical_expansions)
    self.assertTrue(report.promoted)
  def test_bad_labels_are_not_promoted(self):
    train=[t for t in self.tasks if family_split(t.family_id)=='train']
    val=[t for t in self.tasks if family_split(t.family_id)=='validation']
    bad=train_pairwise_perceptron(build_examples(train),epochs=8,reverse_labels=True)
    report=evaluate_ranker(val,bad)
    self.assertTrue(report.exact_agreement)
    self.assertFalse(report.promoted)
  def test_out_of_family_dependency_traps_keep_exact_answer_and_improve_total(self):
    model=self.model(); lexical=ranked=0
    for size in (12,16,20,32):
      task=make_dependency_trap_task(size)
      a=solve_mrv(task,None); b=solve_mrv(task,model)
      self.assertEqual((a.count,a.mask),(b.count,b.mask))
      lexical+=a.expansions; ranked+=b.expansions
    self.assertLess(ranked,lexical)
if __name__=='__main__':unittest.main()

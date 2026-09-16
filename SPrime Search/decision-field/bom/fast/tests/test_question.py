import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'fast')]
from question import QuestionSpec,score_question,rank_questions
from explain import why_question,why_assembly
class QTests(unittest.TestCase):
  def test_zero_value_question_rejected(self):
    q=QuestionSpec('q','noop',('x','y'),(('x',('a','b')),('y',('a','b'))),0)
    self.assertIsNone(score_question(q,('a','b'),('a',)))
  def test_minimax_split(self):
    q22=QuestionSpec('q22','balanced',('y','n'),(('y',('a','b')),('n',('c','d'))),0)
    q31=QuestionSpec('q31','unbalanced',('y','n'),(('y',('a','b','c')),('n',('d',))),0)
    ranked=rank_questions((q31,q22),('a','b','c','d'),('a','b'))
    self.assertEqual(ranked[0].question.stable_id,'q22')
    self.assertEqual(ranked[0].worst_survivors,2)
  def test_frontier_change_breaks_equal_split(self):
    qfront=QuestionSpec('front','frontier split',('y','n'),(('y',('a','c')),('n',('b','d'))),0)
    qplain=QuestionSpec('plain','plain split',('y','n'),(('y',('a','b')),('n',('c','d'))),0)
    ranked=rank_questions((qplain,qfront),('a','b','c','d'),('a','b'))
    self.assertEqual(ranked[0].question.stable_id,'front')
  def test_cost_breaks_remaining_tie(self):
    a=QuestionSpec('a','a',('y','n'),(('y',('a','c')),('n',('b','d'))),3)
    b=QuestionSpec('b','b',('y','n'),(('y',('a','c')),('n',('b','d'))),1)
    self.assertEqual(rank_questions((a,b),('a','b','c','d'),('a','b'))[0].question.stable_id,'b')
  def test_answer_recomputes_frontier_when_dominated_candidate_survives(self):
    q=QuestionSpec('qnew','remove old frontier',('old','new'),(('old',('a','b')),('new',('c',))),0)
    costs={'a':(1,3),'b':(3,1),'c':(4,4)}
    score=score_question(q,('a','b','c'),('a','b'),costs=costs)
    self.assertEqual(dict(score.answer_frontiers)['new'],('c',))
  def test_question_cannot_erase_viable_candidate_from_all_answers(self):
    q=QuestionSpec('bad','bad',('yes','no'),(('yes',('a',)),('no',('b',))),0)
    with self.assertRaisesRegex(ValueError,'omit viable'):
      score_question(q,('a','b','c'),('a','b'))
  def test_why_records(self):
    q=QuestionSpec('q','sensor?',('yes','no'),(('yes',('fused',)),('no',('open',))),1)
    ranked=rank_questions((q,),('fused','open'),('fused','open'))[0]
    w=why_question(ranked)
    self.assertEqual(w['why'],'consequential_question')
    self.assertEqual(w['worst_survivors'],1)
    a=why_assembly('fused',included=True,cost={'memory':1},cache_provenance='fresh')
    self.assertEqual(a['why'],'included')
if __name__=='__main__':unittest.main()

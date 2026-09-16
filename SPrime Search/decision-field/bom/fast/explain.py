from __future__ import annotations

def why_question(score):
    return {
      'why':'consequential_question',
      'question_id':score.question.stable_id,
      'worst_survivors':score.worst_survivors,
      'guaranteed_eliminations':score.guaranteed_eliminations,
      'frontier_change_answers':score.frontier_change_answers,
      'acquisition_cost':score.acquisition_cost,
      'answer_frontiers':[{'answer':a,'frontier':list(f)} for a,f in score.answer_frontiers],
    }

def why_assembly(assembly_id,*,included,reason=None,cost=None,dominated_by=(),cache_provenance='not_checked'):
    return {
      'assembly_id':assembly_id,
      'why':'included' if included else (reason or 'rejected'),
      'cost':dict(cost or {}),
      'dominated_by':list(dominated_by),
      'cache_provenance':cache_provenance,
    }

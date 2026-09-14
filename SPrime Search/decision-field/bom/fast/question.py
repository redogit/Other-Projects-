from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class QuestionSpec:
    stable_id: str
    text: str
    answers: tuple[str,...]
    partitions: tuple[tuple[str,tuple[str,...]],...]
    acquisition_cost: int = 0
    def __post_init__(self):
        if not self.stable_id or not self.text or not self.answers: raise ValueError('question fields must be nonempty')
        if tuple(a for a,_ in self.partitions) != self.answers: raise ValueError('partitions must match answer order')
        if self.acquisition_cost < 0: raise ValueError('acquisition cost must be nonnegative')

@dataclass(frozen=True)
class QuestionScore:
    question: QuestionSpec
    worst_survivors: int
    guaranteed_eliminations: int
    frontier_change_answers: int
    acquisition_cost: int
    rank_key: tuple
    answer_frontiers: tuple[tuple[str,tuple[str,...]],...]

def score_question(question:QuestionSpec, viable, frontier):
    viable=tuple(sorted(set(viable))); frontier=tuple(sorted(set(frontier)))
    vset=set(viable); fset=set(frontier)
    buckets=[]; answer_frontiers=[]
    for answer,members in question.partitions:
        b=tuple(sorted(vset & set(members))); buckets.append(b)
        answer_frontiers.append((answer,tuple(sorted(fset & set(b)))))
    if not buckets: return None
    worst=max(map(len,buckets))
    eliminated=len(viable)-worst
    changes=sum(tuple(sorted(fset & set(b))) != frontier for b in buckets)
    if eliminated==0 and changes==0:return None
    key=(worst,-eliminated,-changes,question.acquisition_cost,question.stable_id)
    return QuestionScore(question,worst,eliminated,changes,question.acquisition_cost,key,tuple(answer_frontiers))

def rank_questions(questions,viable,frontier):
    scored=[score_question(q,viable,frontier) for q in questions]
    return tuple(sorted((s for s in scored if s is not None),key=lambda s:s.rank_key))

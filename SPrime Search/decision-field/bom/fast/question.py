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

def _dominates(a,b):
    return all(x<=y for x,y in zip(a,b)) and any(x<y for x,y in zip(a,b))

def _frontier_ids(members,costs):
    members=tuple(sorted(set(members)))
    return tuple(x for x in members if not any(y!=x and _dominates(costs[y],costs[x]) for y in members))

def score_question(question:QuestionSpec, viable, frontier, costs=None):
    viable=tuple(sorted(set(viable))); frontier=tuple(sorted(set(frontier)))
    vset=set(viable); fset=set(frontier)
    if not set(frontier) <= vset: raise ValueError('frontier must be a subset of viable candidates')
    if costs is not None and any(x not in costs for x in viable): raise ValueError('costs missing viable candidate')
    buckets=[]; answer_frontiers=[]
    covered=set()
    for answer,members in question.partitions:
        b=tuple(sorted(vset & set(members))); buckets.append(b); covered.update(b)
        af=_frontier_ids(b,costs) if costs is not None else tuple(sorted(fset & set(b)))
        answer_frontiers.append((answer,af))
    if covered != vset: raise ValueError('question answers omit viable candidates')
    if not buckets: return None
    worst=max(map(len,buckets))
    eliminated=len(viable)-worst
    changes=sum(af != frontier for _,af in answer_frontiers)
    if eliminated==0 and changes==0:return None
    key=(worst,-eliminated,-changes,question.acquisition_cost,question.stable_id)
    return QuestionScore(question,worst,eliminated,changes,question.acquisition_cost,key,tuple(answer_frontiers))

def rank_questions(questions,viable,frontier,costs=None):
    scored=[score_question(q,viable,frontier,costs=costs) for q in questions]
    return tuple(sorted((s for s in scored if s is not None),key=lambda s:s.rank_key))

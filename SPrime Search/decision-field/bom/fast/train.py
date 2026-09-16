from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,random

@dataclass(frozen=True)
class CoverTask:
    family_id:str
    required_mask:int
    provide_masks:tuple[int,...]
    require_masks:tuple[int,...]

@dataclass(frozen=True)
class TrainingExample:
    family_id:str
    positive:tuple[int,...]
    negative:tuple[int,...]

@dataclass(frozen=True)
class RankerModel:
    weights:tuple[int,...]
    epochs:int
    enabled:bool=True
    reason:str='trained'
    def score(self,features): return sum(w*x for w,x in zip(self.weights,features))

@dataclass(frozen=True)
class SolveResult:
    count:int
    mask:int
    expansions:int

@dataclass(frozen=True)
class EvaluationReport:
    exact_agreement:bool
    lexical_expansions:int
    ranked_expansions:int
    promoted:bool

def family_split(family_id:str)->str:
    bucket=int(hashlib.sha256(family_id.encode()).hexdigest()[:8],16)%10
    return 'train' if bucket<6 else ('validation' if bucket<8 else 'test')

def _pc(x): return int(x).bit_count()

def generate_training_families(count:int,seed:int=20260914):
    out=[]
    for i in range(count):
        fid=f'cover-{seed}-{i:03d}'
        rng=random.Random((seed<<16)^i)
        perm=list(range(5)); rng.shuffle(perm)
        req=(1<<5)-1
        provides=[]; requires=[]
        for b in perm:
            provides.append(1<<b); requires.append(0)
        a=set(perm[:3]); b=set(perm[3:])
        provides += [sum(1<<x for x in a),sum(1<<x for x in b)]; requires += [0,0]
        for _ in range(3):
            bits=rng.sample(range(5),2)
            pm=sum(1<<x for x in bits)
            missing=[x for x in range(5) if not (pm>>x)&1]
            rm=(1<<rng.choice(missing)) if missing else 0
            provides.append(pm); requires.append(rm)
        out.append(CoverTask(fid,req,tuple(provides),tuple(requires)))
    return tuple(out)

def _valid(task,mask):
    provided=0; needed=task.required_mask
    for i in range(len(task.provide_masks)):
        if mask>>i&1:
            provided |= task.provide_masks[i]
            needed |= task.require_masks[i]
    return needed & ~provided == 0

def oracle_min_cover(task:CoverTask):
    best_count=10**9; best_mask=0
    for mask in range(1,1<<len(task.provide_masks)):
        c=_pc(mask)
        if c>best_count: continue
        if _valid(task,mask):
            if c<best_count or (c==best_count and mask<best_mask):
                best_count,best_mask=c,mask
    return best_count,best_mask

def part_features(task:CoverTask,slot:int,missing_mask:int|None=None):
    if missing_mask is None: missing_mask=task.required_mask
    pm=task.provide_masks[slot]; rm=task.require_masks[slot]
    new=_pc(pm & missing_mask)
    return (new,_pc(pm),-_pc(rm),1 if new>1 else 0)

def build_examples(tasks):
    ex=[]
    for task in tasks:
        _,mask=oracle_min_cover(task)
        positives=[i for i in range(len(task.provide_masks)) if mask>>i&1]
        negatives=[i for i in range(len(task.provide_masks)) if not (mask>>i&1)]
        for p in positives:
            pf=part_features(task,p)
            for n in negatives:
                ex.append(TrainingExample(task.family_id,pf,part_features(task,n)))
    return tuple(sorted(ex,key=lambda e:(e.family_id,e.positive,e.negative)))

def train_pairwise_perceptron(examples,epochs:int=8,reverse_labels:bool=False):
    if epochs<1: raise ValueError('epochs')
    width=len(examples[0].positive) if examples else 4
    w=[0]*width
    for _ in range(epochs):
        for e in examples:
            pos,neg=(e.negative,e.positive) if reverse_labels else (e.positive,e.negative)
            if sum(a*b for a,b in zip(w,pos)) <= sum(a*b for a,b in zip(w,neg)):
                for i,(a,b) in enumerate(zip(pos,neg)): w[i]+=a-b
    return RankerModel(tuple(w),epochs)

def _slot_order(task,model):
    slots=list(range(len(task.provide_masks)))
    if model is None:return tuple(slots)
    return tuple(sorted(slots,key=lambda i:(-model.score(part_features(task,i)),i)))

def solve_min_cover(task:CoverTask,model:RankerModel|None=None):
    order=_slot_order(task,model); n=len(order)
    suffix=[0]*(n+1)
    for j in range(n-1,-1,-1): suffix[j]=suffix[j+1] | task.provide_masks[order[j]]
    best_count=n+1; best_mask=0; expansions=0
    def rec(j,selected,provided,needed,count):
        nonlocal best_count,best_mask,expansions
        expansions+=1
        if needed & ~provided == 0:
            if count<best_count or (count==best_count and selected<best_mask):
                best_count,best_mask=count,selected
            return
        if j==n or count>=best_count:return
        missing=needed & ~provided
        if missing & ~(provided | suffix[j]):return
        slot=order[j]; bit=1<<slot
        rec(j+1,selected|bit,provided|task.provide_masks[slot],needed|task.require_masks[slot],count+1)
        rec(j+1,selected,provided,needed,count)
    rec(0,0,0,task.required_mask,0)
    return SolveResult(best_count,best_mask,expansions)

def evaluate_ranker(tasks,model):
    lex=ranked=0; agree=True
    for t in tasks:
        a=solve_min_cover(t,None); b=solve_min_cover(t,model)
        lex+=a.expansions; ranked+=b.expansions
        agree &= (a.count,a.mask)==(b.count,b.mask)
    return EvaluationReport(bool(agree),lex,ranked,bool(agree and ranked<lex))

def model_json(model):
    return json.dumps({'weights':model.weights,'epochs':model.epochs,'enabled':model.enabled,'reason':model.reason},sort_keys=True,separators=(',',':'))+'\n'

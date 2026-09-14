from __future__ import annotations
from dataclasses import dataclass, field
import hashlib, json
from index import CompiledIndex

@dataclass(frozen=True)
class SearchCertificate:
    accepted: bool
    reason: str
    provided_mask: int
    needed_mask: int

@dataclass(frozen=True)
class CandidateEnumeration:
    masks: tuple[int,...]
    checked: int
    rejected_required: int
    rejected_dependency: int

def subset_certificate(index: CompiledIndex, subset_mask: int) -> SearchCertificate:
    n=len(index.part_keys)
    if type(subset_mask) is not int or subset_mask < 0 or subset_mask >= (1<<n):
        raise ValueError('subset mask outside compiled part domain')
    provided=0
    needed=index.required_capability_mask
    for i in range(n):
        if subset_mask>>i & 1:
            provided |= index.provide_masks[i]
            needed |= index.require_masks[i]
    if index.required_capability_mask & ~provided:
        return SearchCertificate(False,'missing_required_capability',provided,needed)
    if needed & ~provided:
        return SearchCertificate(False,'missing_dependency',provided,needed)
    return SearchCertificate(True,'accepted',provided,needed)

def enumerate_indexed_candidates(index: CompiledIndex, active_part_mask: int|None=None) -> CandidateEnumeration:
    n=len(index.part_keys)
    all_mask=(1<<n)-1
    if active_part_mask is None: active_part_mask=all_mask
    if type(active_part_mask) is not int or active_part_mask < 0 or active_part_mask & ~all_mask:
        raise ValueError('active part mask outside compiled part domain')
    masks=[]; checked=rr=rd=0
    subset=active_part_mask
    while subset:
        cert=subset_certificate(index,subset); checked+=1
        if cert.accepted:masks.append(subset)
        elif cert.reason=='missing_required_capability':rr+=1
        else:rd+=1
        subset=(subset-1)&active_part_mask
    return CandidateEnumeration(tuple(sorted(masks)),checked,rr,rd)

@dataclass
class _CacheRecord:
    value: object
    dependencies: frozenset[str]

@dataclass
class IncrementalSearchState:
    index: CompiledIndex
    distinctions: dict[str,object]=field(default_factory=dict)
    _cache: dict[str,_CacheRecord]=field(default_factory=dict)
    @property
    def fingerprint(self)->str:
        raw=json.dumps(self.distinctions,sort_keys=True,separators=(',',':'),default=str).encode()
        return hashlib.sha256(raw).hexdigest()
    def put_cache(self,key:str,value:object,dependencies=())->None:
        self._cache[key]=_CacheRecord(value,frozenset(dependencies))
    def get_cache(self,key:str):
        rec=self._cache.get(key)
        return None if rec is None else rec.value
    def apply_distinction(self,key:str,value:object)->tuple[str,...]:
        changed=self.distinctions.get(key,object()) != value
        self.distinctions[key]=value
        if not changed:return ()
        invalid=tuple(sorted(k for k,r in self._cache.items() if key in r.dependencies))
        for k in invalid:self._cache.pop(k,None)
        return invalid

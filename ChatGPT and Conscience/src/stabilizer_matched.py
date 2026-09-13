"""Matched controls: same validation, preprocessing, ordering and exact output."""
from collections import Counter
from collections.abc import Mapping
from functools import reduce
from math import gcd

def prepare(points: Mapping[int,int], n: int):
    if type(n) is not int or n<0: raise ValueError('n must be a nonnegative integer')
    if not isinstance(points,Mapping): raise TypeError('points must be a mapping')
    for x,b in points.items():
        if type(x) is not int or x<0 or x.bit_length()>n: raise ValueError('invalid coordinate')
        if type(b) is not int or b not in (0,1): raise ValueError('invalid label')
    if not points: return [],0
    counts=Counter(points.values());label=min(counts,key=lambda b:(counts[b],b))
    anchors=sorted(x for x,b in points.items() if b==label)
    common=reduce(gcd,counts.values())
    return anchors,common & -common

def output(n,values=None):
    if values is None: return {'kind':'ALL_NONZERO_TRANSLATIONS','dimension':n}
    return {'kind':'EXPLICIT','dimension':n,'nonzero':sorted(values)}

def anchor_control(points,n):
    anchors,_=prepare(points,n)
    if not anchors:return output(n)
    root=anchors[0];found=[]
    for y in anchors[1:]:
        t=root^y
        for x,b in points.items():
            if points.get(x^t,2)!=b:break
        else:found.append(t)
    return output(n,found)

def reuse_control(points,n):
    anchors,ceiling=prepare(points,n)
    if not anchors:return output(n)
    root=anchors[0];group={0}
    for y in anchors[1:]:
        if len(group)==ceiling:break
        t=root^y
        if t in group:continue
        for x,b in points.items():
            if points.get(x^t,2)!=b:break
        else:group.update([h^t for h in group])
    return output(n,group-{0})

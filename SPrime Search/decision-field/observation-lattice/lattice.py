#!/usr/bin/env python3
"""Task-relative observation partitions for deterministic memoryless control."""
from __future__ import annotations
from itertools import product


def canonical_partition(labels):
    labels=tuple(labels)
    if not labels or labels[0]!=0: raise ValueError('partition must begin with class 0')
    mx=0
    for v in labels:
        if type(v) is not int or v<0 or v>mx+1: raise ValueError('noncanonical partition')
        mx=max(mx,v)
    return labels


def partitions(n=4):
    if type(n) is not int or not 1<=n<=8: raise ValueError('partition size')
    out=[]
    def rec(a,mx):
        if len(a)==n: out.append(tuple(a));return
        for x in range(mx+2): a.append(x);rec(a,max(mx,x));a.pop()
    rec([0],0);return tuple(out)


def refines(fine,coarse):
    fine=canonical_partition(fine);coarse=canonical_partition(coarse)
    if len(fine)!=len(coarse): raise ValueError('carrier mismatch')
    return all(not(fine[i]==fine[j] and coarse[i]!=coarse[j]) for i in range(len(fine)) for j in range(len(fine)))


def map_tuple(byte):
    if type(byte) is not int or not 0<=byte<=255: raise ValueError('local map')
    return tuple((byte>>(2*s))&3 for s in range(4))


def policy_wins(map0,map1,target,policy):
    if len(map0)!=4 or len(map1)!=4 or len(policy)!=4: raise ValueError('four states required')
    if type(target) is not int or not 0<=target<4: raise ValueError('target')
    for a in policy:
        if type(a) is not int or a not in (0,1): raise ValueError('binary action policy')
    for start in range(4):
        state=start;seen=set()
        while state!=target and state not in seen:
            seen.add(state);state=(map1 if policy[state] else map0)[state]
        if state!=target:return False
    return True


def action_partition(policy):
    if len(policy)!=4: raise ValueError('policy')
    labels={};out=[]
    for action in policy:
        if action not in labels: labels[action]=len(labels)
        out.append(labels[action])
    return tuple(out)


def winning_state_policies(map0,map1,target):
    return tuple(p for p in product((0,1),repeat=4) if policy_wins(map0,map1,target,p))


def minimal_sensors(map0,map1,target):
    wins=winning_state_policies(map0,map1,target)
    if not wins:return ()
    candidates={action_partition(p) for p in wins}
    if (0,0,0,0) in candidates:return ((0,0,0,0),)
    return tuple(sorted(candidates))


def sufficient(partition,minimal):
    partition=canonical_partition(partition)
    return any(refines(partition,m) for m in minimal)

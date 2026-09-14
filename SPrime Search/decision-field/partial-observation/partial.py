#!/usr/bin/env python3
"""Exact deterministic partial-observation knowledge states for small finite systems.

Beliefs are nonempty sets of hidden worlds, represented as integer bit masks.
This is set-valued (sure/adversarial) uncertainty, not a probabilistic POMDP.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from math import ceil, log2
from typing import Iterable, Sequence


def _int(v:int, lo:int, hi:int, label:str)->None:
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(f"{label} must be an integer in {lo}..{hi}")


def canonical_partition(labels: Sequence[int]) -> tuple[int,...]:
    labels=tuple(labels)
    if not labels or labels[0] != 0:
        raise ValueError("partition must be a nonempty restricted-growth string beginning at 0")
    mx=0
    for label in labels:
        if type(label) is not int or label < 0 or label > mx+1:
            raise ValueError("partition labels must be canonical with no skipped class ids")
        mx=max(mx,label)
    return labels


def partitions(n:int=4) -> tuple[tuple[int,...],...]:
    _int(n,1,8,"partition size")
    out=[]
    def rec(arr:list[int], mx:int)->None:
        if len(arr)==n:
            out.append(tuple(arr));return
        for label in range(mx+2):
            arr.append(label);rec(arr,max(mx,label));arr.pop()
    rec([0],0)
    return tuple(out)


def refines(fine:Sequence[int], coarse:Sequence[int])->bool:
    fine=canonical_partition(fine);coarse=canonical_partition(coarse)
    if len(fine)!=len(coarse): raise ValueError("partitions must have equal carrier size")
    for a in range(len(fine)):
        for b in range(len(fine)):
            if fine[a]==fine[b] and coarse[a]!=coarse[b]: return False
    return True


@dataclass(frozen=True)
class POSystem:
    transitions: tuple[tuple[int,...], ...]
    observations: tuple[int,...]

    def __post_init__(self)->None:
        if not self.transitions: raise ValueError("at least one action is required")
        n=len(self.observations)
        if not 1 <= n <= 16: raise ValueError("this prototype supports 1..16 hidden worlds")
        obs=canonical_partition(self.observations)
        object.__setattr__(self,"observations",obs)
        for row in self.transitions:
            if len(row)!=n: raise ValueError("each action must map every hidden world")
            for nxt in row:_int(nxt,0,n-1,"world successor")

    @property
    def worlds(self)->int:return len(self.observations)
    @property
    def actions(self)->int:return len(self.transitions)
    @property
    def observation_count(self)->int:return max(self.observations)+1
    @property
    def all_worlds(self)->int:return (1<<self.worlds)-1

    def observation_masks(self)->tuple[int,...]:
        masks=[0]*self.observation_count
        for world,obs in enumerate(self.observations): masks[obs] |= 1<<world
        return tuple(masks)

    def check_belief(self,belief:int)->None:
        _int(belief,1,self.all_worlds,"belief")

    def post(self,belief:int,action:int)->int:
        self.check_belief(belief);_int(action,0,self.actions-1,"action")
        out=0
        for world in range(self.worlds):
            if belief>>world&1: out |= 1<<self.transitions[action][world]
        return out

    def successors(self,belief:int,action:int)->tuple[int,...]:
        post=self.post(belief,action)
        result=tuple(sorted(post & mask for mask in self.observation_masks() if post & mask))
        if not result: raise RuntimeError("deterministic transition produced no successor belief")
        return result

    def consistent_beliefs(self)->tuple[int,...]:
        result=set()
        for cls in self.observation_masks():
            subset=cls
            while subset:
                result.add(subset);subset=(subset-1)&cls
        return tuple(sorted(result))

    def initial_beliefs(self,initial:int)->tuple[int,...]:
        self.check_belief(initial)
        return tuple(sorted(initial & cls for cls in self.observation_masks() if initial & cls))


def sure_safety(system:POSystem,safe_mask:int)->tuple[set[int],dict[int,int]]:
    _int(safe_mask,0,system.all_worlds,"safe mask")
    beliefs=system.consistent_beliefs()
    winning={b for b in beliefs if not (b & ~safe_mask)}
    strategy={}
    while True:
        nxt=set()
        for belief in winning:
            for action in range(system.actions):
                if all(child in winning for child in system.successors(belief,action)):
                    nxt.add(belief);strategy[belief]=action;break
        if nxt==winning:return winning,{b:a for b,a in strategy.items() if b in winning}
        winning=nxt


def sure_current_reach(system:POSystem,target_mask:int)->tuple[set[int],dict[int,int],dict[int,int]]:
    """Finite-horizon sure reach of a *current-state* target knowledge condition.

    Interpreting this as path reachability without a monitor is exact when target
    membership is absorbing. For nonabsorbing path objectives use lift_reach().
    """
    _int(target_mask,0,system.all_worlds,"target mask")
    beliefs=system.consistent_beliefs()
    winning={b for b in beliefs if not (b & ~target_mask)}
    strategy={};level={b:0 for b in winning};depth=0
    while True:
        added=[];depth+=1
        for belief in beliefs:
            if belief in winning:continue
            for action in range(system.actions):
                children=system.successors(belief,action)
                if all(child in winning for child in children):
                    added.append((belief,action));break
        if not added:return winning,strategy,level
        for belief,action in added:
            winning.add(belief);strategy[belief]=action;level[belief]=depth


def wins_from_initial(system:POSystem,initial:int,winning:set[int])->bool:
    return all(belief in winning for belief in system.initial_beliefs(initial))


def lift_reach(system:POSystem,target_mask:int)->tuple[POSystem,int]:
    """Product with a sticky 'target has been visited' monitor.

    Product world index is 2*physical + reached_flag. The observation exposes
    only the original physical observation; the monitor is maintained through
    history rather than granted as a sensor reading.
    """
    _int(target_mask,0,system.all_worlds,"target mask")
    n=system.worlds; rows=[]
    for action in range(system.actions):
        row=[]
        for physical in range(n):
            for flag in (0,1):
                nxt=system.transitions[action][physical]
                nf=flag or bool(target_mask>>nxt&1)
                row.append(2*nxt+int(nf))
        rows.append(tuple(row))
    obs=tuple(system.observations[world//2] for world in range(2*n))
    lifted=POSystem(tuple(rows),obs)
    done=sum(1<<(2*s+1) for s in range(n))
    return lifted,done


def lift_initial_reach(system:POSystem,initial:int,target_mask:int)->int:
    system.check_belief(initial);_int(target_mask,0,system.all_worlds,"target mask")
    out=0
    for state in range(system.worlds):
        if initial>>state&1: out |= 1<<(2*state+int(bool(target_mask>>state&1)))
    return out


def project_physical(product_belief:int, physical_states:int)->int:
    _int(physical_states,1,8,"physical states")
    _int(product_belief,1,(1<<(2*physical_states))-1,"product belief")
    out=0
    for state in range(physical_states):
        if product_belief & (3<<(2*state)): out |= 1<<state
    return out


def memoryless_observation_reach(system:POSystem,target_mask:int,initial:int)->tuple[int,...]|None:
    """Find a stationary action per current observation, if one guarantees reach."""
    _int(target_mask,0,system.all_worlds,"target mask");system.check_belief(initial)
    for policy in product(range(system.actions),repeat=system.observation_count):
        good=True
        for start in range(system.worlds):
            if not initial>>start&1:continue
            world=start;seen=set();hit=False
            for _ in range(system.worlds*system.observation_count+2):
                if target_mask>>world&1:hit=True;break
                if world in seen:break
                seen.add(world)
                world=system.transitions[policy[system.observations[world]]][world]
            if not hit:good=False;break
        if good:return policy
    return None


def no_observation_controller_reach(system:POSystem,target_mask:int,initial:int,memory_states:int)->dict|None:
    """Brute-force autonomous finite-memory controllers; intended only for tiny audits."""
    if system.observation_count!=1: raise ValueError("controller oracle requires one observation class")
    _int(memory_states,1,4,"memory states")
    for actions in product(range(system.actions),repeat=memory_states):
        for updates in product(range(memory_states),repeat=memory_states):
            good=True
            for start in range(system.worlds):
                if not initial>>start&1:continue
                world=start;memory=0;seen=set();hit=False
                for _ in range(system.worlds*memory_states+2):
                    if target_mask>>world&1:hit=True;break
                    key=(world,memory)
                    if key in seen:break
                    seen.add(key)
                    world=system.transitions[actions[memory]][world]
                    memory=updates[memory]
                if not hit:good=False;break
            if good:return {'actions':actions,'updates':updates}
    return None


def absorbing_target(system:POSystem,target_mask:int)->bool:
    _int(target_mask,0,system.all_worlds,"target mask")
    for action in range(system.actions):
        for state in range(system.worlds):
            if target_mask>>state&1 and not (target_mask>>system.transitions[action][state]&1):return False
    return True


def project_belief(belief:int, quotient:Sequence[int])->int:
    quotient=canonical_partition(quotient)
    _int(belief,1,(1<<len(quotient))-1,"belief")
    out=0
    for world,label in enumerate(quotient):
        if belief>>world&1: out |= 1<<label
    return out


@dataclass(frozen=True)
class ObservationController:
    """Finite controller: current observation selects both action and next memory."""
    actions: tuple[tuple[int,...], ...]
    updates: tuple[tuple[int,...], ...]
    start: int = 0

    def validate(self,system:POSystem)->None:
        q=len(self.actions)
        if q<1 or len(self.updates)!=q: raise ValueError("controller tables must be matching and nonempty")
        _int(self.start,0,q-1,"controller start")
        for ar,ur in zip(self.actions,self.updates):
            if len(ar)!=system.observation_count or len(ur)!=system.observation_count:
                raise ValueError("controller row must cover every observation")
            for action in ar:_int(action,0,system.actions-1,"controller action")
            for nxt in ur:_int(nxt,0,q-1,"controller memory successor")

    @property
    def states(self)->int:return len(self.actions)

    def step(self,system:POSystem,world:int,memory:int)->tuple[int,int,int]:
        self.validate(system);_int(world,0,system.worlds-1,"world");_int(memory,0,self.states-1,"memory")
        obs=system.observations[world];action=self.actions[memory][obs];nmem=self.updates[memory][obs]
        return system.transitions[action][world],nmem,action

    def wins_reach(self,system:POSystem,target_mask:int,initial:int)->bool:
        self.validate(system);system.check_belief(initial);_int(target_mask,0,system.all_worlds,"target mask")
        for start in range(system.worlds):
            if not initial>>start&1:continue
            world=start;memory=self.start;seen=set();hit=False
            for _ in range(system.worlds*self.states+2):
                if target_mask>>world&1:hit=True;break
                key=(world,memory)
                if key in seen:break
                seen.add(key)
                world,memory,_=self.step(system,world,memory)
            if not hit:return False
        return True

    def minimize(self,system:POSystem)->tuple["ObservationController",tuple[int,...]]:
        self.validate(system)
        labels=[0]*self.states
        key_to_label={}
        for q,row in enumerate(self.actions):
            key=tuple(row)
            if key not in key_to_label:key_to_label[key]=len(key_to_label)
            labels[q]=key_to_label[key]
        while True:
            mapping={};new=[]
            for q in range(self.states):
                key=(tuple(self.actions[q]),tuple(labels[self.updates[q][o]] for o in range(system.observation_count)))
                if key not in mapping:mapping[key]=len(mapping)
                new.append(mapping[key])
            if new==labels:break
            labels=new
        classes=max(labels)+1;reps=[labels.index(c) for c in range(classes)]
        actions=tuple(self.actions[r] for r in reps)
        updates=tuple(tuple(labels[self.updates[r][o]] for o in range(system.observation_count)) for r in reps)
        return ObservationController(actions,updates,labels[self.start]),tuple(labels)

    def memory_bits(self,system:POSystem)->int:
        minimized,_=self.minimize(system)
        return 0 if minimized.states<=1 else ceil(log2(minimized.states))

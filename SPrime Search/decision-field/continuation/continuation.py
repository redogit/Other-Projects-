#!/usr/bin/env python3
"""Coarsest future-safe quotient for finite deterministic action systems with state labels."""
from collections import deque


def validate(actions, labels):
    labels=tuple(labels); n=len(labels)
    if n<1: raise ValueError('nonempty state set required')
    actions=tuple(tuple(action) for action in actions)
    if not actions: raise ValueError('at least one action required')
    for action in actions:
        if len(action)!=n or any(type(x) is not int or not 0<=x<n for x in action): raise ValueError('invalid total action map')
    return actions,labels


def quotient(actions,labels):
    actions,labels=validate(actions,labels);n=len(labels)
    mapping={};classes=[]
    for value in labels:
        if value not in mapping:mapping[value]=len(mapping)
        classes.append(mapping[value])
    while True:
        keys=[(labels[state],tuple(classes[action[state]] for action in actions)) for state in range(n)]
        mapping={};new=[]
        for key in keys:
            if key not in mapping:mapping[key]=len(mapping)
            new.append(mapping[key])
        if new==classes:return tuple(classes)
        classes=new


def refines(fine,coarse):
    if len(fine)!=len(coarse): raise ValueError('carrier mismatch')
    return all(not(fine[i]==fine[j] and coarse[i]!=coarse[j]) for i in range(len(fine)) for j in range(len(fine)))


def apply_word(actions,state,word):
    actions,_=validate(actions,range(len(actions[0])))
    if type(state) is not int or not 0<=state<len(actions[0]): raise ValueError('state')
    for action in word:
        if type(action) is not int or not 0<=action<len(actions): raise ValueError('action')
        state=actions[action][state]
    return state


def distinguish(actions,labels,left,right):
    actions,labels=validate(actions,labels);n=len(labels)
    if type(left) is not int or type(right) is not int or not 0<=left<n or not 0<=right<n: raise ValueError('state')
    if labels[left]!=labels[right]:return ()
    queue=deque([((left,right),())]);seen={(left,right)}
    while queue:
        (a,b),word=queue.popleft()
        for index,action in enumerate(actions):
            na,nb=action[a],action[b];new_word=word+(index,)
            if labels[na]!=labels[nb]:return new_word
            if (na,nb) not in seen:
                seen.add((na,nb));queue.append(((na,nb),new_word))
    return None

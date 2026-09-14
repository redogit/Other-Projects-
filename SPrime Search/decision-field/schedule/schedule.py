#!/usr/bin/env python3
"""Finite schedule semantics for four-state T4 decision fields.

A schedule is a word over context symbols 0..3. Each context selects one of
four local maps on states 0..3. Finite words compose to a map in the full
four-state transformation monoid (at most 4^4 = 256 maps), which gives exact
coverage of all finite open-loop schedules for a fixed T4 system without
listing infinitely many words.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import ceil, log2
from typing import Iterable, Sequence

STATE_COUNT = 4
CONTEXT_COUNT = 4
IDENTITY_MAP = sum(state << (2 * state) for state in range(STATE_COUNT))
MAX_T4 = (1 << 32) - 1


def _int(value: int, low: int, high: int, label: str) -> None:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{label} must be an integer in {low}..{high}")


def _rank(rank: int) -> None:
    _int(rank, 0, MAX_T4, "transition rank")


def map_tuple(byte: int) -> tuple[int, int, int, int]:
    _int(byte, 0, 255, "local map")
    return tuple((byte >> (2 * state)) & 3 for state in range(STATE_COUNT))


def map_byte(values: Sequence[int]) -> int:
    if len(values) != STATE_COUNT:
        raise ValueError("local map must have exactly four images")
    out = 0
    for state, value in enumerate(values):
        _int(value, 0, 3, "local image")
        out |= value << (2 * state)
    return out


def compose(after: int, before: int) -> int:
    """Return after o before on four states."""
    a, b = map_tuple(after), map_tuple(before)
    return map_byte(tuple(a[b[state]] for state in range(STATE_COUNT)))


def power(local_map: int, exponent: int) -> int:
    _int(local_map, 0, 255, "local map")
    if type(exponent) is not int or exponent < 0:
        raise ValueError("exponent must be a nonnegative integer")
    result, base = IDENTITY_MAP, local_map
    while exponent:
        if exponent & 1:
            result = compose(base, result)
        base = compose(base, base)
        exponent >>= 1
    return result


def context_map(rank: int, context: int) -> int:
    _rank(rank)
    _int(context, 0, CONTEXT_COUNT - 1, "context")
    return (rank >> (8 * context)) & 255


def normalize_word(word: Iterable[int]) -> tuple[int, ...]:
    if isinstance(word, (str, bytes, bytearray)):
        raise ValueError("schedule word must be an iterable of integer context ids")
    result = tuple(word)
    for context in result:
        _int(context, 0, CONTEXT_COUNT - 1, "context")
    return result


def word_map(rank: int, word: Iterable[int]) -> int:
    _rank(rank)
    result = IDENTITY_MAP
    for context in normalize_word(word):
        result = compose(context_map(rank, context), result)
    return result


def apply_word(rank: int, state: int, word: Iterable[int]) -> int:
    _rank(rank)
    _int(state, 0, STATE_COUNT - 1, "state")
    return map_tuple(word_map(rank, word))[state]


def cycles(local_map: int) -> tuple[tuple[int, ...], ...]:
    """Canonical cycle sets of a four-state map, ordered by least element."""
    f = map_tuple(local_map)
    seen: set[int] = set()
    found: list[tuple[int, ...]] = []
    for start in range(STATE_COUNT):
        if start in seen:
            continue
        path: list[int] = []
        pos: dict[int, int] = {}
        state = start
        while state not in pos and state not in seen:
            pos[state] = len(path)
            path.append(state)
            state = f[state]
        if state in pos:
            cycle = path[pos[state]:]
            anchor = cycle.index(min(cycle))
            found.append(tuple(cycle[anchor:] + cycle[:anchor]))
        seen.update(path)
    return tuple(sorted(found))


def periodic_profile(rank: int, block: Iterable[int]) -> dict:
    word = normalize_word(block)
    if not word:
        raise ValueError("periodic block cannot be empty")
    local = word_map(rank, word)
    return {
        "block": word,
        "block_map": local,
        "block_map_images": map_tuple(local),
        "cycles": cycles(local),
    }


def semigroup(rank: int, contexts: Iterable[int] = range(CONTEXT_COUNT)) -> dict[int, tuple[int, ...]]:
    """Exact closure under appending allowed contexts; shortest word per map."""
    _rank(rank)
    generators = tuple(dict.fromkeys(normalize_word(contexts)))
    if not generators:
        return {IDENTITY_MAP: ()}
    seen: dict[int, tuple[int, ...]] = {IDENTITY_MAP: ()}
    queue = deque([IDENTITY_MAP])
    while queue:
        current = queue.popleft()
        prefix = seen[current]
        for context in generators:
            nxt = compose(context_map(rank, context), current)
            if nxt not in seen:
                seen[nxt] = prefix + (context,)
                queue.append(nxt)
    return seen


def reachable_states(rank: int, initial: Iterable[int], contexts: Iterable[int] = range(CONTEXT_COUNT)) -> tuple[int, ...]:
    _rank(rank)
    starts = tuple(dict.fromkeys(initial))
    if not starts:
        raise ValueError("at least one initial state is required")
    for state in starts:
        _int(state, 0, 3, "initial state")
    generators = tuple(dict.fromkeys(normalize_word(contexts)))
    seen = set(starts)
    queue = deque(starts)
    while queue:
        state = queue.popleft()
        for context in generators:
            nxt = map_tuple(context_map(rank, context))[state]
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return tuple(sorted(seen))


def _mask(states: Iterable[int], label: str) -> int:
    mask = 0
    for state in states:
        _int(state, 0, 3, label)
        mask |= 1 << state
    return mask


def adversarial_safety(rank: int, safe_states: Iterable[int], contexts: Iterable[int] = range(CONTEXT_COUNT)) -> tuple[int, ...]:
    """States that remain safe for every infinite allowed context sequence."""
    _rank(rank)
    allowed = tuple(dict.fromkeys(normalize_word(contexts)))
    current = _mask(safe_states, "safe state")
    while True:
        nxt_mask = 0
        for state in range(4):
            if (current >> state) & 1 and all((current >> map_tuple(context_map(rank, c))[state]) & 1 for c in allowed):
                nxt_mask |= 1 << state
        if nxt_mask == current:
            return tuple(state for state in range(4) if (current >> state) & 1)
        current = nxt_mask


def controllable_safety(rank: int, safe_states: Iterable[int], contexts: Iterable[int] = range(CONTEXT_COUNT)) -> tuple[int, ...]:
    """States from which some memoryless context choice preserves safety forever."""
    _rank(rank)
    allowed = tuple(dict.fromkeys(normalize_word(contexts)))
    current = _mask(safe_states, "safe state")
    while True:
        nxt_mask = 0
        for state in range(4):
            if (current >> state) & 1 and any((current >> map_tuple(context_map(rank, c))[state]) & 1 for c in allowed):
                nxt_mask |= 1 << state
        if nxt_mask == current:
            return tuple(state for state in range(4) if (current >> state) & 1)
        current = nxt_mask


def controllable_reach(rank: int, targets: Iterable[int], contexts: Iterable[int] = range(CONTEXT_COUNT)) -> tuple[int, ...]:
    """States from which a scheduler can force eventual target reachability."""
    _rank(rank)
    allowed = tuple(dict.fromkeys(normalize_word(contexts)))
    current = _mask(targets, "target state")
    while True:
        nxt_mask = current
        for state in range(4):
            if not (current >> state) & 1 and any((current >> map_tuple(context_map(rank, c))[state]) & 1 for c in allowed):
                nxt_mask |= 1 << state
        if nxt_mask == current:
            return tuple(state for state in range(4) if (current >> state) & 1)
        current = nxt_mask


def adversarial_reach(rank: int, targets: Iterable[int], contexts: Iterable[int] = range(CONTEXT_COUNT)) -> tuple[int, ...]:
    """States guaranteed to reach a target for every allowed context sequence."""
    _rank(rank)
    allowed = tuple(dict.fromkeys(normalize_word(contexts)))
    current = _mask(targets, "target state")
    while True:
        nxt_mask = current
        for state in range(4):
            if not (current >> state) & 1 and allowed and all((current >> map_tuple(context_map(rank, c))[state]) & 1 for c in allowed):
                nxt_mask |= 1 << state
        if nxt_mask == current:
            return tuple(state for state in range(4) if (current >> state) & 1)
        current = nxt_mask


@dataclass(frozen=True)
class MooreScheduler:
    """Finite history-dependent scheduler over observed plant states."""
    outputs: tuple[int, ...]
    transitions: tuple[tuple[int, int, int, int], ...]
    start: int = 0

    def __post_init__(self) -> None:
        qn = len(self.outputs)
        if qn < 1 or len(self.transitions) != qn:
            raise ValueError("scheduler must have matching nonempty outputs/transitions")
        _int(self.start, 0, qn - 1, "scheduler start")
        for context in self.outputs:
            _int(context, 0, 3, "scheduler output context")
        for row in self.transitions:
            if len(row) != 4:
                raise ValueError("scheduler transition row must cover four observed states")
            for nxt in row:
                _int(nxt, 0, qn - 1, "scheduler memory successor")

    @property
    def states(self) -> int:
        return len(self.outputs)

    def step(self, rank: int, plant_state: int, memory: int) -> tuple[int, int, int]:
        _rank(rank); _int(plant_state, 0, 3, "plant state"); _int(memory, 0, self.states - 1, "memory")
        context = self.outputs[memory]
        plant_next = map_tuple(context_map(rank, context))[plant_state]
        memory_next = self.transitions[memory][plant_next]
        return plant_next, memory_next, context

    def combined_successor(self, rank: int, combined: int) -> int:
        _int(combined, 0, 4 * self.states - 1, "combined state")
        memory, plant = divmod(combined, 4)
        plant_next, memory_next, _ = self.step(rank, plant, memory)
        return 4 * memory_next + plant_next

    def combined_cycles(self, rank: int) -> tuple[tuple[int, ...], ...]:
        total = 4 * self.states
        seen: set[int] = set(); found: list[tuple[int, ...]] = []
        for start in range(total):
            if start in seen: continue
            path: list[int] = []; pos: dict[int, int] = {}; state = start
            while state not in pos and state not in seen:
                pos[state] = len(path); path.append(state); state = self.combined_successor(rank, state)
            if state in pos:
                cyc = path[pos[state]:]; anchor = cyc.index(min(cyc)); found.append(tuple(cyc[anchor:] + cyc[:anchor]))
            seen.update(path)
        return tuple(sorted(found))

    def minimize(self) -> tuple["MooreScheduler", tuple[int, ...]]:
        """Moore minimization over every possible observed-state history."""
        labels = list(self.outputs)
        while True:
            keys = [(self.outputs[q], tuple(labels[self.transitions[q][s]] for s in range(4))) for q in range(self.states)]
            mapping: dict[tuple, int] = {}; new_labels: list[int] = []
            for key in keys:
                if key not in mapping: mapping[key] = len(mapping)
                new_labels.append(mapping[key])
            if new_labels == labels: break
            labels = new_labels
        classes = max(labels) + 1
        reps = [labels.index(c) for c in range(classes)]
        outputs = tuple(self.outputs[q] for q in reps)
        transitions = tuple(tuple(labels[self.transitions[q][s]] for s in range(4)) for q in reps)
        return MooreScheduler(outputs, transitions, labels[self.start]), tuple(labels)

    def memory_bits(self) -> int:
        minimized, _ = self.minimize()
        return 0 if minimized.states <= 1 else ceil(log2(minimized.states))


def periodic_scheduler(word: Iterable[int]) -> MooreScheduler:
    block = normalize_word(word)
    if not block:
        raise ValueError("periodic word cannot be empty")
    n = len(block)
    transitions = tuple(tuple((q + 1) % n for _ in range(4)) for q in range(n))
    return MooreScheduler(block, transitions, 0)

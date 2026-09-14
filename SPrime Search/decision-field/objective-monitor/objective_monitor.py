#!/usr/bin/env python3
"""Pass 11: exact sticky-objective monitor collision census on four-state/two-action plants."""
from collections import deque

STATE_COUNT = 4
ACTION_CODE_COUNT = 256
TRACKED_STATE = 1


def map_from_code(code):
    if type(code) is not int or not 0 <= code < ACTION_CODE_COUNT:
        raise ValueError('action code must be in [0,255]')
    return tuple((code >> (2 * i)) & 3 for i in range(STATE_COUNT))


def reachable_product(actions, initial, tracked=TRACKED_STATE):
    actions = tuple(tuple(a) for a in actions)
    if len(actions) != 2 or any(len(a) != STATE_COUNT for a in actions):
        raise ValueError('exactly two four-state total actions required')
    if any(any(type(x) is not int or not 0 <= x < STATE_COUNT for x in a) for a in actions):
        raise ValueError('invalid action map')
    if type(initial) is not int or not 0 <= initial < STATE_COUNT:
        raise ValueError('invalid initial state')
    if type(tracked) is not int or not 0 <= tracked < STATE_COUNT:
        raise ValueError('invalid tracked state')
    start = (initial, initial == tracked)
    queue = deque([start])
    distance = {start: 0}
    word = {start: ()}
    while queue:
        state, seen = queue.popleft()
        for action_index, action in enumerate(actions):
            nxt = action[state]
            node = (nxt, seen or nxt == tracked)
            if node not in distance:
                distance[node] = distance[(state, seen)] + 1
                word[node] = word[(state, seen)] + (action_index,)
                queue.append(node)
    return distance, word


def initial_case(actions, initial, tracked=TRACKED_STATE):
    distance, word = reachable_product(actions, initial, tracked)
    collisions = []
    for physical in range(STATE_COUNT):
        no = (physical, False)
        yes = (physical, True)
        if no in distance and yes in distance:
            radius = max(distance[no], distance[yes])
            collisions.append({
                'physical_state': physical,
                'radius': radius,
                'word_without_visit': list(word[no]),
                'word_with_visit': list(word[yes]),
            })
    collisions.sort(key=lambda row: (row['radius'], row['physical_state'], row['word_without_visit'], row['word_with_visit']))
    return collisions


def census():
    systems_with_collision = 0
    initial_cases_with_collision = 0
    collision_physical_states = 0
    minimum_certificate_radius_distribution = {}
    initial_cases_by_colliding_state_count = {str(i): 0 for i in range(5)}
    witness = None
    for left_code in range(ACTION_CODE_COUNT):
        left = map_from_code(left_code)
        for right_code in range(ACTION_CODE_COUNT):
            right = map_from_code(right_code)
            actions = (left, right)
            system_has_collision = False
            for initial in range(STATE_COUNT):
                collisions = initial_case(actions, initial)
                count = len(collisions)
                initial_cases_by_colliding_state_count[str(count)] = initial_cases_by_colliding_state_count.get(str(count), 0) + 1
                if not collisions:
                    continue
                system_has_collision = True
                initial_cases_with_collision += 1
                collision_physical_states += count
                radius = collisions[0]['radius']
                minimum_certificate_radius_distribution[str(radius)] = minimum_certificate_radius_distribution.get(str(radius), 0) + 1
                candidate = {
                    'left_code': left_code,
                    'right_code': right_code,
                    'left_map': list(left),
                    'right_map': list(right),
                    'initial_state': initial,
                    **collisions[0],
                }
                key = (candidate['radius'], candidate['left_code'], candidate['right_code'], candidate['initial_state'], candidate['physical_state'])
                if witness is None or key < (witness['radius'], witness['left_code'], witness['right_code'], witness['initial_state'], witness['physical_state']):
                    witness = candidate
            if system_has_collision:
                systems_with_collision += 1
    return {
        'status': 'PASS_BOUNDED',
        'state_count': STATE_COUNT,
        'action_count': 2,
        'ordered_action_map_pairs': ACTION_CODE_COUNT ** 2,
        'initial_state_cases': ACTION_CODE_COUNT ** 2 * STATE_COUNT,
        'tracked_state': TRACKED_STATE,
        'systems_with_monitor_collision': systems_with_collision,
        'initial_cases_with_monitor_collision': initial_cases_with_collision,
        'collision_physical_states': collision_physical_states,
        'minimum_certificate_radius_distribution': dict(sorted(minimum_certificate_radius_distribution.items(), key=lambda kv: int(kv[0]))),
        'initial_cases_by_colliding_state_count': dict(sorted(initial_cases_by_colliding_state_count.items(), key=lambda kv: int(kv[0]))),
        'maximum_minimum_certificate_radius': max(map(int, minimum_certificate_radius_distribution)) if minimum_certificate_radius_distribution else None,
        'witness': witness,
    }


if __name__ == '__main__':
    import json
    print(json.dumps(census(), sort_keys=True, separators=(',', ':')))

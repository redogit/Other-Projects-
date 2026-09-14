#!/usr/bin/env python3
"""Pass 12: exact one-bit controller-memory rescue for two-class sensors."""

STATE_COUNT = 4
ACTION_CODE_COUNT = 256


def map_tuple(code):
    if type(code) is not int or not 0 <= code < ACTION_CODE_COUNT:
        raise ValueError('action code must be in [0,255]')
    return tuple((code >> (2 * s)) & 3 for s in range(STATE_COUNT))


def two_class_partitions():
    out = []
    def rec(a, mx):
        if len(a) == STATE_COUNT:
            if mx == 1:
                c0 = a.count(0)
                profile = '3+1' if max(c0, STATE_COUNT - c0) == 3 else '2+2'
                out.append((tuple(a), profile))
            return
        for label in range(mx + 2):
            rec(a + [label], max(mx, label))
    rec([0], 0)
    return tuple(out)


def memoryless_wins(map0, map1, target, partition, code):
    for start in range(STATE_COUNT):
        state = start
        seen = 0
        while state != target and not ((seen >> state) & 1):
            seen |= 1 << state
            action = (code >> partition[state]) & 1
            state = (map1 if action else map0)[state]
        if state != target:
            return False
    return True


def two_state_controller_cells(code):
    if type(code) is not int or not 0 <= code < 256:
        raise ValueError('controller code must be in [0,255]')
    return tuple(((code >> (2 * cell)) & 1, (code >> (2 * cell + 1)) & 1) for cell in range(4))


def two_state_wins(map0, map1, target, partition, cells):
    if len(cells) != 4:
        raise ValueError('two-state/two-observation controller requires four cells')
    for start in range(STATE_COUNT):
        state = start
        memory = 0
        seen = 0
        while state != target:
            product = 2 * state + memory
            if (seen >> product) & 1:
                return False
            seen |= 1 << product
            action, next_memory = cells[2 * memory + partition[state]]
            state = (map1 if action else map0)[state]
            memory = next_memory
    return True


def census():
    partitions = two_class_partitions()
    if len(partitions) != 7:
        raise RuntimeError('expected seven two-class partitions of four states')
    controllers = tuple((code, two_state_controller_cells(code)) for code in range(256))
    systems = sensor_cases = q1_wins = q2_wins = rescued = systems_rescued = 0
    rescued_by_profile = {'3+1': 0, '2+2': 0}
    rescue_count_distribution = {}
    witness = None

    for target in range(STATE_COUNT):
        absorbing_codes = [code for code in range(ACTION_CODE_COUNT) if map_tuple(code)[target] == target]
        for code0 in absorbing_codes:
            map0 = map_tuple(code0)
            for code1 in absorbing_codes:
                map1 = map_tuple(code1)
                systems += 1
                rescue_count = 0
                for partition, profile in partitions:
                    sensor_cases += 1
                    if any(memoryless_wins(map0, map1, target, partition, code) for code in range(4)):
                        q1_wins += 1
                        q2_wins += 1
                        continue
                    winning_code = None
                    winning_cells = None
                    for controller_code, cells in controllers:
                        if two_state_wins(map0, map1, target, partition, cells):
                            winning_code = controller_code
                            winning_cells = cells
                            break
                    if winning_code is None:
                        continue
                    q2_wins += 1
                    rescued += 1
                    rescue_count += 1
                    rescued_by_profile[profile] += 1
                    candidate_key = (target, code0, code1, partition)
                    if witness is None or candidate_key < witness[0]:
                        witness = (candidate_key, {
                            'target': target,
                            'map0_code': code0,
                            'map1_code': code1,
                            'map0': list(map0),
                            'map1': list(map1),
                            'partition': list(partition),
                            'profile': profile,
                            'controller_code': winning_code,
                            'controller_cells': [
                                {
                                    'memory': memory,
                                    'observation': observation,
                                    'action': winning_cells[2 * memory + observation][0],
                                    'next_memory': winning_cells[2 * memory + observation][1],
                                }
                                for memory in range(2) for observation in range(2)
                            ],
                        })
                rescue_count_distribution[rescue_count] = rescue_count_distribution.get(rescue_count, 0) + 1
                systems_rescued += int(rescue_count > 0)

    return {
        'status': 'PASS_BOUNDED',
        'systems': systems,
        'two_class_partitions': len(partitions),
        'sensor_cases': sensor_cases,
        'memoryless_winning_sensor_cases': q1_wins,
        'two_state_memory_winning_sensor_cases': q2_wins,
        'memory_rescued_sensor_cases': rescued,
        'systems_with_memory_rescue': systems_rescued,
        'rescues_by_profile': rescued_by_profile,
        'rescue_count_distribution': {str(k): rescue_count_distribution[k] for k in sorted(rescue_count_distribution)},
        'witness': witness[1],
    }


if __name__ == '__main__':
    import json
    print(json.dumps(census(), sort_keys=True, separators=(',', ':')))

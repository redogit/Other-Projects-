"""Full-cost consequence-aware selector probe for recovered SAT64.

Usage from the extracted SAT64_GUARD_FEEDBACK_2026-09-13 package root:
    python3 /path/to/consequence_selector_k4.py OUTDIR 4 compiler_0 compiler_1 balanced_0 balanced_4

This adapter imports only the recovered SAT64 exact solver/checker modules. It does not use
source SAT/UNSAT labels for planning; labels are checked only after a non-UNKNOWN result.
"""
import collections
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, 'checks')
from campaign import ROOT, write
from feedback import solve
from verify_feedback import check
from ceiling_probe import condition
from families import compile_cnf


def burden(r):
    unknown = [len(p['variables']) for p in r['parts'] if p['status'] == 'UNKNOWN']
    return (
        1 if r['status'] == 'UNKNOWN' else 0,
        max(unknown, default=0),
        len(unknown),
        r['d'],
    )


def search(out, n, clauses, k=4, node_cap=63, depth_cap=8):
    root_n = n
    counts = collections.Counter(v for c in clauses for v in c)
    nodes = []
    states = 0
    max_depth = 0
    metrics = {
        'planning_candidates': 0,
        'planning_branch_probes': 0,
        'planning_seconds': 0.0,
        'planning_local_assignments_tested': 0,
        'planning_row_operations': 0,
        'fresh_node_solves': 0,
        'reused_planning_certificates': 0,
        'node_local_assignments_tested': 0,
        'node_row_operations': 0,
    }
    start = time.perf_counter()

    def rec(nn, cc, depth, precert=None):
        nonlocal states, max_depth
        idx = len(nodes)
        node = {'id': idx, 'depth': depth}
        nodes.append(node)
        max_depth = max(max_depth, depth)
        if states >= node_cap or depth > depth_cap:
            node.update(status='UNKNOWN', reason='resource_bound')
            return idx, 'UNKNOWN', None
        states += 1

        if precert is None:
            r = solve(nn, cc, 8)
            assert check(nn, cc, r, 8)
            metrics['fresh_node_solves'] += 1
        else:
            r = precert
            assert check(nn, cc, r, 8)
            metrics['reused_planning_certificates'] += 1

        metrics['node_local_assignments_tested'] += r['tested']
        metrics['node_row_operations'] += r['row_operations']
        path = out / f'node_{idx}.json'
        write(path, {'n': nn, 'clauses': cc, 'certificate': r})
        node.update(certificate_file=path.name, free=r['d'], feedback_status=r['status'])

        if r['status'] != 'UNKNOWN':
            node['status'] = r['status']
            return idx, r['status'], r['model']
        if depth == depth_cap:
            node.update(status='UNKNOWN', reason='depth_bound')
            return idx, 'UNKNOWN', None

        candidates = [
            j for j, l in enumerate(r['affine'])
            if j < root_n and any(mask for mask in l)
        ]
        assert candidates
        shortlist = sorted(candidates, key=lambda j: (counts[j], -j), reverse=True)[:k]
        metrics['planning_candidates'] += len(shortlist)

        planned = []
        pstart = time.perf_counter()
        for var in shortlist:
            children = []
            for value in (0, 1):
                n2, c2 = condition(nn, cc, var, value)
                rr = solve(n2, c2, 8)
                assert check(n2, c2, rr, 8)
                metrics['planning_branch_probes'] += 1
                metrics['planning_local_assignments_tested'] += rr['tested']
                metrics['planning_row_operations'] += rr['row_operations']
                children.append((value, n2, c2, rr))
            worst = max(burden(x[3]) for x in children)
            combined = sum(burden(x[3])[1] for x in children)
            planned.append((worst, combined, -counts[var], var, children))
        metrics['planning_seconds'] += time.perf_counter() - pstart

        planned.sort(key=lambda x: x[:4])
        worst, combined, _, var, children = planned[0]
        node.update(
            variable=var,
            planning_shortlist=shortlist,
            selected_worst_burden=list(worst),
            selected_combined_unknown_component=combined,
            children=[],
        )

        statuses = []
        for value, n2, c2, rr in children:
            child, status, model = rec(n2, c2, depth + 1, rr)
            node['children'].append({'value': value, 'id': child})
            statuses.append(status)
            if status == 'SAT':
                model = [v for v in model if v < nn]
                assert all(len(set(c) & set(model)) == 1 for c in cc)
                node['status'] = 'SAT'
                return idx, 'SAT', model

        status = 'UNSAT' if statuses == ['UNSAT', 'UNSAT'] else 'UNKNOWN'
        node['status'] = status
        return idx, status, None

    _, status, model = rec(n, clauses, 0)
    if model is not None:
        assert all(len(set(c) & set(model)) == 1 for c in clauses)
    elapsed = time.perf_counter() - start
    write(out / 'tree.json', {
        'root_n': n,
        'root_clauses': clauses,
        'mode': f'consequence_k{k}',
        'node_cap': node_cap,
        'depth_cap': depth_cap,
        'nodes': nodes,
        'status': status,
        'model': model,
    })
    return {
        'mode': f'consequence_k{k}',
        'status': status,
        'states_evaluated': states,
        'tree_records': len(nodes),
        'maximum_depth': max_depth,
        'seconds_total': elapsed,
        'node_cap': node_cap,
        'depth_cap': depth_cap,
        **metrics,
    }


def main(outdir, k=4, cases=('compiler_0', 'compiler_1', 'balanced_0', 'balanced_4'), record_exporter=None):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    panel = []
    source = json.loads((ROOT / 'evidence/run01/adversarial/source_controls.json').read_text())
    allcases = []
    for name in ('compiler_0', 'compiler_1'):
        x = json.loads((ROOT / 'inputs' / (name + '.json')).read_text())
        allcases.append((name, x['n'], x['clauses'], x['expected']))
    for i in (0, 4):
        x = source[i]
        n, cls = compile_cnf(8, x['source'])
        allcases.append((f'balanced_{i}', n, cls, 'SAT' if x['models'] else 'UNSAT'))

    wanted = set(cases)
    for name, n, cls, expected in allcases:
        if name not in wanted:
            continue
        dest = out / name
        dest.mkdir()
        r = search(dest, n, cls, k=k)
        r.update(name=name, n=n, known_status=expected)
        if r['status'] != 'UNKNOWN':
            assert r['status'] == expected
        if record_exporter is not None:
            record_exporter(name, dict(r), dest)
        panel.append(r)
        print(json.dumps(r), flush=True)
    write(out / 'SUMMARY.json', {'k': k, 'rows': panel, 'universal_goal_status': 'OPEN'})


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]), tuple(sys.argv[3:]))

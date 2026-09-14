from __future__ import annotations

from itertools import combinations, product

from catalog import PartCatalog
from core import AssemblySpec, ObligationSpec, PartSpec


def _ordered(parts):
    return tuple(sorted(parts, key=lambda p: (p.stable_id, p.version)))


def candidate_part_sets(obligation: ObligationSpec, catalog: PartCatalog) -> tuple[tuple[PartSpec, ...], ...]:
    if not isinstance(obligation, ObligationSpec) or not isinstance(catalog, PartCatalog):
        raise ValueError("expected ObligationSpec and PartCatalog")
    specs = catalog.ordered_specs()
    required = set(obligation.required_capabilities)
    out = []
    for size in range(1, len(specs) + 1):
        for subset in combinations(specs, size):
            provided = set().union(*(set(part.provides) for part in subset))
            if not required <= provided:
                continue
            if any(not set(part.requires) <= provided for part in subset):
                continue
            out.append(subset)
    return tuple(out)


def construction_order(parts: tuple[PartSpec, ...]) -> tuple[PartSpec, ...]:
    parts = _ordered(parts)
    if not parts:
        return ()
    providers: dict[str, list[PartSpec]] = {}
    for part in parts:
        for capability in part.provides:
            providers.setdefault(capability, []).append(part)
    incoming = {part: 0 for part in parts}
    outgoing = {part: set() for part in parts}
    for consumer in parts:
        for capability in consumer.requires:
            choices = [p for p in providers.get(capability, ()) if p != consumer]
            if not choices:
                raise ValueError(f"missing construction dependency {capability} for {consumer.stable_id}")
            provider = min(choices, key=lambda p: (p.stable_id, p.version))
            if consumer not in outgoing[provider]:
                outgoing[provider].add(consumer)
                incoming[consumer] += 1
    ready = sorted((p for p in parts if incoming[p] == 0), key=lambda p: (p.stable_id, p.version))
    result = []
    while ready:
        part = ready.pop(0)
        result.append(part)
        for child in sorted(outgoing[part], key=lambda p: (p.stable_id, p.version)):
            incoming[child] -= 1
            if incoming[child] == 0:
                ready.append(child)
                ready.sort(key=lambda p: (p.stable_id, p.version))
    if len(result) != len(parts):
        raise ValueError("construction dependency cycle")
    return tuple(result)


def compatible_wirings(obligation: ObligationSpec, parts: tuple[PartSpec, ...]):
    if not isinstance(obligation, ObligationSpec):
        raise ValueError("expected ObligationSpec")
    parts = _ordered(parts)
    connection_choices = []
    for consumer in parts:
        for input_name, input_type in consumer.input_ports:
            matches = []
            for producer in parts:
                if producer == consumer:
                    continue
                for output_name, output_type in producer.output_ports:
                    if output_type == input_type:
                        matches.append((producer.stable_id, output_name, consumer.stable_id, input_name))
            if matches:
                connection_choices.append(tuple(sorted(set(matches))))
    if not connection_choices:
        return ((),)
    wirings = {tuple(sorted(edges)) for edges in product(*connection_choices)}
    return tuple(sorted(wirings))


def pareto_frontier(assemblies: tuple[AssemblySpec, ...] | list[AssemblySpec]) -> tuple[AssemblySpec, ...]:
    ordered = sorted(assemblies, key=lambda a: (a.cost.items, a.stable_id, a.version))
    if len({(a.stable_id, a.version) for a in ordered}) != len(ordered):
        raise ValueError("duplicate assembly version")
    if not ordered:
        return ()
    dims = ordered[0].cost.dimensions()
    if any(a.cost.dimensions() != dims for a in ordered):
        raise ValueError("cost dimensions differ")
    return tuple(
        assembly
        for assembly in ordered
        if not any(other is not assembly and other.cost.dominates(assembly.cost) for other in ordered)
    )

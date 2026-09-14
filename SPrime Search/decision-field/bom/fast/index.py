from __future__ import annotations
from dataclasses import dataclass
from catalog import PartCatalog
from core import ObligationSpec

@dataclass(frozen=True)
class CompiledIndex:
    part_keys: tuple[tuple[str,int],...]
    part_slots: dict[tuple[str,int],int]
    capability_slots: dict[str,int]
    provide_masks: tuple[int,...]
    require_masks: tuple[int,...]
    required_capability_mask: int
    cost_dimensions: tuple[str,...]
    cost_tuples: tuple[tuple[int,...],...]
    port_edges: tuple[tuple[int,str,int,str],...]

def compile_index(obligation: ObligationSpec, catalog: PartCatalog) -> CompiledIndex:
    if not isinstance(obligation, ObligationSpec) or not isinstance(catalog, PartCatalog):
        raise ValueError('expected ObligationSpec and PartCatalog')
    parts=catalog.ordered_specs()
    part_keys=tuple((p.stable_id,p.version) for p in parts)
    part_slots={k:i for i,k in enumerate(part_keys)}
    capabilities=sorted(set(obligation.required_capabilities).union(*(set(p.provides)|set(p.requires) for p in parts)))
    capability_slots={c:i for i,c in enumerate(capabilities)}
    def mask(names):
        out=0
        for name in names: out |= 1 << capability_slots[name]
        return out
    provide_masks=tuple(mask(p.provides) for p in parts)
    require_masks=tuple(mask(p.requires) for p in parts)
    required_capability_mask=mask(obligation.required_capabilities)
    cost_dimensions=tuple(obligation.cost_dimensions)
    cost_tuples=[]
    for p in parts:
        d=p.cost.as_dict()
        if tuple(sorted(d)) != tuple(sorted(cost_dimensions)):
            raise ValueError(f'cost dimensions differ for {p.stable_id}')
        cost_tuples.append(tuple(d[k] for k in cost_dimensions))
    edges=[]
    for pi,p in enumerate(parts):
        for oname,otype in p.output_ports:
            for ci,c in enumerate(parts):
                if pi==ci: continue
                for iname,itype in c.input_ports:
                    if otype==itype: edges.append((pi,oname,ci,iname))
    return CompiledIndex(part_keys,part_slots,capability_slots,provide_masks,require_masks,required_capability_mask,cost_dimensions,tuple(cost_tuples),tuple(sorted(set(edges))))

from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Z3Result:
    count: int
    mask: int
    solver: str


def z3_available() -> bool:
    try:
        import z3  # noqa: F401
        return True
    except Exception:
        return False


def _bits(mask: int):
    bit = 0
    while mask:
        if mask & 1:
            yield bit
        mask >>= 1
        bit += 1


def solve_z3(task) -> Z3Result:
    try:
        import z3
    except Exception as exc:
        raise RuntimeError("z3-solver is not available") from exc
    n = len(task.provide_masks)
    if len(task.require_masks) != n:
        raise ValueError("provide/require length mismatch")
    selected = [z3.Bool(f"p_{i}") for i in range(n)]
    opt = z3.Optimize()

    def providers_for(bit: int):
        return [selected[i] for i, pm in enumerate(task.provide_masks) if pm & (1 << bit)]

    for bit in _bits(task.required_mask):
        providers = providers_for(bit)
        opt.add(z3.Or(*providers) if providers else z3.BoolVal(False))

    for i, req in enumerate(task.require_masks):
        for bit in _bits(req):
            providers = providers_for(bit)
            opt.add(z3.Implies(selected[i], z3.Or(*providers) if providers else z3.BoolVal(False)))

    count_expr = z3.Sum([z3.If(v, 1, 0) for v in selected])
    mask_expr = z3.Sum([z3.If(v, 1 << i, 0) for i, v in enumerate(selected)])
    opt.minimize(count_expr)
    opt.minimize(mask_expr)
    if opt.check() != z3.sat:
        return Z3Result(-1, 0, z3.get_version_string())
    model = opt.model()
    return Z3Result(model.eval(count_expr).as_long(), model.eval(mask_expr).as_long(), z3.get_version_string())

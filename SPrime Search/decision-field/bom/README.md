# Decision-Field Bill of Materials

This layer treats the existing SPrime decision-field machinery as **one verified assembly**, not as the definition of the architecture.

A BOM search starts from a versioned obligation, then asks which parts are actually required to satisfy it. Parts may provide several intrinsic capabilities at once. Properties that appear only after parts are composed are recorded as verified **emergent effects**, not assigned to a component merely because of its name.

The operational capability vocabulary is:

- `transition`
- `observe`
- `infer`
- `monitor`
- `decide`
- `remember`
- `schedule`

Encoding and verification are sidecars rather than runtime capabilities.

## First bounded experiment

Milestone 1 uses the existing Pass 08 eight-world hidden-mode reachability witness. The obligation is intentionally smaller than the reference architecture: it requires transition dynamics and action selection, but it does **not** require a sensor, belief state, monitor, or memory by definition. Those are candidate materials.

Four assemblies are checked:

1. `synthetic.probe_baseline` — an explicitly synthetic probe/reset/commit protocol used only as a comparison baseline;
2. `pass08.fused_commit` — the actual Pass 08 two-state controller pattern in which a consequential action can also become diagnostic through transition + observation;
3. `openloop.312` — a three-phase open-loop schedule using actions `3,1,2` and no observation component;
4. `invalid.always_zero` — a deliberately cheap invalid control used to ensure failure is not mistaken for Pareto dominance.

All three non-invalid constructions satisfy the same finite reachability obligation. The probe baseline is dominated. The verified Pareto frontier contains:

- `openloop.312`: fewer components, less coupling, and no sensor dependency, but two policy-memory bits;
- `pass08.fused_commit`: one policy-memory bit, but four physical observation classes and an observation component.

Neither dominates the other under the declared cost dimensions. This is the intended result: the BOM exposes a **sensor/memory/construction tradeoff** rather than choosing an architecture by preference.

The fused assembly also receives an emergent-effect certificate for distinguishing the two initial hidden modes under the declared observation contract. The `fused.commit_action` part does not claim an intrinsic `infer` capability; diagnostic value belongs to the verified composition.

## Run

From the repository root:

```sh
python -m unittest discover -s "SPrime Search/decision-field/bom/tests" -v
python "SPrime Search/decision-field/bom/audit.py" --out /tmp/bom-fresh
```

The audit checks the BOM hidden-mode transition table against Pass 08's `hidden_system()` and hashes the Pass 06–08 reference sources before and after execution. Development-only runs outside a complete repository may use `--skip-reference-check`; such a run is labeled `PASS_DEV` and is not sufficient for promotion.

## Evidence boundaries

- Pass 06–08 files and scientific evidence are wrapped and referenced, not rewritten by the BOM.
- The dedicated-probe baseline is synthetic; it is not presented as a historical Pass 08 design.
- Fewer components is not globally better. Only dimensions declared by the obligation participate in Pareto comparison.
- The current search is finite and deterministic, not a globally optimal architecture search.
- Passing this hidden-mode obligation does not establish universal equivalence between sensing, memory, scheduling, or inference.
- An emergent-effect certificate is obligation- and assembly-specific.

See:

- design: `docs/superpowers/specs/2026-09-14-decision-field-bom-design.md`
- implementation plan: `docs/superpowers/plans/2026-09-14-decision-field-bom-implementation.md`
- canonical bounded outputs: `evidence/`

# S'1 Observer Field Addendum

Date: 2026-09-15
Status: APPROVED_IN_CHAT / BASELINE_REQUIREMENT
Parent spec: `docs/superpowers/specs/2026-09-15-s1-models-dimensional-deformation-lab-design.md`

## Why this addendum exists

After the parent S'1 design was written, the observer model was strengthened. Experiment 0 no longer treats observation as one global camera plus later optional observers.

The baseline now includes a **distributed observer field** over the sampled 3D and 4D compass/reference structures.

This addendum supersedes only the parent spec's statement that Experiment 0 requires only the human/play observer plus internal comparison machinery. The human remains Observer 0 for UX, but the model itself contains point observers from the start.

## Continuous ideal and finite executable model

Mathematical ideal:

```text
O3 = { O_p^(3) : p in C3 }
O4 = { O_q^(4) : q in C4 }
```

Every point carries a local observer frame.

The executable implementation uses finite deterministic samples:

```text
C3^(N3) = {p_1, ..., p_N3}
C4^(N4) = {q_1, ..., q_N4}
```

Every sampled point is an observer.

The implementation must never claim that a finite mesh instantiates every point of a continuum. Mesh refinement is an explicit later/convergence control.

## Eye/observer dimensional rule

For the bounded model, an `n`-dimensional point observer produces an `(n-1)`-dimensional local observation carrier:

```text
3D point observer -> 2D local observation
4D point observer -> 3D local observation
```

This is an observer/projection contract for the experiment, not a biological or physical-law claim.

## One observer = one task = one repairable degree

Each sampled observer has exactly one assigned task:

```text
Observer = location + local frame + task + one repair parameter
```

V0 task registry:

```text
x   observe x-component residual
 y  observe y-component residual
 z  observe z-component residual
 w  observe w-component residual
xw  observe xw-plane angular residual
 yw observe yw-plane angular residual
 zw observe zw-plane angular residual
```

Whitespace above is presentation only; canonical task ids are `x|y|z|w|xw|yw|zw`.

Tasks are assigned deterministically from stable observer ids. Task classes may repeat at different locations. Repetition is intentional: spatially separated observers with the same task provide controls.

An observer may report only its assigned scalar observation and may repair only its assigned scalar calibration parameter.

An `xw` observer cannot repair `yw`. A `w` observer cannot alter `x`, `y`, or `z` calibration.

## Observational repair is not object repair

Let `M` be the immutable mirror and `L_t` the live object.

For observer `i` with task `tau_i`:

```text
delta_i(t) = measure_tau_i(O_i(L_t)) - measure_tau_i(O_i(M))
```

Its permitted repair is:

```text
alpha_i <- alpha_i + repair_delta_i
```

where `alpha_i` is that observer's one scalar calibration parameter.

The repair must not mutate:

- `L_t`;
- `M`;
- another observer;
- another task dimension;
- the source event/action history.

Core boundary:

```text
OBSERVATIONAL_REPAIR != OBJECT_REPAIR
```

## Same-observer mirror rule remains mandatory

Each point observer compares live and mirror through the same local frame/task contract.

```text
O_i(L_t) vs O_i(M)
```

Changing an observer calibration changes the derived observation only. It does not change the source live/mirror states.

## Observer-field output

Do not collapse the field to one scalar by default.

Preserve a per-observer record:

```text
{
  observerId,
  sourcePointId,
  sourceDimension,
  task,
  calibration,
  liveValue,
  mirrorValue,
  residual,
  repairedResidual,
  operatorVersion
}
```

Global summaries are derived views and must retain links to the underlying observer records.

## Reconstruction question

The observer field creates a bounded inverse problem:

```text
Phi(X) = { O_i(X) }
```

A later experiment may test whether `Phi(X1) = Phi(X2)` implies `X1 = X2` for a declared finite object family.

Experiment 0 must not assume injectivity or unique 4D reconstruction. Ambiguity is retained as a result.

## Mesh refinement

Observer density is versioned and deterministic.

A later convergence test may compare:

```text
N1 < N2 < N3 < ...
```

and ask whether a deformation/observer signature survives refinement.

Experiment 0 needs at least two deterministic fixture densities for tests, but the UI may expose one default density.

Boundary:

```text
FEATURE_AT_ONE_MESH != CONTINUUM_INVARIANT
```

## Experience/replay integration

Saved experiences must preserve enough observer-field metadata to reconstruct the field:

- observer-field schema/version;
- deterministic sample density/seed or exact observer ids;
- task-assignment version;
- per-observer calibration values if changed;
- source live/mirror event identity;
- operator version.

Replay reconstructs the same observer field before applying saved observational repairs.

Reframe may change the displayed aggregation/view while leaving the preserved observer records/source event unchanged.

## Accessibility / play

The player does not need to inspect every point observer manually.

Default UI may show:

- the object/shell visualization;
- a sparse sample of observer markers;
- a task filter;
- one selected observer's local report;
- a text summary of observer counts, task distribution, and largest residuals.

Keyboard navigation must allow selecting observer/task without precise pointer input.

## Testing additions

Experiment 0 must add tests for:

1. every sampled point receives exactly one observer;
2. every observer receives exactly one task;
3. task assignment is deterministic;
4. task classes repeat across distinct locations for control coverage;
5. one-DOF repair changes only the assigned calibration scalar;
6. observational repair does not mutate live/mirror/source event;
7. same observer/frame is used for live and mirror measurement;
8. observer-field replay reconstructs identical observer ids/tasks/calibrations;
9. two mesh densities are deterministic;
10. no finite mesh is labeled a complete continuum;
11. aggregate summaries retain source observer ids;
12. unresolved reconstruction ambiguity is preserved rather than forced to equality.

## Claim ceiling

This observer field is an experimental representation and measurement architecture.

It does not establish:

- biological perception rules for hypothetical 4D organisms;
- physical fourth-dimensional vision;
- unique reconstruction of arbitrary 4D objects;
- a physical deformation of space;
- a Hodge-cycle or open-problem result.

It gives us a reproducible way to ask what many locally bounded observers can distinguish under controlled one-degree transformations.
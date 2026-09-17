# Parameterized Decision Field Core — implementation profile

This file specializes the canonical federation specification in `redogit/redogit/DECISION_FIELD_CORE_2026-09-17.md` for executable operator research.

## Type

```text
DecisionField<X,O,D,R,F,E,G,U>
```

- `X`: possibilities / conditions
- `O`: observer, obligation, task or goal context
- `D`: consequentially distinct quotient/classes
- `R`: typed relations
- `F`: admitted operators
- `E`: evidence/provenance/uncertainty
- `G`: desired result / acceptance condition
- `U`: unresolved remainder

## Operator contract

Every operator must expose:

```text
name
precondition(field)
apply(field) -> field | branch-set | result
preserves
may_mutate
cost
certificate
failure
lift/reconstruction map
```

No operator may silently change the target obligation.

## Core execution loop

```text
function Solve(field):
    field = Normalize(field)

    while true:
        if GoalSatisfied(field):
            return Result(field)

        if CertifiedImpossible(field):
            return ImpossibleCertificate(field)

        actions = GenerateOperators(field)
        actions = [a for a in actions if a.precondition(field)]

        probes = [Probe(field, a) for a in actions]
        best = SelectByCertifiedGainCost(probes)

        if best.has_exact_progress:
            field = Apply(best)
            field = PropagateAllConsequences(field)
            field = Learn(field)
            field = RotateLearnedRelations(field)
            field = RepairToFixedPoint(field)
            continue

        # Exact completeness fallback.
        branches = ExactBranch(field)
        child_results = [Solve(RepairToFixedPoint(c)) for c in branches]
        return CombineExact(child_results)
```

## Relation to existing bounded operator lab

The previous finite NAND/XOR and signed-heading experiments remain calibration fixtures. They do not become universal laws. They now instantiate the same interface:

```text
Boolean/NAND fixture:
  X = finite Boolean functions/program states
  R = behavior equality, NAND composition, cost
  F = compose NAND, enumerate, verify
  G = requested truth table / bounded minimum gate witness

4D signed-heading fixture:
  X = {-1,0,+1}^4 \ {0}
  R = support/sign/symmetry relations
  F = normalize, orbit/group, compare
  G = bounded heading/orbit result
```

## GYRO-DEAN specialization

```text
X = student/cohort candidates and exact residual states
R = exclusions, capacities, implication/cover/frame/algebra relations
F = filter, q-core, cover rotation, LP, dual-frame, SAT, SQL-factor,
    certified Macaulay/MPCA, branch, learn, reconstruct, verify
G = four distinct size-q cohorts with zero violations
```

The solver remains exact because branch-and-reduce is the final fallback. The current research question is whether the polynomial carriers can be proved to dissipate every hard core in polynomial total cost. That remains OPEN.

## Quantum specialization boundary

A quantum measurement process can instantiate the structural interface:

```text
X = density operator + measurement context
R = quantum operator/tensor relations
F = allowed physical evolution / quantum instrument
G = observed outcome and conditioned state
```

But:

```text
SHARED_DECISION_FIELD_STRUCTURE != SHARED_PHYSICAL_MECHANISM
QUANTUM_COLLAPSE != CLASSICAL_BOOLEAN_BRANCHING
```

Quantum probabilities and state updates remain governed by quantum mechanics.

## Evidence rule

Operators are promoted from generator to admitted runtime only after task-local proof/test evidence.

```text
candidate -> exact definition -> counterprobe -> executable verifier
          -> evidence-qualified admission -> runtime
```

Failures stay in the ledger and may generate a new operator or carrier.

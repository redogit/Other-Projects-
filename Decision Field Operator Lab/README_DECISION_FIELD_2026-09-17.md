# Decision Field Operator Lab — Parameterized Core Update

This update generalizes the finite operator lab into a reusable **parameterized Decision Field** while preserving every earlier finite result as a calibration fixture rather than a universal law.

## New core

- [`DECISION_FIELD_CORE_2026-09-17.md`](DECISION_FIELD_CORE_2026-09-17.md) — parameterized field/operator contract.
- [`decision_field.py`](decision_field.py) — generic exact solver kernel with fixed-point normalization, typed operators, gravity score, memoization and exact fallback branching.
- [`test_decision_field.py`](test_decision_field.py) — executable contract tests.

Run:

```sh
cd "Decision Field Operator Lab"
python -m unittest -v test_decision_field.py
```

The generic kernel is intentionally domain-neutral. A domain supplies:

```text
possibilities
relations
evidence
observer/task/goal
normalization/learning
operators
terminal proof predicates
exact fallback branch
result combiner
```

## Parameterized form

```text
DF = (X, O, D, R, F, E, G, U)
```

with:

```text
one Decision Field
+ a set of typed functions that operate on it
+ evidence-qualified operator selection/composition
-> desired result or certified unresolved/impossible result
```

## Preserved calibration boundaries

Existing NAND/XOR, signed-heading and finite operator experiments remain bounded fixtures.

```text
FINITE_OPERATOR_RESULT != UNIVERSAL_DECISION_LAW
XOR_CALIBRATION != UNIVERSAL_BALANCE_LAW
SHARED_STRUCTURE != SHARED_DOMAIN_MECHANISM
```

The open P-vs-NP specialization is documented separately in:

`../P versus NP Repair Lab/GYRO_DEAN_DECISION_FIELD_2026-09-17.md`.

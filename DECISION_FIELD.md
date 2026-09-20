# Decision Field

Canonical cross-project specification:

- https://github.com/redogit/redogit/blob/main/DECISION_FIELD_CORE_2026-09-17.md
- https://github.com/redogit/redogit/blob/main/DECISION_FIELD_THREAD_SYNTHESIS_2026-09-17.md
- https://github.com/redogit/redogit/blob/main/decision-field-federation-v1.json

Local reference implementation:

- [`Decision Field Operator Lab/DECISION_FIELD_CORE_2026-09-17.md`](Decision%20Field%20Operator%20Lab/DECISION_FIELD_CORE_2026-09-17.md)
- [`Decision Field Operator Lab/decision_field.py`](Decision%20Field%20Operator%20Lab/decision_field.py)
- [`Decision Field Operator Lab/test_decision_field.py`](Decision%20Field%20Operator%20Lab/test_decision_field.py)
- [`Decision Field Operator Lab/decision-field.schema.json`](Decision%20Field%20Operator%20Lab/decision-field.schema.json)

Open-math specialization:

- [`P versus NP Repair Lab/GYRO_DEAN_DECISION_FIELD_2026-09-17.md`](P%20versus%20NP%20Repair%20Lab/GYRO_DEAN_DECISION_FIELD_2026-09-17.md)

Core parameterization:

```text
DF = (X, O, D, R, F, E, G, U)
```

and the working statement is:

> One Decision Field plus a typed set of functions that operate on it, preserve declared invariants/evidence boundaries, and transform it toward a desired bounded result.

Historical project files are not rewritten by this pointer.

```text
CONNECTED != MERGED
METHOD_TRANSFER != EVIDENCE_TRANSFER
SHARED_STRUCTURE != SHARED_MECHANISM
```


## RMAPL / Ω bounded reference runtime

The September 20 successor implements a bounded reference runtime in the local Decision Field Operator Lab. It is derived upward from native contracts and keeps explicit per-domain remainder and reconstruction/loss accounting.

Canonical local runtime and evidence:

- [RMAPL Ω successor design](docs/superpowers/specs/2026-09-20-rmapl-omega-conditional-repair-design.md)
- [RMAPL Ω domain collation](Decision%20Field%20Operator%20Lab/RMAPL_OMEGA_DOMAIN_COLLATION_2026-09-20.md)
- [RMAPL v0 grammar](Decision%20Field%20Operator%20Lab/RMAPL_V0_GRAMMAR.md)
- [Ω runtime](Decision%20Field%20Operator%20Lab/omega.py)
- [conditional RMAPL runtime](Decision%20Field%20Operator%20Lab/rmapl_runtime.py)
- [frozen bounded evidence](Decision%20Field%20Operator%20Lab/evidence/RMAPL_OMEGA_RESULTS.json)

Historical predecessor design remains preserved on branch `design/rmapl-omega-conditional-repair-20260918`; it is lineage, not rewritten history.

```text
DOMAIN_FIRST != UNIVERSAL_SCHEMA_FIRST
COMMON_STRUCTURE != COMPLETE_DOMAIN_SEMANTICS
OMEGA_VIEW != NATIVE_OBJECT
RMAPL_PROFILE != RMAL_CORE_FRONTEND
METHOD_TRANSFER != EVIDENCE_TRANSFER
MAXIMAL_WITHIN_DECLARED_SCOPE != GLOBAL_COMPLETENESS
```

The current RMAL cooperative implementation protocol remains separately authoritative for its own implemented handoff/cooperation syntax. This RMAPL runtime does not claim RMALC parser support or complete bidirectional structured-return runtime.

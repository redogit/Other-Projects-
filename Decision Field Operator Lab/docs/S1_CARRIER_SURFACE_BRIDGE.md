# S′ Carrier–Surface Executable Bridge

**Status:** bounded owner-local reference implementation  
**Owner:** `redogit/Other-Projects-` / Decision Field Operator Lab  
**Scientific authority:** unchanged

## Governing invariant

> **Object identity is invariant; coordinates are negotiable.**

This bridge makes the current-working S′ semantic model layer executable without replacing the native S′ Models Lab or treating working model definitions as owner-pinned implementations.

## One object, four Surfaces

The fixture `s1-semantic-object/v1` projects the same identified object onto four distinct carrier Surfaces:

1. **candidate-state** — `S -> S′`, where the candidate remains explicitly unadmitted;
2. **survivor** — retained counterexample/witness plus the next lawful cut;
3. **semantic-work-unit** — shared reconstruction object carrying obligations, invariants, decision state, candidate, survivor, schedule, provenance, claim ceiling, and remainder;
4. **multi-timescale** — the schedule contract `tau_s < tau_w < tau_T < tau_K`.

Each projection carries a full reconstruction sidecar. The visible Surface payload can therefore stay task-local without claiming it alone is sufficient to reconstruct the source.

## Two transport layers

The executable path is:

```text
S′ semantic object
  -> Carrier–Surface record
  -> RMAPL Omega v0
  -> Carrier–Surface record
  -> S′ semantic object
```

Ω remains a projection/interchange carrier:

```text
OMEGA_VIEW != NATIVE_OBJECT
METHOD_TRANSFER != EVIDENCE_TRANSFER
```

## Reconstruction and loss

A carrier with its declared reconstruction payload can round-trip the fixture exactly.

A deliberately sidecar-stripped carrier is classified `UNKNOWN`, not `ROTATION`.

A carrier whose protected object identity is changed is classified `SEMANTIC_DECAY`.

Therefore:

```text
PROJECTION_SUCCESS != RECONSTRUCTION_SUCCESS
ROTATION != MUTATION != SEMANTIC_DECAY
```

## One-degree repair

The reference repair surface currently authorizes only one schedule coordinate per repair candidate:

```text
schedule.tau_s
schedule.tau_w
schedule.tau_T
schedule.tau_K
```

The frozen counterexample sets `tau_w = 20` while `tau_T = 16`, producing the typed residual `schedule-order`.

The one-degree repair changes only:

```text
schedule.tau_w: 20 -> 4
```

and closes that residual. The repaired result remains a **candidate**:

```text
REPAIRED != ADMITTED
```

Object identity, subject state, obligations, invariant map, claim ceiling, provenance, and unresolved remainder are protected from this repair surface.

## Verification

Run:

```sh
python -m unittest discover -s "Decision Field Operator Lab" -p "test_*.py" -v
python "Decision Field Operator Lab/run_s1_carrier_surface_audit.py" --check
```

Frozen evidence: `evidence/S1_CARRIER_SURFACE_RESULTS.json`.

## Claim ceiling

This establishes bounded software behavior for one declared fixture, four carrier projections, one Ω transport path, negative reconstruction/tamper controls, and one schedule repair.

It does **not** establish:

- scientific validation of the S′ model family;
- general learning performance;
- equivalence of the four model semantics beyond the protected common kernel;
- an RMALC implementation of these models;
- automatic admission of a repaired candidate;
- evidence transfer between native S′ work, Conscience64, Ω, or other projects.

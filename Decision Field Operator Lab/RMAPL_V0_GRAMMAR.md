# RMAPL v0 Grammar

Status: bounded reference profile. This is **not** a claim that RMALC accepts RMAPL syntax.

```text
program       := "RMAPL 0" NL "PROGRAM " IDENT NL "LOAD " IDENT NL bound* block* "RUN" NL?
bound         := "BOUND " IDENT "=" JSON NL
block         := repair | fitter
repair        := "REPAIR " IDENT NL
                 "WHEN " STRING NL
                 "REQUIRES " JSON_ARRAY NL
                 "TARGETS " JSON_ARRAY NL
                 "PRESERVES " JSON_ARRAY NL
                 "MAY_MUTATE " JSON_ARRAY NL
                 "FORBIDS " JSON_ARRAY NL
                 "APPLY " IDENT NL
                 "EVIDENCE " JSON_ARRAY NL
                 "COST " JSON_NUMBER NL
                 "END" NL
fitter        := "FITTER " IDENT NL
                 "WHEN " STRING NL
                 "REQUIRES " JSON_ARRAY NL
                 "PRESERVES " JSON_ARRAY NL
                 "OBJECTIVES " JSON_OBJECT NL
                 "APPLY " IDENT NL
                 "EVIDENCE " JSON_ARRAY NL
                 "COST " JSON_NUMBER NL
                 "END" NL
```

Identifiers match `[A-Za-z_][A-Za-z0-9_.:-]*`.

JSON is strict finite JSON. `NaN`, `Infinity`, comments inside JSON, duplicate language fields, missing fields, reordered block fields, unknown top-level operations, duplicate block identifiers, duplicate bounds, negative cost, and content after `RUN` fail closed.

`WHEN` is an exact residual-kind string in v0. It is not an arbitrary expression language.

`OBJECTIVES` maps objective names to exactly `"max"` or `"min"`.

The parser produces immutable RMAPL IR records. Runtime operator semantics are supplied by an explicit registry; parsing a program does not admit, verify, or execute an operator.

```text
PARSE_PASS != OPERATOR_ADMISSION
RMAPL_PROFILE != RMAL_CORE_FRONTEND
```

## Parser contract repairs — 2026-09-20

**Finite numeric representation.** Decimal/exponent JSON numbers must decode to finite Python floats at every nesting depth. An exponent such as `1e309` is rejected rather than admitted as infinity. Ordinary floating-point rounding and underflow remain; this is not exact rational parsing. `COST` additionally requires a non-negative finite float, and an integer too large for that conversion raises a contextual `ValueError`.

**Unambiguous objects.** Duplicate decoded keys in any JSON object are rejected, including identical repeated values, nested objects, and escaped spellings of the same key. Different objects may use the same key. This is the RMAPL profile's fail-closed rule; it does not claim that every JSON decoder must reject duplicates. Malformed objective values produce an `OBJECTIVES` validation error instead of incidental container-hashing errors.

**Deeply immutable parsed bounds.** `parse_rmapl` freezes JSON objects in `Program.bounds` as read-only mappings and JSON arrays as tuples, recursively. Scalar types/values, object iteration order, array order, and empty-container distinctions survive. Callers needing mutable JSON containers must explicitly reconstruct dictionaries and lists; parsed bounds are not a mutable JSON working buffer. This guarantee concerns parsed output, not manually constructed `Program` instances.

**Instruction lines versus string data.** `NL` accepts LF, CRLF, or CR. U+0085, U+2028, and U+2029 inside JSON strings remain string data, not instruction separators. Escaped and literal representations of these characters decode equivalently. Existing blank-line and full-line-comment handling remains.

Regression witnesses: `test_rmapl_contract_gaps.py`. These parser repairs do not change Omega, the RMAPL execution engine, operator admission, scientific evidence, or RMALC validation status.

## Runtime bound resolution — 2026-09-20

`run_program` treats the initial Omega `resourceBounds` and parsed `Program.bounds` as independent constraints. For each of `maxCandidates` and `maxSteps`, every explicitly supplied value must be a positive integer (not a Boolean, float, string, null, or container). Both bound containers must be mappings. Invalid declarations fail before any registered operator executes; a valid value on the other side cannot hide them.

When both sides declare a limit, the effective value is their minimum. When only one side declares it, that value is used. The existing defaults (`maxCandidates=32`, `maxSteps=1`) apply only when neither side declares the respective limit. For example, an input `maxSteps=1` plus program `maxSteps=3` executes at most one scheduler step; a program `maxSteps=1` can likewise tighten an input `maxSteps=3`.

Effective limits remain visible in `result["generation"]`. Original input records and unrelated native bound metadata remain unchanged. To increase a previously supplied input limit intentionally, the caller must supply an appropriately revised input; a program override alone no longer widens it.

This repair concerns **initial limit composition**, not a new resource scheduler. Existing `maxCandidates` application remains per eligible-specification list for each current state in each step; it is not a run-wide operator-call quota. Bounds are resolved at call entry, not dynamically re-resolved from generated candidates. Registered operators still require an external sandbox/controller for wall-clock, memory, or other process-level limits. No scientific or fresh RMALC conformance claim follows.

Regression witnesses: `test_rmapl_runtime_bounds.py`. Runtime admission, branch/cycle handling, Omega schema, parser, stress harness, and pre-existing tests are unchanged by this repair.

**Audited evidence successor.** The unchanged stress harness supplies an input candidate cap of 4 and a program cap of 8 in its 1,024 runtime fixtures. Correct composition changes the reported effective cap from 8 to 4, requiring a new runtime-family digest and overall report digest. `test_runtime_bounds_evidence_transition.py` checks the actual harness observations against the exact preserved predecessor in `evidence/history/RMAPL_OMEGA_STRESS_PRE_RUNTIME_BOUNDS_20260920.json`: restoring just that effective cap reconstructs the old runtime digest. All other report fields, four other family digests, checks, case counts, failures, and claim ceilings remain identical. Existing full byte-for-byte replay remains required; this is an explained successor, not relaxed verification.

## Repair mutation scope — 2026-09-20

`REPAIR MAY_MUTATE` is an admission allowlist over semantic Omega paths, not merely descriptive metadata. After canonical Omega validation, a repair that would otherwise pass `PRESERVES` and `FORBIDS` must restrict every semantic change to a declared path or its descendants. For example, `MAY_MUTATE ["state.x"]` permits changing `state.x`, but not `state.guard`, `state.xyz`, or `residuals`. An empty allowlist permits no semantic changes. Removing residuals requires an explicit `residuals` permission; out-of-scope removal cannot create an admitted `SUCCESS`.

Paths use the existing dot-separated mapping-key convention and semantic aliases (`identity` -> `nativeIdentity`, `claim-ceiling` -> `claimCeiling`). Matching uses path segments, not string prefixes. A literal key containing a dot does not impersonate a nested path. The v0 notation has no key escaping or array-index addressing; such structures require an appropriate enclosing-subtree permission. Arrays, additions, deletions, and container/type replacements are atomic at their affected path. Permission for `state.guard.value` does not permit deleting or replacing `state.guard` itself.

Canonical JSON comparison preserves type distinctions such as `false` versus `0` while ignoring irrelevant object-key ordering. The derived `id` and `construction` mirrors are excluded from the semantic change walk only after `validate_omega` checks their consistency; naming either in the allowlist does not authorize changes elsewhere.

`PRESERVES` and `FORBIDS` still win over mutation permission and retain their existing rejection diagnostics. An additional scope violation is returned as an unadmitted `MUTATION`, retained in the branch record, with sorted changed paths in `inspection.mutated` and a failed `may_mutate` gate. Existing successful audit shapes remain unchanged. `FITTER` has no `MAY_MUTATE` clause in v0 and retains its existing contract.

This checks candidate admission after an operator returns. It does not sandbox arbitrary Python, prove the truth of operator-supplied metrics/reconstruction claims, or establish global evidence authority. Callers must still declare appropriate protected fields and use independent validation. No schema, parser, scheduling, initial bound-resolution, fresh RMALC, or scientific claim is changed. Regression witnesses: `test_rmapl_mutation_scope.py`.

## FITTER authority floor — 2026-09-20

`FITTER` retains its v0 syntax and its existing flexible fitting contract over ordinary mutable state, subject to declared `PRESERVES`. It still has no `MAY_MUTATE` clause.

After canonical Omega validation, every fitter additionally inherits a fixed runtime authority floor. A fitter candidate is rejected as an unadmitted `MUTATION` if it changes any of:

```text
nativeIdentity
sourceRefs
evidence
claimCeiling
provenance
```

The authority floor is not an evidence verifier: it preserves the input carrier's authority-bearing identity, source references, evidence records, claim ceiling, and provenance against fitter rewrite. It does not establish the truth of those records.

Existing `PRESERVES` diagnostics retain precedence. If a candidate already violates an explicitly declared preserved path, that existing rejection record is kept rather than replaced with a redundant `fitter_authority` diagnostic. Otherwise, an authority-floor violation is retained in `inspection.mutated` and reported by a failed `fitter_authority` gate with the changed paths.

Ordinary state fitting remains permitted when declared preserves survive. This change adds no FITTER syntax, no Omega schema field, no new evidence class, and no change to REPAIR `MAY_MUTATE` behavior.

```text
FITTER != AUTHORITY_REWRITER
FIT != EVIDENCE_PROMOTION
METHOD_TRANSFER != EVIDENCE_TRANSFER
```

This is an admission check after a registered Python operator returns. It is not a sandbox and does not prove operator-supplied metrics, reconstruction claims, or scientific validity. Regression witnesses: `test_rmapl_fitter_authority_floor.py`.


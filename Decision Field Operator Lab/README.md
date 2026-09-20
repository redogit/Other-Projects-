# Decision Field Operator Lab

A bounded, exact calibration lab for the **state-space / decision-field / operator-builder** work.

This project connects:

- primitive construction;
- Boolean operators and their duals/opposites;
- permutation and symmetry;
- iterable/enumerable/calculable search contracts;
- the signed consequential-change projection `-S' / 0 / +S'`;
- the 4D Compass orientation grammar;
- `PROPOSE → VERIFY → ADMIT_UNIQUE → PROMOTE`.

It does **not** treat XOR as a universal decision law. XOR is one discriminator inside a larger operator field.

## Computational contract

### Mathematical question

Can a small audited builder:

1. enumerate the complete binary Boolean operator space;
2. construct every Boolean behavior from a tiny primitive basis;
3. organize a finite signed 4D orientation space by certified symmetry;
4. keep consequential gain, consequential loss, representation-only motion and unresolved status separate;
5. compare operators under declared obligations without pretending that one operator is universally optimal?

### Exact surrogate implemented here

- Boolean domain: all functions `f : {0,1}² → {0,1}`.
- Complete behavior count: `2^(2^2) = 16`.
- Primitive construction basis: binary `NAND`.
- Construction model: straight-line/DAG-style reuse of previously available Boolean masks.
- Search bound: at most 5 NAND gates, deterministic semantic-state deduplication, no beam truncation in the published audit.
- Compass domain: every nonzero vector in `{-1,0,+1}^4`.
- Compass symmetry: coordinate permutations plus independent sign changes.
- Consequential-change score: independent `gain`, `loss`, `magnitude`, signed projection, representation-only flag, cost and unresolved flag.
- Arithmetic: exact integers, finite sets and truth masks; no floating approximation is used except the derived signed ratio.

### What a pass establishes

For this declared finite calibration only:

- all 16 binary Boolean functions are enumerated;
- each has a verified NAND construction within the stated bound;
- the 80 signed 4D headings are enumerated;
- a separate signed-permutation construction reproduces the same four support-size orbits;
- the admission protocol detects semantic duplicates before promotion;
- the supplied balance fixtures select different operators when the obligations change.

### What it does **not** establish

- no universal novelty detector;
- no theorem that XOR is "balance";
- no claim that every decision field is finite or decidable;
- no claim that enumeration implies decision;
- no P-versus-NP consequence;
- no transfer of the NAND gate costs here into another project's cost model;
- no claim that `S'` is observer-independent or obligation-independent.

## Exact finite results

The committed concise audit currently records:

- **16 / 16** binary Boolean operators;
- every behavior NAND-constructible within **≤ 5** gates in the declared straight-line model;
- `XOR` shortest witnessed construction: **4** NAND gates;
- `XNOR` shortest witnessed construction: **5** NAND gates;
- negative control: `XNOR` is **not** reached within the exhaustive 4-gate search;
- **80** nonzero signed 4D headings;
- support-size split: **8 + 24 + 32 + 16**;
- the same split is independently reconstructed as four signed-permutation orbits.

The Compass orbit templates are therefore:

```text
(1,0,0,0)
(1,1,0,0)
(1,1,1,0)
(1,1,1,1)
```

Signs and coordinate permutations generate the 80 oriented headings.

## Operator field

The exact Boolean registry includes all 16 truth tables, including:

`AND`, `NAND`, `OR`, `NOR`, `XOR`, `XNOR`, both implications, both directional differences, both negations, projections, and constants.

The wider registry also names structural operators such as:

`PRESERVE`, `PERMUTE`, `CANONICALIZE`, `SPLIT`, `MERGE`, `REPAIR`, `MUX`, `FILTER`, `THRESHOLD_K`, and `EXACTLY_K`.

Those wider operators are deliberately marked **incomparable on the binary Boolean fixtures** unless an explicit domain bridge is provided. Registration is not the same as pretending they share one truth-table semantics.

## Signed S′ discipline

For declared consequential distinctions:

```text
gain  = after - before
loss  = before - after
magnitude = gain + loss
signed = (gain - loss) / magnitude
```

when `magnitude > 0`.

This deliberately preserves the case:

```text
gain = 1
loss = 1
signed = 0
magnitude = 2
```

as **real change whose signed projection cancels**, not "nothing happened."

A pure permutation or representation change receives `representation_only=true` only when the protected distinction set is unchanged.

## Balance experiment

The same 16 Boolean operators are ranked under the same cost-vector form:

```text
(violations, NAND-gates, operator-id)
```

but with different declared obligations.

The finite fixtures intentionally produce different winners:

- exclusive change → `XOR`;
- agreement → `XNOR`;
- intersection → `AND`;
- coverage → `OR`;
- endpoint-preserving symmetric partial obligation → `AND`.

So the experiment rejects the shortcut:

```text
XOR == universal balance
```

while retaining XOR as a useful separator when the obligation really is exclusivity/difference.

No unweighted sum of unlike costs is called a total optimum.

## Algorithmic-builder protocol

The admission machine is:

```text
PROPOSE
  ↓
VERIFY
  ↓
ADMIT_UNIQUE
  ↓
PROMOTE
```

A verified composite can become a reusable builder primitive while its derivation remains available. A second construction with the same semantic key is retained as `DUPLICATE` rather than manufactured into novelty.

## GSFL successor profiles

The canonical six-operator loop above remains unchanged. Additional GSFL behavior is carried through removable successor profiles rather than silently redefining canonical operators.

### GSFL v0.1 operator projection

`gsfl-operator-profile.json` projects the completed GSFL v0.1 operations into reusable operators while preserving separate semantic, evidence, and authority effects.

### GSFL v0.1 bidirectional macro cycle

`gsfl-bidirectional-macro-profile.json` composes those verified operators into five macros:

```text
SEEK → QUESTION → REFRAME → BUILD → RETURN_INWARD
```

with exact expansion:

```text
SEEK          = OBSERVE → GROUND → TRACE_TOOL
QUESTION      = DISTINGUISH → COMPARE → AUDIT_CONFOUNDS
REFRAME       = MAP → ROTATE → RELATE → PRESERVE
BUILD         = COMPOSE → REPAIR → VERIFY → SELECT → HANDOFF
RETURN_INWARD = RECONSTRUCT → TEACH_BACK → DERIVE_COROLLARIES
                 → COMPARE → PRESERVE → FIT
```

The macro profile uses 19 unique existing operators across 21 invocations. It is a composition layer, not a primitive-authority layer. See [`GSFL_BIDIRECTIONAL_MACRO_CYCLE.md`](GSFL_BIDIRECTIONAL_MACRO_CYCLE.md).

```text
MACRO != NEW_PRIMITIVE
OUTWARD_EXPLORATION != VALIDATION
INWARD_COHERENCE != PROOF
BUILD != TRUTH
```

## RMAPL / Ω bounded reference runtime

This lab also contains the bounded **RMAPL 0** conditional repair/fitting profile and the strict `rmapl-omega/v0` interchange/inspection envelope.

The implementation is deliberately additive:

- `omega.py` — strict deterministic Ω normalization, identity, inspection records, and reconstruction/loss reports;
- `omega.schema.json` — closed Draft 2020-12 interchange schema;
- `omega_adapters.py` — native Decision Field, S'1, GSFL, image-surface, dimensional-ladder, Suggest, and Hodge projections with explicit native remainder;
- `rmapl.py` and `RMAPL_V0_GRAMMAR.md` — exact small RMAPL v0 parser/IR;
- `rmapl_runtime.py` — bounded conditional repair/fitting execution, typed evidence admission, consequential-equivalence quotienting, Pareto branch preservation, Knowledge Decay accounting, side-effect guards, and cycle/resource stop certificates;
- `run_rmapl_omega_audit.py` + `evidence/RMAPL_OMEGA_RESULTS.json` — deterministic frozen bounded evidence.

Native schemas remain authoritative. Ω is a projection, not a replacement. RMAPL 0 is a reference profile and is **not** claimed as an RMALC frontend.

```text
OMEGA_VIEW != NATIVE_OBJECT
RMAPL_PROFILE != RMAL_CORE_FRONTEND
METHOD_TRANSFER != EVIDENCE_TRANSFER
SOFTWARE_VERIFICATION != SCIENTIFIC_VALIDATION
MAXIMAL_WITHIN_DECLARED_SCOPE != GLOBAL_COMPLETENESS
```

Design and derivation records:

- [September 20 successor design](../docs/superpowers/specs/2026-09-20-rmapl-omega-conditional-repair-design.md)
- [September 20 domain collation](RMAPL_OMEGA_DOMAIN_COLLATION_2026-09-20.md)
- [implementation plan](../docs/superpowers/plans/2026-09-20-rmapl-omega-reference-runtime.md)

## Run

Python 3.10+; standard library only.

```sh
python -m unittest discover -s "Decision Field Operator Lab" -p "test_*.py" -v
python "Decision Field Operator Lab/run_audit.py" --check
python "Decision Field Operator Lab/run_gsfl_operator_audit.py" --check
python "Decision Field Operator Lab/run_gsfl_bidirectional_audit.py" --check
python "Decision Field Operator Lab/run_contextual_multicarrier_audit.py" --check
python "Decision Field Operator Lab/run_rmapl_omega_audit.py" --check
```

`run_audit.py --check` reruns the exact finite operator-field contract. The GSFL audit commands independently reproduce the operator-projection and bidirectional-macro successor evidence.

## Evidence

- `evidence/RESULTS.json` — concise committed finite operator-field results.
- `evidence/GSFL_OPERATOR_RESULTS.json` — GSFL operator-projection evidence.
- `evidence/GSFL_BIDIRECTIONAL_RESULTS.json` — bidirectional macro-cycle evidence.
- generated `AUDIT.json` — full bounded experiment state.
- generated `OPERATOR_TABLE.json` — full operator periodic table, NAND derivation certificates, algebraic properties, Compass census, enumeration contracts and balance fixtures.

The committed results and generated artifacts are reproducible from source. They are evidence about their declared bounded computations, not universal mathematical or semantic proof.

# Hodge Span Lab

An exact rational linear-algebra aid for the existing
[Conscience64 Hodge research spine](https://github.com/redogit/conscience64/tree/b6da9fcc8e56019b27656f7e244a8b1f763ed15c/research/hodge).
It helps ask: which supplied target directions are outside the span of supplied cycle-class vectors?
It does not compute those classes from equations or establish that any input is a Hodge class.

## Use it

Python 3.10+, standard library only. From the repository root:

```sh
python "Hodge Span Lab/span.py" "Hodge Span Lab/example.json"
python -m unittest discover -s "Hodge Span Lab" -p 'test_*.py' -v
```

Copy the synthetic example locally. Declare a common ordered basis and supply rows
as exact integers or rational strings such as `"1/3"`. JSON floating-point numbers
are rejected. Maximum ambient dimension is 32; each list permits 64 vectors;
input scalars are limited to 256 bits. The CLI rejects files exceeding 1 MB.
These bounds limit input, not a guarantee of runtime or intermediate expression size.

The example has three candidate rows but rank two. One target direction is missing.
The returned covector pairs to zero with every supplied cycle vector but not with
the missing target. Anyone can check those dot products without trusting the elimination routine.
Zero/duplicate vectors are allowed and do not increase rank. An empty target list
is vacuously contained and is not evidence of geometric completeness.

## Before a result can support geometry

Keep a separate record of the variety and smooth/projective hypotheses, codimension,
coefficient field, basis source, construction and algebraicity of each cycle,
class-map calculation, completeness of the rational Hodge target, and exact source revisions.
This tool does not authenticate any of those records. It diagnoses supplied coordinates only.
Target rank is not inferred from a complex Hodge number or a Hodge diamond.

The calculation is over the rationals, not an integral lattice. For example,
`[1,0]` belongs to the rational span of `[2,0]`; that does not show integral generation.
Containment of supplied targets does not show that the targets exhaust the true Hodge space.
A missing supplied direction means a construction task remains **conditional on valid input geometry**;
it is not a counterexample to the Hodge conjecture.

## Research use

1. Start with authenticated exact classes from a calibration or selected family.
2. Inspect repeated/dependent candidate rows before generating more cycles.
3. Check returned separating covectors independently.
4. Try a construction aimed at a detected direction; retain the failed attempt too.
5. Rerun with new input and preserve both input hashes. A changed basis or target invalidates stale comparisons.

This makes the public spine's `CYCLE_COUNT != CYCLE_CLASS_RANK` distinction executable.
It does not settle auxiliary-factor cancellation, an intersection calculation,
join nonvanishing or any theorem dependency. No P-versus-NP reduction is proposed.

## Verification

Tests include all 81 two-by-two integer matrices with entries in {-1,0,1}, using an
independent determinant rank oracle, and direct dot-product checks for every returned
separator in that family. Additional cases cover duplicates, exact fractions, empty
spans and malformed inputs. This is bounded software verification, not independent
geometric replication. Recorded execution is under `evidence/hodge-span-001/`.

Original code and prose are new assistant-authored research tooling at the user's request.
Linked research retains its own provenance and license. No third-party dataset or private archive is bundled.

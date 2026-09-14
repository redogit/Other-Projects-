# D2v1 canonical-byte repair — September 14, 2026

The update-first review found a byte-preservation defect in the D2 successor at commit `614f6823a6bbe6cbff64470ed53df646252a1f09`. The decoder extracted seven instruction bits but did not reject bit 7. Consequently `443280` was accepted with rank 3, then returned as `443200` after the float-carrier round-trip. Behavior was preserved while source bytes were silently changed.

The parser now rejects a set reserved high bit before decoding an instruction. All word-consuming APIs use this parser. Canonical D2 words, rank order, the legal population and behavior tables are unchanged. This narrows implementation acceptance to the language actually counted by the producer. It does not create a new language version or silently normalize malformed input.

The separate terminal strings remain legal. Register references still must point to an input or earlier instruction. Canonical instructions remain ASCII bytes, including control characters; callers should continue using hex or exact binary transport when text display is unsuitable.

## Evidence

`evidence/canonical-boundary-001` records:

- Every one- and two-byte raw payload: 65,792 cases, exactly 597 admitted. The independent grammar oracle uses no production parser or ranker.
- 31,455 canonical rank checks: every rank through three operations, 2,048 seeded longer samples and ten depth-boundary ranks. The count includes repeated boundary/sample occurrences.
- 10,260 high-bit mutation occurrences, rejected at every tested word API.
- Independent scalar Boolean evaluation, byte/float inverses, mutable bytearray input, malformed headers/lengths and invalid rank/float types.

`evidence/canonical-census-001` records two complete native enumerations, each evaluating 205,315,794 nonterminal programs, plus three terminal words. The two 16-primitive sweeps also match exactly. All 256 shortest witnesses retain their exact behavior, byte and float round-trips; all four published repair records match `SUMMARY.json`. Only XOR and XNOR close all 256 behaviors by five operations in the declared single-added-primitive sweep.

Both bounded manifests validated against their declared inputs and outputs. Python was 3.12.14; the compiler was g++ 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04), using `-O3 -std=c++17`. The census contract records the compiler requirement; this note supplies the observed compiler version. Concurrent execution of the boundary and census runs was used only for correctness checks, not timing comparisons.

The historical summary, selector and both native producers remain byte-identical. The audit accepts `--output` and refuses to overwrite existing scientific result files, preserving prior runs. Fresh native binaries live only in a temporary directory. No global cache is added.

## Why the repair is sufficient for this defect

Each canonical instruction has one operation bit and two three-bit operand fields, so every meaningful bit is contained in positions 0 through 6. Rejecting bit 7 removes the previously ignored freedom. At depth j, the two operand indexes range from 0 through j+2; the rank digit therefore ranges from 0 through `2*(j+3)^2-1`. Mixed-radix division uniquely recovers those digits and fields. Terminals occupy their separate first three ranks. The fixed binary64 exponent and exact fraction payload preserve each allowed rank. Thus the high-bit alias cannot survive the repaired shared parser.

This is a local code/proof review and independent-oracle implementation by the same assistant, not external peer review or formal verification. Exhaustive empirical coverage of all byte strings through five instructions is not claimed. The native census covers canonical programs; the adversarial raw-byte sweep has the smaller explicit bound above.

D2 adds XOR to the instruction basis. Its compactness result must not be substituted into NAND-only circuit budgets in the P-versus-NP line. It establishes no general SAT algorithm or natural-language meaning.

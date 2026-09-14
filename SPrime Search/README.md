# SPrime Search — complete bounded candidate census

September 13, 2026 · Pass 03 · Implementation home: `redogit/Other-Projects-/SPrime Search/`.

**The search now joins UTF-8 transport, candidate generation, complete behavior checking, exact counts and reversible witness indexing.** It does not identify arbitrary human ideas or recover a universal definition of the user's S′.

## What was actually searched

Use the inherited grammar `E ::= x | y | z | N E E`, where N means NAND and each token is one UTF-8 byte. There is no whitespace, hidden dictionary, implicit constant or shared subexpression. A behavior is the output on all eight three-input assignments, with row 000 at bit 0 and row 111 at bit 7.

The old eight-byte working set contains **471 programs and 38 behaviors**. The search now counts every program through a **1,024-byte capacity**, classified by length and all 256 behaviors. Full binary trees have odd length, so the longest admitted expression is 1,023 bytes; there are no exactly 1,024-byte expressions in this grammar. No padding was silently added.

There are approximately **4.618287934596 × 10^547 programs** through this bound. The exact integer has 548 decimal digits. This is a symbolic census using an exact recurrence, not that many individually executed programs. All complete UTF-8 strings through eight bytes number 168,570,276,329,617,409; strings outside the declared program grammar are retained as outside its semantics, not labeled meaningless.

## A complete S′ repair search

For this assistant-constructed fixture, start from S=x. Protect its four outputs where z=0. Require output 1 at input 001 and output 0 at input 111. The output on rows 011 and 101 is deliberately unspecified. This is a small executable repair problem, not a theory of human choice.

A candidate f passes exactly when:

```text
((f XOR 0xf0) AND 0x55) == 0
((f XOR 0x02) AND 0x82) == 0
```

Exactly four behavior tables satisfy those conditions:

| Table | Shortest program | Bytes | Changed rows from x |
|---|---|---:|---:|
| 0x52 | `NNxNzzNzNzNNzxNzy` | 17 | 3 |
| 0x5a | `NNxNzzNzNxx` | 11 | 4 |
| 0x72 | `NNxNzyNzNyy` | 11 | 2 |
| 0x7a | `NNxNzyNzNyx` | 11 | 3 |

There is **no passing candidate within eight bytes**. At an eleven-byte capacity, there are **320 passing programs representing three behaviors**. At seventeen bytes, all four passing behaviors are available. Through 1,024 bytes, approximately **2.179183158737 × 10^545 expression witnesses** pass. Exact counts, all four alternatives and the differing unprotected outputs are written by the audit.

The 0x5a program is x XOR z. The 0x72 program selects x when z=0 and NOT y when z=1. Both meet the six specified row obligations, while differing elsewhere. A minimum-output-change policy prefers 0x72, but that is an explicit optimization criterion, not proof that its unspecified decisions are the intended ones.

These behaviors are new to the declared eight-byte working set, not historically new Boolean functions. At the full bound, 218 behaviors were not expressible in that starting set. A longer representation makes additional behaviors available; it does not establish scientific or cultural novelty.

## Why whole families can be checked quickly

Let C[k,f] be the number of expressions with k NAND nodes and behavior f. At k=0 the three terminals each have count one. A larger expression has a unique root NAND, an ordered left subtree and an ordered right subtree. Therefore:

```text
C[k,f] = sum C[i,a] * C[k-1-i,b]
         over i=0..k-1 and NAND(a,b)=f.
```

Every summand represents a disjoint group of program strings, so induction proves the exact count. The sum over f independently equals `Catalan(k)*3^(k+1)`.

The implementation accelerates the inner AND convolution using an upper-set zeta transform, pointwise multiplication and Möbius inversion, followed by complementing the output index for NAND. This is an application of established algebraic counting/weighted parsing ideas, not a claimed new general algorithm. The code checks its result against direct untransformed convolution on small lengths and against explicitly enumerated programs.

The counting pass took 6.27 and 6.31 seconds in the two final local runs; the full audits took 7.04 and 7.07 seconds. These are shared-container observations, not a speed guarantee or a claim to have executed 10^547 programs.

The smallest representative of every behavior was evaluated on all eight rows. All 65,536 NAND combinations satisfy the closure and shortest-cost inequalities. Structural induction covers all finite expression depths on this fixed input domain. Counts of expression multiplicities beyond 1,024 bytes were not evaluated; closure does not falsely make that infinite set finite.

## Get a witness directly

The witness ordering is by node count, left subtree size, left and right behavior, then child ranks. It is not byte-lexicographic order. Each parsed tree is unique; the disjoint product counts support exact rank/unrank without listing every preceding string.

```sh
python "SPrime Search/search.py" --max-bytes 8
python "SPrime Search/search.py" --max-bytes 1024
python "SPrime Search/search.py" --max-bytes 1024 --table 0x5a --length 1023 --rank 0
python "SPrime Search/run_audit.py" --out sprime-results
```

Python 3.10+ standard library. The audit uses the unchanged sibling `S1024 Compression Lab/sections1024.py` and checks its pinned hash before import. No network requests, external packages or execution of generated Python are required.

The audit produces all 471 short programs as CSV; complete 256-behavior counts and shortest witnesses; every accepted behavior; long witness samples; syntax partitions; alliteration counts; verification summaries and an execution manifest. Large counts are decimal strings in JSON to prevent downstream floating-point rounding.

## Float64 and the remaining byte space

Every one of the 471 short programs was recovered from one positive finite float64 carrier using a length-then-UTF-8-rank mapping. This is a bit-level codec, not `float(large_integer)` and not semantic geometry. All chosen long witnesses reconstructed through the inherited multiword SP1024-1 carrier. A full raw 1,024-byte payload uses 133 float64 carriers before metadata; that expands storage, not compresses it.

The full 1,024-byte syntax universe is partitioned into complete UTF-8, extendable incomplete prefixes, and invalid UTF-8. Complete text outside the NAND grammar remains outside this interpreter's semantics. The next byte length 1,025 is counted syntactically but its program multiplicities remain explicitly beyond this pass. Arbitrarily long sequences require additional carrier storage or explicit dependencies; one word does not gain unlimited capacity.

## Alliteration, tested separately

Alliteration concerns sounds, not merely matching initial letters. A separate hand-specified English fixture labels the onsets of eight words: sun, sea, city, cat, car, phone, fun and fish. Sequences use single spaces and at least two words. Of **45 sequences fitting eight bytes, 15 have a shared onset**. The recurrence also counts all sequences and shared-onset sequences through 1,024 bytes within this tiny lexicon.

`city cat` has matching first letters but fails the shared-onset test. `city sun` and `phone fun` pass despite different first letters. Unknown vocabulary returns UNKNOWN. No dictionary corpus was imported, no audio was analyzed, and this is not a multilingual or stress-aware prosody model. Sound similarity does not make a statement true or a behavior equivalent.

## Evidence, failures and boundaries

Two final runs produced identical copies of all nine scientific output files. Checks include:

- 34,491 individually enumerated programs through eleven bytes and 16 length slices compared to direct convolution;
- all 471 short-program rank/float inverses, all 256 shortest witnesses and all 65,536 shortest-cost composition checks;
- 24 selected longer rank/unrank, scalar-evaluation and multiword-transport cases through 1,023 bytes;
- 65,793 short raw-byte cases checked against Python strict decoding with a separate extendability oracle;
- 512 Catalan count identities, variable-renaming count symmetry, alliteration small-domain enumeration and 12 rejected invalid requests.

The first two audit attempts exceeded the process time budget in long-witness retrieval. Retrieval was optimized by using exact reachable supports and approaching a rank from the nearer end, without changing the ordering or counted set. A subsequent test exposed an oracle issue: Python's non-final incremental decoder can buffer `ed a0`, even though it has no valid UTF-8 completion. The independent oracle was corrected to test strict completion/extendability. The inherited UTF-8 implementation was not changed. The source snapshots and failure ledger are retained in the downloadable run package.

A passing audit verifies these finite implementation paths. The recurrence, inverse and closure arguments provide their stated mathematical coverage. There is no proof assistant, independent human replication, general semantic test, corpus training or claim of discovering a law of human cognition. No cultural record, prior codec, existing project or workflow is overwritten.

## Sources and interpretation

- [RFC 3629, sections 3–4](https://www.rfc-editor.org/rfc/rfc3629.html): strict UTF-8 syntax and invalid encodings. Stored text is not normalized.
- [Goodman, Semiring Parsing (1999)](https://aclanthology.org/J99-4004/): established weighted-parsing framework; bibliographic calibration rather than an external proof of this implementation.
- [Björklund et al., The fast intersection transform (2008)](https://arxiv.org/abs/0809.2489): related subset-transform counting literature; not a claim that this code reproduces the paper's full algorithm.
- [Cambridge Dictionary, alliteration](https://dictionary.cambridge.org/dictionary/english/alliteration): sound-based definition. The eight-word onset assignment is an assistant-authored fixture.

The user's instinct remains an open research direction. This pass supplies an actual candidate family, exact admission rule, counted accepted set, counterexamples and indexed witnesses. Extending the semantic domain requires a new interpreter and verifier; it must not silently inherit the old PASS.

## Pass 04: compact reuse and context

[Compact reuse and context](compact/README.md) tests a distinct versioned NAND register language: 412,909,356 words through eight UTF-8 bytes, with explicit unresolved outputs and fallback to the parent tree grammar. The results above remain scoped to the original grammar.

## September 14: semantic query compilation repair

[The compact query-cache repair](compact/CACHE_REPAIR_2026-09-14.md) validates
semantic states before cache access and adds bounded retention and explicit
release. The four accepted behaviors and D1 bounds remain unchanged. The parent
verifier now defaults to a current versioned record; the historical record is
preserved, including its obsolete README hash.

# Pass 04 — compact reuse and context

**Executed bounded result, September 13, 2026.** This additive pass keeps the old
NAND tree grammar unchanged and introduces a different, version-tagged language.
It separates a representation limit from missing task information.

## The result

The original eight-byte tree language has no passing repair. The new `D1`
register language has **767,096 passing words representing three of the four
previously accepted behaviors**, all within eight UTF-8 bytes. The two-byte
`D1` language/version tag is included. The external decoder, runtime registers,
input values and codec-version agreement are additional dependencies.

| Behavior | Old shortest tree bytes / gates | D1 bytes / gates | D1 word as hexadecimal |
|---|---:|---:|---|
| `0x52` | 17 / 8 | Not reachable within six gates | No D1 word in this bound |
| `0x5a` | 11 / 5 | **6 / 4** | `443122233345` |
| `0x72` | 11 / 5 | **6 / 4** | `44312a233345` |
| `0x7a` | 11 / 5 | **7 / 5** | `4431202a24334e` |

The first compact word is `D1"#3E`, computing x XOR z. Its four gates are:

```text
r3 = NAND(x, z)
r4 = NAND(x, r3)
r5 = NAND(z, r3)
output = NAND(r4, r5)
```

The result r3 is computed once and reused. Under the same compact instruction
packing but without computed-value sharing, this behavior needs the five gates
of a minimum tree, hence seven bytes including the tag. Compact packing accounts
for one part of the reduction; sharing removes another gate/byte. For `0x7a`,
five gates remain necessary, so its byte saving is packing, not reduced gate count.
Neither effect is claimed as a new general compiler technique.

Every reported shortest D1 witness was decoded from a positive finite float64,
independently evaluated on all eight input rows, expanded back into the old tree
grammar, and checked against the same truth table. A float is an opaque carrier,
not a number on which arbitrary arithmetic preserves the program.

## A full, genuinely executed census

The C++ traversal individually evaluates **412,909,356 legal D1 words**: three
terminal-only words and every ordered one-through-six-gate program. Counts include
dead gates, repeated inputs and redundant spellings; they are not independent
ideas or evidence. There are **192 reachable behaviors** and **64 not reachable
in this D1 bound**. Of the 192, 154 were not expressible in the previous eight-byte
tree grammar. No new Boolean truth table or historical invention is claimed.

At gate j there are exactly `(3+j)^2` ordered register choices. The independent
population formula is:

```text
3 + sum(k=1..6) product(j=0..k-1) (3+j)^2 = 412,909,356
```

Every choice is visited once. Histograms are recorded per gate count, so a witness
is shortest in D1 only when all smaller gate counts are exhausted. The last
register is always the output. Instructions refer only backwards, which proves
termination and prevents cyclic or missing references. This does not establish
minimum size among all programming languages, encodings or gate libraries.

D1 programs consist of `D1` followed by 1..6 bytes; byte j is
`0x20 + 8*a + b`, with `0 <= a,b < 3+j`. Terminal-only words are `D1x`, `D1y`,
and `D1z`. Exact spaces and punctuation are significant. No normalization or
whitespace stripping is allowed. Every byte is ASCII and therefore valid UTF-8
under [RFC 3629](https://www.rfc-editor.org/rfc/rfc3629.html).

The native census took 4.30 and 4.27 seconds on this shared container. The complete
runs, including compilation and independent checks, took 9.49 and 9.30 seconds.
These are local measurements, not a performance guarantee. The scientific output
files were identical across both final runs.

## The context that still matters

Keep the original obligations: baseline x, preserve rows 000/010/100/110,
require 1 on 001 and 0 on 111. Nothing specifies outputs on 011 and 101.
An exact query planner asks for those two outputs. These are requests to the
actual specification owner or an authorized oracle; the program does not invent
the answers. The regression cases below use explicitly synthetic answers.

| Required output on 011 | Required output on 101 | Required behavior | Route |
|---:|---:|---|---|
| 0 | 0 | `0x52` | Keep the known 17-byte parent tree; outside current D1 bound |
| 0 | 1 | `0x72` | 6-byte D1 word |
| 1 | 0 | `0x5a` | 6-byte D1 word |
| 1 | 1 | `0x7a` | 7-byte D1 word |

Both bits are independently unspecified, so two binary questions are necessary
and sufficient to identify the exact complete behavior among all four. No answer
leaves the candidate set unchanged. A contradictory answer is rejected rather
than relaxing a protected output. A previously accepted candidate is rechecked
when context changes. Noisy answers or arbitrary real-world contexts need a
separate model. This planner seeks exact behavior identification, not the
weaker task of selecting any action acceptable across multiple worlds.

All **6,561 partial binary-output specifications** were checked: an unspecified
row can be 0 or 1, and unit-cost queries require exactly the number of independent
unknown rows to recover the full truth table. These are exhaustive checks of this
small model, not evidence that every natural-language requirement is known.

## More encodings do not constitute more evidence

Among the same three behaviors:

| Behavior | D1 encodings through eight bytes |
|---|---:|
| `0x5a` | 302,672 |
| `0x72` | 346,312 |
| `0x7a` | 118,112 |

The predecessor tree census through 1,024 bytes gave `0x7a` the most encodings;
D1 gives `0x72` the most. The budgets/encodings differ, and no equal-budget speed
comparison is implied. The unchanged semantic alternatives demonstrate why raw
encoding multiplicity is not an invariant measure of evidential support.
An encoding-based prior may be used only with a separately justified model;
repeated encodings are not independent confirmations of unspecified outputs.

## Run and inspect

Python 3.10+ and g++ with C++17 support are required for the complete census.
No downloads, API keys or new package installations are performed by the audit.
The parent `search.py` and its pinned `S1024` dependency are checked before use.

```sh
python "SPrime Search/compact/compact.py" --hex 443122233345
python "SPrime Search/compact/compact.py" --rank 412909355
python "SPrime Search/compact/run_audit.py" --out compact-results
python "SPrime Search/compact/verify.py"
```

`rank` and `unrank` cover all D1 words in gate-count/ordered-reference order;
they do not sort words by truth, usefulness or natural-language meaning.
The audit regenerates complete histograms and all 192 shortest witnesses.
Selected evidence is committed under `evidence/`; the downloadable run package
retains both full result sets, the native census, manifests and development log.

## Verification and remaining limits

An independent Python scalar-Boolean traversal checks all **133,356 words through
four gates** against the native histograms and checks their rank inverses. All
192 shortest witnesses pass eight scalar evaluations, tree translation and
float round trips. There are 527 additional boundary/seeded rank/float cases;
14 malformed requests are rejected. The inherited 256 tree witnesses and all
65,536 composition-cost inequalities are rechecked.

A mutable-cache counterprobe found that returning the cached query-plan dictionary
allowed a caller to corrupt a later answer. The public API now returns an isolated
copy, and the final runs check mutation isolation. The correction and preliminary
compiler warnings are preserved in the development log, not hidden.

This pass does not rerun the 1.4-million-entry alliteration branch, add cultural
records, solve arbitrary UTF-8 semantics, certify production security, or establish
a theory of human cognition. None of the original projects or workflows is modified.
The parser/compiler/codec implementations and source metadata are shared external
costs; six payload bytes do not contain their complete environment.

## Source and prior-art calibration

- Parent: `SPrime Search/` at commit `e5c727c29f5714a9dce6507de0470f90844094b9`.
- [RFC 3629](https://www.rfc-editor.org/rfc/rfc3629.html): ASCII/UTF-8 compatibility.
- [ABC documentation](https://www-cad.eecs.berkeley.edu/~alanmi/abc/abc.htm): DAG-aware
  rewriting and sharing in established logic-synthesis practice. Documentation
  reviewed; ABC was not executed and no superiority comparison was performed.
- [Tate et al., Equality Saturation, POPL 2009](https://www.cs.cornell.edu/~lerner/papers/popl09.html):
  author abstract reviewed as prior-art calibration. This is not an implementation
  of that paper or a claim of new equality-saturation machinery.

The useful next question is not simply whether more strings can be generated.
It is which limitation belongs to the representation, which belongs to the allowed
operations, and which belongs to missing evidence about the intended result.

## September 14 repair: validated, bounded query compilation

[Semantic query cache repair](CACHE_REPAIR_2026-09-14.md) fixes a warm-cache type
validation bypass, retains at most 128 compiled plans, and adds explicit
`clear_query_cache()` and `query_cache_info()` operations. Existing D1 semantics
and scientific outputs are preserved. New versioned publication records keep
the historical evidence intact while restoring current verification.

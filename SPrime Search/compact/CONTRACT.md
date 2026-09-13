# Pass 04 — compact reuse and unresolved context

Date: 2026-09-13. Recorded before execution of this pass. Author: assisting AI;
this is not independent preregistration. Parent repository commit:
`e5c727c29f5714a9dce6507de0470f90844094b9`.

## Motivation and exact question
The previous no-repair result at eight bytes is relative to the tree grammar,
not to every possible interpreter. Test whether an explicitly versioned compact
straight-line NAND language can represent the four unchanged repair behaviors
inside eight UTF-8 bytes. Separately determine the unobserved specification
bits required to select among those behaviors. No claim about arbitrary natural
language, cultural truth, human cognition, global code-size optimality or a new
logic-synthesis algorithm.

## D1 wire format (a NEW language)
- Exactly ASCII `D1` followed by one through six instruction bytes.
- Instruction byte = 0x20 + 8*a + b, with 0 <= a,b < 3+gate_index.
- Registers 0,1,2 initially contain x,y,z. Gate j appends NAND(a,b) at 3+j.
- Last register is the output. Previously computed registers may be reused.
- Alternative terminal-only words: D1x, D1y, D1z. No empty program.
- No implicit constants, whitespace stripping, reordering, numeric float
  arithmetic, code execution with eval/exec, cycles or external memory.
- At most six gates; all instruction bytes 0x20..0x5f are single-byte UTF-8.
  Length is 3..8 bytes including the two-byte format/version tag.
- Ordered operands, repeated inputs, dead gates and distinct instruction words
  are counted separately. All are distinct encodings; not independent evidence.

This has 3 terminal words plus sum(k=1..6) product(i=0..k-1)(3+i)^2
candidate words. Enumerate every word in native C++; count all 256 complete truth
tables at every gate count. Preserve a shortest word for each reachable behavior.
Truth-table bit i is output on x,y,z = binary digits of i (000..111).

## Frozen repair and information boundary
Keep parent S=x, protected rows mask 0x55, required mask 0x82, required bits 0x02.
All acceptable tables must satisfy both masks. Unspecified rows 011 and 101 must
not be filled by majority of encodings, shortest cost, or an invented oracle.
Test all four completions; test unavailable answers, malformed labels and a
contradiction with protected rows. Query answers below are synthetic test inputs,
not user preferences. A new context version must invalidate a cached acceptance
when a new protected observation disagrees.

## Controls and reproducibility
1. Product-of-choices count oracle at each gate count.
2. Independent Python enumeration through four gates (all output histograms),
   plus independent row-at-a-time interpretation of shortest witnesses.
3. Recheck parent shortest tree certificate and all 65,536 composition inequalities.
4. Rank/unrank for arbitrary words in D1 and inherited one-float UTF-8 carrier.
5. Compare compact packing and computed-value reuse separately: original tree
   gate count versus compact DAG gate count. Decoder/source overhead remains an
   external shared dependency and must not be hidden in payload savings.
6. Invalid version, invalid character, forward reference, truncation, excessive
   length, malformed queries, float out-of-range, and contradictory-context tests.
7. Two executions; deterministic scientific result files must match exactly.
   Record timings separately. Runs are bounded to 45 seconds per process.
8. Preserve original source bytes and old claims; add new files only, with a new
   pointer in the parent README. No archive, old transport, workflow, production
   database or other repository is changed.

## Why enumeration certifies the bound
At step j the only legal ordered choices are [0,3+j)^2. A recursive traversal of
all such choices visits every legal word once. Its last register provides the
complete eight-row behavior. A breadth in gate-count witness is shortest in D1
if all smaller gate counts have been exhausted. A missing behavior is outside
the tested D1 bound, not uncomputable. Neither the repeated truth-table results
nor more surface encodings create historical or semantic novelty.

## Sources / provenance
RFC 3629, section 3: ASCII strings are UTF-8. ABC official documentation describes
DAG-aware logic sharing; equality saturation (Tate et al., POPL 2009) is further
prior-art calibration. These establish background, not correctness of new code.
The inherited UTF-8 codec and previous shortest-witness ledger are retained with
byte hashes. Source and output hashes are recorded in a complete run manifest.

# SPrime Search — Pass 03 contract

2026-09-13. This contract is recorded before the final audit. An exploratory timing/count prototype preceded it; this is not independent preregistration.

## Subject, request and completed output
The user asks for all S′ candidates over UTF-8 in a float64, onward through combinations, iterations and possibly alliteration. The assistant implements a specific search contract, not a recovered universal definition of the user's S′.

S′ here is a finite program in `E ::= x | y | z | N E E`, with NAND N. Each token is one UTF-8 byte, without whitespace, constants or shared nodes. Inputs are all eight (x,y,z) assignments, ordered 000 through 111. Bit i is the output on row i. There are 256 complete behaviors. The searched byte capacity is 1..1,024, so full binary trees occupy odd lengths through 1,023. Source words, float bits, behavior signatures, known behaviors and accepted repairs are distinct.

## Mathematical task
Count every program by length and complete behavior; return every accepted behavior and directly index any of its expression witnesses. Counts use arbitrary-precision integers. Counted multiplicities are ordered expression trees, not graph circuits, cultural ideas or proven original discoveries.

Baseline x has table 0xf0. Protect rows 000,010,100,110 (mask 0x55). Require output 1 at 001 and 0 at 111 (required mask 0x82, required values 0x02). Accept f iff `(f XOR baseline)&protected == 0` and `(f XOR required_values)&required == 0`. The comparison working set is all behaviors expressible within eight bytes. These requirements are an assistant-constructed regression/repair fixture, not empirical human preferences.

Two controls: forcing a protected row to change must yield zero solutions; apparent equivalence on one row must not justify a full behavioral merge. Return a witness on all eight rows. Count byte length separately from changed outputs. Identity renamings under equal-cost token aliases must not alter semantic counts.

## Algorithm and evidence
Use a behavior-indexed inside recurrence. An accelerated implementation uses upper-set zeta transforms to turn AND convolution into pointwise multiplication; invert, then complement the output index for NAND. Independently check small results by direct 256-by-256 convolutions and literal expression enumeration. Every length's summed count must equal Catalan(k)*3^(k+1), k NAND nodes. Byte strings outside this grammar remain OUTSIDE_DECLARED_SEMANTICS, not meaningless or invalid UTF-8.

Rank order: node count, left-node count, left behavior, right behavior, left witness rank, right witness rank. Not byte-lexicographic order. Unique parse and disjoint products give exact rank/unrank. Randomly selected long-rank checks remain samples, separate from the induction argument. Closest/shortest means minimum serialized tree byte length only, not minimum circuit, general edit distance or cognitive effort.

Reuse the exact inherited SP1024-1 dependency only after its SHA-256 matches. Separately demonstrate one-float transport for complete UTF-8 strings <=8 bytes using length-then-byte-lexical ranks and positive normal binary64 patterns. Larger witnesses use multiword transport. Finite float storage is not numeric arithmetic. Count framing, decoder and external lengths as dependencies.

## Alliteration
Use an explicitly hand-specified eight-word English test lexicon with one initial-phoneme label each. Count sequences of at least two words with a single ASCII space and equal initial-phoneme labels through 1,024 bytes. Verify small cases by literal enumeration. This is a narrow initial-consonant convention, not multilingual, stress-aware, dialect-complete or a test of meaning. Unknown words return UNKNOWN, not false. Do not mistake alliteration for iteration or evidence of truth.

## Remainder and limits
Partition syntax, interpretable programs, accepted/rejected repairs and out-of-bound lengths. A grammar closure proof covers all finite expression depths on this input domain; multiplicity counts are evaluated only through the bound. No claims about arbitrary natural-language semantics, universal truth, the completeness of human cultural records, or global historical novelty. No corpus training, private Library export or runtime-authority change. Preserve prior project files and append this work only in redogit/Other-Projects-.

## Execution
Final audit: two deterministic runs, positive and negative controls, exact output comparison, recorded source hashes/versions, process timeout 45 seconds per invocation. Sampling seed 20260913. Timing is local shared-host observation, not a performance guarantee. A package-local verifier is not official Mathbox validation or a proof assistant. Failures stay in the run ledger.

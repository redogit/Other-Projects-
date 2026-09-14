# Pass 06 result — widen the decision field, not the opcode set

## Result

D2 already closes the three-input / one-output behavior space, so Pass 06 adds **no opcode**. It introduces canonical Algebraic Normal Form coordinates and widens the field to four/five inputs, multiple outputs, and temporal state transitions.

- All **65,536** four-input one-output Boolean functions were exhaustively transformed, inverted, evaluated on all 16 rows, text-encoded and float-round-tripped: **1,048,576 row evaluations**.
- Every five-input one-output behavior has a unique 32-bit ANF coordinate, so all **2^32** functions have an exact eight-byte ASCII form `A5......`; 10,003 boundary/deterministic cases plus all 32 basis vectors were individually checked.
- Every four-input two-output map has a 32-bit product coordinate: **2^32** maps. `B4......` uses eight ASCII bytes.
- A two-bit state plus two-bit context with two-bit next-state output is the same 32-bit map space: **2^32 deterministic transition systems**. `T4......` uses eight ASCII bytes.

## Constructed temporal repair

Baseline: next state equals current state in every context. Context 0 is protected. Six context/state outcomes are required to change. Ten of sixteen transition entries are fixed, six are free, yielding exactly `4^6 = 4096` admissible systems.

The complete repair cube was enumerated. The unique minimum entry-Hamming repair changes exactly those six required entries. Its canonical identifier is:

```text
T4BmLMXk
rank = 0x662cc5e4
output ANF masks = 0x78f2, 0x92c4
```

The context requirements form a conflict graph requiring three distinct context classes. Therefore at least **two binary context bits** are needed. One bit cannot preserve all declared distinctions.

## Exact boundary

A complete deterministic map with `n` binary inputs and `m` binary outputs needs `m * 2^n` behavior bits.

Within the chosen two-byte tag plus base64 source encoding:

- 5 inputs × 1 output = 32 bits: fits exactly in eight ASCII/UTF-8 bytes.
- 4 inputs × 2 outputs = 32 bits: fits exactly in eight bytes.
- 4 inputs × 3 outputs = 48 bits: does not fit in eight tagged ASCII bytes, although it fits the 48-bit payload of the tagged normal-float carrier.
- 6 inputs × 1 output = 64 bits: exceeds both this tagged float payload and the eight-byte tagged text envelope.

These are carrier/representation boundaries, not impossibility results for larger carriers, external dictionaries, or other protocols.

## Evidence boundary

ANF is a canonical behavior coordinate, not a shortest circuit and not worst-case compression. Algebraic degree is an exact GF(2) interaction-order property, not a universal measure of conceptual complexity. The temporal repair and context obligations are synthetic. No cultural meaning, human preference, cognition law, or training data is inferred.

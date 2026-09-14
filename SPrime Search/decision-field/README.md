# Decision Field Pass 06 — canonical coordinates, multiple outputs, and time

This successor does **not** add another D2 opcode. D2 already spans every three-input / one-output Boolean behavior. Pass 06 widens the decision field and changes representation deliberately: executable gate programs remain one layer; canonical behavior coordinates become another.

## Exact field sizes
For `n` binary inputs and `m` binary outputs, a complete deterministic decision map needs exactly `m * 2^n` behavior bits and there are `2^(m*2^n)` possible maps.

- Four inputs, one output: **65,536** maps, 16 behavior bits.
- Five inputs, one output: **4,294,967,296** maps, 32 behavior bits.
- Four inputs, two outputs: **4,294,967,296** maps, 32 behavior bits.
- Two state bits + two context bits -> two next-state bits: the same **2^32** map space, now interpreted temporally.

The code uses Algebraic Normal Form (ANF) coordinates. Every Boolean function has a unique multilinear polynomial over GF(2); the subset Möbius transform converts truth-table bits to ANF coefficients and is inverted by the same transform. This is canonical behavior representation, **not compression in the information-theoretic worst case** and not a shortest circuit.

## What was exhaustively checked
Every one of the **65,536 four-input / one-output functions** was transformed to ANF, transformed back, evaluated on all 16 rows, encoded as canonical ASCII, decoded, and round-tripped through a tagged positive-normal float carrier: **1,048,576 row evaluations**.

The exact algebraic-degree distribution is:

| degree | functions |
|---:|---:|
| zero function (`-1`) | 1 |
| 0 | 1 |
| 1 | 30 |
| 2 | 2,016 |
| 3 | 30,720 |
| 4 | 32,768 |

The degree gives a precise GF(2) interaction-order distinction. It is not a universal measure of conceptual complexity.

## Five inputs still fit in eight UTF-8 bytes
`A5` stores a 32-bit ANF coefficient mask as six URL-safe base64 symbols after the two-byte ASCII tag. Every canonical source word is therefore exactly **8 ASCII/UTF-8 bytes**. The field contains `2^32` functions; they were not individually enumerated. Coverage follows from the 32-bit coefficient bijection. The implementation checks all 32 basis vectors plus 10,003 deterministic boundary/sample cases.

The next sharp source-envelope boundary is six inputs: a one-output truth table has **64 bits**, so a two-character tag plus base64 payload cannot fit in eight ASCII bytes.

## Two outputs and temporal decisions
`B4` represents two four-input output functions as a single 32-bit rank and uses eight ASCII bytes. `T4` gives the same 32 bits temporal meaning:

```text
row = context * 4 + current_state
payload[row] = two-bit next_state
```

Thus a two-bit state plus two-bit context decision field contains **2^32 deterministic transition systems**. The product/bijection is exact; 10,005 selected 32-bit systems were individually round-tripped. All **256 local maps of four states** were exhaustively classified by fixed points and cycle profile.

## A harder context repair
The synthetic baseline keeps state unchanged in every context. Context 0 is protected as idle. Six other context/state entries are required to change. Ten of sixteen transition entries are then fixed and six remain free, so exactly

`4^6 = 4096`

transition systems satisfy the obligations. The complete free-entry repair cube was also enumerated. The unique minimum entry-Hamming repair changes exactly the six forced entries; all other entries remain at baseline.

The partial requirements generate a context-conflict graph. Four named contexts cannot all be collapsed: the minimum valid coloring has **three context classes**, requiring at least **two binary context bits**. One context bit is insufficient for these obligations. This is a constructed finite witness of “complexify the context only when collapsed situations demand different actions.” It is not a claim about human cognition.

The minimum repair is itself a canonical `T4` word and a tagged one-float carrier. Its two output bits also have exact four-input ANF masks, linking temporal behavior back to the canonical static field.

## Carrier boundary
The tagged float carrier fixes exponent 1023 and reserves four fraction bits for a format tag, leaving **48 protocol payload bits**. The current tags use only the declared canonical width of their object: A4 uses 16 bits and A5/B4/T4 use 32. High unused payload bits are rejected at both encoding and decoding. This is an opaque carrier protocol; numerical arithmetic on the float is not assigned meaning.

With the two-byte self-describing ASCII tag, the eight-byte envelope has six base64 payload characters = 36 encoded bits. Therefore the exact self-describing frontier includes:

- 5 inputs x 1 output (32 bits) — fits;
- 4 inputs x 2 outputs (32 bits) — fits;
- 4 inputs x 3 outputs (48 bits) — **does not** fit as eight-byte tagged text, although a separately defined 48-bit tagged-float format could fit that payload;
- 6 inputs x 1 output (64 bits) — fits neither the current tagged-float payload nor the eight-byte tagged text envelope.

Those are representation capacity boundaries, not impossibility results for larger carriers or shared external context.

## Hardening after adversarial review

A harder pass found and repaired two boundary defects without changing the original scientific `SUMMARY.json`: noncanonical high float payloads were accepted under narrower format tags, and several public helpers did not consistently reject out-of-domain ranks/input counts. See `HARDENING_2026-09-14.md` and `evidence/HARDENING_VERIFICATION.json`.

The temporal stress tests also found a consequential distinction: **fixed-context stability does not imply stability under a changing context schedule**. Among 64 four-state maps that each converge to a unique fixed-point attractor, 1,008 of the 4,096 ordered pairs create a 2- or 3-cycle in their two-step composition. Thus `transition system + context schedule`, not a local map alone, is the subject for switched temporal claims.

For six-input / one-output behavior, the complete field contains exactly `2^64` functions while binary64 has only `2^64 - 2^53` finite bit patterns. Therefore one finite binary64 value cannot injectively carry the entire A6 field. A canonical exact fallback splits on the highest input and carries two A5 objects; this was checked on all 64 basis functions plus 100,000 deterministic 64-bit samples and 20,000 paired textual-codec cases.

## Run

```sh
cd "SPrime Search/decision-field"
python audit.py
python stress_audit.py
```

Python standard library only. The evidence files are generated locally. No cultural corpus, natural-language interpretation, training data, or user preference is inferred.

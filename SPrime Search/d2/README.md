# D2v1 — minimal complexification

Pass 05, September 13, 2026. This is a bounded three-input Boolean synthesis result, not a universal theory of ideas.

D1 used compact NAND-only register programs and left 64 of 256 behaviors unreachable in its compact bound. D2v1 adds exactly one opcode bit: each instruction selects either NAND or XOR and carries two three-bit register indexes. The format is the ASCII header `D2` plus one to five one-byte instructions; `D2x`, `D2y`, and `D2z` are terminal words.

A complete native census individually evaluated 205,315,794 nonterminal words (205,315,797 legal words including the terminals). Every one of the 256 three-input Boolean truth tables appears. The shortest-depth distribution is 3 terminal behaviors, then 10 / 23 / 65 / 122 / 33 behaviors at one through five gates. Therefore every behavior has a D2v1 word of at most seven bytes.

All four previously admitted repair behaviors now fit: `0x52` uses four instructions / six bytes, `0x5a` is one XOR instruction / three bytes, and `0x72` and `0x7a` each use four instructions / six bytes. The outputs at rows `011` and `101` still determine which repair is required; encoding multiplicity does not answer those context questions.

All 16 possible binary Boolean primitives were tested as the single second primitive alongside NAND through five operations. Exactly XOR and XNOR reached all 256 behaviors. XOR is used in D2v1 because it directly implements an admitted repair and has a simple parity interpretation. This is an engineering choice, not a novelty claim.

D2v1 has only 205,315,797 legal words, so its exact language rank fits well below the 52 fraction bits of a binary64 normal value. The implementation maps a D2 rank into a positive normal float64 bit pattern with exponent 1023. All 256 shortest witnesses were checked through `word -> rank -> float bits -> rank -> word`. The float is an opaque carrier; arithmetic on it is not semantic computation.

Run:

```sh
python "SPrime Search/d2/audit.py"
python "SPrime Search/d2/d2.py" --hex 4432000a1c55
```

The audit compiles the C++17 census and primitive sweep, runs the census twice, checks exact program populations, verifies all 256 shortest witnesses independently row-by-row, checks rank/float inverses, and retains the four repair witnesses. `SUMMARY.json` records the bounded result; `selector.json` records the two-context-bit mapping.

The methodological result is narrower: **complexify only enough to remove a witnessed obstruction**. One opcode bit closes the compact three-input behavior gap. Nothing here establishes natural-language meaning, historical novelty, human cognition, or the correct real-world obligations.

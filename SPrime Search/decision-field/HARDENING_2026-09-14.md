# Pass 06 hardening — September 14, 2026

This pass attacks the canonical decision-field implementation rather than adding new opcodes. The original scientific `SUMMARY.json` remains byte-identical after the repairs.

## Defects found and repaired

1. **Tagged float canonicality.** `A4`, `A5`, `B4`, and `T4` tags previously accepted payload bits beyond their declared 16/32-bit object widths. Forged high payloads could therefore enter the tagged carrier domain. Encode and decode now enforce format-specific widths. Existing valid carriers are unchanged.
2. **Domain validation.** `get_next()` accepted negative and over-width transition integers, while `algebraic_degree`, `eval_anf`, and `truth_from_anf` had inconsistent input-domain validation. Those public paths now reject out-of-domain values before interpretation.

## Hard checks

Two deterministic stress runs produced identical JSON. The suite includes the complete 262,144-word lexical payload space for `A4`; 65,814 independently evaluated ANF coefficient cases through four inputs plus 20,032 five-input checks; the full A4 coefficient-weight distribution; 39,338 valid and 808 malformed/tag-boundary float cases; all 65,536 four-state map compositions; 200,000 associativity checks; 750 independently brute-forced repair cubes; 5,000 context-partition cases; and 100,064 six-input split checks plus 20,000 paired-`A5` text reconstructions.

## Temporal counterexample: schedule is part of the subject

A fixed-context cycle census is insufficient when context changes over time. There are 125 local four-state maps whose cycles are all fixed points. Among their 15,625 ordered pairs, 2,700 two-step compositions create a 2-cycle and 264 create a 3-cycle.

A stronger counterexample uses local maps that each have exactly one fixed-point attractor. There are 64 such maps. Of their 4,096 ordered pairs, **960** compositions create a 2-cycle and **48** create a 3-cycle. One witness is:

```text
A = [1,1,0,0]   # every state eventually reaches fixed point 1
B = [0,2,0,0]   # every state eventually reaches fixed point 0
B after A = [2,2,0,0]   # 0 <-> 2 in the two-step composition
```

Thus the correct temporal subject is `transition system + context schedule`. Local context maps remain useful evidence but do not alone certify switched trajectories. Order is broadly consequential: 62,712 of 65,536 ordered map pairs do not commute.

## Six-input finite-float boundary

There are exactly `2^64` six-input, one-output Boolean functions. Binary64 has `2^64 - 2^53` **finite** bit patterns because exponent-all-ones patterns are non-finite. Therefore no injective encoding can place the entire A6 behavior space into one finite binary64 value, even if every finite sign/exponent/fraction pattern is used. The shortfall is exactly `2^53` patterns.

If binary64 is abandoned as a finite-float carrier and all raw 64-bit patterns—including NaNs and infinities—are treated as opaque storage, the cardinalities match, but that is a different carrier contract.

A canonical exact finite-float fallback requires no new Boolean operator: split on the highest input into two 5-input truth tables and carry two `A5` objects. All 64 basis functions plus 100,000 deterministic 64-bit samples were reconstructed exactly; 20,000 were additionally passed through both textual `A5` codecs.

This is a representation lower bound and a temporal-context correction, not a theory of human idea formation.

# Pass 06 contract

Goal: widen the previously closed three-input/one-output decision field without adding arbitrary opcodes. Keep executable programs, canonical behavior identity, context, and temporal transition semantics separate.

Declared representations:
- `A4` / `A5`: one-output Algebraic Normal Form coordinates for four/five binary inputs;
- `B4`: two four-input output functions packed as one 32-bit rank;
- `T4`: two-bit state + two-bit context -> two-bit next-state transition table, also 32 bits.

Coverage:
- exhaustively verify all 65,536 four-input one-output functions and all 16 input rows;
- for five-input functions, rely on the exact 32-bit ANF bijection, checking all basis vectors and deterministic samples rather than claiming 2^32 individual visits;
- for two-output and temporal 32-bit fields, rely on product/bijection arguments plus deterministic samples;
- exhaustively classify all 256 local four-state maps;
- exhaustively enumerate the 4,096-member constructed repair cube and verify the unique minimum repair;
- find the minimum context-class coloring under the declared partial obligations.

Cost/complexity distinctions:
- ANF coefficient count and algebraic degree are representation properties, not human cognitive complexity;
- canonical behavior coordinates are not shortest circuits;
- carrier bits, source bytes, execution cost, context acquisition cost, and semantic authority remain separate.

Carrier:
- fixed exponent 1023, four fraction bits for a versioned format tag, 48 fraction bits for exact payload;
- numerical operations on the float are not meaningful;
- eight-byte ASCII self-description uses a two-character format tag and six base64-url payload symbols.

Non-claims:
- no universal model of idea formation;
- no human/cultural semantics inferred;
- no proof that larger fields are impossible with larger or externally assisted carriers;
- no compression claim from changing between equally sized truth/ANF coordinates;
- no claim that sampled 2^32 members were individually exhausted.

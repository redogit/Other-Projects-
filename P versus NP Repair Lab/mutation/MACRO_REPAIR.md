# Repair the dependency block together

## Exact class

F consists of exactly one nonempty positive clause C and any number of implications x_i → x_j. The baseline is all zero. Protected positions must remain zero. The cost is the number of bits changed to one. All variables and clauses are explicitly listed.

## Algorithm and argument

Compile implications into a directed graph. For each variable v in C, compute its forward-reachable set R(v), including v itself. Reject R(v) if it intersects a protected position. Among remaining distinct sets, choose one with minimum cardinality, breaking ties by unsigned assignment value. Count distinct minimum sets.

Each R(v) is a feasible model whenever it avoids protected positions: it makes C true and is closed under every implication. Conversely, any feasible model T contains some v in C and, by repeated implications, contains R(v). Thus |T| ≥ |R(v)|. At a global minimum equality must hold, and finite-set inclusion with equal size implies T=R(v). The algorithm therefore finds the exact minimum and counts all distinct minimizers. If no closure survives protection, no feasible model exists.

Graph construction and at most |C| traversals take O(|F| + |C|(n+m)) conventional graph operations, where m is the number of implication edges, before set serialization/tie comparison. Polynomial bit-mask serialization, distinct-set comparison and output storage do not change polynomiality. The implementation sorts adjacency sets for reproducible traversal; this adds polynomial sorting work. This is a direct reachability corollary for this restricted class, not a novelty or general SAT claim.

For the previously tested F_n (all pairwise implications plus one positive clause containing every variable), every reachable closure is the whole variable set. One dependency-block repair changes all n bits at once. It does not get trapped by the temporary conflict increase of single-bit moves. A protected zero anywhere correctly makes repair infeasible.

## Limits and next distinction

The implementation rejects formulas outside this class. An arbitrary baseline introduces a different objective; multiple positive clauses require simultaneously hitting several requirements. No polynomial extension to either is inferred here. The general exact layered solver remains available within its finite cap and reports resource exhaustion explicitly.

This gives the semantic-mutation line a useful next decision: discover a certified tractable relation structure before selecting a repair operator. One-bit conflict descent is only a heuristic; graph closure supplies an exact repair under the stated structure. Neither this special case nor its compiler settles the main P versus NP / Partial-Hard target.

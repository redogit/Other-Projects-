# Semantic query cache repair — September 14, 2026

The finite semantics and D1 language are unchanged. This repair makes invalid
input rejection independent of cache history and gives retained plans an
explicit limit and release operation.

## Reproduced fault

The previous public `query_plan` called a memoized function whose input checks
ran only on cache misses. Python treats `(False, True)`, `(0.0, 1.0)` and
`(0, 1)` as equal dictionary keys. Consequently, the malformed first two tuples
were rejected on a cold cache but accepted after the integer tuple was compiled.
`typed=True` on the decorator alone would not distinguish the contents of a tuple.

The public boundary now checks an exact tuple containing distinct, sorted,
exact integers in 0..255 before cache access. `refine` uses the same boundary;
validation no longer compiles a complete question tree just to filter candidates.
Unknown answers still preserve the candidate set; contradictory answers still fail.

## Compile, use and release

```python
import compact

tables = (82, 90, 114, 122)
plan = compact.query_plan(tables)  # Compile the exact question tree before use.
print(plan['row'], plan['questions'])
print(compact.query_cache_info())
compact.clear_query_cache()
```

Only 128 completed public plans are retained, with least-recently-used eviction.
One compilation uses a temporary memo for its own recursive subproblems and
clears it in a `finally` block. Each subproblem is the original candidate set
restricted by some output-row labels. There are at most `3**8 = 6,561` such
restrictions, since each of eight rows is unqueried, zero or one. This is a
fixed-domain bound, not a general polynomial-time synthesis result.

Returned plans are isolated copies. Clearing cached plans leaves caller-owned
copies usable; callers must also drop those copies to release their references.
Cache statistics count entries, hits and misses, not allocated bytes. No immediate
garbage collection or process-memory reduction is promised. Concurrent compilation
can add a new entry after a clear; this is a local synchronous utility, not a
global cancellation mechanism.

Planning includes input validation, candidate partitioning, minimax search and
copying the result. Repeated queries can reuse a finished plan; a cache miss pays
its construction cost. This is custom question-tree compilation, not native
machine-code compilation. No universal execution optimum is claimed.

## Checks and evidence

`test_cache_repair.py` contains six regression tests, including cold and warm
boolean/float rejection, malformed containers, bounded eviction, explicit clear,
copy isolation and refinement without unnecessary compilation. It also compares
the complete returned plan against a separate uncached scalar minimax oracle for
all 255 nonempty subsets of the eight tables 0..7, including the row tie break.

The existing full D1 audit was rerun twice. Each run individually enumerated all
412,909,356 legal words through six gates, checked 133,356 short words with the
scalar oracle, and checked all 6,561 partial specifications. The eight generated
scientific JSON outputs matched across runs. The six corresponding previously
committed scientific outputs also matched their historical bytes. Exact timings,
source hashes and limitations are in
[`evidence/CACHE_REPAIR_2026-09-14.json`](evidence/CACHE_REPAIR_2026-09-14.json).

```sh
python "SPrime Search/compact/test_cache_repair.py"
python "SPrime Search/compact/run_audit.py" --out compact-repair-results
python "SPrime Search/compact/verify.py"
python "SPrime Search/verify.py"
```

The package verifiers default to explicit versioned September 14 publication
records. Historical records remain byte-for-byte unchanged and can be selected
with `--record`. They describe historical bytes and can reject later files.
Before this repair, the parent verifier already rejected its README because the
compact-pass link had been added after the old hash was recorded. The new parent
record fixes that stale default without rewriting the old record. Verification
checks declared files, including missing or changed files; it does not reject
unlisted user files, authenticate authorship or establish mathematical truth.

## Research boundary

The four accepted truth tables still differ on unspecified rows 011 and 101.
Neither encoding multiplicity, shortest representation nor cache reuse supplies
the missing output obligations. Equality on currently observed rows cannot be
reused as equality on newly observed rows. When obligations change, refine the
admitted candidate set and compile its new plan.

With n Boolean inputs, a complete truth table has `2**n` rows and the possible
table space has `2**(2**n)` members. Speed on the present fixed set of 256 tables
does not provide a polynomial SAT algorithm or a resolution of P versus NP.
CNF-constrained assignment repair and minimum NAND representation have different
input contracts and must keep separate complexity claims.

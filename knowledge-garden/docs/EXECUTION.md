# Execution and recovery

September 14, 2026 · Knowledge Garden 1.1.0 · catalog 2026-09-14.1.

## Task-sized work

A working set combines selected catalog entries with a title and six explicit task fields: subject, motivator, request, obligation, surface and output definition. The Garden does not infer missing fields or execute their contents. The title is limited to 120 characters; each task field to 2,000 characters.

The [version 2 export schema](../working-set.schema.json) has its own `format_version`, separate from the catalog's `schema_version`. An export includes selected records, internal connections, capabilities and their source closure. Import also accepts the Garden's earlier proposal format. It validates shape, depth and size before preparing a review.

Restore applies task text and available IDs against the current catalog. Changed records, missing IDs and catalog-version differences appear in the review. Imported records do not replace the catalog or acquire execution authority. A restore retains one previous active state for Undo; a later restore replaces that undo state. Review alone does not change active work.

## Clear with an explicit scope

| Control | Effect | Recovery |
| --- | --- | --- |
| Clear active work | Clears selected IDs, title, task fields, pending import, restore preview, undo and temporary download references | Restore a saved checkpoint or downloaded export |
| Save and clear | Writes a checkpoint first, then clears active work | Review and restore that checkpoint; a write failure preserves active work |
| Remove checkpoint | Removes the selected saved checkpoint and a preview of that checkpoint | A previously downloaded export, if one exists |
| Clear saved checkpoints | Removes only `knowledge-garden.checkpoints.v1` from this browser origin after review; active work stays intact | A previously downloaded export, if one exists |

Checkpoint storage has a twelve-record limit and a 2 MiB UTF-8 budget. It never silently prunes older records. File import has a 1 MiB UTF-8 limit and depth bound of 32. Storage errors leave active work intact; malformed saved history is left untouched rather than silently overwritten. There is no cross-tab locking, so use one tab when changing checkpoints. Browser storage belongs to an origin; changing host or port changes which saved checkpoints are visible.

Clearing drops the application's references to active data, aborts pending file reading and revokes temporary download URLs. Garbage collection and browser memory reclamation remain runtime decisions. This does not clear the catalog, other browser data, the operating system's cache or ChatGPT memory. Saved checkpoints intentionally keep their data until removed. There is no promise of a particular heap reduction.

## Compile before serving

The maintained startup path is `npm start`. Its `prestart` step always builds `build/catalog.plan.json` for the current catalog, then starts the read-only server. `npm run build` supports an explicit build step; direct `node server.mjs` refuses a missing or stale plan. The programmatic `createServer` API compiles before listening when no plan is supplied.

The compiler produces numeric lookup slots for children, projects, connections, capabilities, sources and relation types, plus prepared literal-search text. Validation checks the compiler and catalog versions, source and plan fingerprints, index bounds, ordering, coverage and agreement with the catalog. Rehashing a wrong child relationship does not make it valid. Fingerprints detect content differences; they do not certify authorship or trust.

This is catalog-specific query-plan compilation. Task text is data. No `eval`, generated executable instructions, external compiler, network execution or source-project runtime is involved. A closed server releases its executor and snapshot; create a new server to listen again.

For later execution changes, keep this sequence: define the exact task and output, compile the known structure before serving, validate that the plan still agrees with its source, compare outputs, measure the complete incremental cost, then preserve evidence and recovery handles while releasing active references. Apply new compilers only to clearly specified workloads; do not describe an unmeasured path as optimal.

## Measured costs

The [benchmark JSON](../evidence/COMPILATION_BENCHMARK.json) records one local Node v24.19.0 run on the shipped 50-node catalog. Sixty distinct query results matched the earlier scan expressions. Timings use seven alternating-order trials after warmup, with 50,000 detail queries or 10,000 search queries per trial.

| Query workload | Median scan time per trial | Median compiled time per trial | Observed ratio |
| --- | ---: | ---: | ---: |
| Node detail | 183.553 ms | 7.860 ms | 23.35× |
| Literal search | 167.612 ms | 41.664 ms | 4.02× |

The actual Node build process took 62.141 ms, plan read/parse 0.291 ms and executor initialization 2.937 ms. Isolated in-memory compilation took 4.167 ms and is already included within the build-process cost; do not add it again. The compiled JSON plan is 9,816 bytes, alongside a 50,285-byte minified catalog. The measured extra startup cost amortizes at roughly 18,546 detail queries or 5,174 search queries under these synthetic workloads. A small session may never recover that cost.

These are query timings, excluding HTTP, response serialization, browser work, the npm wrapper and common server startup. They do not predict full-app latency. The three heap observations are noisy process measurements: the benchmark deliberately retains its input catalog and plan, and later samples include trial and JIT activity. They do not measure browser clearing or prove a memory saving.

The [preliminary run](../evidence/COMPILATION_PRELIMINARY.json) is retained with its correction: it used an unfrozen scan baseline and omitted real build-process and file costs. Its amortization estimate is superseded. Neither run establishes universal optimality.

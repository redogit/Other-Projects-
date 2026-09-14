# Verification record

September 14, 2026 · Knowledge Garden 1.1.0 · catalog 2026-09-14.1.

## Version 1.1 continuation

The complete suite passed **109/109 tests**, zero failures and zero skips, on Node v24.19.0. It retains the 76 version 1.0 checks and adds 24 working-set tests, seven compiler tests, a server-release lifecycle test and one UI state-flow test with multiple assertions. The catalog and twelve-route API contract are unchanged; the OpenAPI contract retains version 1.0.0.

Working-set checks cover current and legacy export parsing, exact task preservation, source closure, mismatched catalog versions, changed and missing entries, malformed and oversized inputs, bounded history, quota errors and preservation of unrelated browser-storage keys. The UI state test executes the actual application functions with a minimal DOM substitute. It checks save-before-clear ordering, storage-failure preservation, review without mutation, restore and undo, file-read cancellation and independent active/history clearing. It is not a rendered browser test.

Compiler checks compare details for all 50 catalog entries with independent scans, plus hierarchy, typed connections, capabilities, literal Unicode search, status filtering and self-relations. They reject stale, corrupted and rechecksummed semantically inconsistent plans. Caller mutation cannot change the executor snapshot; disposed executors and closed servers reject reuse.

A second reviewer found two defects in the first implementation: a closed server still retained its catalog, and a rechecksummed invalid child index could pass validation. Both were fixed. The bounded recheck observed release of both disposed-executor and closed-server catalog references using WeakRef and requested garbage collection; a forged self-child index was rejected before execution. This is evidence about those references, not a promise of an exact runtime or browser heap reduction.

An actual CLI smoke check confirmed that a missing plan and a stale plan both prevent startup, and that `npm start` builds before listening. The started server returned HTTP 200 with expected content types for `/`, `/working-set.mjs`, `/api/catalog` and a search query. It was then stopped. Updated UI syntax and static checks found 73 unique IDs, matching selectors, ten explicitly labelled input controls and one visible polite status region.

[Execution and recovery](EXECUTION.md) reports the observed query timings and build costs. The final benchmark checks sixty distinct outputs and uses seven alternating-order timing trials per workload. The earlier measurement is retained with its correction: its scan baseline was not frozen and it omitted real build-process/file costs. The corrected evidence includes actual Node build-process, plan-loading and executor-initialization measurements. Neither benchmark measures end-to-end UI performance.

Rendered browser and assistive-technology acceptance remain open for the reason recorded below. Add task editing, import preview, restore/undo, failed checkpoint writes, save-and-clear, individual checkpoint removal and active/history clear focus behavior to that acceptance pass. No browser acceptance result is inferred from the DOM substitute.

## Version 1.0 baseline retained

The following records the earlier 76-test baseline, before task recovery and compilation were added.

## Executed

`npm test` passed **76/76 tests**, zero failures and zero skips, on **Node v24.19.0**. This total includes 23 top-level tests and 53 subtests. The package declares Node 22 or later; Node 22 was not separately exercised in this environment.

The checks cover:

- The shipped catalog: 50 nodes, including 33 projects; 29 typed relations; 28 source summaries; 11 capability declarations; six proposed trails.
- Unique identities, existing references, cycle-free containment, strict published fields, nonempty source references, capability transport/status pairs and scoped support records.
- All twelve GET API routes and HEAD behavior; exact lookup, literal search, pagination, typed connection filters and explicit errors.
- Read-only method enforcement, fixed static-file routes, traversal rejection, malformed input, request bounds and Host checks.
- OpenAPI coverage of the implemented routes.

The UI passed JavaScript syntax and static HTML checks: 37 unique IDs, matching label targets and script selectors, and no inline event handlers or HTML injection path. A local in-process server served `/`, `/styles.css`, `/app.js` and `/api/catalog` with HTTP 200 and the expected content types.

## Source review

Separate read-only reviews checked Master/Orbit roles and the Conscience64 capability descriptions. They corrected a learner-routing label, narrowed the RIVIR static-repair status, and kept the fractal original as unresolved rather than absent. A public-content scan found no private Library identifiers, raw conversation records, local source paths, credential assignments or signed source URLs in the catalog.

The final repository refresh also read the newly published project entry points at `3c09ab6c07a854f8cc3feb585822cc7c5fd8dcde`. Those reports informed navigation and status labels; their computations were not rerun.

This verifies the inspected integration boundaries; it is not a full security audit or independent scientific validation.

## Not completed here

Rendered visual, browser-interaction and screen-reader acceptance checks were not completed. The local runtime lacked a browser binary, its standard download timed out, and the available cloud browser rejected the local app URL with `ERR_BLOCKED_BY_CLIENT`. Native semantic controls, focus handling, responsive styles and reduced-motion rules were reviewed as source only.

Before calling browser acceptance complete, exercise a desktop and narrow viewport, keyboard search and hierarchy navigation, typed-connection detail, trail gathering, add/remove focus, JSON download and back/forward deep links. Record actual assistive-technology behavior separately.

No source-project runtime, scientific experiment, RIVIR SDK test, Windows/Excel/JAWS workflow, Jira session, companion exchange or live deployment was run by these Garden checks.

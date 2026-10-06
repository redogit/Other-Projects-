# SDD ledger — plan: docs/superpowers/plans/2026-10-04-fkdb-f10-plan-b-local-workflow-adapters.md

Execution mode: native inline with per-task TDD/review gates; no subagent dispatch tool is exposed.

Ruling: continue on the existing `fkdb-direct-successor` branch and PR #116 because Plan B is a direct FKDB progression over the verified Plan A substrate — cost if wrong: Plan A and Plan B share one review branch rather than separate PRs, but all Plan B changes remain commit-bounded and reversible.

Ruling: register each new adapter test in CTest during its RED step because GitHub Actions is the executable environment available here — cost if wrong: CMake test registration lands earlier than the written Plan B Task 8, but no runtime authority is widened.

Plan B pre-flight:
- no vendor adapter exists yet;
- no local process execution will be added;
- all file adapters must receive resolved roots through the bridge policy;
- Zotero will use literal-loopback read-only HTTP only;
- ToolCarrier remains the admission boundary;
- cross-carrier FKDB index promotion remains deferred to Plan E.


Task 1: RED verified at 4a3b555 — only fkdb_local_adapters failed because the registry module was absent; the prior 48-test Plan A baseline remained green.
Task 1: complete — generic bounded LocalAdapterRegistry, policy-backed adapter caps/config, token-gated /collect endpoint, carrier validation, and empty-default production adapter policy; Linux and Windows dedicated matrices completed success with 49 tests.


Task 2: RED verified at 5ddf183 — only fkdb_adapter_mathbox failed because the adapter module was absent; the prior 49-test baseline remained green.
Task 2: complete — known-but-policy-disabled Mathbox adapter collects bounded raw .mathbox config/events, preserves lexical event order, records invalid JSON as explicit remainder, rejects symlink escape through bridge root resolution, and never promotes proof-recorded to proved; Linux and Windows dedicated matrices completed success with 50 tests.


Task 3: RED verified at 602d75d — only fkdb_adapter_superpowers failed because the module was absent; the prior 50-test baseline remained green.
Task 3: first GREEN was Linux-success but Windows exposed a test-fixture newline translation mismatch; production correctly preserved CRLF source bytes. Ruling: make the fixture byte-exact instead of normalizing source data — cost if wrong: test fixture becomes stricter while production raw-byte semantics remain unchanged.
Task 3: complete — bounded Superpowers specs/plans/progress collection with deterministic ordering, raw Markdown preservation, workflow-only authority/evidence ceilings, symlink confinement and explicit file/byte limits; Linux and Windows dedicated matrices completed success with 51 tests.


Task 4: RED verified at 20212ac — only fkdb_adapter_zotero failed because the module was absent; the prior 51-test baseline remained green.
Task 4: Ruling: local API over-limit responses must return PARTIAL + ZOTERO_RESULT_LIMIT_REACHED rather than silently truncate — cost if wrong: callers must handle an explicit partial state, but no bibliographic records disappear without remainder.
Task 4: complete — literal-loopback GET-only Zotero Desktop local API adapter with redirect denial, bounded URL-encoded search, preserved Zotero item/citation keys, no attachment/fulltext fetches, and raw portable BibTeX/RIS/CSL-JSON carriers; Linux and Windows dedicated matrices completed success with 52 tests.


Task 5: RED verified at 69ffc5a — only fkdb_adapter_wolfram failed because the module was absent; the prior 52-test baseline remained green.
Task 5: complete — bounded .wl/.m/.nb artifact collection, raw artifact SHA in source_version/provenance, base64 binary notebook carrier, executable discovery as DEGRADED LOCAL_PROCESS_PROBE only, and no RUN capability; Linux and Windows dedicated matrices completed success with 53 tests.


Task 6: RED verified at 1d6a69c — only fkdb_wasm_hif_contract failed for absent generic collection types/operations; all adapter/runtime gates remained green.
Task 6: complete — vendor-neutral collection-status/collect-request/collection-result WIT types, native async collect-local in 0.3, and explicit collection-operation/begin-collect polling in 0.2; WIT contains no Mathbox/Superpowers/Zotero/Wolfram names; Linux and Windows dedicated matrices completed success with 53 tests.


Task 7: RED verified at ded4acd — only fkdb_wasm_hif_contract and fkdb_web_host_node failed for missing safe rich descriptor projection/rendering; all 51 adapter/runtime tests remained green.
Task 7: complete — browser client sanitizes descriptors to tool_id/locality/state/capabilities/unresolved_requirements, drops arbitrary bridge fields, and index.html renders only the safe projection with no remote-login CTA; Linux and Windows dedicated matrices completed success with 53 tests.
Task 8 self-review: no Critical issue found. Intentional remainder: browser collection mutations still require an out-of-band bridge token; Plan B only exposes read-only discovery/status in the browser. ToolCarrier collection results are not yet admitted into FKDB's source index (Plan E).


Task 8: verification complete at head c570a881686373badb4f4313679c06a1af366b3f.
- Dedicated RMAPL Browser RMAL Bootstrap: Linux 53/53 PASS; Windows 53/53 PASS.
- Plan B gates passed: fkdb_local_adapters, fkdb_adapter_mathbox, fkdb_adapter_superpowers, fkdb_adapter_zotero, fkdb_adapter_wolfram, fkdb_wasm_hif_contract, and fkdb_web_host_node.
- Broad Decision Field audit: SUCCESS across exact bounded tests, operator-field evidence, GSFL projection, GSFL bidirectional macros, contextual multicarrier reasoning, S1 Carrier-Surface bridge, RMAPL Omega conditional repair, scale-4 adversarial stress, and frozen stress evidence.
- No Critical issue found in self-review.
- Intentional remainder preserved: no Wolfram execution; no Zotero writes/fulltext/attachment-file reads; no cloud sync; no SciSpace/Consensus/Exa/Linear/Supabase/Railway adapters yet; collected ToolCarriers are not yet promoted into the FKDB cross-carrier source index.
Task 8: complete — Plan B implementation boundary is verified and ready to be promoted in FKDB CURRENT/README/PR state.

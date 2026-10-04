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

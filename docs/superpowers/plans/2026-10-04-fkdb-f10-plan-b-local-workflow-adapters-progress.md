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

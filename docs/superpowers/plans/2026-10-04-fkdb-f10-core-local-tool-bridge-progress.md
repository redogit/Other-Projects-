# SDD ledger — plan: docs/superpowers/plans/2026-10-04-fkdb-f10-core-local-tool-bridge.md

Execution mode: native inline because no subagent dispatch tool is exposed; user approved subagent-driven/native execution.

Ruling: use the existing `fkdb-direct-successor` branch as the isolated workspace — repository access is through GitHub rather than a local checkout/worktree — cost if wrong: branch-level rather than filesystem-level isolation, but no changes touch main directly.

Pre-flight shared-interface scan:

| Producer | Consumer | Interface | Finding |
|---|---|---|---|
| Task 1 | Task 4 | capability graph / host semantics | clean: Task 4 extends WIT after Task 1 establishes host capability vocabulary |
| Task 1 | Task 5 | execution/profile semantics | clean: browser client consumes host/bridge state without redefining selection |
| Task 2 | Task 3 | ToolCarrier validation | clean: bridge must validate Task 2 carriers before acknowledgement |
| Task 2 | Task 4 | ToolCarrier logical fields | clean: WIT mirrors Task 2 carrier semantics |
| Task 2 | Task 5 | ToolCarrier/tool descriptors | clean: UI consumes descriptors/status only |
| Task 3 | Task 5 | bridge HTTP API | clean: client consumes exact v1 endpoints produced by bridge |
| Task 3 | Task 6 | bridge tests/CTest | clean |
| Task 4 | Task 6 | WIT contract tests/CTest | clean |
| Task 5 | Task 6 | browser/page tests/CTest | clean |

Task self-consistency scan:
- Task 1: clean.
- Task 2: clean.
- Task 3: clean; security-sensitive behavior is test-gated and deny-by-default.
- Task 4: clean.
- Task 5: clean.
- Task 6: clean.

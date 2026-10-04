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

Task 1: Ruling: legacy Node fixture asserted `detected.componentModel03 === true`, which contradicts the approved Task 1 contract removing that canonical capability; replace the fixture with `componentNative03` and assert `componentBrowserTranspiled03 === false` — cost if wrong: one compatibility fixture change, while legacy callers remain covered by `selectHostProfile()` tests.

Task 1: complete (commits 75d5375..80ffcfd, tests: RMAPL Browser RMAL Bootstrap run 79 -> Linux SUCCESS, Windows SUCCESS; RED run 76 failed only the new capability assertions before implementation; compatibility defects were repaired under the recorded ruling).

Task 2: Ruling: register the ToolCarrier test in CTest during RED instead of waiting for Task 6 — remote GitHub CI is the available execution environment, so early registration is required to observe the mandated failing test; Task 6 retains final matrix/documentation ownership — cost if wrong: one CMake test entry lands earlier than planned, with no runtime behavior change.

Task 2: complete (commits f7cfa91..79a6861, tests: RMAPL Browser RMAL Bootstrap run 82 -> Linux SUCCESS, Windows SUCCESS; RED run 81 failed only fkdb_tool_carrier because module/schemas were absent, then 47/47 matrix passed after implementation).

Task 3: Ruling: register the Local Tool Bridge security test in CTest during RED for the same remote-CI reason as Task 2; default production policy remains deny-by-default and no process grant is added — cost if wrong: another test entry lands before Task 6, without widening runtime authority.

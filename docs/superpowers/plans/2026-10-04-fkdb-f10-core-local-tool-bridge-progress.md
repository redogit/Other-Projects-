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

Task 3: complete (commits 4279a34..4bdeffc, tests: RMAPL Browser RMAL Bootstrap run 88 -> Linux SUCCESS, Windows SUCCESS; RED run 85 failed only because the bridge module/policy were absent; run 87 exposed Windows absolute-path spelling in process subcommand identity, repaired by canonical absolute-path comparison without relaxing raw command matching).

Task 4: complete (commits 6bccae4..3df8491, tests: RMAPL Browser RMAL Bootstrap run 92 -> Linux SUCCESS, Windows SUCCESS; RED run 90 failed only the new local-tool WIT assertions; 0.3 native-async and 0.2 explicit-poll contracts now share the same logical tool types).

Task 5: Ruling: the pre-existing returned-home assertion still expected ["history","lineage"] after the approved TOOLS relation was added; update that fixture to ["history","tools","lineage"] while preserving the progression-history assertions — cost if wrong: one navigation expectation could mask an unintended extra home relation, but manifest/link-parity and dedicated TOOLS tests independently constrain the exact set.

Task 5: complete (commits 2d28d43..6411033, tests: RMAPL Browser RMAL Bootstrap run 102 -> Linux SUCCESS, Windows SUCCESS; RED run 96 failed only missing client/TOOLS surfaces; first GREEN run 100 exposed one stale returned-home fixture, ruled and corrected without changing runtime semantics).

Task 6: Ruling: no further CMake edit is needed because fkdb_tool_carrier and fkdb_local_tool_bridge were deliberately registered during Tasks 2/3 to make RED observable in remote CI; run 102 verifies the resulting final dedicated matrix on Linux and Windows — cost if wrong: Task 6 does not create a distinct CMake-only commit, but the final matrix still exercises the intended gates.

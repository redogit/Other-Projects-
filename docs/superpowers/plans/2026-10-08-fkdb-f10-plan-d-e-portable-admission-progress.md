# FKDB F10 Plan D/E portable providers and admission progress

## Retained implementation — PR #119

Plan D uses one `PortableProviderAdapter` for SciSpace, Consensus, Exa and Linear
JSON envelopes. It preserves provider/source identity and record values, emits
canonical JSON carrier bytes/hash, reports malformed records and returned-record
limits explicitly, and uses provider-specific authority scopes with
`PORTABLE_PROVIDER_RECORD_UNVERIFIED`. Original export formatting and JSONL parsing
are outside this implemented boundary. Production policy remains empty/opt-in.

Plan E implements callable ToolCarrier validation/admission, explicitly declared
same-subject/different-claim contradiction inspection, external index-record projection
and collision-rejecting `EXT-` overlays. Tests query an overlaid index and confirm the
canonical static index is unchanged. No browser/HTTP collection-to-index workflow is
implemented automatically; source/evidence authority is not promoted. Current limits
are 1 MiB per admitted payload and 32 distinct index terms per record by default.
An aggregate carrier-count bound is not claimed.

## Historical exact-head verification — 2026-10-08 UTC

All three job logs fetch and check out
`2a7180c7e26117e2834603ac0be82fda186ec016` before executing:

| Gate | Job | Result |
| --- | --- | --- |
| Dedicated Linux | [113268261453](https://github.com/redogit/Other-Projects-/actions/runs/37764369121/job/113268261453) | 57/57 CTest targets PASS |
| Dedicated Windows | [113268261909](https://github.com/redogit/Other-Projects-/actions/runs/37764369121/job/113268261909) | 57/57 CTest targets PASS |
| Broad Decision Field audit | [113268466797](https://github.com/redogit/Other-Projects-/actions/runs/37764369185/job/113268466797) | 356 unittest tests and all evidence/stress steps PASS |

Dedicated targets include Plan B, Supabase, Railway, `fkdb_adapter_portable_provider`
and `fkdb_cross_carrier`. These receipts establish the prior implemented scope and do
not override the missing Plan C secret-path regressions discovered in PR #118.

## Integration and repair gate — 2026-10-10 UTC

Retain all Plan D/E code and tests while incorporating `main` at
`51b30bd28239b29eab68bf64c472d68923827166` and the PR #118 negative history.
Final verification is pending the Plan C secret-path repair, its synthetic regressions,
dedicated Linux/Windows execution and current broad audit on one exact final head.
The broad workflow now includes pinned Hodge dependency verification and tests.

The [Plan C progress ledger](2026-10-05-fkdb-f10-plan-c-local-infrastructure-adapters-progress.md)
records the required gate and subsequent receipts. No new final-head success or full
rollout closeout is claimed here before those executions complete.

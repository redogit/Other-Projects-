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

## Verified repair integration — 2026-10-10 UTC

Plan D/E code and tests are retained while incorporating `main` at
`51b30bd28239b29eab68bf64c472d68923827166` and the full PR #118 negative history.
Exact repair head `49a0154d60d5f0d8a419c3ac808a11442e169402` passes:

| Gate | Exact-head job | Result |
| --- | --- | --- |
| Dedicated Linux | [114125101762](https://github.com/redogit/Other-Projects-/actions/runs/38022100985/job/114125101762) | 59/59 CTest targets PASS |
| Dedicated Windows | [114125101696](https://github.com/redogit/Other-Projects-/actions/runs/38022100985/job/114125101696) | 59/59 CTest targets PASS |
| Current broad audit | [114125100934](https://github.com/redogit/Other-Projects-/actions/runs/38022100692/job/114125100934) | 376 bounded tests, 14 Hodge tests and all 8 evidence/stress steps PASS |

Both dedicated matrices include portable providers and cross-carrier overlays together
with Plan B, both Plan C adapters and the new secret-path/HTTP import suites. The
validator, admission, direct index projection and external overlay reject recognizable
retained Supabase/Railway secret sources without changing provider authority/evidence.
The original four synthetic witnesses now pass under the unchanged PR #118 probe.
Independent agent code review passed 82 affected tests with no remaining
Critical/Important finding. No independent human review is claimed.

The [Plan C progress ledger](2026-10-05-fkdb-f10-plan-c-local-infrastructure-adapters-progress.md)
and [repair evidence](../../../Decision%20Field%20Operator%20Lab/fkdb/evidence/plan-c-secret-repair/README.md)
retain exact checkout/timestamp receipts, raw red/green logs, review scope and recovery
guidance. Sensitive path names and recognizable declared vendor sources are the tested
policy; opaque source declarations or credentials under ordinary names are outside it.

Subsequent documentation commits require their own exact-head native and broad merge
gates. The final metadata-head receipt is tracked live in
[PR #119](https://github.com/redogit/Other-Projects-/pull/119); repair-head success is not
transferred to that later commit.

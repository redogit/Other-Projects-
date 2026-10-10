# FKDB F10 Plan D Portable Research/Project Adapters

**Goal:** ingest durable SciSpace, Consensus, Exa and Linear exports/user-provided records
without requiring their remote APIs.

## Design

Use one generic `PortableProviderAdapter` configured by provider policy rather than four
independent parsers. The implemented input is one user-selected JSON envelope under
an allowed root; JSONL is not implemented.

Provider policies:

- SciSpace: `RESEARCH_DISCOVERY_ONLY`
- Consensus: `RESEARCH_SYNTHESIS_ONLY`
- Exa: `SEARCH_DISCOVERY_ONLY`
- Linear: `PROJECT_WORKFLOW_ONLY`

Required envelope fields:

```text
schema = fkdb/portable-provider/v1
provider
exported_at
records[]
```

Each record preserves provider source identity and JSON field values. Its carrier payload
is deterministic canonical JSON (sorted keys and compact separators), hashed as emitted;
original export-file formatting is not preserved. Optional common fields (query, title,
authors, doi_or_url, source_url, external_id, parent_id, labels) remain in the record when
present; absent fields are not inferred.

## Security / evidence rules

- no network access;
- no authentication;
- no remote synchronization;
- no HTML execution;
- bounded files/bytes/records;
- path confinement and symlink rejection through the Local Tool Bridge;
- provider agreement does not become truth;
- Linear issue status does not become scientific evidence;
- search rank does not become authority;
- malformed records remain explicit remainder.

## Verification

Add one generic adapter module and tests covering all four provider policies, malformed
envelopes, record limits, JSON-value preservation and authority separation. Register
four known adapter IDs in code while production policy remains opt-in.

Plan D and the Plan E callable admission/index-overlay helpers are implemented on
PR #119. Historical exact-head receipts at `2a7180c...` and retained Plan D/E verification
at the repaired/integrated head `49a0154...` are recorded in the [Plan D/E progress ledger](2026-10-08-fkdb-f10-plan-d-e-portable-admission-progress.md).
No automatic browser/HTTP collection-to-index workflow is claimed.

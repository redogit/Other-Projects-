# FKDB F10 Plan D Portable Research/Project Adapters

**Goal:** ingest durable SciSpace, Consensus, Exa and Linear exports/user-provided records
without requiring their remote APIs.

## Design

Use one generic `PortableProviderAdapter` configured by provider policy rather than four
independent parsers. Input is a user-selected JSON/JSONL artifact under an allowed root.

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

Each record must preserve provider source identity and raw JSON payload. Optional common
fields (query, title, authors, doi_or_url, source_url, external_id, parent_id, labels)
are copied only when present; absence remains absence.

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
envelopes, record limits, raw-payload preservation and authority separation. Register
four known adapter IDs in code while production policy remains opt-in.

After Plan D, Plan E admits validated ToolCarriers into the FKDB source index.

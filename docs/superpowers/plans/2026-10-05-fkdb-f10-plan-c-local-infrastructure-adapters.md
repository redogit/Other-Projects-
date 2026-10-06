# FKDB F10 Plan C Local Infrastructure Adapters Implementation Plan

> **For agentic workers:** execute task-by-task with TDD and per-task verification.

**Goal:** Add local-first Supabase and Railway infrastructure adapters to FKDB without requiring hosted projects, remote APIs, or local process execution.

**Architecture:** Reuse the verified Plan B LocalAdapterRegistry and ToolCarrier boundary. Supabase is a bounded local-project artifact adapter over the `supabase/` tree. Railway is a bounded repository artifact adapter that prefers current `.railway/railway.ts` Infrastructure as Code and preserves legacy `railway.json` / `railway.toml` as deprecated historical records. Both are opt-in and read-only.

## Constraints

- No Supabase cloud project is required.
- No Railway cloud project is required.
- No Supabase CLI or Railway CLI process execution.
- No database connections or hosted deployment queries.
- No secrets, `.env`, generated credentials, access tokens, or service keys are collected.
- All paths pass through bridge read-root containment.
- All collection is bounded by adapter max-files/max-bytes.
- ToolCarrier admission remains mandatory.
- `LOCAL_PROJECT_ARTIFACT != LIVE_INFRASTRUCTURE_STATE`.
- `RAILWAY_CONFIG != DEPLOYMENT_SUCCESS`.
- `SUPABASE_MIGRATION != APPLIED_DATABASE_STATE`.
- `LEGACY_RAILWAY_CONFIG != CURRENT_RAILWAY_AUTHORITY`.

## Task 1 — Supabase local-project adapter

Create:
- `Decision Field Operator Lab/tools/fkdb_adapter_supabase.py`
- `Decision Field Operator Lab/test_fkdb_adapter_supabase.py`

Modify:
- `Decision Field Operator Lab/tools/fkdb_local_adapters.py`
- `Decision Field Operator Lab/rmal-browser/CMakeLists.txt`

Collect only:
- `supabase/config.toml`
- `supabase/migrations/*.sql`
- `supabase/seed.sql`
- `supabase/functions/**/*.ts`
- `supabase/functions/**/*.json`

Explicitly ignore/reject:
- `.env*`
- files containing obvious secret/key filenames
- paths escaping allowed root

Authority/evidence:
- `SUPABASE_LOCAL_PROJECT_ARTIFACT_ONLY`
- `CONFIG_OR_MIGRATION_NOT_APPLIED_STATE`

Tests:
- unavailable project;
- deterministic lexical collection;
- config/migration/function carrier kinds;
- secret filename exclusion;
- symlink escape rejection;
- max-file/max-byte PARTIAL remainder;
- no claim that migration was applied.

## Task 2 — Railway local/portable deployment-artifact adapter

Create:
- `Decision Field Operator Lab/tools/fkdb_adapter_railway.py`
- `Decision Field Operator Lab/test_fkdb_adapter_railway.py`

Modify:
- `Decision Field Operator Lab/tools/fkdb_local_adapters.py`
- `Decision Field Operator Lab/rmal-browser/CMakeLists.txt`

Prefer:
- `.railway/railway.ts`

Also preserve when present:
- `railway.json`
- `railway.toml`
- `Dockerfile`
- `nixpacks.toml`
- `Procfile`
- explicitly requested portable build/deploy/log snapshots under an allowed root

Legacy Railway configs must carry:
- `RAILWAY_CONFIG_AS_CODE_DEPRECATED`
- cutoff metadata `2026-12-01`

Authority/evidence:
- `RAILWAY_REPOSITORY_ARTIFACT_ONLY`
- `DEPLOYMENT_ARTIFACT_NOT_LIVE_DEPLOYMENT_STATE`

Tests:
- IaC preferred/current marker;
- legacy config preserved + deprecated remainder;
- no live cloud-state claim;
- deterministic ordering;
- bounds/symlink containment;
- portable log snapshot raw preservation.

## Task 3 — Registry/browser-safe status integration

Modify:
- `Decision Field Operator Lab/tools/fkdb_local_adapters.py`
- `Decision Field Operator Lab/test_fkdb_web_host.mjs` only if needed

Requirements:
- register known Supabase/Railway adapters in code;
- production policy remains `adapters: []`;
- browser sees only safe descriptors already defined by Plan B;
- no remote login prompt or hosted project URL.

## Task 4 — Verify and promote Plan C

Modify after green verification:
- `Decision Field Operator Lab/fkdb/CURRENT.md`
- `Decision Field Operator Lab/rmal-browser/README.md`
- PR #116 body
- Plan C progress ledger

Verification:
- dedicated Linux + Windows browser/RMAL matrix;
- broad Decision Field audit;
- Plan B gates remain green.

Remainder after Plan C:
- Supabase local runtime/database queries are not performed;
- Railway live deployment state is not queried;
- no cloud sync;
- Plan D portable SciSpace/Consensus/Exa/Linear adapters remain;
- Plan E ToolCarrier -> FKDB source-index admission remains.

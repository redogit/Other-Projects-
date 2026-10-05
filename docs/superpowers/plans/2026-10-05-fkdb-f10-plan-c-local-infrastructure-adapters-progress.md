# SDD ledger — plan: docs/superpowers/plans/2026-10-05-fkdb-f10-plan-c-local-infrastructure-adapters.md

Execution mode: native inline with TDD and exact-head CI gates.

Ruling: Plan C stays on PR #116 because it is a direct adapter extension over the verified Plan A/B registry — cost if wrong: one review branch carries multiple bounded increments, but every adapter remains isolated by files/tests and reversible.

Ruling: Railway current authority is `.railway/railway.ts` Infrastructure as Code. Legacy `railway.json` and `railway.toml` are retained as historical carriers with explicit deprecation/cutoff metadata rather than treated as current authority — cost if wrong: a future Railway change requires metadata revision, not carrier loss.

Ruling: Supabase Plan C collects local project artifacts only and does not invoke the CLI or query a database; this preserves the fail-closed process boundary — cost if wrong: runtime-state visibility is deferred, but no hidden process/network authority is introduced.

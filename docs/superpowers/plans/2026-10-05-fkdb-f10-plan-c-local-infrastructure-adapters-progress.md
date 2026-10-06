# SDD ledger — plan: docs/superpowers/plans/2026-10-05-fkdb-f10-plan-c-local-infrastructure-adapters.md

Execution mode: native inline with TDD and exact-head CI gates.

Ruling: Plan C stays on PR #116 because it is a direct adapter extension over the verified Plan A/B registry — cost if wrong: one review branch carries multiple bounded increments, but every adapter remains isolated by files/tests and reversible.

Ruling: Railway current authority is `.railway/railway.ts` Infrastructure as Code. Legacy `railway.json` and `railway.toml` are retained as historical carriers with explicit deprecation/cutoff metadata rather than treated as current authority — cost if wrong: a future Railway change requires metadata revision, not carrier loss.

Ruling: Supabase Plan C collects local project artifacts only and does not invoke the CLI or query a database; this preserves the fail-closed process boundary — cost if wrong: runtime-state visibility is deferred, but no hidden process/network authority is introduced.


Task 1: RED verified at 5544d47 — prior 53-test Plan B baseline remained green and only fkdb_adapter_supabase failed because the adapter module was absent.
Task 1: complete — bounded read-only Supabase local-project adapter collects config.toml, migrations, seed.sql, and Edge Function TS/JSON artifacts; secret-like files are excluded; runtime/applied state is explicitly not claimed; Linux and Windows dedicated matrices passed 54/54.

## Merged-main reconciliation — 2026-10-06 UTC / 2026-10-05 America/New_York

**Decision: IMPLEMENTED / CLOSEOUT BLOCKED. Plan D is NOT advanced.**

The Task 1 entries above are historical receipts, not a complete current security
claim. PR #116 merged at `f3573799185df44b03a1eb1e333bb0721a0805a1`
(2026-10-06 01:49:32 UTC, October 5 evening Eastern). The inspected newer `main`
base is `4a05785e4376c558ed7ad761f89db9dd241bca7b`, including PR #117.
Both adapter implementations and their tests are present at this base.

Reconciliation ruling: modify only `Decision Field Operator Lab/fkdb/CURRENT.md`
and this progress ledger; preserve historical entries and existing implementations.
A passing baseline cannot override a reproduced negative safety witness. Cost of
this scope: the defects remain unfixed, explicitly blocking promotion.

### Executed CI receipts

Dedicated workflow: `.github/workflows/rmal-browser-bootstrap.yml`.

| Run/job | Revision actually checked out | Outcome |
| --- | --- | --- |
| [Linux rerun, job 112098041000](https://github.com/redogit/Other-Projects-/actions/runs/37401111554/job/112098041000) | `f3573799185df44b03a1eb1e333bb0721a0805a1` | 55/55 CTest targets PASS; log 03:47:27–03:48:07 UTC |
| [Windows rerun, job 112097407455](https://github.com/redogit/Other-Projects-/actions/runs/37401111554/job/112097407455) | `f3573799185df44b03a1eb1e333bb0721a0805a1` | 55/55 CTest targets PASS; log 03:44:52–03:45:52 UTC |
| [Broad audit rerun, job 112097134392](https://github.com/redogit/Other-Projects-/actions/runs/37401310629/job/112097134392) | `4a05785e4376c558ed7ad761f89db9dd241bca7b` | All audit job steps completed successfully |

Dedicated reruns executed the existing configuration/build/test sequence:

```sh
cmake -S "Decision Field Operator Lab/rmal-browser" -B build/rmal-browser -G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Release
cmake --build build/rmal-browser --parallel 2
ctest --test-dir build/rmal-browser --output-on-failure
```

The 55 targets include ToolCarrier, Local Tool Bridge, local registry, the four
Plan B adapters, Supabase (target 54) and Railway (target 55). These are CTest target
counts, not a claim that exactly 55 individual Python assertions were executed.
The broad workflow rerun passed its bounded-tests step, operator/GSFL/contextual/
S1/Omega evidence-reproduction steps, scale-4 stress and frozen-stress checks.

`PLAN-C-MATRIX-001` — verification gap: no dedicated matrix at the newer exact
`4a05785...` head was executed. The workflow has `workflow_dispatch`, but the
available Actions write operations exposed reruns only. A rerun preserves its
original revision; it does not test today's `main`. One Linux retry during the
Windows run was refused because the workflow was running; the later Linux rerun
above completed. Carried-forward job success was distinguished from fresh execution
by reading log timestamps. No aggregate green status was substituted for that check.

A comparison of `f357379...` to `4a05785...` changes only
`Decision Field Operator Lab/rmapl_runtime.py` and
`Decision Field Operator Lab/test_rmapl_mutation_scope.py`. Adapter/test/registry
blobs remain unchanged. This narrows source drift but does NOT transfer the entire
native matrix result to the newer head. No exact-head dedicated gate is claimed.

### Supplemental execution on exact current-main source

Four files were read from `4a05785...`, reconstructed locally, and verified against
their Git blob IDs before execution:

| Source file under `Decision Field Operator Lab/tools/` | Git blob SHA-1 |
| --- | --- |
| `fkdb_adapter_supabase.py` | `588c571cec3f97bdf6f5ef2d769946ef67d592d1` |
| `fkdb_adapter_railway.py` | `14d8bf17f83dd7188db05cb0bc19de2d838d5806` |
| `fkdb_local_adapters.py` | `d63fa00b2c3f3e9f7d959715d441939edc31d548` |
| `fkdb_tool_carrier.py` | `6d2de97b8d87bde7f0454f9af8b430b7361fb172` |

Local Linux/Python 3.13.5 execution used the actual adapters, registry and carrier
validator with an explicitly limited read-root/enablement policy fixture. It did
not execute the HTTP bridge, native browser build, Windows, a vendor CLI, a database
or a hosted service. The full supplemental suite ran 10 test methods: 8 passed,
2 failed, with 4 failed assertions/subtests, zero errors and zero skips; exit 1.

Verified positive controls:

- disabled adapters are absent from registry descriptor output;
- requested-root symlink containment holds even when the target is another allowed
  read root; Railway snapshot `../` escape is rejected;
- static single-file and aggregate byte ceilings, exact-byte admission and file-count
  limits return explicit PARTIAL remainder without exceeding the tested payload budget;
- collection is deterministic, preserves fixture bytes/SHA-256, leaves fixture files
  unchanged and retains artifact-only authority plus false runtime/live-state flags;
- invalid UTF-8 returns explicit PARTIAL remainder;
- Supabase excludes recognized `.env.json`, `secrets.json` and `service_role.json`
  basenames within matching function JSON globs.

Source inspection separately confirmed the production policy remains
`adapters: []`, `read_roots: []`, `write_roots: []`, `processes: []` and an empty
environment allowlist. The HTTP collect route checks origin/token and explicit
adapter enablement before calling the registry; direct registry collection is not
itself an authorization gate. Those bridge targets passed in the merge-SHA matrices;
no new local HTTP integration execution is claimed here.

The checked-in adapter tests do not directly cover these secret-path counterexamples
or explicit max-byte cases. Static payload limits are not a proof of bounded
candidate-directory enumeration, concurrent-growth safety or race-hard containment.
These stronger resource/hostile-filesystem guarantees remain unverified.

### Retained negative witnesses

`PLAN-C-SECRET-001` — Railway's explicit snapshot collection accepts `.env.json`,
`service_role.json` and `secrets.txt` because each has a permitted snapshot extension
and resolves within the allowed/requested root. Each produced `COLLECTED`, one
validated ToolCarrier, the exact synthetic payload, and no exclusion remainder.
There is no secret-name filtering at this adapter/registry/validator path. Expected:
deny or explicitly omit these secret-like artifacts before reading/admitting payloads.

`PLAN-C-SECRET-002` — Supabase collected
`supabase/functions/secrets/credentials.json` as an `edge-function` ToolCarrier.
Its secret predicate checks the resolved basename and does not exclude this
credential-like path. Expected: deny or explicitly omit this path before payload
admission. This finding limits, rather than erases, the historical narrower
secret-basename tests. No real credential was read or exposed in any probe.

The following minimal witness was also executed against the four hash-verified
source files, with `PYTHONPATH` pointing to that source directory. In a repository
checkout, set `PYTHONPATH` to `Decision Field Operator Lab/tools`. It intentionally
uses a policy fixture, not an emulated claim of HTTP integration. Expected output
at this base: four `FAIL` lines followed by an assertion failure (exit 1).

```python
"""Synthetic local-policy fixture; real adapters, registry, and carrier validator.
Run with PYTHONPATH pointing to the four verified source modules or repo tools.
This does not exercise the HTTP bridge or any live infrastructure.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from fkdb_adapter_supabase import SupabaseAdapter
from fkdb_adapter_railway import RailwayAdapter
from fkdb_local_adapters import LocalAdapterRegistry

class ReadPolicyFixture:
    adapter_max_files = 32
    adapter_max_bytes = 65536
    def __init__(self, root):
        self.read_roots = (root.resolve(),)
    def adapter_enabled(self, tool_id):
        return tool_id in {"supabase", "railway"}
    def resolve_allowed_path(self, path, mode):
        resolved = Path(path).resolve()
        if mode != "READ" or not resolved.is_relative_to(self.read_roots[0]):
            raise PermissionError("outside read root")
        return resolved

registry = LocalAdapterRegistry()
registry.register(SupabaseAdapter())
registry.register(RailwayAdapter())
cases = [("railway", ".env.json"), ("railway", "service_role.json"),
         ("railway", "secrets.txt"),
         ("supabase", "supabase/functions/secrets/credentials.json")]
failures = []
for tool, name in cases:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b'{"marker":"SYNTHETIC_ONLY_NOT_A_CREDENTIAL"}\n')
        options = {"snapshot_paths": [name]} if tool == "railway" else {}
        try:
            result = registry.collect(tool, {"root": str(root), "options": options},
                                      ReadPolicyFixture(root))
        except PermissionError:
            print("PASS", tool, name, "denied")
            continue
        identities = [c["source_identity"] for c in result["carriers"]]
        leaked = name in identities
        print("FAIL" if leaked else "PASS", tool, name, result["status"], identities)
        if leaked:
            failures.append((tool, name))
assert not failures, f"secret-path exclusions failed: {failures}"
```

### Task reconciliation and next step

- Task 1: implementation and historical 54/54 receipt retained; supplemental secret
  path counterexample remains open. Do not generalize basename exclusions to all secrets.
- Task 2: Railway implementation and checked-in tests are present; Linux/Windows
  merge-SHA targets pass. Full task acceptance is BLOCKED by `PLAN-C-SECRET-001`.
- Task 3: registration and opt-in HTTP wiring are present; production defaults remain
  empty and authority flags stay artifact-only. No new process/network authority.
- Task 4: records reconciled; Plan C closeout is BLOCKED by both secret witnesses and
  the exact-newer-head dedicated-matrix gap. Nothing here promotes Plan D or Plan E.

Next one-degree step: retain and turn the secret witnesses into negative regressions,
repair exclusions within the existing adapters, then rerun both native matrices and
the broad audit on one exact final implementation head with Plan B still green.
Resolve or explicitly bound the resource/hostile-filesystem claim ceiling. Only then
record Plan D (portable SciSpace/Consensus/Exa/Linear) as next; source-index admission
remains Plan E. No runtime/database/deployment/cloud synchronization is admitted.

Railway IaC/deprecation/cutoff assertions were checked as repository-encoded metadata,
not independently verified vendor policy or live deployment authority.

Final review: author self-review; no independent reviewer was available. The two-file
scope preserves all pre-existing ledger text and unrelated CURRENT sections; no adapter,
test, workflow, README or historical PR body is changed by this reconciliation.

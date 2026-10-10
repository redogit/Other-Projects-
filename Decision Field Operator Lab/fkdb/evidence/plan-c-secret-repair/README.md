# Plan C secret-path repair execution evidence

The original synthetic negative witnesses and every supplemental red/green cycle are retained here. Local-only source heads in the raw logs identify the scratch integration; the pre-repair adapter blobs are reproducible from PR #119 head `2a7180c7e26117e2834603ac0be82fda186ec016`. No real credentials or live infrastructure were accessed.

The shared path policy excludes secret-sensitive requested and resolved project-relative paths before collection payload reads. Validation, bundle/HTTP import, Plan E admission, direct index projection and external overlay also reject recognizable declared Supabase/Railway sources. Changing locality/adapter labels does not bypass this exclusion. Existing secret substring exclusions are preserved; Windows separators, case, trailing dots/spaces and alternate stream base/name components are screened. Valid configuration, migration, function, build and snapshot artifacts remain available.

The 23 new security regression methods and 134 dedicated FKDB Python tests pass. Repair commit `49a0154d60d5f0d8a419c3ac808a11442e169402` passed native Linux and Windows 59/59 CTest targets each, 376 broad bounded tests, 14 pinned-dependency tests and all eight evidence/stress commands. The raw CI logs, extracted receipts, source hashes and local full-audit execution records are retained below. The final documentation commit must pass these same exact-head gates before merge; its current receipt is recorded in [PR #119](https://github.com/redogit/Other-Projects-/pull/119). The earlier local GCC native build failed the pinned upstream final-C23 requirement; the resulting 16 missing native executables in the supplemental CTest attempt are recorded, not promoted to passing evidence. The pin and compiler requirements were preserved.

## Recovery and limitations

Keep the production adapter opt-in empty unless separately configured. Recollect legitimate artifacts from their original read-only sources under the repaired boundary; rebuild disposable external overlays rather than reusing pre-fix retained projections. Retain rejected synthetic carriers only as negative evidence. If a regression appears, hold merge/collection and fix forward without weakening the secret policy. PR #118 history and Plan D/E provider implementations remain available through the retained parent commits.

Detection is based on recognizable declared vendor identities and sensitive path names. Opaque/misdeclared metadata and credential contents under ordinary names are outside this policy. Candidate directory enumeration, concurrent file growth and race-hard reads remain unproved. No automatic browser collection-to-index workflow, remote synchronization or authority promotion is claimed.

## Exact repair-head receipts

| Gate | Job | Result |
| --- | --- | --- |
| Native Linux | [114125101762](https://github.com/redogit/Other-Projects-/actions/runs/38022100985/job/114125101762) | 59/59 CTest targets |
| Native Windows | [114125101696](https://github.com/redogit/Other-Projects-/actions/runs/38022100985/job/114125101696) | 59/59 CTest targets |
| Broad audit | [114125100934](https://github.com/redogit/Other-Projects-/actions/runs/38022100692/job/114125100934) | 376 bounded tests, 14 dependency tests, eight evidence/stress steps |

Both original prohibited-file cases are deterministic in the security suites. The unchanged PR #118 counterprobe also passes all four cases at this revision. Shared helper checks cover Windows name syntax portably; symbolic-link fixtures depend on host privileges and do not establish race-hard reads.

See [structured CI receipts](ci-at-repair-head/receipts.json), [local exact-head audit](local-broad-at-repair-head/local-broad-report.json), [independent agent review](independent-agent-review.md) and [execution manifest](execution.json). Final metadata-head CI is recorded in PR #119 because a commit cannot embed its own final SHA and later execution receipts.

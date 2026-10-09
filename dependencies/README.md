# Canonical Hodge dependency

Hodge research is authoritative in [redogit/hodge](https://github.com/redogit/hodge).
The shared Decision Field and MiniGX consumers remain here. They use the exact
canonical revision and raw SHA-256 values in `hodge.lock.json`, rather than old
local artifact paths or a moving upstream branch.

From the repository root:

```sh
python3 tools/hodge_dependency.py fetch
python3 tools/hodge_dependency.py verify
python3 -m unittest discover -s tools/tests -v
python3 -m unittest discover -s "Decision Field Operator Lab" -p "test_*.py" -v
python3 "Decision Field Operator Lab/run_rmapl_omega_audit.py" --check
python3 "Decision Field Operator Lab/run_rmapl_omega_stress.py" --check
python3 "RMAOS MiniGX/VERIFY.py"
```

Only `fetch` accesses the network. It checks out full commit
`365ce68da4f1d8dee3fd3cc7344b5e085dec364f` into ignored `.dependencies/hodge` and
checks all locked artifacts before admitting the checkout. Readers verify the
revision and artifact bytes on every resolution, and fail if anything is missing
or altered. No fallback to former locations is allowed. Existing checkouts are
never overwritten by `fetch`.

For offline use or a different filesystem layout, set `HODGE_REPOSITORY_ROOT` to
an existing checkout at exactly the locked revision; the same checks apply.
The cache and generated APK assets are reproducible dependency/build outputs,
not competing authoritative research copies. MiniGX compiler/runtime code and
generic fullscreen vertex shader remain local.

The pin is Hodge PR #2's merge commit, with the same Git tree
`7ed95a18946999e2b805a2b63dcdabc00aee76ed` as its CI-passing head
`ac0eac30105c6241b3dbb3f8fdb86d85824f86b9`. The lock records canonical paths,
Git blob identities, predecessor repository/revision/paths, and raw SHA-256 values.
All three artifacts are byte-identical to predecessor revision
`4a05785e4376c558ed7ad761f89db9dd241bca7b`; native provenance and frozen evidence
remain unchanged. A dependency update requires an explicit reviewed lock change
and a rerun of affected verification, never automatic tracking of upstream main.

`SOFTWARE_VERIFICATION != MATHEMATICAL_PROOF`,
`METHOD_TRANSFER != EVIDENCE_TRANSFER`, and `BYTE_IDENTITY != SEMANTIC_TRUTH`.

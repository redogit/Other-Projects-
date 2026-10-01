# Bounded negative TLS evidence — PR #107

Source: PR #107 at `73c9e807c9bc57db6bdf0c299a7f8eb7b5bcfe74`.
This increment adds executable checks and a retrieved Windows execution receipt.
CI uploads `tls-negative-receipt.json` tagged with the exact verification commit,
including partial failures. The archived successful receipt below is evidence
for its recorded commit, not a claim about unexecuted future revisions.

## Controlled checks

| Case | Explicit SSL policy | Native loopback handshake |
|---|---|---|
| Valid localhost endpoint | accept | exact response bytes, one encrypted request |
| Same endpoint, request for 127.0.0.1 | `CERT_E_CN_NO_MATCH` / `800b010f` | `SEC_E_WRONG_PRINCIPAL` / `80090322` |
| New untrusted localhost endpoint | `CERT_E_UNTRUSTEDROOT` / `800b0109` | `SEC_E_UNTRUSTED_ROOT` / `80090325` |
| Trusted localhost endpoint expired two days before run | `CERT_E_EXPIRED` / `800b0101` | `SEC_E_CERT_EXPIRED` / `80090328` |

The policy probe compiles the actual `win32_tls.c` into a separate test binary.
Only certificate acquisition is replaced with a supplied fixture. The real
`CertGetCertificateChain`, `CertVerifyCertificateChainPolicy`, hostname argument,
zero ignore flags, and rejection branch all run unchanged. A generic failure
cannot satisfy the exact policy error oracle.

The loopback test invokes the unmodified production SChannel executable. Each
negative must exit 68 with the specific handshake error, send no HTTP request,
leave a preexisting response-file sentinel unchanged, and make exactly one TLS
connection. The successful control prevents a broken listener, invalid fixture
setup or universally failing client from being reported as rejection evidence.
The ephemeral local port is a test endpoint; the RMAPL request planner continues
to declare HTTPS port 443.

Fixtures are generated each run with distinct keys, a localhost DNS SAN, and
server-auth usage. Validity windows have a two-day margin around the run clock;
no machine clock is changed. There are no remote AIA/CDP dependencies. The test
peer serves TLS 1.2 to remain inside the existing bounded client profile. This
does not change the client's system-default TLS policy or prove TLS 1.3 support.

Only the disposable GitHub-hosted Windows runner temporarily trusts the two
self-signed endpoint fixtures needed to isolate name/time rejection. The harness
refuses other environments and non-administrator accounts, uses LocalMachine Root
on that disposable runner, records only its own created
certificates for removal, verifies removal in `finally`, and deletes the fixture
directory/private keys. The untrusted fixture is never installed. No production
custom-CA option, alternate chain engine, certificate-ignore flag, validation
callback bypass, revocation disablement, or trust-store modification is added.
The explicit probe and loopback checks are complementary, not independent
implementations. Revocation availability and compromised roots are outside this
finite fixture set.

The first harness run, [36795336889](https://github.com/redogit/Other-Projects-/actions/runs/36795336889),
passed strict compilation and portable regressions but stalled during controlled
fixture setup/testing. The initial CurrentUser Root provisioning was suspect:
[the .NET runtime issue](https://github.com/dotnet/runtime/issues/24160) documents
its interactive trust dialog. The harness now uses administrator machine-store
provisioning on the disposable runner, logs each stage and bounds the step at
three minutes. It does not automate or suppress a trust dialog. Timeout or forced
job termination can preclude `finally`; the hosted runner is then discarded.

## Session and admission boundaries

A TLS carrier error previously escaped `drive_browser` and terminated the live
session. The new regression first reproduced that failure. The router now returns
`tls-carrier-failed:<detail>` with the original TLS residual; no response bytes
are injected and the existing main loop retains the last admitted view.

Session regressions compare source, DOM, layout, hit map, full camera including
pixels/PGM, current URL/page and history. They check zero plaintext-carrier calls
on TLS failure and on invalid decrypted HTTP, and one TLS call. Malformed and
non-200 decrypted responses reach the existing RMAPL gate and become
`http-response-invalid`; they never replace the admitted page. These portable
session checks use controlled carrier callbacks, while the Windows checks above
exercise actual certificate policy and encrypted sockets. Do not conflate them.

## Retained external failure

The latest inspected workflow at the source commit was
[run 36787338052](https://github.com/redogit/Other-Projects-/actions/runs/36787338052).
Its Windows build and credential self-test passed; `example.com:443` failed with
exit 68: `TLS renegotiation is outside bounded profile`. The decrypted-response
boundary step did not run. This remains a non-deterministic external smoke check
and is not negative certificate-policy evidence.

That historical failure is retained unchanged. Subsequent workflow revisions keep
the same external smoke but make it non-blocking: the step outcome is always
recorded and uploaded as `tls-external-smoke.json`, and decrypted HTTP bytes are
checked only when the smoke succeeds. Deterministic local certificate-policy,
loopback rejection, portable session, strict-build, and credential checks remain
hard merge gates. This does not relax certificate policy or add renegotiation
support merely to accommodate one external server behavior.

## Executed Windows evidence

[Run 36795934036](https://github.com/redogit/Other-Projects-/actions/runs/36795934036),
job `110159251951`, checked out exactly
`7f1b41b316914ace2ecc4d67494e8345aa09ed29`. Both `/W4 /WX` native builds, credential
self-test, all four controlled cases in the table, and fixture cleanup passed.
The three negatives returned the exact expected SSL policy and SChannel errors,
sent no application request and preserved the response sentinel. The positive
control returned the exact local response. The Windows request/session suites
passed 5/5 and 7/7 respectively. Local full-suite validation passed 239/239 tests,
and the existing audit/frozen stress checks passed.

The recorded run's overall TLS job **failed** afterwards on the separate
`example.com` smoke check with the same exit 68 renegotiation-profile residual.
Do not retroactively report that historical job as green or count that external
failure as deterministic evidence. Newer runs may be green while preserving an
external-smoke failure as a non-blocking recorded outcome; their deterministic
gates must be evaluated separately.

The original `tls-negative-receipt.json` is preserved byte-for-byte as
[`evidence/rmapl_tls_negative_7f1b41b.json`](../evidence/rmapl_tls_negative_7f1b41b.json).
It was retrieved from
[artifact 11133019218](https://github.com/redogit/Other-Projects-/actions/runs/36795934036/artifacts/11133019218).

- Downloaded ZIP SHA-256:
  `f40bb76e4f2ee19840050a16c50764d9bcaba058950b9fb067d50af3c0128587`
- Extracted receipt SHA-256:
  `196416e58577bfe477f7ef3162b24d5919cd4e320521a718b56627f5aed1c5bc`
- Job log: all fixture certificates removed at `2026-10-01T00:24:29Z`.

The archive commit changes only this report and the preserved receipt. The
executable test inputs are those of the recorded verification commit.

## Claim ceilings

- `TLS_HANDSHAKE_SUCCESS != RESPONSE_ADMISSION`
- `CERTIFICATE_POLICY_PASS != TRUSTED_PAGE_CONTENT`
- `SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION`
- Finite fixtures do not establish general TLS-client correctness or trustworthy
  page semantics. A retained admitted image is software state evidence, not a
  visual usability certification.

Policy error reference:
[Microsoft CERT_CHAIN_POLICY_STATUS](https://learn.microsoft.com/en-us/windows/win32/api/wincrypt/ns-wincrypt-cert_chain_policy_status).

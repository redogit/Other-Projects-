# Bounded negative TLS evidence — PR #107

Source: PR #107 at `73c9e807c9bc57db6bdf0c299a7f8eb7b5bcfe74`.
This increment adds executable checks; a checked-in harness is not a passing
Windows execution receipt. CI uploads `tls-negative-receipt.json` tagged with
the exact verification commit, including partial failures.

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
refuses other environments, uses CurrentUser Root, records only its own created
certificates for removal, verifies removal in `finally`, and deletes the fixture
directory/private keys. The untrusted fixture is never installed. No production
custom-CA option, alternate chain engine, certificate-ignore flag, validation
callback bypass, revocation disablement, or trust-store modification is added.
The explicit probe and loopback checks are complementary, not independent
implementations. Revocation availability and compromised roots are outside this
finite fixture set.

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
boundary step did not run. This remains a non-deterministic external smoke check,
still gating as before, and is not negative certificate-policy evidence. This
change does not relax the profile to conceal that failure.

## Claim ceilings

- `TLS_HANDSHAKE_SUCCESS != RESPONSE_ADMISSION`
- `CERTIFICATE_POLICY_PASS != TRUSTED_PAGE_CONTENT`
- `SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION`
- Finite fixtures do not establish general TLS-client correctness or trustworthy
  page semantics. A retained admitted image is software state evidence, not a
  visual usability certification.

Policy error reference:
[Microsoft CERT_CHAIN_POLICY_STATUS](https://learn.microsoft.com/en-us/windows/win32/api/wincrypt/ns-wincrypt-cert_chain_policy_status).

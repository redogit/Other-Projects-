# Bounded SChannel post-handshake continuation evidence — PR #109

Source execution head: `9a4d47a45a274ce4510801abdd88812a69d232ef`.

This increment addresses the previously retained `SEC_I_RENEGOTIATE` receive
boundary without changing certificate-ignore policy, trust-store selection,
request construction, response admission, or plaintext fallback behavior.

## Contract

Microsoft's Schannel documentation states that `DecryptMessage` can return
`SEC_I_RENEGOTIATE` for a post-handshake TLS protocol message and that a
client must return to `InitializeSecurityContext`, passing the
`DecryptMessage`-modified input as `SECBUFFER_TOKEN`.

References:

- https://learn.microsoft.com/en-us/windows/win32/secauthn/decryptmessage--schannel
- https://learn.microsoft.com/en-us/windows/win32/secauthn/initializesecuritycontext--schannel

The implementation remains bounded:

- at most 4 post-handshake messages per receive operation;
- at most 8 `InitializeSecurityContext` legs for one continuation;
- client-authentication requests remain outside the profile;
- `SEC_E_INCOMPLETE_MESSAGE` and `SECBUFFER_EXTRA` are handled explicitly;
- every completed continuation re-runs the existing explicit
  `CertGetCertificateChain` + `CertVerifyCertificateChainPolicy` hostname
  policy and refreshes `SECPKG_ATTR_STREAM_SIZES`;
- no certificate-ignore flag, custom CA, alternate trust engine, plaintext
  downgrade, or other network library was added.

## Controlled Windows execution

Workflow run:
https://github.com/redogit/Other-Projects-/actions/runs/36810196308

The production `win32_tls.exe` was compiled with `/W4 /WX` and exercised
against the existing disposable Windows certificate harness.

| Case | Protocol | Result |
|---|---|---|
| positive-control | TLS 1.2 | accepted, exact HTTP request/response |
| post-handshake-tls13 | TLS 1.3 | accepted, exact HTTP request/response, **2 bounded post-handshake continuations** |
| hostname-mismatch | TLS 1.2 | rejected with `CERT_E_CN_NO_MATCH` / `SEC_E_WRONG_PRINCIPAL` |
| untrusted-chain | TLS 1.2 | rejected with `CERT_E_UNTRUSTEDROOT` / `SEC_E_UNTRUSTED_ROOT` |
| expired | TLS 1.2 | rejected with `CERT_E_EXPIRED` / `SEC_E_CERT_EXPIRED` |

The TLS 1.3 positive peer requests two OpenSSL session tickets. The test requires
the production carrier to report at least one post-handshake continuation; the
recorded run reported exactly two.

All three negative certificate cases still:

- send no HTTP application request;
- leave the prior response-file sentinel unchanged;
- return the exact expected policy and SChannel errors;
- use the same system trust and explicit hostname policy as before.

Fixture certificates were removed successfully after the run.

Controlled evidence artifact:

- artifact id: `11139631622`
- artifact ZIP digest:
  `sha256:4aec7366244447cf6bc01293ebcd12a0dd010e57ed02b097c1cdfc7d5cc1802a`
- receipt schema: `rmapl-controlled-tls-evidence/v2`

## External smoke

The separate `example.com:443` smoke also succeeded on the same source head.
The carrier reported **1 post-handshake continuation**, and the subsequent
workflow boundary verified that the decrypted bytes begin with the bounded
`HTTP/1.1 200 ` response form.

This is supporting, non-deterministic evidence only. It is not used to establish
certificate-rejection behavior or general TLS correctness.

External-smoke artifact:

- artifact id: `11139751061`
- artifact ZIP digest:
  `sha256:de8e6ed638d2f179cb1acf7d1946af715b261f3de970bc3948422842182be026`

## Evidence boundaries

- `POST_HANDSHAKE_CONTINUATION != GENERAL_TLS_RENEGOTIATION_SUPPORT`
- `TLS_HANDSHAKE_SUCCESS != RESPONSE_ADMISSION`
- `CERTIFICATE_POLICY_PASS != TRUSTED_PAGE_CONTENT`
- `EXTERNAL_SMOKE_SUCCESS != SECURITY_CERTIFICATION`
- `SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION`

The browser still admits decrypted content only through the existing RMAPL HTTP
response-admission gate.

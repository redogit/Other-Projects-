/* Test-only certificate acquisition seam. The chain builder, SSL policy and
 * rejection branch below are the exact static production implementation.
 * No flags, trust engines or certificate policy are overridden. */
#define SECURITY_WIN32
#define WIN32_LEAN_AND_MEAN
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <security.h>
#include <wincrypt.h>

static PCCERT_CONTEXT fixture_certificate;
static SECURITY_STATUS SEC_ENTRY fixture_query(
    PCtxtHandle context, unsigned long attribute, void *output
);

#define QueryContextAttributesW fixture_query
#define wmain carrier_wmain
#include "win32_tls.c"
#undef wmain
#undef QueryContextAttributesW

static SECURITY_STATUS SEC_ENTRY fixture_query(
    PCtxtHandle context, unsigned long attribute, void *output
) {
    (void)context;
    if (attribute != SECPKG_ATTR_REMOTE_CERT_CONTEXT) return SEC_E_UNSUPPORTED_FUNCTION;
    *(PCCERT_CONTEXT *)output = CertDuplicateCertificateContext(fixture_certificate);
    return SEC_E_OK;
}

int wmain(int argc, wchar_t **argv) {
    ByteBuffer der = {0};
    wchar_t error[512] = {0};
    wchar_t expected_error[128];
    wchar_t *end = NULL;
    unsigned long expected;
    CtxtHandle unused;
    int accepted;
    int matched;
    if (argc != 4) return 64;
    expected = wcstoul(argv[3], &end, 16);
    if (!argv[3][0] || !end || *end) return 64;
    if (!read_file_bytes(argv[1], 65536, &der, error, 512)) return 65;
    fixture_certificate = CertCreateCertificateContext(
        X509_ASN_ENCODING, der.data, (DWORD)der.size);
    buffer_free(&der);
    if (!fixture_certificate) return 66;
    SecInvalidateHandle(&unused);
    accepted = validate_remote_certificate(&unused, argv[2], error, 512);
    _snwprintf_s(expected_error, 128, _TRUNCATE,
        L"TLS certificate policy rejected server: 0x%08lx", expected);
    matched = expected == 0 ? accepted : (!accepted && wcscmp(error, expected_error) == 0);
    wprintf(L"explicit-policy host=%ls expected=0x%08lx accepted=%d detail=%ls\n",
        argv[2], expected, accepted, error);
    CertFreeCertificateContext(fixture_certificate);
    return matched ? 0 : 1;
}

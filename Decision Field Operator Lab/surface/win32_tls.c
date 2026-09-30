#define SECURITY_WIN32
#define WIN32_LEAN_AND_MEAN
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <security.h>
#include <schannel.h>
#include <wincrypt.h>
#include <stdint.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "secur32.lib")
#pragma comment(lib, "crypt32.lib")

typedef struct ByteBuffer {
    uint8_t *data;
    size_t size;
    size_t capacity;
} ByteBuffer;

typedef struct TlsClient {
    SOCKET socket_handle;
    CredHandle credentials;
    CtxtHandle context;
    int credentials_valid;
    int context_valid;
    SecPkgContext_StreamSizes stream_sizes;
    ByteBuffer pending_encrypted;
} TlsClient;

static void buffer_free(ByteBuffer *buffer) {
    if (!buffer) return;
    free(buffer->data);
    buffer->data = NULL;
    buffer->size = 0;
    buffer->capacity = 0;
}

static int buffer_reserve(ByteBuffer *buffer, size_t needed, size_t hard_limit) {
    size_t next = 0;
    uint8_t *grown = NULL;
    if (!buffer || needed > hard_limit) return 0;
    if (needed <= buffer->capacity) return 1;

    next = buffer->capacity ? buffer->capacity : 8192;
    while (next < needed) {
        size_t doubled = next * 2;
        if (doubled < next || doubled > hard_limit) {
            next = hard_limit;
            break;
        }
        next = doubled;
    }
    if (next < needed) return 0;
    grown = (uint8_t *)realloc(buffer->data, next);
    if (!grown) return 0;
    buffer->data = grown;
    buffer->capacity = next;
    return 1;
}

static int buffer_append(
    ByteBuffer *buffer,
    const void *data,
    size_t size,
    size_t hard_limit
) {
    if (!buffer || (!data && size)) return 0;
    if (size > hard_limit - buffer->size) return 0;
    if (!buffer_reserve(buffer, buffer->size + size, hard_limit)) return 0;
    if (size) memcpy(buffer->data + buffer->size, data, size);
    buffer->size += size;
    return 1;
}

static int read_file_bytes(
    const wchar_t *path,
    size_t max_bytes,
    ByteBuffer *out,
    wchar_t *error,
    size_t error_cap
) {
    FILE *file = NULL;
    __int64 length = 0;
    if (_wfopen_s(&file, path, L"rb") != 0 || !file) {
        wcsncpy_s(error, error_cap, L"could not open request file", _TRUNCATE);
        return 0;
    }
    if (_fseeki64(file, 0, SEEK_END) != 0) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"could not seek request file", _TRUNCATE);
        return 0;
    }
    length = _ftelli64(file);
    if (length <= 0 || (uint64_t)length > (uint64_t)max_bytes) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"request size outside bounds", _TRUNCATE);
        return 0;
    }
    if (_fseeki64(file, 0, SEEK_SET) != 0) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"could not rewind request file", _TRUNCATE);
        return 0;
    }
    if (!buffer_reserve(out, (size_t)length, max_bytes)) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"request allocation failed", _TRUNCATE);
        return 0;
    }
    if (fread(out->data, 1, (size_t)length, file) != (size_t)length) {
        fclose(file);
        buffer_free(out);
        wcsncpy_s(error, error_cap, L"could not read complete request", _TRUNCATE);
        return 0;
    }
    fclose(file);
    out->size = (size_t)length;
    return 1;
}

static int write_file_bytes(
    const wchar_t *path,
    const ByteBuffer *buffer,
    wchar_t *error,
    size_t error_cap
) {
    FILE *file = NULL;
    if (!buffer || !buffer->data || !buffer->size) {
        wcsncpy_s(error, error_cap, L"refusing to write empty TLS response", _TRUNCATE);
        return 0;
    }
    if (_wfopen_s(&file, path, L"wb") != 0 || !file) {
        wcsncpy_s(error, error_cap, L"could not open TLS response output", _TRUNCATE);
        return 0;
    }
    if (fwrite(buffer->data, 1, buffer->size, file) != buffer->size) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"could not write complete TLS response", _TRUNCATE);
        return 0;
    }
    if (fclose(file) != 0) {
        wcsncpy_s(error, error_cap, L"could not close TLS response output", _TRUNCATE);
        return 0;
    }
    return 1;
}

static int wide_to_utf8(const wchar_t *input, char *output, int output_cap) {
    return WideCharToMultiByte(
        CP_UTF8,
        WC_ERR_INVALID_CHARS,
        input,
        -1,
        output,
        output_cap,
        NULL,
        NULL
    ) > 0;
}

static int send_all(SOCKET socket_handle, const uint8_t *data, size_t size) {
    size_t sent = 0;
    while (sent < size) {
        size_t remaining = size - sent;
        int chunk = remaining > INT_MAX ? INT_MAX : (int)remaining;
        int rc = send(socket_handle, (const char *)(data + sent), chunk, 0);
        if (rc == SOCKET_ERROR || rc == 0) return 0;
        sent += (size_t)rc;
    }
    return 1;
}

static int recv_append(
    SOCKET socket_handle,
    ByteBuffer *buffer,
    size_t hard_limit,
    int *closed
) {
    uint8_t temp[16384];
    int rc = recv(socket_handle, (char *)temp, (int)sizeof(temp), 0);
    if (rc == 0) {
        *closed = 1;
        return 1;
    }
    if (rc == SOCKET_ERROR) return 0;
    return buffer_append(buffer, temp, (size_t)rc, hard_limit);
}

static int connect_host(
    const char *host,
    const char *port,
    SOCKET *out_socket,
    wchar_t *error,
    size_t error_cap
) {
    struct addrinfo hints;
    struct addrinfo *results = NULL;
    struct addrinfo *item = NULL;
    SOCKET connected = INVALID_SOCKET;
    DWORD timeout_ms = 5000;
    int rc = 0;

    ZeroMemory(&hints, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    rc = getaddrinfo(host, port, &hints, &results);
    if (rc != 0 || !results) {
        wcsncpy_s(error, error_cap, L"TLS address resolution failed", _TRUNCATE);
        return 0;
    }

    for (item = results; item; item = item->ai_next) {
        SOCKET candidate = socket(item->ai_family, item->ai_socktype, item->ai_protocol);
        if (candidate == INVALID_SOCKET) continue;
        setsockopt(candidate, SOL_SOCKET, SO_RCVTIMEO, (const char *)&timeout_ms, sizeof(timeout_ms));
        setsockopt(candidate, SOL_SOCKET, SO_SNDTIMEO, (const char *)&timeout_ms, sizeof(timeout_ms));
        if (connect(candidate, item->ai_addr, (int)item->ai_addrlen) == 0) {
            connected = candidate;
            break;
        }
        closesocket(candidate);
    }
    freeaddrinfo(results);

    if (connected == INVALID_SOCKET) {
        wcsncpy_s(error, error_cap, L"TLS could not connect to resolved host", _TRUNCATE);
        return 0;
    }
    *out_socket = connected;
    return 1;
}

static void tls_client_init(TlsClient *client) {
    ZeroMemory(client, sizeof(*client));
    client->socket_handle = INVALID_SOCKET;
    SecInvalidateHandle(&client->credentials);
    SecInvalidateHandle(&client->context);
}

static void tls_client_free(TlsClient *client) {
    if (!client) return;
    if (client->context_valid) {
        DeleteSecurityContext(&client->context);
        client->context_valid = 0;
    }
    if (client->credentials_valid) {
        FreeCredentialsHandle(&client->credentials);
        client->credentials_valid = 0;
    }
    if (client->socket_handle != INVALID_SOCKET) {
        closesocket(client->socket_handle);
        client->socket_handle = INVALID_SOCKET;
    }
    buffer_free(&client->pending_encrypted);
}

static int send_schannel_output(
    SOCKET socket_handle,
    SecBuffer *buffer,
    wchar_t *error,
    size_t error_cap
) {
    int ok = 1;
    if (buffer->pvBuffer && buffer->cbBuffer) {
        ok = send_all(socket_handle, (const uint8_t *)buffer->pvBuffer, buffer->cbBuffer);
        if (!ok) {
            wcsncpy_s(error, error_cap, L"TLS handshake send failed", _TRUNCATE);
        }
    }
    if (buffer->pvBuffer) {
        FreeContextBuffer(buffer->pvBuffer);
        buffer->pvBuffer = NULL;
        buffer->cbBuffer = 0;
    }
    return ok;
}

static int validate_remote_certificate(
    CtxtHandle *context,
    const wchar_t *host,
    wchar_t *error,
    size_t error_cap
) {
    PCCERT_CONTEXT certificate = NULL;
    PCCERT_CHAIN_CONTEXT chain = NULL;
    CERT_CHAIN_PARA chain_para;
    SSL_EXTRA_CERT_CHAIN_POLICY_PARA ssl_para;
    CERT_CHAIN_POLICY_PARA policy_para;
    CERT_CHAIN_POLICY_STATUS policy_status;
    SECURITY_STATUS sec_status = SEC_E_INTERNAL_ERROR;
    int ok = 0;

    ZeroMemory(&chain_para, sizeof(chain_para));
    ZeroMemory(&ssl_para, sizeof(ssl_para));
    ZeroMemory(&policy_para, sizeof(policy_para));
    ZeroMemory(&policy_status, sizeof(policy_status));

    sec_status = QueryContextAttributesW(
        context,
        SECPKG_ATTR_REMOTE_CERT_CONTEXT,
        &certificate
    );
    if (sec_status != SEC_E_OK || !certificate) {
        wcsncpy_s(error, error_cap, L"TLS remote certificate unavailable", _TRUNCATE);
        goto cleanup;
    }

    chain_para.cbSize = sizeof(chain_para);
    if (!CertGetCertificateChain(
            NULL,
            certificate,
            NULL,
            certificate->hCertStore,
            &chain_para,
            0,
            NULL,
            &chain)) {
        wcsncpy_s(error, error_cap, L"TLS certificate chain construction failed", _TRUNCATE);
        goto cleanup;
    }

    ssl_para.cbSize = sizeof(ssl_para);
    ssl_para.dwAuthType = AUTHTYPE_SERVER;
    ssl_para.fdwChecks = 0;
    ssl_para.pwszServerName = (LPWSTR)host;

    policy_para.cbSize = sizeof(policy_para);
    policy_para.pvExtraPolicyPara = &ssl_para;

    policy_status.cbSize = sizeof(policy_status);
    if (!CertVerifyCertificateChainPolicy(
            CERT_CHAIN_POLICY_SSL,
            chain,
            &policy_para,
            &policy_status)) {
        wcsncpy_s(error, error_cap, L"TLS certificate policy execution failed", _TRUNCATE);
        goto cleanup;
    }
    if (policy_status.dwError != 0) {
        _snwprintf_s(
            error,
            error_cap,
            _TRUNCATE,
            L"TLS certificate policy rejected server: 0x%08lx",
            policy_status.dwError
        );
        goto cleanup;
    }
    ok = 1;

cleanup:
    if (chain) CertFreeCertificateChain(chain);
    if (certificate) CertFreeCertificateContext(certificate);
    return ok;
}

static int tls_handshake(
    TlsClient *client,
    const wchar_t *host_w,
    const char *host_a,
    const char *port_a,
    wchar_t *error,
    size_t error_cap
) {
    SCH_CREDENTIALS sch_credentials;
    TimeStamp expiry;
    SECURITY_STATUS status = SEC_E_INTERNAL_ERROR;
    ULONG context_attr = 0;
    DWORD requirements =
        ISC_REQ_SEQUENCE_DETECT |
        ISC_REQ_REPLAY_DETECT |
        ISC_REQ_CONFIDENTIALITY |
        ISC_REQ_EXTENDED_ERROR |
        ISC_REQ_ALLOCATE_MEMORY |
        ISC_REQ_STREAM |
        ISC_REQ_USE_SUPPLIED_CREDS;
    SecBuffer out_buffer;
    SecBufferDesc out_desc;
    const size_t handshake_limit = 1024U * 1024U;
    int closed = 0;

    ZeroMemory(&sch_credentials, sizeof(sch_credentials));
    sch_credentials.dwVersion = SCH_CREDENTIALS_VERSION;
    sch_credentials.dwFlags =
        SCH_CRED_AUTO_CRED_VALIDATION |
        SCH_CRED_NO_DEFAULT_CREDS |
        SCH_CRED_REVOCATION_CHECK_CHAIN_EXCLUDE_ROOT;

    status = AcquireCredentialsHandleW(
        NULL,
        UNISP_NAME_W,
        SECPKG_CRED_OUTBOUND,
        NULL,
        &sch_credentials,
        NULL,
        NULL,
        &client->credentials,
        &expiry
    );
    if (status != SEC_E_OK) {
        _snwprintf_s(error, error_cap, _TRUNCATE, L"AcquireCredentialsHandle failed: 0x%08lx", status);
        return 0;
    }
    client->credentials_valid = 1;

    if (!connect_host(host_a, port_a, &client->socket_handle, error, error_cap)) {
        return 0;
    }

    ZeroMemory(&out_buffer, sizeof(out_buffer));
    out_buffer.BufferType = SECBUFFER_TOKEN;
    out_desc.ulVersion = SECBUFFER_VERSION;
    out_desc.cBuffers = 1;
    out_desc.pBuffers = &out_buffer;

    status = InitializeSecurityContextW(
        &client->credentials,
        NULL,
        (SEC_WCHAR *)host_w,
        requirements,
        0,
        SECURITY_NATIVE_DREP,
        NULL,
        0,
        &client->context,
        &out_desc,
        &context_attr,
        &expiry
    );
    if (status != SEC_I_CONTINUE_NEEDED && status != SEC_E_OK) {
        if (out_buffer.pvBuffer) FreeContextBuffer(out_buffer.pvBuffer);
        _snwprintf_s(error, error_cap, _TRUNCATE, L"initial TLS context failed: 0x%08lx", status);
        return 0;
    }
    client->context_valid = 1;
    if (!send_schannel_output(client->socket_handle, &out_buffer, error, error_cap)) {
        return 0;
    }

    while (status != SEC_E_OK) {
        SecBuffer in_buffers[2];
        SecBufferDesc in_desc;

        if (client->pending_encrypted.size == 0 || status == SEC_E_INCOMPLETE_MESSAGE) {
            closed = 0;
            if (!recv_append(
                    client->socket_handle,
                    &client->pending_encrypted,
                    handshake_limit,
                    &closed)) {
                wcsncpy_s(error, error_cap, L"TLS handshake receive failed", _TRUNCATE);
                return 0;
            }
            if (closed) {
                wcsncpy_s(error, error_cap, L"TLS peer closed during handshake", _TRUNCATE);
                return 0;
            }
        }

        ZeroMemory(in_buffers, sizeof(in_buffers));
        in_buffers[0].BufferType = SECBUFFER_TOKEN;
        in_buffers[0].pvBuffer = client->pending_encrypted.data;
        in_buffers[0].cbBuffer = (unsigned long)client->pending_encrypted.size;
        in_buffers[1].BufferType = SECBUFFER_EMPTY;

        in_desc.ulVersion = SECBUFFER_VERSION;
        in_desc.cBuffers = 2;
        in_desc.pBuffers = in_buffers;

        ZeroMemory(&out_buffer, sizeof(out_buffer));
        out_buffer.BufferType = SECBUFFER_TOKEN;

        status = InitializeSecurityContextW(
            &client->credentials,
            &client->context,
            (SEC_WCHAR *)host_w,
            requirements,
            0,
            SECURITY_NATIVE_DREP,
            &in_desc,
            0,
            NULL,
            &out_desc,
            &context_attr,
            &expiry
        );

        if (!send_schannel_output(client->socket_handle, &out_buffer, error, error_cap)) {
            return 0;
        }

        if (status == SEC_E_INCOMPLETE_MESSAGE) {
            continue;
        }

        if (status != SEC_I_CONTINUE_NEEDED && status != SEC_E_OK) {
            _snwprintf_s(error, error_cap, _TRUNCATE, L"TLS handshake failed: 0x%08lx", status);
            return 0;
        }

        if (in_buffers[1].BufferType == SECBUFFER_EXTRA && in_buffers[1].cbBuffer) {
            size_t extra = in_buffers[1].cbBuffer;
            if (extra > client->pending_encrypted.size) {
                wcsncpy_s(error, error_cap, L"TLS handshake returned invalid extra buffer", _TRUNCATE);
                return 0;
            }
            memmove(
                client->pending_encrypted.data,
                client->pending_encrypted.data + client->pending_encrypted.size - extra,
                extra
            );
            client->pending_encrypted.size = extra;
        } else {
            client->pending_encrypted.size = 0;
        }
    }

    if (!validate_remote_certificate(&client->context, host_w, error, error_cap)) {
        return 0;
    }

    status = QueryContextAttributesW(
        &client->context,
        SECPKG_ATTR_STREAM_SIZES,
        &client->stream_sizes
    );
    if (status != SEC_E_OK) {
        _snwprintf_s(error, error_cap, _TRUNCATE, L"TLS stream size query failed: 0x%08lx", status);
        return 0;
    }
    if (!client->stream_sizes.cbMaximumMessage) {
        wcsncpy_s(error, error_cap, L"TLS stream maximum message is zero", _TRUNCATE);
        return 0;
    }
    return 1;
}

static int tls_send_plaintext(
    TlsClient *client,
    const uint8_t *data,
    size_t size,
    wchar_t *error,
    size_t error_cap
) {
    size_t offset = 0;
    const SecPkgContext_StreamSizes *sizes = &client->stream_sizes;

    while (offset < size) {
        size_t remaining = size - offset;
        size_t chunk = remaining;
        size_t total = 0;
        uint8_t *record = NULL;
        SecBuffer buffers[4];
        SecBufferDesc desc;
        SECURITY_STATUS status = SEC_E_INTERNAL_ERROR;

        if (chunk > sizes->cbMaximumMessage) chunk = sizes->cbMaximumMessage;
        if (chunk > SIZE_MAX - sizes->cbHeader ||
            chunk + sizes->cbHeader > SIZE_MAX - sizes->cbTrailer) {
            wcsncpy_s(error, error_cap, L"TLS record size overflow", _TRUNCATE);
            return 0;
        }
        total = sizes->cbHeader + chunk + sizes->cbTrailer;
        record = (uint8_t *)malloc(total);
        if (!record) {
            wcsncpy_s(error, error_cap, L"TLS record allocation failed", _TRUNCATE);
            return 0;
        }

        memcpy(record + sizes->cbHeader, data + offset, chunk);
        ZeroMemory(buffers, sizeof(buffers));
        buffers[0].BufferType = SECBUFFER_STREAM_HEADER;
        buffers[0].pvBuffer = record;
        buffers[0].cbBuffer = sizes->cbHeader;
        buffers[1].BufferType = SECBUFFER_DATA;
        buffers[1].pvBuffer = record + sizes->cbHeader;
        buffers[1].cbBuffer = (unsigned long)chunk;
        buffers[2].BufferType = SECBUFFER_STREAM_TRAILER;
        buffers[2].pvBuffer = record + sizes->cbHeader + chunk;
        buffers[2].cbBuffer = sizes->cbTrailer;
        buffers[3].BufferType = SECBUFFER_EMPTY;

        desc.ulVersion = SECBUFFER_VERSION;
        desc.cBuffers = 4;
        desc.pBuffers = buffers;

        status = EncryptMessage(&client->context, 0, &desc, 0);
        if (status != SEC_E_OK) {
            free(record);
            _snwprintf_s(error, error_cap, _TRUNCATE, L"TLS EncryptMessage failed: 0x%08lx", status);
            return 0;
        }

        total =
            (size_t)buffers[0].cbBuffer +
            (size_t)buffers[1].cbBuffer +
            (size_t)buffers[2].cbBuffer;
        if (!send_all(client->socket_handle, record, total)) {
            free(record);
            wcsncpy_s(error, error_cap, L"TLS encrypted send failed", _TRUNCATE);
            return 0;
        }
        free(record);
        offset += chunk;
    }
    return 1;
}

static int tls_receive_plaintext(
    TlsClient *client,
    size_t max_plaintext,
    ByteBuffer *plaintext,
    wchar_t *error,
    size_t error_cap
) {
    size_t encrypted_limit = max_plaintext + 1024U * 1024U;
    int saw_close_notify = 0;

    if (encrypted_limit < max_plaintext) {
        wcsncpy_s(error, error_cap, L"TLS encrypted buffer bound overflow", _TRUNCATE);
        return 0;
    }

    for (;;) {
        SECURITY_STATUS status = SEC_E_INCOMPLETE_MESSAGE;
        SecBuffer buffers[4];
        SecBufferDesc desc;
        size_t extra = 0;
        int closed = 0;
        int have_data = 0;

        if (client->pending_encrypted.size == 0) {
            if (!recv_append(
                    client->socket_handle,
                    &client->pending_encrypted,
                    encrypted_limit,
                    &closed)) {
                wcsncpy_s(error, error_cap, L"TLS encrypted receive failed", _TRUNCATE);
                return 0;
            }
            if (closed) {
                if (saw_close_notify) break;
                wcsncpy_s(error, error_cap, L"TLS TCP close occurred without close_notify", _TRUNCATE);
                return 0;
            }
        }

        ZeroMemory(buffers, sizeof(buffers));
        buffers[0].BufferType = SECBUFFER_DATA;
        buffers[0].pvBuffer = client->pending_encrypted.data;
        buffers[0].cbBuffer = (unsigned long)client->pending_encrypted.size;
        buffers[1].BufferType = SECBUFFER_EMPTY;
        buffers[2].BufferType = SECBUFFER_EMPTY;
        buffers[3].BufferType = SECBUFFER_EMPTY;

        desc.ulVersion = SECBUFFER_VERSION;
        desc.cBuffers = 4;
        desc.pBuffers = buffers;

        status = DecryptMessage(&client->context, &desc, 0, NULL);

        if (status == SEC_E_INCOMPLETE_MESSAGE) {
            if (!recv_append(
                    client->socket_handle,
                    &client->pending_encrypted,
                    encrypted_limit,
                    &closed)) {
                wcsncpy_s(error, error_cap, L"TLS encrypted receive failed", _TRUNCATE);
                return 0;
            }
            if (closed) {
                wcsncpy_s(error, error_cap, L"TLS closed with incomplete record", _TRUNCATE);
                return 0;
            }
            continue;
        }

        if (status == SEC_I_CONTEXT_EXPIRED) {
            saw_close_notify = 1;
        } else if (status == SEC_I_RENEGOTIATE) {
            wcsncpy_s(error, error_cap, L"TLS renegotiation is outside bounded profile", _TRUNCATE);
            return 0;
        } else if (status != SEC_E_OK) {
            _snwprintf_s(error, error_cap, _TRUNCATE, L"TLS DecryptMessage failed: 0x%08lx", status);
            return 0;
        }

        for (int i = 1; i < 4; i++) {
            if (buffers[i].BufferType == SECBUFFER_DATA && buffers[i].cbBuffer) {
                if (!buffer_append(
                        plaintext,
                        buffers[i].pvBuffer,
                        buffers[i].cbBuffer,
                        max_plaintext)) {
                    wcsncpy_s(error, error_cap, L"TLS plaintext exceeded declared bound", _TRUNCATE);
                    return 0;
                }
                have_data = 1;
            } else if (buffers[i].BufferType == SECBUFFER_EXTRA && buffers[i].cbBuffer) {
                extra = buffers[i].cbBuffer;
            }
        }

        if (extra) {
            if (extra > client->pending_encrypted.size) {
                wcsncpy_s(error, error_cap, L"TLS decrypt returned invalid extra buffer", _TRUNCATE);
                return 0;
            }
            memmove(
                client->pending_encrypted.data,
                client->pending_encrypted.data + client->pending_encrypted.size - extra,
                extra
            );
            client->pending_encrypted.size = extra;
        } else {
            client->pending_encrypted.size = 0;
        }

        if (saw_close_notify) {
            if (client->pending_encrypted.size != 0) {
                wcsncpy_s(error, error_cap, L"TLS bytes remained after close_notify", _TRUNCATE);
                return 0;
            }
            break;
        }

        if (!have_data && client->pending_encrypted.size == 0) {
            continue;
        }
    }

    if (!plaintext->size) {
        wcsncpy_s(error, error_cap, L"TLS produced empty plaintext response", _TRUNCATE);
        return 0;
    }
    return 1;
}

static int tls_transport(
    const wchar_t *host_w,
    const char *host_a,
    const char *port_a,
    const ByteBuffer *request,
    size_t max_response,
    ByteBuffer *response,
    wchar_t *error,
    size_t error_cap
) {
    TlsClient client;
    int ok = 0;
    tls_client_init(&client);

    if (!tls_handshake(&client, host_w, host_a, port_a, error, error_cap)) {
        goto cleanup;
    }
    if (!tls_send_plaintext(
            &client,
            request->data,
            request->size,
            error,
            error_cap)) {
        goto cleanup;
    }
    if (!tls_receive_plaintext(
            &client,
            max_response,
            response,
            error,
            error_cap)) {
        goto cleanup;
    }
    ok = 1;

cleanup:
    tls_client_free(&client);
    return ok;
}

static int self_test_credentials(void) {
    SCH_CREDENTIALS sch_credentials;
    CredHandle credentials;
    TimeStamp expiry;
    SECURITY_STATUS status = SEC_E_INTERNAL_ERROR;

    ZeroMemory(&sch_credentials, sizeof(sch_credentials));
    SecInvalidateHandle(&credentials);
    sch_credentials.dwVersion = SCH_CREDENTIALS_VERSION;
    sch_credentials.dwFlags =
        SCH_CRED_AUTO_CRED_VALIDATION |
        SCH_CRED_NO_DEFAULT_CREDS |
        SCH_CRED_REVOCATION_CHECK_CHAIN_EXCLUDE_ROOT;

    status = AcquireCredentialsHandleW(
        NULL,
        UNISP_NAME_W,
        SECPKG_CRED_OUTBOUND,
        NULL,
        &sch_credentials,
        NULL,
        NULL,
        &credentials,
        &expiry
    );
    if (status != SEC_E_OK) {
        fwprintf(stderr, L"SChannel credential self-test failed: 0x%08lx\n", status);
        return 1;
    }
    FreeCredentialsHandle(&credentials);
    wprintf(L"win32 TLS credential self-test PASS\n");
    return 0;
}

int wmain(int argc, wchar_t **argv) {
    WSADATA wsa;
    wchar_t error[512] = {0};
    char host_a[1024];
    char port_a[32];
    ByteBuffer request = {0};
    ByteBuffer response = {0};
    unsigned long max_response = 0;
    wchar_t *end = NULL;
    int result = 1;

    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        fwprintf(stderr, L"WSAStartup failed\n");
        return 70;
    }

    if (argc == 2 && wcscmp(argv[1], L"--self-test") == 0) {
        result = self_test_credentials();
        WSACleanup();
        return result;
    }

    if (argc != 11 ||
        wcscmp(argv[1], L"--host") != 0 ||
        wcscmp(argv[3], L"--port") != 0 ||
        wcscmp(argv[5], L"--request") != 0 ||
        wcscmp(argv[7], L"--out") != 0 ||
        wcscmp(argv[9], L"--max") != 0) {
        fwprintf(
            stderr,
            L"usage: win32_tls.exe --host <host> --port <port> "
            L"--request <request.bin> --out <response.bin> --max <bytes>\n"
            L"       win32_tls.exe --self-test\n"
        );
        WSACleanup();
        return 64;
    }

    if (!wide_to_utf8(argv[2], host_a, (int)sizeof(host_a)) ||
        !wide_to_utf8(argv[4], port_a, (int)sizeof(port_a))) {
        fwprintf(stderr, L"TLS host or port conversion failed\n");
        WSACleanup();
        return 65;
    }

    max_response = wcstoul(argv[10], &end, 10);
    if (!argv[10][0] || !end || *end != L'\0' ||
        max_response == 0 || max_response > 16UL * 1024UL * 1024UL) {
        fwprintf(stderr, L"max response must be in [1,16777216]\n");
        WSACleanup();
        return 66;
    }

    if (!read_file_bytes(argv[6], 1024UL * 1024UL, &request, error, 512)) {
        fwprintf(stderr, L"%ls\n", error);
        WSACleanup();
        return 67;
    }

    if (!tls_transport(
            argv[2],
            host_a,
            port_a,
            &request,
            (size_t)max_response,
            &response,
            error,
            512)) {
        fwprintf(stderr, L"%ls\n", error);
        buffer_free(&request);
        buffer_free(&response);
        WSACleanup();
        return 68;
    }

    if (!write_file_bytes(argv[8], &response, error, 512)) {
        fwprintf(stderr, L"%ls\n", error);
        buffer_free(&request);
        buffer_free(&response);
        WSACleanup();
        return 69;
    }

    buffer_free(&request);
    buffer_free(&response);
    WSACleanup();
    return 0;
}

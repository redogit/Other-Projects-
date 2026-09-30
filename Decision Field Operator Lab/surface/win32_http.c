#define WIN32_LEAN_AND_MEAN
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdint.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#pragma comment(lib, "ws2_32.lib")

typedef struct ByteBuffer {
    uint8_t *data;
    size_t size;
} ByteBuffer;

typedef struct LoopbackServer {
    SOCKET listener;
    HANDLE ready;
    int ok;
} LoopbackServer;

static void buffer_free(ByteBuffer *buffer) {
    if (!buffer) return;
    free(buffer->data);
    buffer->data = NULL;
    buffer->size = 0;
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
    uint8_t *data = NULL;

    if (!path || !out) return 0;
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
    data = (uint8_t *)malloc((size_t)length);
    if (!data) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"request allocation failed", _TRUNCATE);
        return 0;
    }
    if (fread(data, 1, (size_t)length, file) != (size_t)length) {
        free(data);
        fclose(file);
        wcsncpy_s(error, error_cap, L"could not read complete request file", _TRUNCATE);
        return 0;
    }
    fclose(file);
    out->data = data;
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
    if (!path || !buffer || !buffer->data) return 0;
    if (_wfopen_s(&file, path, L"wb") != 0 || !file) {
        wcsncpy_s(error, error_cap, L"could not open response output", _TRUNCATE);
        return 0;
    }
    if (fwrite(buffer->data, 1, buffer->size, file) != buffer->size) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"could not write complete response", _TRUNCATE);
        return 0;
    }
    if (fclose(file) != 0) {
        wcsncpy_s(error, error_cap, L"could not close response output", _TRUNCATE);
        return 0;
    }
    return 1;
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

static int recv_bounded(
    SOCKET socket_handle,
    size_t max_bytes,
    ByteBuffer *out,
    wchar_t *error,
    size_t error_cap
) {
    size_t capacity = max_bytes < 8192 ? max_bytes : 8192;
    size_t used = 0;
    uint8_t *data = NULL;

    if (max_bytes == 0) {
        wcsncpy_s(error, error_cap, L"max response bytes must be positive", _TRUNCATE);
        return 0;
    }
    data = (uint8_t *)malloc(capacity);
    if (!data) {
        wcsncpy_s(error, error_cap, L"response allocation failed", _TRUNCATE);
        return 0;
    }

    for (;;) {
        if (used == capacity) {
            size_t next = capacity * 2;
            uint8_t *grown = NULL;
            if (next < capacity || next > max_bytes) next = max_bytes;
            if (next == capacity) {
                free(data);
                wcsncpy_s(error, error_cap, L"response exceeded declared byte bound", _TRUNCATE);
                return 0;
            }
            grown = (uint8_t *)realloc(data, next);
            if (!grown) {
                free(data);
                wcsncpy_s(error, error_cap, L"response reallocation failed", _TRUNCATE);
                return 0;
            }
            data = grown;
            capacity = next;
        }

        {
            size_t available = capacity - used;
            int chunk = available > INT_MAX ? INT_MAX : (int)available;
            int rc = recv(socket_handle, (char *)(data + used), chunk, 0);
            if (rc == 0) break;
            if (rc == SOCKET_ERROR) {
                free(data);
                wcsncpy_s(error, error_cap, L"socket receive failed", _TRUNCATE);
                return 0;
            }
            used += (size_t)rc;
        }
    }

    if (used == 0) {
        free(data);
        wcsncpy_s(error, error_cap, L"empty response", _TRUNCATE);
        return 0;
    }
    out->data = data;
    out->size = used;
    return 1;
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
        wcsncpy_s(error, error_cap, L"address resolution failed", _TRUNCATE);
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
        wcsncpy_s(error, error_cap, L"could not connect to any resolved address", _TRUNCATE);
        return 0;
    }
    *out_socket = connected;
    return 1;
}

static int http_transport(
    const char *host,
    const char *port,
    const ByteBuffer *request,
    size_t max_response_bytes,
    ByteBuffer *response,
    wchar_t *error,
    size_t error_cap
) {
    SOCKET socket_handle = INVALID_SOCKET;
    if (!host || !*host || !port || !*port || !request || !request->data || !request->size) {
        wcsncpy_s(error, error_cap, L"invalid transport arguments", _TRUNCATE);
        return 0;
    }
    if (!connect_host(host, port, &socket_handle, error, error_cap)) return 0;
    if (!send_all(socket_handle, request->data, request->size)) {
        closesocket(socket_handle);
        wcsncpy_s(error, error_cap, L"socket send failed", _TRUNCATE);
        return 0;
    }
    shutdown(socket_handle, SD_SEND);
    if (!recv_bounded(socket_handle, max_response_bytes, response, error, error_cap)) {
        closesocket(socket_handle);
        return 0;
    }
    closesocket(socket_handle);
    return 1;
}

static DWORD WINAPI loopback_server_thread(LPVOID raw) {
    LoopbackServer *server = (LoopbackServer *)raw;
    static const char expected_prefix[] = "GET /test HTTP/1.1\r\n";
    static const char response[] =
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html\r\n"
        "Connection: close\r\n"
        "\r\n"
        "<h1>LOOPBACK</h1>";
    SOCKET client = INVALID_SOCKET;
    char request[2048];
    size_t used = 0;

    SetEvent(server->ready);
    client = accept(server->listener, NULL, NULL);
    if (client == INVALID_SOCKET) return 1;

    for (;;) {
        int rc = 0;
        size_t available = sizeof(request) - 1 - used;
        if (available == 0) {
            closesocket(client);
            return 2;
        }
        rc = recv(client, request + used, (int)available, 0);
        if (rc <= 0) {
            closesocket(client);
            return 2;
        }
        used += (size_t)rc;
        request[used] = '\0';
        if (strstr(request, "\r\n\r\n")) break;
    }

    if (strncmp(request, expected_prefix, strlen(expected_prefix)) != 0) {
        closesocket(client);
        return 3;
    }
    if (!send_all(client, (const uint8_t *)response, strlen(response))) {
        closesocket(client);
        return 4;
    }
    shutdown(client, SD_SEND);
    closesocket(client);
    server->ok = 1;
    return 0;
}

static int loopback_transport_test(const ByteBuffer *supplied_request) {
    SOCKET listener = INVALID_SOCKET;
    struct sockaddr_in address;
    int address_len = sizeof(address);
    LoopbackServer server;
    HANDLE thread = NULL;
    ByteBuffer request = {0};
    ByteBuffer response = {0};
    wchar_t error[256] = {0};
    char port[16];
    static const char request_text[] =
        "GET /test HTTP/1.1\r\n"
        "Host: 127.0.0.1\r\n"
        "Connection: close\r\n"
        "\r\n";
    static const char body_marker[] = "<h1>LOOPBACK</h1>";
    DWORD wait_rc = 0;
    int result = 1;

    ZeroMemory(&server, sizeof(server));
    ZeroMemory(&address, sizeof(address));

    listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (listener == INVALID_SOCKET) {
        fwprintf(stderr, L"self-test listener socket failed\n");
        goto cleanup;
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    address.sin_port = 0;
    if (bind(listener, (struct sockaddr *)&address, sizeof(address)) == SOCKET_ERROR ||
        listen(listener, 1) == SOCKET_ERROR ||
        getsockname(listener, (struct sockaddr *)&address, &address_len) == SOCKET_ERROR) {
        fwprintf(stderr, L"self-test loopback bind/listen failed\n");
        goto cleanup;
    }

    _snprintf_s(port, sizeof(port), _TRUNCATE, "%u", (unsigned)ntohs(address.sin_port));
    server.listener = listener;
    server.ready = CreateEventW(NULL, TRUE, FALSE, NULL);
    if (!server.ready) {
        fwprintf(stderr, L"self-test event creation failed\n");
        goto cleanup;
    }
    thread = CreateThread(NULL, 0, loopback_server_thread, &server, 0, NULL);
    if (!thread) {
        fwprintf(stderr, L"self-test thread creation failed\n");
        goto cleanup;
    }
    if (WaitForSingleObject(server.ready, 2000) != WAIT_OBJECT_0) {
        fwprintf(stderr, L"self-test server did not become ready\n");
        goto cleanup;
    }

    if (supplied_request) {
        request = *supplied_request;
    } else {
        request.data = (uint8_t *)request_text;
        request.size = strlen(request_text);
    }
    if (!http_transport("127.0.0.1", port, &request, 65536, &response, error, 256)) {
        fwprintf(stderr, L"self-test transport failed: %ls\n", error);
        goto cleanup;
    }
    {
        uint8_t *terminated = NULL;
        if (response.size < strlen(body_marker)) {
            fwprintf(stderr, L"self-test response body too short\n");
            goto cleanup;
        }
        terminated = (uint8_t *)realloc(response.data, response.size + 1);
        if (!terminated) {
            fwprintf(stderr, L"self-test response termination allocation failed\n");
            goto cleanup;
        }
        response.data = terminated;
        response.data[response.size] = 0;
        if (!strstr((const char *)response.data, body_marker)) {
            fwprintf(stderr, L"self-test response body mismatch\n");
            goto cleanup;
        }
    }
    wait_rc = WaitForSingleObject(thread, 2000);
    if (wait_rc != WAIT_OBJECT_0 || !server.ok) {
        fwprintf(stderr, L"self-test server verification failed\n");
        goto cleanup;
    }

    wprintf(L"win32 http transport self-test PASS\n");
    result = 0;

cleanup:
    buffer_free(&response);
    if (thread) {
        if (WaitForSingleObject(thread, 0) != WAIT_OBJECT_0) {
            closesocket(listener);
            WaitForSingleObject(thread, 1000);
            listener = INVALID_SOCKET;
        }
        CloseHandle(thread);
    }
    if (server.ready) CloseHandle(server.ready);
    if (listener != INVALID_SOCKET) closesocket(listener);
    return result;
}

static int self_test(void) {
    return loopback_transport_test(NULL);
}

static int wide_to_utf8(const wchar_t *input, char *output, int output_cap) {
    int count = WideCharToMultiByte(
        CP_UTF8,
        WC_ERR_INVALID_CHARS,
        input,
        -1,
        output,
        output_cap,
        NULL,
        NULL
    );
    return count > 0;
}

int wmain(int argc, wchar_t **argv) {
    WSADATA wsa;
    wchar_t error[256] = {0};
    char host[1024];
    char port[32];
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
        result = self_test();
        WSACleanup();
        return result;
    }
    if (argc == 3 && wcscmp(argv[1], L"--self-test-request") == 0) {
        ByteBuffer supplied = {0};
        if (!read_file_bytes(argv[2], 1024UL * 1024UL, &supplied, error, 256)) {
            fwprintf(stderr, L"%ls\n", error);
            WSACleanup();
            return 72;
        }
        result = loopback_transport_test(&supplied);
        buffer_free(&supplied);
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
            L"usage: win32_http.exe --host <host> --port <port> "
            L"--request <request.bin> --out <response.bin> --max <bytes>\n"
            L"       win32_http.exe --self-test\n"
            L"       win32_http.exe --self-test-request <request.bin>\n"
        );
        WSACleanup();
        return 64;
    }

    if (!wide_to_utf8(argv[2], host, (int)sizeof(host)) ||
        !wide_to_utf8(argv[4], port, (int)sizeof(port))) {
        fwprintf(stderr, L"host or port conversion failed\n");
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

    if (!read_file_bytes(argv[6], 1024UL * 1024UL, &request, error, 256)) {
        fwprintf(stderr, L"%ls\n", error);
        WSACleanup();
        return 67;
    }

    if (!http_transport(
            host,
            port,
            &request,
            (size_t)max_response,
            &response,
            error,
            256)) {
        fwprintf(stderr, L"%ls\n", error);
        buffer_free(&request);
        WSACleanup();
        return 68;
    }

    if (!write_file_bytes(argv[8], &response, error, 256)) {
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

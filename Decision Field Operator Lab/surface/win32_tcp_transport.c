#define WIN32_LEAN_AND_MEAN
#define UNICODE
#define _UNICODE
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <process.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#pragma comment(lib, "Ws2_32.lib")

typedef struct ByteBuffer {
    uint8_t *data;
    size_t length;
} ByteBuffer;

typedef struct SelfTestServer {
    SOCKET listener;
    int ok;
} SelfTestServer;

static void buffer_free(ByteBuffer *buffer) {
    if (!buffer) return;
    free(buffer->data);
    buffer->data = NULL;
    buffer->length = 0;
}

static int read_file(
    const wchar_t *path,
    ByteBuffer *out,
    wchar_t *error,
    size_t error_cap
) {
    FILE *file = NULL;
    __int64 length = 0;
    uint8_t *data = NULL;

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
    if (length <= 0 || length > 16LL * 1024LL * 1024LL) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"request file size outside bounds", _TRUNCATE);
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
    out->length = (size_t)length;
    return 1;
}

static int write_file(
    const wchar_t *path,
    const ByteBuffer *buffer,
    wchar_t *error,
    size_t error_cap
) {
    FILE *file = NULL;
    if (!buffer || !buffer->data) {
        wcsncpy_s(error, error_cap, L"response buffer is empty", _TRUNCATE);
        return 0;
    }
    if (_wfopen_s(&file, path, L"wb") != 0 || !file) {
        wcsncpy_s(error, error_cap, L"could not open response file", _TRUNCATE);
        return 0;
    }
    if (fwrite(buffer->data, 1, buffer->length, file) != buffer->length) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"could not write complete response file", _TRUNCATE);
        return 0;
    }
    if (fclose(file) != 0) {
        wcsncpy_s(error, error_cap, L"could not close response file", _TRUNCATE);
        return 0;
    }
    return 1;
}

static int send_all(
    SOCKET socket_handle,
    const uint8_t *data,
    size_t length,
    wchar_t *error,
    size_t error_cap
) {
    size_t sent = 0;
    while (sent < length) {
        size_t remaining = length - sent;
        int chunk = remaining > INT_MAX ? INT_MAX : (int)remaining;
        int result = send(
            socket_handle,
            (const char *)(data + sent),
            chunk,
            0
        );
        if (result == SOCKET_ERROR || result == 0) {
            _snwprintf_s(
                error,
                error_cap,
                _TRUNCATE,
                L"send failed: %d",
                WSAGetLastError()
            );
            return 0;
        }
        sent += (size_t)result;
    }
    return 1;
}

static int append_bytes(
    ByteBuffer *buffer,
    const uint8_t *data,
    size_t count,
    size_t max_bytes,
    wchar_t *error,
    size_t error_cap
) {
    size_t new_length = 0;
    uint8_t *new_data = NULL;

    if (count > max_bytes - buffer->length) {
        wcsncpy_s(error, error_cap, L"response exceeds declared byte bound", _TRUNCATE);
        return 0;
    }
    new_length = buffer->length + count;
    if (new_length == 0) return 1;

    new_data = (uint8_t *)realloc(buffer->data, new_length);
    if (!new_data) {
        wcsncpy_s(error, error_cap, L"response allocation failed", _TRUNCATE);
        return 0;
    }
    memcpy(new_data + buffer->length, data, count);
    buffer->data = new_data;
    buffer->length = new_length;
    return 1;
}

static int tcp_exchange(
    const wchar_t *host,
    const wchar_t *port,
    const ByteBuffer *request,
    size_t max_response_bytes,
    ByteBuffer *response,
    wchar_t *error,
    size_t error_cap
) {
    ADDRINFOW hints;
    PADDRINFOW addresses = NULL;
    PADDRINFOW current = NULL;
    SOCKET socket_handle = INVALID_SOCKET;
    int gai = 0;
    int connected = 0;
    uint8_t chunk[4096];

    ZeroMemory(&hints, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_protocol = IPPROTO_TCP;

    gai = GetAddrInfoW(host, port, &hints, &addresses);
    if (gai != 0 || !addresses) {
        _snwprintf_s(
            error,
            error_cap,
            _TRUNCATE,
            L"DNS/address resolution failed: %d",
            gai
        );
        return 0;
    }

    for (current = addresses; current; current = current->ai_next) {
        socket_handle = socket(
            current->ai_family,
            current->ai_socktype,
            current->ai_protocol
        );
        if (socket_handle == INVALID_SOCKET) continue;

        if (connect(
                socket_handle,
                current->ai_addr,
                (int)current->ai_addrlen
            ) == 0) {
            connected = 1;
            break;
        }

        closesocket(socket_handle);
        socket_handle = INVALID_SOCKET;
    }
    FreeAddrInfoW(addresses);

    if (!connected || socket_handle == INVALID_SOCKET) {
        _snwprintf_s(
            error,
            error_cap,
            _TRUNCATE,
            L"TCP connect failed: %d",
            WSAGetLastError()
        );
        return 0;
    }

    if (!send_all(
            socket_handle,
            request->data,
            request->length,
            error,
            error_cap
        )) {
        closesocket(socket_handle);
        return 0;
    }

    if (shutdown(socket_handle, SD_SEND) == SOCKET_ERROR) {
        _snwprintf_s(
            error,
            error_cap,
            _TRUNCATE,
            L"TCP send shutdown failed: %d",
            WSAGetLastError()
        );
        closesocket(socket_handle);
        return 0;
    }

    for (;;) {
        int received = recv(
            socket_handle,
            (char *)chunk,
            (int)sizeof(chunk),
            0
        );
        if (received == 0) break;
        if (received == SOCKET_ERROR) {
            _snwprintf_s(
                error,
                error_cap,
                _TRUNCATE,
                L"recv failed: %d",
                WSAGetLastError()
            );
            closesocket(socket_handle);
            buffer_free(response);
            return 0;
        }
        if (!append_bytes(
                response,
                chunk,
                (size_t)received,
                max_response_bytes,
                error,
                error_cap
            )) {
            closesocket(socket_handle);
            buffer_free(response);
            return 0;
        }
    }

    closesocket(socket_handle);
    if (response->length == 0) {
        wcsncpy_s(error, error_cap, L"TCP peer returned zero bytes", _TRUNCATE);
        return 0;
    }
    return 1;
}

static unsigned __stdcall self_test_server(void *raw) {
    SelfTestServer *server = (SelfTestServer *)raw;
    SOCKET peer = INVALID_SOCKET;
    char request[4] = {0};
    size_t offset = 0;

    peer = accept(server->listener, NULL, NULL);
    if (peer == INVALID_SOCKET) return 1;

    while (offset < sizeof(request)) {
        int received = recv(
            peer,
            request + offset,
            (int)(sizeof(request) - offset),
            0
        );
        if (received <= 0) {
            closesocket(peer);
            return 2;
        }
        offset += (size_t)received;
    }

    if (memcmp(request, "PING", 4) != 0) {
        closesocket(peer);
        return 3;
    }

    if (send(peer, "PONG", 4, 0) != 4) {
        closesocket(peer);
        return 4;
    }

    shutdown(peer, SD_SEND);
    closesocket(peer);
    server->ok = 1;
    return 0;
}

static int self_test(void) {
    SOCKET listener = INVALID_SOCKET;
    struct sockaddr_in addr;
    int addr_len = (int)sizeof(addr);
    wchar_t port[16] = {0};
    SelfTestServer server;
    uintptr_t thread_handle = 0;
    ByteBuffer request = {0};
    ByteBuffer response = {0};
    wchar_t error[256] = {0};
    uint8_t ping[4] = {'P','I','N','G'};
    DWORD wait_result = 0;

    listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (listener == INVALID_SOCKET) {
        fwprintf(stderr, L"self-test listener socket failed\n");
        return 1;
    }

    ZeroMemory(&addr, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = 0;

    if (bind(
            listener,
            (const struct sockaddr *)&addr,
            (int)sizeof(addr)
        ) == SOCKET_ERROR ||
        listen(listener, 1) == SOCKET_ERROR ||
        getsockname(
            listener,
            (struct sockaddr *)&addr,
            &addr_len
        ) == SOCKET_ERROR) {
        closesocket(listener);
        fwprintf(stderr, L"self-test bind/listen failed\n");
        return 2;
    }

    _snwprintf_s(
        port,
        sizeof(port) / sizeof(port[0]),
        _TRUNCATE,
        L"%u",
        (unsigned)ntohs(addr.sin_port)
    );

    server.listener = listener;
    server.ok = 0;
    thread_handle = _beginthreadex(
        NULL,
        0,
        self_test_server,
        &server,
        0,
        NULL
    );
    if (!thread_handle) {
        closesocket(listener);
        fwprintf(stderr, L"self-test server thread failed\n");
        return 3;
    }

    request.data = ping;
    request.length = sizeof(ping);

    if (!tcp_exchange(
            L"localhost",
            port,
            &request,
            64,
            &response,
            error,
            256
        )) {
        closesocket(listener);
        WaitForSingleObject((HANDLE)thread_handle, 5000);
        CloseHandle((HANDLE)thread_handle);
        fwprintf(stderr, L"self-test transport failed: %ls\n", error);
        buffer_free(&response);
        return 4;
    }

    wait_result = WaitForSingleObject((HANDLE)thread_handle, 5000);
    closesocket(listener);
    CloseHandle((HANDLE)thread_handle);

    if (wait_result != WAIT_OBJECT_0 ||
        !server.ok ||
        response.length != 4 ||
        memcmp(response.data, "PONG", 4) != 0) {
        buffer_free(&response);
        fwprintf(stderr, L"self-test response mismatch\n");
        return 5;
    }

    buffer_free(&response);
    wprintf(L"win32 TCP transport self-test PASS\n");
    return 0;
}

int wmain(int argc, wchar_t **argv) {
    WSADATA wsa;
    ByteBuffer request = {0};
    ByteBuffer response = {0};
    wchar_t error[256] = {0};
    size_t max_response_bytes = 262144;
    unsigned long long parsed_max = 0;
    int result = 0;

    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        fwprintf(stderr, L"WSAStartup failed\n");
        return 70;
    }

    if (argc == 2 && wcscmp(argv[1], L"--self-test") == 0) {
        result = self_test();
        WSACleanup();
        return result;
    }

    if (argc != 5 && argc != 6) {
        fwprintf(
            stderr,
            L"usage: win32_tcp_transport.exe <host> <port> <request.bin> <response.bin> [max-response-bytes]\n"
        );
        fwprintf(stderr, L"       win32_tcp_transport.exe --self-test\n");
        WSACleanup();
        return 64;
    }

    if (argc == 6) {
        wchar_t *end = NULL;
        parsed_max = _wcstoui64(argv[5], &end, 10);
        if (!end || *end != L'\0' ||
            parsed_max < 1 ||
            parsed_max > 16ULL * 1024ULL * 1024ULL) {
            fwprintf(stderr, L"max-response-bytes outside [1,16777216]\n");
            WSACleanup();
            return 64;
        }
        max_response_bytes = (size_t)parsed_max;
    }

    if (!read_file(argv[3], &request, error, 256)) {
        fwprintf(stderr, L"%ls\n", error);
        WSACleanup();
        return 65;
    }

    if (!tcp_exchange(
            argv[1],
            argv[2],
            &request,
            max_response_bytes,
            &response,
            error,
            256
        )) {
        buffer_free(&request);
        fwprintf(stderr, L"%ls\n", error);
        WSACleanup();
        return 66;
    }

    if (!write_file(argv[4], &response, error, 256)) {
        buffer_free(&request);
        buffer_free(&response);
        fwprintf(stderr, L"%ls\n", error);
        WSACleanup();
        return 67;
    }

    buffer_free(&request);
    buffer_free(&response);
    WSACleanup();
    return 0;
}

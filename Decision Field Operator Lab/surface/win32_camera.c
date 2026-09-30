#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#pragma comment(lib, "user32.lib")
#pragma comment(lib, "gdi32.lib")

typedef struct CameraFrame {
    int width;
    int height;
    uint8_t *gray;
    uint32_t *bgra;
} CameraFrame;

static CameraFrame g_frame = {0};
static BITMAPINFO g_bmi = {0};

static void frame_free(CameraFrame *frame) {
    if (!frame) return;
    free(frame->gray);
    free(frame->bgra);
    frame->gray = NULL;
    frame->bgra = NULL;
    frame->width = 0;
    frame->height = 0;
}

static int is_space_byte(uint8_t c) {
    return c == ' ' || c == '\t' || c == '\r' || c == '\n' || c == '\f';
}

static int skip_ws_comments(const uint8_t *data, size_t size, size_t *pos) {
    while (*pos < size) {
        if (is_space_byte(data[*pos])) {
            (*pos)++;
            continue;
        }
        if (data[*pos] == '#') {
            while (*pos < size && data[*pos] != '\n') (*pos)++;
            continue;
        }
        break;
    }
    return *pos < size;
}

static int parse_uint_token(
    const uint8_t *data,
    size_t size,
    size_t *pos,
    unsigned *out
) {
    unsigned value = 0;
    int digits = 0;
    if (!skip_ws_comments(data, size, pos)) return 0;
    while (*pos < size) {
        uint8_t c = data[*pos];
        if (c < '0' || c > '9') break;
        if (value > 100000000U) return 0;
        value = value * 10U + (unsigned)(c - '0');
        (*pos)++;
        digits = 1;
    }
    if (!digits) return 0;
    *out = value;
    return 1;
}

static int decode_p5(
    const uint8_t *data,
    size_t size,
    CameraFrame *out,
    wchar_t *error,
    size_t error_cap
) {
    size_t pos = 0;
    unsigned width = 0, height = 0, maxval = 0;
    size_t pixels = 0;

    if (!data || !out || size < 4) {
        wcsncpy_s(error, error_cap, L"camera stream is empty", _TRUNCATE);
        return 0;
    }
    if (data[0] != 'P' || data[1] != '5') {
        wcsncpy_s(error, error_cap, L"camera stream is not P5", _TRUNCATE);
        return 0;
    }
    pos = 2;
    if (!parse_uint_token(data, size, &pos, &width) ||
        !parse_uint_token(data, size, &pos, &height) ||
        !parse_uint_token(data, size, &pos, &maxval)) {
        wcsncpy_s(error, error_cap, L"invalid P5 header", _TRUNCATE);
        return 0;
    }
    if (width == 0 || height == 0 || width > 16384U || height > 16384U) {
        wcsncpy_s(error, error_cap, L"camera dimensions outside bounds", _TRUNCATE);
        return 0;
    }
    if (maxval != 255U) {
        wcsncpy_s(error, error_cap, L"only 8-bit P5 camera streams are supported", _TRUNCATE);
        return 0;
    }
    if (pos >= size || !is_space_byte(data[pos])) {
        wcsncpy_s(error, error_cap, L"P5 header is missing raster separator", _TRUNCATE);
        return 0;
    }
    pos++; /* exactly one required header/raster separator */

    pixels = (size_t)width * (size_t)height;
    if (pixels / (size_t)width != (size_t)height) {
        wcsncpy_s(error, error_cap, L"camera dimension multiplication overflow", _TRUNCATE);
        return 0;
    }
    if (size - pos != pixels) {
        wcsncpy_s(error, error_cap, L"P5 raster size does not match dimensions", _TRUNCATE);
        return 0;
    }

    out->gray = (uint8_t *)malloc(pixels);
    out->bgra = (uint32_t *)malloc(pixels * sizeof(uint32_t));
    if (!out->gray || !out->bgra) {
        frame_free(out);
        wcsncpy_s(error, error_cap, L"camera allocation failed", _TRUNCATE);
        return 0;
    }
    memcpy(out->gray, data + pos, pixels);
    out->width = (int)width;
    out->height = (int)height;

    for (size_t i = 0; i < pixels; i++) {
        uint32_t g = (uint32_t)out->gray[i];
        out->bgra[i] = g | (g << 8) | (g << 16);
    }
    return 1;
}

static int read_file_bytes(
    const wchar_t *path,
    uint8_t **data,
    size_t *size,
    wchar_t *error,
    size_t error_cap
) {
    FILE *file = NULL;
    __int64 length = 0;
    uint8_t *buffer = NULL;

    if (_wfopen_s(&file, path, L"rb") != 0 || !file) {
        wcsncpy_s(error, error_cap, L"could not open camera file", _TRUNCATE);
        return 0;
    }
    if (_fseeki64(file, 0, SEEK_END) != 0) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"could not seek camera file", _TRUNCATE);
        return 0;
    }
    length = _ftelli64(file);
    if (length <= 0 || length > 512LL * 1024LL * 1024LL) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"camera file size outside bounds", _TRUNCATE);
        return 0;
    }
    if (_fseeki64(file, 0, SEEK_SET) != 0) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"could not rewind camera file", _TRUNCATE);
        return 0;
    }

    buffer = (uint8_t *)malloc((size_t)length);
    if (!buffer) {
        fclose(file);
        wcsncpy_s(error, error_cap, L"camera file allocation failed", _TRUNCATE);
        return 0;
    }
    if (fread(buffer, 1, (size_t)length, file) != (size_t)length) {
        free(buffer);
        fclose(file);
        wcsncpy_s(error, error_cap, L"could not read complete camera file", _TRUNCATE);
        return 0;
    }
    fclose(file);
    *data = buffer;
    *size = (size_t)length;
    return 1;
}

static LRESULT CALLBACK camera_wndproc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
    (void)wparam;
    (void)lparam;

    switch (msg) {
    case WM_ERASEBKGND:
        return 1;
    case WM_PAINT: {
        PAINTSTRUCT ps;
        RECT client;
        HDC dc = BeginPaint(hwnd, &ps);
        GetClientRect(hwnd, &client);
        SetStretchBltMode(dc, COLORONCOLOR);
        StretchDIBits(
            dc,
            0, 0, client.right - client.left, client.bottom - client.top,
            0, 0, g_frame.width, g_frame.height,
            g_frame.bgra,
            &g_bmi,
            DIB_RGB_COLORS,
            SRCCOPY
        );
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_SIZE:
        InvalidateRect(hwnd, NULL, FALSE);
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    default:
        return DefWindowProcW(hwnd, msg, wparam, lparam);
    }
}

static int self_test(void) {
    static const uint8_t sample[] = {
        'P','5','\n','2',' ','2','\n','2','5','5','\n',
        0, 64, 128, 255
    };
    CameraFrame frame = {0};
    wchar_t error[128] = {0};
    int ok = decode_p5(sample, sizeof(sample), &frame, error, 128);
    if (!ok) {
        fwprintf(stderr, L"self-test decode failed: %ls\n", error);
        return 1;
    }
    if (frame.width != 2 || frame.height != 2 ||
        frame.gray[0] != 0 || frame.gray[1] != 64 ||
        frame.gray[2] != 128 || frame.gray[3] != 255 ||
        frame.bgra[1] != 0x00404040U) {
        frame_free(&frame);
        fwprintf(stderr, L"self-test pixel mismatch\n");
        return 2;
    }
    frame_free(&frame);
    wprintf(L"win32 camera self-test PASS\n");
    return 0;
}

int wmain(int argc, wchar_t **argv) {
    static const wchar_t CLASS_NAME[] = L"RMAPLIndependentBrowserCamera";
    uint8_t *file_data = NULL;
    size_t file_size = 0;
    wchar_t error[256] = {0};
    WNDCLASSW wc = {0};
    HWND hwnd = NULL;
    RECT rect = {0, 0, 640, 256};
    MSG msg = {0};

    if (argc == 2 && wcscmp(argv[1], L"--self-test") == 0) {
        return self_test();
    }
    if (argc != 2) {
        fwprintf(stderr, L"usage: win32_camera.exe <frame.pgm>\n");
        fwprintf(stderr, L"       win32_camera.exe --self-test\n");
        return 64;
    }

    if (!read_file_bytes(argv[1], &file_data, &file_size, error, 256)) {
        fwprintf(stderr, L"%ls\n", error);
        return 65;
    }
    if (!decode_p5(file_data, file_size, &g_frame, error, 256)) {
        free(file_data);
        fwprintf(stderr, L"%ls\n", error);
        return 66;
    }
    free(file_data);

    ZeroMemory(&g_bmi, sizeof(g_bmi));
    g_bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    g_bmi.bmiHeader.biWidth = g_frame.width;
    g_bmi.bmiHeader.biHeight = -g_frame.height; /* top-down */
    g_bmi.bmiHeader.biPlanes = 1;
    g_bmi.bmiHeader.biBitCount = 32;
    g_bmi.bmiHeader.biCompression = BI_RGB;

    wc.lpfnWndProc = camera_wndproc;
    wc.hInstance = GetModuleHandleW(NULL);
    wc.lpszClassName = CLASS_NAME;
    wc.hCursor = LoadCursorW(NULL, IDC_ARROW);
    if (!RegisterClassW(&wc)) {
        frame_free(&g_frame);
        fwprintf(stderr, L"RegisterClassW failed: %lu\n", GetLastError());
        return 67;
    }

    rect.right = g_frame.width * 4;
    rect.bottom = g_frame.height * 4;
    AdjustWindowRect(&rect, WS_OVERLAPPEDWINDOW, FALSE);

    hwnd = CreateWindowExW(
        0,
        CLASS_NAME,
        L"RMAPL Independent Browser Camera",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT,
        rect.right - rect.left,
        rect.bottom - rect.top,
        NULL, NULL, wc.hInstance, NULL
    );
    if (!hwnd) {
        frame_free(&g_frame);
        fwprintf(stderr, L"CreateWindowExW failed: %lu\n", GetLastError());
        return 68;
    }

    ShowWindow(hwnd, SW_SHOWDEFAULT);
    UpdateWindow(hwnd);

    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    frame_free(&g_frame);
    return (int)msg.wParam;
}

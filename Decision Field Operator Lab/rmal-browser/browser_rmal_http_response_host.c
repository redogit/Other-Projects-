#include "rmal/rmal.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct ResponseFixture {
    const char *name;
    const unsigned char *bytes;
    size_t size;
    bool admitted;
    int64_t status;
    const char *html;
    const char *residual_kind;
    const char *residual_detail;
    const char *consequence;
    bool append_history;
    bool promote_pending;
    bool clear_navigation;
    bool clear_render;
} ResponseFixture;

typedef struct ResponseHost {
    const ResponseFixture *current;
    size_t results;
} ResponseHost;

static const unsigned char VALID_RESPONSE[] =
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/html\r\n"
    "Connection: close\r\n"
    "\r\n"
    "<h1>FETCHED</h1>";

static const unsigned char NOT_FOUND_RESPONSE[] =
    "HTTP/1.1 404 Not Found\r\n\r\n<h1>NO</h1>";

static const unsigned char MISSING_DELIMITER_RESPONSE[] =
    "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n<h1>NO</h1>";

static const unsigned char EMPTY_BODY_RESPONSE[] =
    "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n";

static const ResponseFixture FIXTURES[] = {
    {
        "valid",
        VALID_RESPONSE,
        sizeof(VALID_RESPONSE) - 1U,
        true,
        200,
        "<h1>FETCHED</h1>",
        "html-tokenization-pending",
        "http-response-admitted",
        "http-response-admitted",
        true, true, true, true
    },
    {
        "not_found",
        NOT_FOUND_RESPONSE,
        sizeof(NOT_FOUND_RESPONSE) - 1U,
        false,
        0,
        "",
        "http-response-invalid",
        "requires-http11-200-header-delimiter-utf8-body",
        "http-response-invalid",
        false, false, false, false
    },
    {
        "missing_delimiter",
        MISSING_DELIMITER_RESPONSE,
        sizeof(MISSING_DELIMITER_RESPONSE) - 1U,
        false,
        0,
        "",
        "http-response-invalid",
        "requires-http11-200-header-delimiter-utf8-body",
        "http-response-invalid",
        false, false, false, false
    },
    {
        "empty_body",
        EMPTY_BODY_RESPONSE,
        sizeof(EMPTY_BODY_RESPONSE) - 1U,
        false,
        0,
        "",
        "http-response-invalid",
        "requires-http11-200-header-delimiter-utf8-body",
        "http-response-invalid",
        false, false, false, false
    }
};

static const size_t FIXTURE_COUNT = sizeof(FIXTURES) / sizeof(FIXTURES[0]);

static RmalStatus ok_status(void) {
    RmalStatus status = {0};
    status.ok = true;
    return status;
}

static RmalStatus error_status(const char *message) {
    RmalStatus status = {0};
    status.ok = false;
    snprintf(status.message, sizeof(status.message), "%s", message);
    return status;
}

static char *dup_text(const char *text) {
    size_t size = strlen(text) + 1U;
    char *copy = (char *)malloc(size);
    if (copy) memcpy(copy, text, size);
    return copy;
}

static int utf8_valid(const unsigned char *data, size_t size) {
    size_t i = 0;
    while (i < size) {
        unsigned char c = data[i];
        if (c == 0U) return 0;
        if (c <= 0x7fU) { i += 1U; continue; }
        if ((c & 0xe0U) == 0xc0U) {
            if (i + 1U >= size || c < 0xc2U ||
                (data[i + 1U] & 0xc0U) != 0x80U) return 0;
            i += 2U; continue;
        }
        if ((c & 0xf0U) == 0xe0U) {
            if (i + 2U >= size ||
                (data[i + 1U] & 0xc0U) != 0x80U ||
                (data[i + 2U] & 0xc0U) != 0x80U) return 0;
            if (c == 0xe0U && data[i + 1U] < 0xa0U) return 0;
            if (c == 0xedU && data[i + 1U] >= 0xa0U) return 0;
            i += 3U; continue;
        }
        if ((c & 0xf8U) == 0xf0U) {
            if (i + 3U >= size || c > 0xf4U ||
                (data[i + 1U] & 0xc0U) != 0x80U ||
                (data[i + 2U] & 0xc0U) != 0x80U ||
                (data[i + 3U] & 0xc0U) != 0x80U) return 0;
            if (c == 0xf0U && data[i + 1U] < 0x90U) return 0;
            if (c == 0xf4U && data[i + 1U] >= 0x90U) return 0;
            i += 4U; continue;
        }
        return 0;
    }
    return 1;
}

static RmalStatus response_select(
    void *context,
    const RmalValue *arguments,
    size_t count,
    RmalValue *result
) {
    ResponseHost *host = (ResponseHost *)context;
    if (!host || count != 1U || arguments[0].kind != RMAL_VALUE_STRING ||
        !arguments[0].as.string) {
        return error_status("BrowserResponseSelect requires one string");
    }
    host->current = NULL;
    for (size_t i = 0; i < FIXTURE_COUNT; ++i) {
        if (strcmp(arguments[0].as.string, FIXTURES[i].name) == 0) {
            host->current = &FIXTURES[i];
            break;
        }
    }
    if (!host->current) return error_status("unknown response fixture");
    size_t ack_size = strlen(host->current->name) + sizeof(":ACK");
    char *ack = (char *)malloc(ack_size);
    if (!ack) return error_status("response select allocation failed");
    snprintf(ack, ack_size, "%s:ACK", host->current->name);
    result->kind = RMAL_VALUE_STRING;
    result->as.string = ack;
    return ok_status();
}

static RmalStatus response_length(
    void *context,
    const RmalValue *arguments,
    size_t count,
    RmalValue *result
) {
    (void)arguments;
    ResponseHost *host = (ResponseHost *)context;
    if (!host || !host->current || count != 0U) {
        return error_status("BrowserResponseLength requires selected fixture");
    }
    result->kind = RMAL_VALUE_INT;
    result->as.integer = (int64_t)host->current->size;
    return ok_status();
}

static RmalStatus response_byte(
    void *context,
    const RmalValue *arguments,
    size_t count,
    RmalValue *result
) {
    ResponseHost *host = (ResponseHost *)context;
    if (!host || !host->current || count != 1U ||
        arguments[0].kind != RMAL_VALUE_INT ||
        arguments[0].as.integer < 0 ||
        (uint64_t)arguments[0].as.integer >= (uint64_t)host->current->size) {
        return error_status("BrowserResponseByte index outside fixture");
    }
    result->kind = RMAL_VALUE_INT;
    result->as.integer =
        (int64_t)host->current->bytes[(size_t)arguments[0].as.integer];
    return ok_status();
}

static RmalStatus response_utf8(
    void *context,
    const RmalValue *arguments,
    size_t count,
    RmalValue *result
) {
    ResponseHost *host = (ResponseHost *)context;
    if (!host || !host->current || count != 2U ||
        arguments[0].kind != RMAL_VALUE_INT ||
        arguments[1].kind != RMAL_VALUE_INT ||
        arguments[0].as.integer < 0 || arguments[1].as.integer < 0) {
        return error_status("BrowserResponseUtf8 requires start,length integers");
    }
    size_t start = (size_t)arguments[0].as.integer;
    size_t length = (size_t)arguments[1].as.integer;
    if (start > host->current->size || length > host->current->size - start) {
        return error_status("BrowserResponseUtf8 slice outside fixture");
    }
    const unsigned char *data = host->current->bytes + start;
    if (!utf8_valid(data, length)) {
        result->kind = RMAL_VALUE_STRING;
        result->as.string = dup_text("");
        return result->as.string ? ok_status() : error_status("UTF-8 sentinel allocation failed");
    }
    char *text = (char *)malloc(length + 1U);
    if (!text) return error_status("UTF-8 slice allocation failed");
    memcpy(text, data, length);
    text[length] = '\0';
    result->kind = RMAL_VALUE_STRING;
    result->as.string = text;
    return ok_status();
}

static int value_string_equals(const RmalValue *value, const char *expected) {
    return value && value->kind == RMAL_VALUE_STRING && value->as.string &&
        strcmp(value->as.string, expected) == 0;
}

static RmalStatus response_result(
    void *context,
    const RmalValue *arguments,
    size_t count,
    RmalValue *result
) {
    ResponseHost *host = (ResponseHost *)context;
    if (!host || !host->current || count != 10U ||
        arguments[0].kind != RMAL_VALUE_BOOL ||
        arguments[1].kind != RMAL_VALUE_INT ||
        arguments[6].kind != RMAL_VALUE_BOOL ||
        arguments[7].kind != RMAL_VALUE_BOOL ||
        arguments[8].kind != RMAL_VALUE_BOOL ||
        arguments[9].kind != RMAL_VALUE_BOOL) {
        return error_status("BrowserResponseResult argument contract violated");
    }
    const ResponseFixture *expected = host->current;
    if (arguments[0].as.boolean != expected->admitted ||
        arguments[1].as.integer != expected->status ||
        !value_string_equals(&arguments[2], expected->html) ||
        !value_string_equals(&arguments[3], expected->residual_kind) ||
        !value_string_equals(&arguments[4], expected->residual_detail) ||
        !value_string_equals(&arguments[5], expected->consequence) ||
        arguments[6].as.boolean != expected->append_history ||
        arguments[7].as.boolean != expected->promote_pending ||
        arguments[8].as.boolean != expected->clear_navigation ||
        arguments[9].as.boolean != expected->clear_render) {
        return error_status("RMAL response decision differs from fixture contract");
    }

    printf(
        "RMAL_HTTP_RESPONSE fixture=%s admitted=%s status=%" PRId64
        " residual=%s detail=%s consequence=%s history=%s promote=%s clear_nav=%s clear_render=%s body_hex=",
        expected->name,
        arguments[0].as.boolean ? "true" : "false",
        arguments[1].as.integer,
        arguments[3].as.string,
        arguments[4].as.string,
        arguments[5].as.string,
        arguments[6].as.boolean ? "true" : "false",
        arguments[7].as.boolean ? "true" : "false",
        arguments[8].as.boolean ? "true" : "false",
        arguments[9].as.boolean ? "true" : "false"
    );
    const unsigned char *p = (const unsigned char *)arguments[2].as.string;
    while (*p) { printf("%02x", (unsigned int)*p); ++p; }
    putchar('\n');

    size_t ack_size = strlen(expected->consequence) + sizeof(":ACK");
    char *ack = (char *)malloc(ack_size);
    if (!ack) return error_status("response result allocation failed");
    snprintf(ack, ack_size, "%s:ACK", expected->consequence);
    result->kind = RMAL_VALUE_STRING;
    result->as.string = ack;
    host->results += 1U;
    return ok_status();
}

static FILE *open_binary_read(const char *path) {
#if defined(_WIN32)
    FILE *file = NULL;
    if (fopen_s(&file, path, "rb") != 0) return NULL;
    return file;
#else
    return fopen(path, "rb");
#endif
}

static char *read_file(const char *path) {
    FILE *file = open_binary_read(path);
    if (!file) return NULL;
    if (fseek(file, 0, SEEK_END) != 0) { fclose(file); return NULL; }
    long end = ftell(file);
    if (end < 0) { fclose(file); return NULL; }
    rewind(file);
    size_t size = (size_t)end;
    char *buffer = (char *)malloc(size + 1U);
    if (!buffer) { fclose(file); return NULL; }
    size_t got = fread(buffer, 1U, size, file);
    fclose(file);
    if (got != size) { free(buffer); return NULL; }
    buffer[size] = '\0';
    return buffer;
}

static int print_status(const char *stage, const RmalStatus *status) {
    fprintf(stderr, "%s failed at %d:%d: %s\n", stage,
            status ? status->line : 0,
            status ? status->column : 0,
            status ? status->message : "unknown");
    return 1;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: browser_rmal_http_response_host <browser_http_response.rmal>\n");
        return 64;
    }
    char *source = read_file(argv[1]);
    if (!source) return 65;

    RmalStatus status = {0};
    RmalProgram *program = rmal_parse_source(source, argv[1], &status);
    free(source);
    if (!program) return print_status("parse", &status);
    RmalBytecode *bytecode = rmal_compile(program, &status);
    if (!bytecode) {
        rmal_program_free(program);
        return print_status("compile", &status);
    }
    RmalVm *vm = rmal_vm_create();
    if (!vm) {
        rmal_bytecode_free(bytecode);
        rmal_program_free(program);
        return 66;
    }

    ResponseHost host = {0};
    struct Binding { const char *name; size_t arity; RmalNativeFunction fn; } bindings[] = {
        {"BrowserResponseSelect", 1U, response_select},
        {"BrowserResponseLength", 0U, response_length},
        {"BrowserResponseByte", 1U, response_byte},
        {"BrowserResponseUtf8", 2U, response_utf8},
        {"BrowserResponseResult", 10U, response_result},
    };
    for (size_t i = 0; i < sizeof(bindings)/sizeof(bindings[0]); ++i) {
        status = rmal_vm_bind_native(vm, bindings[i].name, bindings[i].arity,
                                     bindings[i].fn, &host);
        if (!status.ok) {
            rmal_vm_free(vm);
            rmal_bytecode_free(bytecode);
            rmal_program_free(program);
            return print_status("bind", &status);
        }
    }

    RmalValue result = {0};
    status = rmal_vm_run(vm, bytecode, true, &result);
    rmal_value_free(&result);
    int rc = 0;
    if (!status.ok) rc = print_status("run", &status);
    else if (host.results != FIXTURE_COUNT) {
        fprintf(stderr, "response results incomplete: %zu/%zu\n", host.results, FIXTURE_COUNT);
        rc = 67;
    } else {
        printf("RMAL_HTTP_RESPONSE_RECEIPT fixtures=%zu policy_in_rmal=true python_runtime_used=false\n",
               host.results);
    }

    rmal_vm_free(vm);
    rmal_bytecode_free(bytecode);
    rmal_program_free(program);
    return rc;
}

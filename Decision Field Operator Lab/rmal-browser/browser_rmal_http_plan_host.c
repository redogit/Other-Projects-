#include "rmal/rmal.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct ExpectedPlan {
    const char *scheme;
    const char *host;
    int64_t port;
    const char *transport_kind;
    const char *transport_detail;
    const char *consequence;
    const char *request;
    int64_t max_response_bytes;
} ExpectedPlan;

typedef struct PlanHost {
    size_t index;
} PlanHost;

static const ExpectedPlan EXPECTED[] = {
    {
        "http",
        "127.0.0.1",
        80,
        "native-http-transport-pending",
        "rmapl-request-ready",
        "http-request-planned",
        "GET /test HTTP/1.1\r\n"
        "Host: 127.0.0.1\r\n"
        "Connection: close\r\n"
        "Accept: text/html\r\n"
        "User-Agent: RMAPL-Independent/0\r\n"
        "\r\n",
        262144
    },
    {
        "https",
        "example.com",
        443,
        "native-tls-transport-pending",
        "rmapl-tls-request-ready",
        "https-request-planned",
        "GET /docs HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Connection: close\r\n"
        "Accept: text/html\r\n"
        "User-Agent: RMAPL-Independent/0\r\n"
        "\r\n",
        262144
    }
};

static const size_t EXPECTED_COUNT = sizeof(EXPECTED) / sizeof(EXPECTED[0]);

static RmalStatus status_ok(void) {
    RmalStatus status = {0};
    status.ok = true;
    return status;
}

static RmalStatus status_error(const char *message) {
    RmalStatus status = {0};
    snprintf(status.message, sizeof(status.message), "%s", message);
    return status;
}

static int value_string_equals(const RmalValue *value, const char *expected) {
    return value &&
        value->kind == RMAL_VALUE_STRING &&
        value->as.string &&
        strcmp(value->as.string, expected) == 0;
}

static int value_int_equals(const RmalValue *value, int64_t expected) {
    return value &&
        value->kind == RMAL_VALUE_INT &&
        value->as.integer == expected;
}

static void print_hex(const char *text) {
    const unsigned char *p = (const unsigned char *)text;
    while (*p) {
        printf("%02x", (unsigned int)*p);
        ++p;
    }
}

static RmalStatus browser_plan_result(
    void *context,
    const RmalValue *arguments,
    size_t count,
    RmalValue *result
) {
    PlanHost *host = (PlanHost *)context;
    if (!host || !arguments || !result) {
        return status_error("BrowserPlanResult received invalid host arguments");
    }
    if (count != 8U) {
        return status_error("BrowserPlanResult requires eight arguments");
    }
    if (host->index >= EXPECTED_COUNT) {
        return status_error("BrowserPlanResult exceeded declared fixture count");
    }

    const ExpectedPlan *expected = &EXPECTED[host->index];
    if (!value_string_equals(&arguments[0], expected->scheme) ||
        !value_string_equals(&arguments[1], expected->host) ||
        !value_int_equals(&arguments[2], expected->port) ||
        !value_string_equals(&arguments[3], expected->transport_kind) ||
        !value_string_equals(&arguments[4], expected->transport_detail) ||
        !value_string_equals(&arguments[5], expected->consequence) ||
        !value_string_equals(&arguments[6], expected->request) ||
        !value_int_equals(&arguments[7], expected->max_response_bytes)) {
        return status_error("RMAL HTTP planner result differs from declared fixture");
    }

    printf(
        "RMAL_HTTP_PLAN index=%zu scheme=%s host=%s port=%" PRId64
        " transport=%s detail=%s consequence=%s max=%" PRId64 " request_hex=",
        host->index,
        arguments[0].as.string,
        arguments[1].as.string,
        arguments[2].as.integer,
        arguments[3].as.string,
        arguments[4].as.string,
        arguments[5].as.string,
        arguments[7].as.integer
    );
    print_hex(arguments[6].as.string);
    putchar('\n');

    const char *consequence = arguments[5].as.string;
    size_t ack_size = strlen(consequence) + sizeof(":ACK");
    char *ack = (char *)malloc(ack_size);
    if (!ack) return status_error("BrowserPlanResult acknowledgement allocation failed");
    snprintf(ack, ack_size, "%s:ACK", consequence);

    result->kind = RMAL_VALUE_STRING;
    result->as.string = ack;
    host->index += 1U;
    return status_ok();
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
    if (fseek(file, 0, SEEK_END) != 0) {
        fclose(file);
        return NULL;
    }
    long end = ftell(file);
    if (end < 0) {
        fclose(file);
        return NULL;
    }
    rewind(file);
    size_t size = (size_t)end;
    char *buffer = (char *)malloc(size + 1U);
    if (!buffer) {
        fclose(file);
        return NULL;
    }
    size_t got = fread(buffer, 1U, size, file);
    fclose(file);
    if (got != size) {
        free(buffer);
        return NULL;
    }
    buffer[size] = '\0';
    return buffer;
}

static int print_status(const char *stage, const RmalStatus *status) {
    fprintf(
        stderr,
        "%s failed at %d:%d: %s\n",
        stage,
        status ? status->line : 0,
        status ? status->column : 0,
        status ? status->message : "unknown"
    );
    return 1;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: browser_rmal_http_plan_host <browser_http_plan.rmal>\n");
        return 64;
    }

    char *source = read_file(argv[1]);
    if (!source) {
        fprintf(stderr, "cannot read RMAL HTTP plan: %s\n", argv[1]);
        return 65;
    }

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

    PlanHost host = {0};
    status = rmal_vm_bind_native(
        vm,
        "BrowserPlanResult",
        8U,
        browser_plan_result,
        &host
    );
    if (!status.ok) {
        rmal_vm_free(vm);
        rmal_bytecode_free(bytecode);
        rmal_program_free(program);
        return print_status("bind", &status);
    }

    RmalValue result = {0};
    status = rmal_vm_run(vm, bytecode, true, &result);
    rmal_value_free(&result);

    int rc = 0;
    if (!status.ok) {
        rc = print_status("run", &status);
    } else if (host.index != EXPECTED_COUNT) {
        fprintf(stderr, "HTTP planner calls incomplete: %zu/%zu\n", host.index, EXPECTED_COUNT);
        rc = 67;
    } else {
        printf(
            "RMAL_HTTP_PLAN_RECEIPT calls=%zu python_runtime_used=false\n",
            host.index
        );
    }

    rmal_vm_free(vm);
    rmal_bytecode_free(bytecode);
    rmal_program_free(program);
    return rc;
}

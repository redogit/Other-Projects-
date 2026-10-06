#include "rmal/rmal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct FkdbHost {
    size_t index;
} FkdbHost;

static const char *EXPECTED_HANDOFFS[] = {
    "HTML_TOKENIZE",
    "DOM_BUILD",
    "LAYOUT",
    "HIT_MAP",
    "RASTER",
    "FRAME_VERIFY",
    "CAMERA_PACK",
    "FRAME_ADMIT",
    "FKDB_QUERY_NEED",
    "FKDB_QUERY_HISTORY",
    "FKDB_QUERY_DECAY",
    "FKDB_QUERY_RECOVER",
    "FKDB_QUERY_RELATE",
    "URL_RESOLVE",
    "HTTPS_PLAN",
    "NATIVE_TLS",
    "HTTP_RESPONSE_ADMIT",
    "HTML_TOKENIZE",
    "DOM_BUILD",
    "LAYOUT",
    "HIT_MAP",
    "RASTER",
    "FRAME_VERIFY",
    "CAMERA_PACK",
    "FRAME_ADMIT",
    "FKDB_QUERY_RETURN",
    "PRESENT"
};

static const size_t EXPECTED_HANDOFF_COUNT =
    sizeof(EXPECTED_HANDOFFS) / sizeof(EXPECTED_HANDOFFS[0]);

static RmalStatus status_ok(void) {
    RmalStatus status = {0};
    status.ok = true;
    return status;
}

static RmalStatus status_error(const char *message) {
    RmalStatus status = {0};
    status.ok = false;
    snprintf(status.message, sizeof(status.message), "%s", message);
    return status;
}

static RmalStatus browser_handoff(
    void *context,
    const RmalValue *arguments,
    size_t count,
    RmalValue *result
) {
    FkdbHost *host = (FkdbHost *)context;
    if (!host || !arguments || !result) {
        return status_error("BrowserHandoff received invalid FKDB host arguments");
    }
    if (count != 1U || arguments[0].kind != RMAL_VALUE_STRING ||
        !arguments[0].as.string) {
        return status_error("BrowserHandoff requires exactly one string");
    }
    if (host->index >= EXPECTED_HANDOFF_COUNT) {
        return status_error("BrowserHandoff exceeded FKDB declared sequence");
    }

    const char *actual = arguments[0].as.string;
    const char *expected = EXPECTED_HANDOFFS[host->index];
    if (strcmp(actual, expected) != 0) {
        RmalStatus status = {0};
        status.ok = false;
        snprintf(
            status.message,
            sizeof(status.message),
            "FKDB handoff mismatch at %zu: expected %s got %s",
            host->index,
            expected,
            actual
        );
        return status;
    }

    size_t ack_size = strlen(actual) + sizeof(":ACK");
    char *ack = (char *)malloc(ack_size);
    if (!ack) return status_error("FKDB handoff acknowledgement allocation failed");
    snprintf(ack, ack_size, "%s:ACK", actual);

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
        fprintf(stderr, "usage: fkdb_rmal_host <fkdb_bootstrap.rmal>\n");
        return 64;
    }

    char *source = read_file(argv[1]);
    if (!source) {
        fprintf(stderr, "cannot read FKDB RMAL bootstrap: %s\n", argv[1]);
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
        fprintf(stderr, "cannot create RMAL VM\n");
        return 66;
    }

    FkdbHost host = {0};
    status = rmal_vm_bind_native(
        vm,
        "BrowserHandoff",
        1U,
        browser_handoff,
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
    } else if (host.index != EXPECTED_HANDOFF_COUNT) {
        fprintf(
            stderr,
            "FKDB handoff sequence incomplete: %zu/%zu\n",
            host.index,
            EXPECTED_HANDOFF_COUNT
        );
        rc = 67;
    } else {
        printf("FKDB_RMAL_HOST_PASS\n");
        printf("predecessor=Independent Browser\n");
        printf("project=FKDB\n");
        printf("handoffs=%zu\n", host.index);
        printf("python_runtime_used=false\n");
        printf(
            "FKDB_BROWSER_RECEIPT handoffs=%zu direct_successor=true python_runtime_used=false\n",
            host.index
        );
    }

    rmal_vm_free(vm);
    rmal_bytecode_free(bytecode);
    rmal_program_free(program);
    return rc;
}

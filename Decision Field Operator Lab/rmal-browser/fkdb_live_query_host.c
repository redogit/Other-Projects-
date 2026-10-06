#include "rmal/rmal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct FkdbQueryHost {
    const char *query;
    int received;
    char status[32];
    char route[32];
    char cost[16];
} FkdbQueryHost;

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

static char *copy_string(const char *value) {
    size_t n = strlen(value);
    char *copy = (char *)malloc(n + 1U);
    if (!copy) return NULL;
    memcpy(copy, value, n + 1U);
    return copy;
}

static RmalStatus query_text(
    void *context,
    const RmalValue *arguments,
    size_t count,
    RmalValue *result
) {
    (void)arguments;
    FkdbQueryHost *host = (FkdbQueryHost *)context;
    if (!host || !result) return status_error("FkdbQueryText invalid context");
    if (count != 0U) return status_error("FkdbQueryText takes no arguments");
    char *copy = copy_string(host->query);
    if (!copy) return status_error("FkdbQueryText allocation failed");
    result->kind = RMAL_VALUE_STRING;
    result->as.string = copy;
    return status_ok();
}

static RmalStatus query_result(
    void *context,
    const RmalValue *arguments,
    size_t count,
    RmalValue *result
) {
    FkdbQueryHost *host = (FkdbQueryHost *)context;
    if (!host || !arguments || !result) {
        return status_error("FkdbQueryResult invalid arguments");
    }
    if (count != 4U) return status_error("FkdbQueryResult requires four strings");
    for (size_t i = 0; i < count; ++i) {
        if (arguments[i].kind != RMAL_VALUE_STRING || !arguments[i].as.string) {
            return status_error("FkdbQueryResult arguments must be strings");
        }
    }

    const char *raw = arguments[0].as.string;
    const char *status_value = arguments[1].as.string;
    const char *route_value = arguments[2].as.string;
    const char *cost_value = arguments[3].as.string;

    if (strcmp(raw, host->query) != 0) {
        return status_error("FKDB query source expression changed in routing");
    }

    snprintf(host->status, sizeof(host->status), "%s", status_value);
    snprintf(host->route, sizeof(host->route), "%s", route_value);
    snprintf(host->cost, sizeof(host->cost), "%s", cost_value);
    host->received = 1;

    size_t ack_size = strlen(status_value) + sizeof(":ACK");
    char *ack = (char *)malloc(ack_size);
    if (!ack) return status_error("FkdbQueryResult acknowledgement allocation failed");
    snprintf(ack, ack_size, "%s:ACK", status_value);
    result->kind = RMAL_VALUE_STRING;
    result->as.string = ack;
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
    if (argc < 2 || argc > 3) {
        fprintf(stderr, "usage: fkdb_live_query_host <fkdb_live_query.rmal> [query]\n");
        return 64;
    }
    const char *query = argc == 3 ? argv[2] : "";

    char *source = read_file(argv[1]);
    if (!source) {
        fprintf(stderr, "cannot read FKDB live query program: %s\n", argv[1]);
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

    FkdbQueryHost host = {0};
    host.query = query;
    status = rmal_vm_bind_native(vm, "FkdbQueryText", 0U, query_text, &host);
    if (!status.ok) {
        rmal_vm_free(vm);
        rmal_bytecode_free(bytecode);
        rmal_program_free(program);
        return print_status("bind-text", &status);
    }
    status = rmal_vm_bind_native(vm, "FkdbQueryResult", 4U, query_result, &host);
    if (!status.ok) {
        rmal_vm_free(vm);
        rmal_bytecode_free(bytecode);
        rmal_program_free(program);
        return print_status("bind-result", &status);
    }

    RmalValue result = {0};
    status = rmal_vm_run(vm, bytecode, true, &result);
    rmal_value_free(&result);

    int rc = 0;
    if (!status.ok) {
        rc = print_status("run", &status);
    } else if (!host.received) {
        fprintf(stderr, "FKDB live query produced no result\n");
        rc = 67;
    } else {
        printf("FKDB_LIVE_QUERY_HOST_PASS\n");
        printf(
            "FKDB_LIVE_QUERY_RECEIPT status=%s route=%s cost=%s source_preserved=true query_bytes=%zu\n",
            host.status, host.route, host.cost, strlen(query)
        );
    }

    rmal_vm_free(vm);
    rmal_bytecode_free(bytecode);
    rmal_program_free(program);
    return rc;
}

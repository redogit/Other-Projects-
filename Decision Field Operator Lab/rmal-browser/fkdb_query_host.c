#include "rmal/rmal.h"

#include <stdio.h>
#include <stdlib.h>

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
        fprintf(stderr, "usage: fkdb_query_host <fkdb_query.rmal>\n");
        return 64;
    }

    char *source = read_file(argv[1]);
    if (!source) {
        fprintf(stderr, "cannot read FKDB query kernel: %s\n", argv[1]);
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

    RmalValue result = {0};
    status = rmal_vm_run(vm, bytecode, true, &result);
    rmal_value_free(&result);

    int rc = 0;
    if (!status.ok) {
        rc = print_status("run", &status);
    } else {
        printf("FKDB_QUERY_HOST_PASS\n");
        printf("policy_in_rmal=true\n");
        printf("python_runtime_used=false\n");
        printf("FKDB_QUERY_RECEIPT policy_in_rmal=true python_runtime_used=false\n");
    }

    rmal_vm_free(vm);
    rmal_bytecode_free(bytecode);
    rmal_program_free(program);
    return rc;
}

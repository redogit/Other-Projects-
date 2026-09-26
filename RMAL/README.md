# RMAL 3 — C++20 Language Toolchain

RMAL is a programming language implementation in C++20.

Pipeline:

`source -> lexer -> parser -> AST -> compiler -> RMALBC1 bytecode -> VM -> trace/audit`

The native language keeps the established RMAL declarative carriers (`CONTEXT`, `RELATION`, `PRESERVE`, `CLAIM`, `EVIDENCE`, `VERIFY`, etc.) while adding executable programming constructs: constants and variables, functions and recursion, conditionals, loops, arithmetic, strings, booleans, assertions and printing.

## Build

```bash
cmake -S RMAL -B RMAL/build
cmake --build RMAL/build --config Release
ctest --test-dir RMAL/build --output-on-failure
```

## CLI

```text
rmalc check file.rmal
rmalc compile file.rmal
rmalc run file.rmal
rmalc trace file.rmal
rmalc audit file.rmal
rmalc selfcheck
```

The implementation is dependency-light: C++20 standard library only.

## Evidence boundary

`PARSE != VALIDATE != EXECUTE != EVIDENCE != ADMIT`

Successful compiler execution establishes compiler/runtime behavior only. It does not promote scientific, historical, legal, or other domain claims carried by RMAL source.

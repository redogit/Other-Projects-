# RMAPL v0 Grammar

Status: bounded reference profile. This is **not** a claim that RMALC accepts RMAPL syntax.

```text
program       := "RMAPL 0" NL "PROGRAM " IDENT NL "LOAD " IDENT NL bound* block* "RUN" NL?
bound         := "BOUND " IDENT "=" JSON NL
block         := repair | fitter
repair        := "REPAIR " IDENT NL
                 "WHEN " STRING NL
                 "REQUIRES " JSON_ARRAY NL
                 "TARGETS " JSON_ARRAY NL
                 "PRESERVES " JSON_ARRAY NL
                 "MAY_MUTATE " JSON_ARRAY NL
                 "FORBIDS " JSON_ARRAY NL
                 "APPLY " IDENT NL
                 "EVIDENCE " JSON_ARRAY NL
                 "COST " JSON_NUMBER NL
                 "END" NL
fitter        := "FITTER " IDENT NL
                 "WHEN " STRING NL
                 "REQUIRES " JSON_ARRAY NL
                 "PRESERVES " JSON_ARRAY NL
                 "OBJECTIVES " JSON_OBJECT NL
                 "APPLY " IDENT NL
                 "EVIDENCE " JSON_ARRAY NL
                 "COST " JSON_NUMBER NL
                 "END" NL
```

Identifiers match `[A-Za-z_][A-Za-z0-9_.:-]*`.

JSON is strict finite JSON. `NaN`, `Infinity`, comments inside JSON, duplicate language fields, missing fields, reordered block fields, unknown top-level operations, duplicate block identifiers, duplicate bounds, negative cost, and content after `RUN` fail closed.

`WHEN` is an exact residual-kind string in v0. It is not an arbitrary expression language.

`OBJECTIVES` maps objective names to exactly `"max"` or `"min"`.

The parser produces immutable RMAPL IR records. Runtime operator semantics are supplied by an explicit registry; parsing a program does not admit, verify, or execute an operator.

```text
PARSE_PASS != OPERATOR_ADMISSION
RMAPL_PROFILE != RMAL_CORE_FRONTEND
```

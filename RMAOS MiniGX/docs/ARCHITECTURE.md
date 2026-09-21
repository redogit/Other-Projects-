# MiniGX Architecture

MiniGX takes the live typed-dataflow strengths of vvvv, TouchDesigner, Max/Jitter and Pure Data and rebuilds them under RMAL/RMAOS contracts.

## Domains

`STATE FIELD OBSERVER CONTROL GEOMETRY POINT RELATION SIGNAL FEEDBACK POST TRACE GAME`

## Identity and provenance

The graph `digest` is semantic: source filename, comments and layout do not change it. The IR separately records `provenance.source_file` and `provenance.source_sha256`.

## Compiler fail-closed rules

Unknown ops/families/relations, duplicate directives, duplicate fields/params/nodes/claims/edges, negative stages, missing endpoints, invalid feedback sources and undeclared ordinary cycles are rejected.

## Runtime fail-closed rules

The Android runtime verifies schema/digest/cardinality/execution order/endpoints and requires one backend mapping for every declared current op. RMAL parameters drive shader carrier selection and native graphics/control parameters.

`FRAME_FEEDBACK` is currently scalar frame-state feedback, not a framebuffer/texture feedback pass. That distinction is explicit.

## Single-source shader carrier

Root `shaders/` are authoritative. Gradle syncs them into generated APK assets; committed duplicate Android shader copies are forbidden. CI byte-compares packaged assets back to root source.

## Scientific boundary

W114 remains the frozen mathematical object; MiniGX is a visualization/interaction/search carrier. Visual survival is not algebraic-cycle evidence.

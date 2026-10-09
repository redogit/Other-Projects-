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

The W114 circuit and fragment shader are authoritative in the canonical Hodge repository. The root dependency lock pins their commit and SHA-256 checksums. Explicit `python3 tools/hodge_dependency.py fetch` from the repository root provisions a verified checkout; consumers do not fetch implicitly or fall back to deleted local copies.

The generic fullscreen vertex shader remains under MiniGX `shaders/`. Gradle tracks the lock, resolver, compiler, asset generator, both canonical inputs and vertex shader, then generates the Java contract, IR and APK shader assets. The generator removes stale owned assets. CI byte-compares packaged shaders and the entire IR, including canonical raw-source provenance, and rejects duplicate or unexpected MiniGX assets. Committed duplicate Android shader copies are forbidden.

## Scientific boundary

W114 remains the frozen mathematical object; MiniGX is a visualization/interaction/search carrier. Visual stability is not algebraic-cycle evidence.

# RMAOS MiniGX — RMAL Circuit Graphics Runtime

MiniGX is the native graphics/circuit successor for RMAOS MINGX (`org.rmaos.mingx`). The browser/WebView carrier remains predecessor evidence.

## Authority chain

```text
RMAL circuit source
 -> fail-closed MiniGX compiler
 -> semantic MiniGX digest + separate source provenance hash
 -> typed execution order
 -> generated Java contract
 -> native OpenGL ES 3.1 RMAOS runtime
 -> trace/game carrier
```

The semantic digest is independent of the source filename. Carrier filename and raw-source SHA-256 are retained separately as provenance.

## Runtime binding

The compiled graph now controls the runtime shader carrier, ray-step limit, Five-Eyes count, spark/branch budgets, visual BPM, frame-state feedback decay/mix, bloom and exposure. Every current MiniGX op must have exactly one runtime backend mapping or startup fails closed.

Shaders have one source of truth under `shaders/`; Gradle copies those exact bytes into the APK. CI compares packaged shader bytes and embedded IR against source after every build.

## Hard gates

- 14 compiler/unit tests.
- 5,000 generated DAGs + 5,000 injected-cycle counterprobes.
- 250,000-operation deterministic Java game-state stress.
- GLSL vertex/fragment validation.
- Native Android build.
- APK source/IR parity.
- Existing Decision Field/RMAPL regression suite remains separate.

## Boundaries

```text
MINIGX_RMAL_SURFACE != RMALC_CORE_FRONTEND
GPU_VISUAL != HODGE_EVIDENCE
GAME_SURVIVOR != ALGEBRAIC_CYCLE
GAME_SCORE != MATHEMATICAL_EVIDENCE
COGNATE != IDENTITY
GENERATE != VERIFY != ADMIT
COMPILED != TRUE
SOFTWARE_VERIFICATION != MATHEMATICAL_PROOF
```

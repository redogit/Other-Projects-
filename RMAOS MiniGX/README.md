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

The W114 circuit and fragment shader are canonical in [Hodge](https://github.com/redogit/hodge), at `experiments/w114-perturbation/rmaos/circuits/w114_perturbation.rmal` and `experiments/w114-perturbation/rmaos/shaders/w114_field.frag`. This repository retains the generic compiler, native MiniGX runtime and fullscreen vertex shader. `../dependencies/hodge.lock.json` pins the canonical commit and exact artifact checksums; no local W114 source copy is authoritative.

From the repository root, provision the dependency explicitly before verification or builds:

```sh
python3 tools/hodge_dependency.py fetch
cd 'RMAOS MiniGX'
python3 VERIFY.py
python3 -m unittest discover -v -s toolchain -p 'test*.py'
cd android/rmaos-minigx
gradle :app:assembleDebug
```

The fetch creates a detached canonical checkout under `.dependencies/hodge`. For an already provisioned checkout, set `HODGE_REPOSITORY_ROOT` to its absolute path; the same commit and checksum checks apply. Consumers never fetch implicitly and fail with the provisioning instruction if inputs are unavailable or changed. The source archive includes the lock and resolver so this recipe also works after extraction. Generated IR retains the canonical circuit filename and unchanged raw-source hash; historical evidence files remain frozen.

## Runtime binding

The compiled graph now controls the runtime shader carrier, ray-step limit, five-observer count, point/branch budgets, pulse rate, frame-state feedback decay/mix, bloom and exposure. Every current MiniGX op must have exactly one runtime backend mapping or startup fails closed.

The W114 fragment has one canonical source in Hodge; the generic vertex shader remains under `shaders/`. Gradle verifies both canonical inputs and generates the Java contract, IR and exact shader bytes in build assets. CI compares packaged shader bytes and the complete embedded IR, including raw-source provenance, against verified inputs after every build.

## Hard gates

- 14 compiler/unit tests plus canonical asset generation and parity regressions.
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
ROBUST_GAME_CANDIDATE != ALGEBRAIC_CYCLE
GAME_SCORE != MATHEMATICAL_EVIDENCE
COGNATE != IDENTITY
GENERATE != VERIFY != ADMIT
COMPILED != TRUE
SOFTWARE_VERIFICATION != MATHEMATICAL_PROOF
```

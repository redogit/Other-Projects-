# RMAOS MiniGX — RMAL Circuit Graphics Runtime

**Status:** new native RMAOS MINGX graphics/circuit carrier.

MiniGX rebuilds the Five Eyes Fermat FIRE prototype as a native Android GPU runtime under the canonical RMAOS package identity \`org.rmaos.mingx\`.

## Source-of-truth chain

\`\`\`text
RMAL circuit source
  -> MiniGX compiler (minigxc.py)
  -> canonical rmaos/minigx-ir/v1
  -> deterministic SHA-256 graph digest
  -> generated Java graph contract
  -> native RMAOS MINGX OpenGL ES 3.1 runtime
  -> visual field + game state + trace taps
\`\`\`

The browser/WebView game is predecessor evidence, not the MiniGX runtime.

## Implemented

- RMAL ENTITY/RELATE circuit surface using established RMAL semantic forms.
- Fail-closed MiniGX compiler with typed node/operator whitelist.
- Explicit FEEDBACK_TO cycles; accidental ordinary dataflow cycles are rejected.
- Canonical JSON IR and generated Java graph metadata.
- Native GLSurfaceView / OpenGL ES 3.1 renderer. No WebView and no Internet permission.
- Standalone shader assets validated separately from Java.
- Procedural field shader: volumetric FIRE, five orbiting eyes, circuits, sparks and storm shell.
- Native touch: drag, pinch, tap FIRE, double-tap REVERSE/BBF, long-press HOMEWARD.
- Stable CYC:MGX object IDs, integrity, unique-way coverage, score/combo, ASH, EMBER, SURVIVOR.
- Native HUD over the GPU surface.
- Frozen W114 center carried in the RMAL graph.

## Build

\`\`\`sh
python VERIFY.py
python -m unittest -v toolchain/test_minigxc.py
cd android/rmaos-minigx
gradle :app:assembleDebug
\`\`\`

The existing RMAOS raw-metal direction remains compatible: package identity is \`org.rmaos.mingx\`, \`minSdk=33\`, \`targetSdk=35\`, and the compiler is Python.

## Boundaries

\`\`\`text
MINIGX_RMAL_SURFACE != RMALC_CORE_FRONTEND
MINIGX_IR != MATHEMATICAL_OBJECT
GPU_VISUAL != HODGE_EVIDENCE
GAME_SURVIVOR != ALGEBRAIC_CYCLE
GAME_SCORE != MATHEMATICAL_EVIDENCE
COGNATE != IDENTITY
VISUAL_PROJECTION_ORBIT != MATHEMATICAL_DIMENSION
GENERATE != VERIFY != ADMIT
COMPILED != TRUE
SOFTWARE_VERIFICATION != MATHEMATICAL_PROOF
\`\`\`

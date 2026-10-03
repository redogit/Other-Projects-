# Independent Browser — RMAL / RMALC bootstrap

This directory is the first migration rung away from the Python-hosted RMAPL
runtime used by the independent browser.

## Authority

RMAL and RMALC are **not copied into this repository**.

The build pins the canonical toolchain:

- repository: `redogit/DnD`
- branch lineage: `master`
- exact commit: `57786dd85cb13c4a8f657ae4a66ca6d4058854fa`
- RMAL / RMALC: 3.1
- implementation: ISO C23

`CMakeLists.txt` fetches that exact commit and fails if the resulting Git head
does not match the pin.

## What this proves

`browser_bootstrap.rmal` runs browser orchestration in the canonical RMAL VM.
The host binds one opt-in native capability, `BrowserHandoff(string)`, through
RMAL's stable C callback ABI.

The checked sequence covers:

```text
render:
  HTML_TOKENIZE
  DOM_BUILD
  LAYOUT
  HIT_MAP
  RASTER
  FRAME_VERIFY
  CAMERA_PACK
  FRAME_ADMIT

network:
  URL_RESOLVE
  HTTPS_PLAN
  NATIVE_TLS
  HTTP_RESPONSE_ADMIT

render again
PRESENT
```

The RMAL program owns the order and assertions. The C host only acknowledges
the explicit capability boundary and fails on any unexpected handoff.

This path executes without Python.

## Build

```sh
cmake -S "Decision Field Operator Lab/rmal-browser" \
      -B build/rmal-browser \
      -G Ninja \
      -DCMAKE_C_COMPILER=clang \
      -DCMAKE_BUILD_TYPE=Release
cmake --build build/rmal-browser --parallel
ctest --test-dir build/rmal-browser --output-on-failure
```

## Migration boundary

This is deliberately **not** a claim that arbitrary RMAPL already compiles to
RMAL.

```text
CURRENT BROWSER:
RMAPL source -> Python RMAPL parser/VM -> native carriers

BOOTSTRAP NOW ADDED:
RMAL source -> RMALC -> native RMAL VM -> explicit browser handoffs

NEXT:
RMAPL operator lowering -> RMAL source -> RMALC -> native RMAL VM
                                              -> existing native carriers

LATER:
RMAPL lowering implemented in RMAL itself
```

Claim ceilings:

- `RMAL_BOOTSTRAP != FULL_RMAPL_LOWERING`
- `NATIVE_RMAL_VM != SELF_HOSTED_RMAPL_COMPILER`
- `HANDOFF_SEQUENCE_VERIFIED != BROWSER_SEMANTIC_EQUIVALENCE`
- `PINNED_TOOLCHAIN != FORKED_TOOLCHAIN_AUTHORITY`

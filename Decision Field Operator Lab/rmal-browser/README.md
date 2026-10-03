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


## First semantic migration: HTTP request planning

`browser_http_plan.rmal` ports the bounded semantics of
`independent_browser_http.rmapl::browser_http_plan` onto native RMAL.

The RMAL implementation owns:

- HTTP -> port 80 / `native-http-transport-pending`;
- HTTPS -> port 443 / `native-tls-transport-pending`;
- exact HTTP/1.1 GET request construction;
- the 262144-byte response bound;
- unsupported-scheme refusal.

`browser_rmal_http_plan_host` executes that logic under the native RMAL VM and
emits a Python-free receipt.

`verify_http_plan_equivalence.py` then uses the existing RMAPL planner only as
a differential oracle and requires equal host, port, residual kind/detail,
response bound and exact request bytes for HTTP and HTTPS fixtures.

```text
RMAPL planner ───────┐
                     ├─ exact bounded equivalence check
RMAL/RMALC planner ──┘

RMAL runtime path: no Python
Differential verifier: Python test oracle only
```

This advances the migration boundary:

```text
before: browser orchestration only in RMAL
now:    browser orchestration + HTTP request-planning semantics in RMAL
next:   lower additional RMAPL operator families, then automate lowering
```

Additional ceiling:

- `BOUNDED_HTTP_PLAN_EQUIVALENCE != GENERAL_RMAPL_LOWERING`
- `PYTHON_DIFFERENTIAL_ORACLE != RMAL_RUNTIME_DEPENDENCY`


## Automated lowering family: HTTP request planner

The HTTP planner is no longer maintained twice by hand.

Canonical semantic source:

```text
examples/independent_browser_http.rmapl
  OPERATOR browser_http_plan
```

Lowering contract:

```text
browser_http_plan.lowering.json
        +
lower_rmapl_http_plan.py
        ↓
browser_http_plan.rmal
        ↓
RMALC 3.1
        ↓
native RMAL VM
```

`browser_http_plan.rmal` is a generated artifact. The lowerer consumes the
immutable RMAPL parser IR and accepts only the admitted planner family. It fails
closed if the operator introduces a new opcode, branch label, input path,
output path, residual shape, request-construction chain, or return shape.

CI requires all three layers simultaneously:

1. committed generated RMAL == lowerer output from current RMAPL;
2. generated RMAL parses/compiles/runs under pinned canonical RMALC;
3. native RMAL output remains exactly equivalent to the current RMAPL planner
   for the bounded HTTP/HTTPS fixtures.

Python is currently used to perform this **build-time lowering and differential
verification**. It is not used by the generated RMAL runtime path.

```text
BUILD_TIME_PYTHON != RUNTIME_PYTHON
GENERATED_RMAL != PROVED_GENERAL_LOWERING
BOUNDED_LOWERING_FAMILY != ALL_RMAPL
```

The next migration obligation is to expand the fail-closed lowering families,
then implement the lowerer itself in RMAL so the final build-time Python
dependency can be retired without discarding the RMAPL evidence lineage.


## Generated HTTP response-admission family

`browser_http_response.rmal` is generated from
`independent_browser_http.rmapl::browser_http_response_admit`.

RMAL owns the policy:

- require the bounded `HTTP/1.1 200 ` status prefix;
- scan for the first `CRLF CRLF` header/body delimiter;
- require a non-empty body;
- request bounded UTF-8 projection of that body;
- choose admitted vs invalid residual/consequence;
- declare the admitted state-transition contract:
  append current URL to history, promote pending URL, clear navigation
  transients, and clear render state before the next HTML-tokenization pass.

The native host does **not** decide any of those. It exposes only the mechanical
operations RMAL 3.1 currently lacks because its executable value domain has no
byte-buffer kind:

```text
BrowserResponseSelect(test fixture)
BrowserResponseLength()
BrowserResponseByte(index)
BrowserResponseUtf8(start, length)
BrowserResponseResult(...)   # records RMAL's decision
```

The response migration is checked against four byte streams:

- valid 200 + HTML body;
- 404 response;
- 200 response missing `CRLF CRLF`;
- 200 response with an empty body.

Differential verification compares RMAL against the current RMAPL operator for
status, body bytes, residual kind/detail, consequence, history append, pending
URL promotion, navigation clearing and render-state clearing.

```text
BYTE_MECHANICS_CALLBACKS != HTTP_POLICY
BOUNDED_RESPONSE_ADMISSION != GENERAL_HTTP_PARSER
PYTHON_DIFFERENTIAL_ORACLE != RMAL_RUNTIME_DEPENDENCY
```

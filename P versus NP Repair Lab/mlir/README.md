# P-vs-NP MLIR successor

This directory is the MLIR-based successor surface for the P-vs-NP Repair Lab.

## Boundary

The legacy Python/C++ execution paths remain authoritative for their current finite scope until the corresponding MLIR path has passed the frozen parity contract. Historical evidence files and negative results are predecessors and are not rewritten.

`MLIR parity is a representation/migration result, not evidence for P=NP or P!=NP.`

## Toolchain

- LLVM/MLIR: exactly `23.1.1` (`llvmorg-23.1.1`)
- CMake: `>= 3.20`
- Ninja
- C++17 for the MLIR project
- Python standard library for migration/parity tooling

The fast legacy path does not require MLIR. This project requires an explicit MLIR installation and does not vendor or silently download LLVM.

The CI gate constructs the toolchain from the official LLVM 23.1.1 source release rather than accepting a moving package alias:

```text
archive: llvm-project-23.1.1.src.tar.xz
sha256: ebe9be46fe8756d58c5b198ffad0fa2a766257add81a4dc52179bfacc7888ee6
```

That source identity is part of the parity environment. A future LLVM/MLIR version is a new environment and requires an explicit compatibility review rather than an automatic upgrade.

## Configure against an existing exact toolchain

Set `LLVM_DIR` and `MLIR_DIR` to the 23.1.1 CMake package directories:

```bash
cmake -S "P versus NP Repair Lab/mlir" \
  -B build/pnp-mlir \
  -G Ninja \
  -DMLIR_DIR="$MLIR_DIR" \
  -DLLVM_DIR="$LLVM_DIR"
```

Configuration fails when LLVM/MLIR is absent or does not match 23.1.1. That failure is intentional: an unreviewed ABI/API version is not silently admitted.

## Reproduce the exact source toolchain used by CI

```bash
LLVM_VERSION=23.1.1
LLVM_SHA256=ebe9be46fe8756d58c5b198ffad0fa2a766257add81a4dc52179bfacc7888ee6
curl --fail --location --output llvm-project-${LLVM_VERSION}.src.tar.xz \
  "https://github.com/llvm/llvm-project/releases/download/llvmorg-${LLVM_VERSION}/llvm-project-${LLVM_VERSION}.src.tar.xz"
printf '%s  %s\n' "$LLVM_SHA256" "llvm-project-${LLVM_VERSION}.src.tar.xz" | sha256sum --check --strict
tar -xJf "llvm-project-${LLVM_VERSION}.src.tar.xz"

cmake -S "llvm-project-${LLVM_VERSION}.src/llvm" -B build/llvm-${LLVM_VERSION} -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_ENABLE_PROJECTS=mlir \
  -DLLVM_TARGETS_TO_BUILD=Native \
  -DLLVM_ENABLE_ASSERTIONS=ON \
  -DLLVM_INCLUDE_TESTS=OFF \
  -DMLIR_INCLUDE_TESTS=OFF \
  -DLLVM_INCLUDE_EXAMPLES=OFF \
  -DLLVM_INCLUDE_BENCHMARKS=OFF \
  -DLLVM_INCLUDE_DOCS=OFF \
  -DMLIR_ENABLE_BINDINGS_PYTHON=OFF

cmake --build build/llvm-${LLVM_VERSION} --parallel 2 --target \
  llvm-config llvm-tblgen mlir-tblgen mlir-opt FileCheck not
```

Then configure this project with:

```bash
LLVM_DIR="$PWD/build/llvm-${LLVM_VERSION}/lib/cmake/llvm"
MLIR_DIR="$PWD/build/llvm-${LLVM_VERSION}/lib/cmake/mlir"
cmake -S "P versus NP Repair Lab/mlir" -B build/pnp-mlir -G Ninja \
  -DLLVM_DIR="$LLVM_DIR" -DMLIR_DIR="$MLIR_DIR"
```

## Build and test

```bash
cmake --build build/pnp-mlir --parallel 2 --target pnp-opt check-pnp-mlir
python3 -m unittest discover -s "P versus NP Repair Lab/mlir/test/python" -v
```

The Python parity tests can run before MLIR is present. The dialect parse/print/verifier tests require the exact MLIR toolchain.

## Frozen migration rule

```text
legacy executable semantics
        ↓
MLIR mirror
        ↓
parity verification
        ↓
MLIR-native passes
        ↓
legacy becomes reference/oracle
```

Do not demote the legacy implementation until the declared parity gate is green. A compact or cleaner IR is not itself evidence that computation became cheaper.

## Standing distinctions

```text
PROPOSAL != ADMISSION
REFERENCE != EVIDENCE
UNKNOWN != 0
UNKNOWN != false
TEMPORAL_SIGNAL != PROOF
LEVEL_UP != AUTHORITY_UP
COST_MOVED != COST_ELIMINATED
FINITE_PARITY != UNIVERSALITY
```

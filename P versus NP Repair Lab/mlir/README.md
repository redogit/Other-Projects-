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

## Configure

```bash
cmake -S "P versus NP Repair Lab/mlir" \
  -B build/pnp-mlir \
  -G Ninja \
  -DMLIR_DIR="$MLIR_DIR" \
  -DLLVM_DIR="$LLVM_DIR"
```

Configuration fails when LLVM/MLIR is absent or does not match 23.1.1. That failure is intentional: an unreviewed ABI/API version is not silently admitted.

## Build and test

After the dialect/tool tasks are present:

```bash
cmake --build build/pnp-mlir --target pnp-opt check-pnp-mlir
python3 -m unittest discover -s "P versus NP Repair Lab/mlir/test/python" -v
```

## Standing distinctions

```text
PROPOSAL != ADMISSION
REFERENCE != EVIDENCE
UNKNOWN != 0
UNKNOWN != false
TEMPORAL_SIGNAL != PROOF
LEVEL_UP != AUTHORITY_UP
```

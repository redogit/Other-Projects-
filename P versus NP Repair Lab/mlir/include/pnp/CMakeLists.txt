add_mlir_dialect(CoreOps pnp_core)
add_mlir_dialect(CarrierOps pnp_carrier)
add_mlir_dialect(EvidenceOps pnp_evidence)

set(LLVM_TARGET_DEFINITIONS CoreDialect.td)
mlir_tablegen(CoreOpsAttributes.h.inc -gen-attrdef-decls -attrdefs-dialect=pnp_core)
mlir_tablegen(CoreOpsAttributes.cpp.inc -gen-attrdef-defs -attrdefs-dialect=pnp_core)
add_mlir_dialect_tablegen_target(MLIRCoreAttributesIncGen)

add_custom_target(PNPMLIRHeaders
  DEPENDS
    MLIRCoreOpsIncGen
    MLIRCoreAttributesIncGen
    MLIRCarrierOpsIncGen
    MLIREvidenceOpsIncGen
)

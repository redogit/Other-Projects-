add_mlir_dialect(CoreOps pnp_core)
add_mlir_dialect(CarrierOps pnp_carrier)
add_mlir_dialect(EvidenceOps pnp_evidence)

add_custom_target(PNPMLIRHeaders
  DEPENDS
    MLIRCoreOpsIncGen
    MLIRCarrierOpsIncGen
    MLIREvidenceOpsIncGen
)

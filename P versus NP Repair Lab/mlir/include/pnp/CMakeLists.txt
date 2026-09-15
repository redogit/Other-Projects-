add_mlir_dialect(CoreOps pnp_core)
add_mlir_dialect(CarrierOps pnp_carrier)
add_mlir_dialect(EvidenceOps pnp_evidence)

add_dependencies(PNPMLIRHeaders
  MLIRCoreOpsIncGen
  MLIRCarrierOpsIncGen
  MLIREvidenceOpsIncGen
)

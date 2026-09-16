#ifndef PNP_EVIDENCE_DIALECT
#define PNP_EVIDENCE_DIALECT

include "mlir/IR/OpBase.td"


def PNPEvidence_Dialect : Dialect {
  let name = "pnp_evidence";
  let cppNamespace = "::pnp::evidence";
  let summary = "Verification, evidence state, cost vectors, and claim ceilings";
  let useDefaultTypePrinterParser = 1;
  let extraClassDeclaration = [{
    void registerTypes();
  }];
}

class PNPEvidence_Op<string mnemonic, list<Trait> traits = []>
    : Op<PNPEvidence_Dialect, mnemonic, traits>;

#endif

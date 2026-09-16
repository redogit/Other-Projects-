#ifndef PNP_EVIDENCE_TYPES
#define PNP_EVIDENCE_TYPES

include "mlir/IR/AttrTypeBase.td"
include "pnp/EvidenceDialect.td"

class PNPEvidence_Type<string name, string mnemonic, list<Trait> traits = []>
    : TypeDef<PNPEvidence_Dialect, name, traits> {
  let mnemonic = mnemonic;
}

def PNPEvidence_CertificateType : PNPEvidence_Type<"Certificate", "certificate"> {
  let summary = "Evidence certificate handle; presence does not imply independent verification";
}

#endif

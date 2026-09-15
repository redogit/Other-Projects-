#ifndef PNP_EVIDENCE_OPS
#define PNP_EVIDENCE_OPS

include "pnp/EvidenceTypes.td"
include "mlir/Interfaces/SideEffectInterfaces.td"


def PNPEvidence_CertificateOp : PNPEvidence_Op<"certificate", [Pure]> {
  let summary = "Reference a bounded certificate without promoting its claim";
  let arguments = (ins AnyType:$subject, StrAttr:$verifier, StrAttr:$reference);
  let results = (outs PNPEvidence_CertificateType:$result);
  let assemblyFormat = "$subject attr-dict `:` type($subject) `->` type($result)";
}

def PNPEvidence_RecordCostOp : PNPEvidence_Op<"record_cost"> {
  let summary = "Attach a named nonnegative cost vector to a certificate";
  let arguments = (ins PNPEvidence_CertificateType:$certificate, DictionaryAttr:$costs);
  let assemblyFormat = "$certificate attr-dict `:` type($certificate)";
  let hasVerifier = 1;
}

#endif

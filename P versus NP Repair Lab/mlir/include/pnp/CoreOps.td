#ifndef PNP_CORE_OPS
#define PNP_CORE_OPS

include "pnp/CoreDialect.td"
include "mlir/Interfaces/SideEffectInterfaces.td"


def PNPCore_SourceOp : PNPCore_Op<"source", [Pure]> {
  let summary = "Introduce a source problem carrier with stable identity";
  let arguments = (ins StrAttr:$source_id, StrAttr:$obligation);
  let results = (outs AnyType:$result);
  let assemblyFormat = "attr-dict `:` type($result)";
}

def PNPCore_ReturnOp : PNPCore_Op<"return"> {
  let summary = "Record an evidence-qualified symbolic verdict";
  let arguments = (ins AnyType:$subject, PNPCore_StatusAttr:$status);
  let assemblyFormat = "$subject attr-dict `:` type($subject)";
}

#endif

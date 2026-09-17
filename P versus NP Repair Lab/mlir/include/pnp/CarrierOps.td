#ifndef PNP_CARRIER_OPS
#define PNP_CARRIER_OPS

include "pnp/CarrierTypes.td"
include "mlir/Interfaces/SideEffectInterfaces.td"


def PNPCarrier_IdentityOp : PNPCarrier_Op<"identity", [Pure, AllTypesMatch<["input", "result"]>]> {
  let summary = "Identity transport used for carrier parse/print and parity tests";
  let arguments = (ins PNPCarrier_CarrierType:$input);
  let results = (outs PNPCarrier_CarrierType:$result);
  let assemblyFormat = "$input attr-dict `:` type($input)";
}

#endif

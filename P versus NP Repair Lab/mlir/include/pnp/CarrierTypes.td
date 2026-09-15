#ifndef PNP_CARRIER_TYPES
#define PNP_CARRIER_TYPES

include "mlir/IR/AttrTypeBase.td"
include "pnp/CarrierDialect.td"

class PNPCarrier_Type<string name, string mnemonic, list<Trait> traits = []>
    : TypeDef<PNPCarrier_Dialect, name, traits> {
  let mnemonic = mnemonic;
}

def PNPCarrier_CarrierType : PNPCarrier_Type<"Carrier", "carrier"> {
  let summary = "A typed representation carrying a declared obligation";
  let parameters = (ins StringRefParameter<"carrier kind">:$kind);
  let assemblyFormat = "`<` $kind `>`";
  let genVerifyDecl = 1;
}

#endif

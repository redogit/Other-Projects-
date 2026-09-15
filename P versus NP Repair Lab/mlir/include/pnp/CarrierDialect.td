#ifndef PNP_CARRIER_DIALECT
#define PNP_CARRIER_DIALECT

include "mlir/IR/OpBase.td"


def PNPCarrier_Dialect : Dialect {
  let name = "pnp_carrier";
  let cppNamespace = "::pnp::carrier";
  let summary = "Typed exact and obligation-relative carrier values";
  let useDefaultTypePrinterParser = 1;
  let extraClassDeclaration = [{
    void registerTypes();
  }];
}

class PNPCarrier_Op<string mnemonic, list<Trait> traits = []>
    : Op<PNPCarrier_Dialect, mnemonic, traits>;

#endif

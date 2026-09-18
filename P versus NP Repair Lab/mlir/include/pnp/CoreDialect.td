#ifndef PNP_CORE_DIALECT
#define PNP_CORE_DIALECT

include "mlir/IR/AttrTypeBase.td"
include "mlir/IR/OpBase.td"


def PNPCore_Dialect : Dialect {
  let name = "pnp_core";
  let cppNamespace = "::pnp::core";
  let summary = "Authority-bearing P-vs-NP problem and verdict semantics";
  let useDefaultAttributePrinterParser = 1;
  let extraClassDeclaration = [{
    void registerAttributes();
  }];
}

class PNPCore_Op<string mnemonic, list<Trait> traits = []>
    : Op<PNPCore_Dialect, mnemonic, traits>;

class PNPCore_Attr<string name, string attrMnemonic, list<Trait> traits = []>
    : AttrDef<PNPCore_Dialect, name, traits> {
  let mnemonic = attrMnemonic;
}

def PNPCore_StatusAttr : PNPCore_Attr<"Status", "status"> {
  let summary = "Symbolic SAT/UNSAT/UNKNOWN/BOUND status";
  let parameters = (ins StringRefParameter<"status literal">:$value);
  let assemblyFormat = "`<` $value `>`";
  let genVerifyDecl = 1;
}

#endif

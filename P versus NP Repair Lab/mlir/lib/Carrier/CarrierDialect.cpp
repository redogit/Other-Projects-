#include "pnp/CarrierDialect.h"
#include "pnp/CarrierOps.h"
#include "pnp/CarrierTypes.h"

#include "mlir/IR/Builders.h"
#include "mlir/IR/DialectImplementation.h"
#include "llvm/ADT/StringRef.h"
#include "llvm/ADT/TypeSwitch.h"

using namespace mlir;
using namespace pnp::carrier;

#include "pnp/CarrierOpsDialect.cpp.inc"

#define GET_TYPEDEF_CLASSES
#include "pnp/CarrierOpsTypes.cpp.inc"

#define GET_OP_CLASSES
#include "pnp/CarrierOps.cpp.inc"

LogicalResult CarrierType::verify(function_ref<InFlightDiagnostic()> emitError,
                                  StringRef kind) {
  static constexpr StringLiteral allowed[] = {
      "cnf", "boundary_relation", "gf2", "bijunctive", "horn",
      "dual_horn", "matching", "explicit_relation", "shared_dag", "circuit",
      "partial_hard_survivor", "nullary"};
  for (StringRef item : allowed)
    if (kind == item)
      return success();
  return emitError() << "unknown carrier kind '" << kind << "'";
}

void PNPCarrierDialect::registerTypes() {
  addTypes<
#define GET_TYPEDEF_LIST
#include "pnp/CarrierOpsTypes.cpp.inc"
      >();
}

void PNPCarrierDialect::initialize() {
  addOperations<
#define GET_OP_LIST
#include "pnp/CarrierOps.cpp.inc"
      >();
  registerTypes();
}

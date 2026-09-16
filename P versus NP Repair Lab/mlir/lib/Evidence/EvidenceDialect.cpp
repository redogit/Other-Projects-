#include "pnp/EvidenceDialect.h"
#include "pnp/EvidenceOps.h"
#include "pnp/EvidenceTypes.h"

#include "mlir/IR/BuiltinAttributes.h"
#include "mlir/IR/DialectImplementation.h"

using namespace mlir;
using namespace pnp::evidence;

#include "pnp/EvidenceOpsDialect.cpp.inc"

#define GET_TYPEDEF_CLASSES
#include "pnp/EvidenceOpsTypes.cpp.inc"

void EvidenceDialect::registerTypes() {
  addTypes<
#define GET_TYPEDEF_LIST
#include "pnp/EvidenceOpsTypes.cpp.inc"
      >();
}

void EvidenceDialect::initialize() {
  addOperations<
#define GET_OP_LIST
#include "pnp/EvidenceOps.cpp.inc"
      >();
  registerTypes();
}

LogicalResult RecordCostOp::verify() {
  DictionaryAttr costs = getCosts();
  if (costs.empty())
    return emitOpError("requires at least one named cost dimension");

  for (NamedAttribute named : costs) {
    Attribute value = named.getValue();
    if (auto integer = dyn_cast<IntegerAttr>(value)) {
      if (integer.getValue().isNegative())
        return emitOpError("cost dimension '") << named.getName()
               << "' must be nonnegative";
      continue;
    }
    if (auto real = dyn_cast<FloatAttr>(value)) {
      if (real.getValueAsDouble() < 0.0)
        return emitOpError("cost dimension '") << named.getName()
               << "' must be nonnegative";
      continue;
    }
    return emitOpError("cost dimension '") << named.getName()
           << "' must be an integer or floating-point attribute";
  }
  return success();
}

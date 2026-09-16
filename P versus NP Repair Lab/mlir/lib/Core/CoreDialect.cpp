#include "pnp/CoreDialect.h"
#include "pnp/CoreAttrs.h"
#include "pnp/CoreOps.h"

#include "mlir/IR/DialectImplementation.h"
#include "llvm/ADT/StringSwitch.h"

using namespace mlir;
using namespace pnp::core;

#include "pnp/CoreOpsDialect.cpp.inc"

#define GET_ATTRDEF_CLASSES
#include "pnp/CoreOpsAttributes.cpp.inc"

LogicalResult StatusAttr::verify(function_ref<InFlightDiagnostic()> emitError,
                                 StringRef value) {
  bool valid = value == "SAT" || value == "UNSAT" || value == "UNKNOWN" ||
               value == "BOUND";
  if (valid)
    return success();
  return emitError() << "expected status SAT, UNSAT, UNKNOWN, or BOUND; got '"
                     << value << "'";
}

void CoreDialect::registerAttributes() {
  addAttributes<
#define GET_ATTRDEF_LIST
#include "pnp/CoreOpsAttributes.cpp.inc"
      >();
}

void CoreDialect::initialize() {
  addOperations<
#define GET_OP_LIST
#include "pnp/CoreOps.cpp.inc"
      >();
  registerAttributes();
}

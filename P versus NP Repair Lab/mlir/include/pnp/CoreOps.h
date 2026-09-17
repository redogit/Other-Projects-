#ifndef PNP_CORE_OPS_H
#define PNP_CORE_OPS_H

#include "pnp/CoreAttrs.h"
#include "pnp/CoreDialect.h"
#include "mlir/IR/OpDefinition.h"
#include "mlir/Interfaces/SideEffectInterfaces.h"

#define GET_OP_CLASSES
#include "pnp/CoreOps.h.inc"

#endif

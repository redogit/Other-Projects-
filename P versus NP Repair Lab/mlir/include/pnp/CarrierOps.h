#ifndef PNP_CARRIER_OPS_H
#define PNP_CARRIER_OPS_H

#include "pnp/CarrierDialect.h"
#include "pnp/CarrierTypes.h"
#include "mlir/IR/OpDefinition.h"
#include "mlir/Interfaces/SideEffectInterfaces.h"

#define GET_OP_CLASSES
#include "pnp/CarrierOps.h.inc"

#endif

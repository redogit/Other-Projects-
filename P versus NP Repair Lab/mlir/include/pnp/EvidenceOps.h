#ifndef PNP_EVIDENCE_OPS_H
#define PNP_EVIDENCE_OPS_H

#include "pnp/EvidenceDialect.h"
#include "pnp/EvidenceTypes.h"
#include "mlir/Bytecode/BytecodeOpInterface.h"
#include "mlir/IR/OpDefinition.h"
#include "mlir/Interfaces/SideEffectInterfaces.h"

#define GET_OP_CLASSES
#include "pnp/EvidenceOps.h.inc"

#endif

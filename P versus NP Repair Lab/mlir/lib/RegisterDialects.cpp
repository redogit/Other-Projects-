#include "pnp/RegisterDialects.h"

#include "pnp/CarrierDialect.h"
#include "pnp/CoreDialect.h"
#include "pnp/EvidenceDialect.h"
#include "mlir/IR/DialectRegistry.h"

void pnp::registerDialects(mlir::DialectRegistry &registry) {
  registry.insert<pnp::core::CoreDialect,
                  pnp::carrier::CarrierDialect,
                  pnp::evidence::EvidenceDialect>();
}

#ifndef PNP_REGISTER_DIALECTS_H
#define PNP_REGISTER_DIALECTS_H

namespace mlir {
class DialectRegistry;
}

namespace pnp {
void registerDialects(mlir::DialectRegistry &registry);
}

#endif

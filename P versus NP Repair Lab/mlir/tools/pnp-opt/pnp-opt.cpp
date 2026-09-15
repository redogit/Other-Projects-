#include "pnp/RegisterDialects.h"

#include "mlir/IR/DialectRegistry.h"
#include "mlir/Tools/mlir-opt/MlirOptMain.h"

int main(int argc, char **argv) {
  mlir::DialectRegistry registry;
  pnp::registerDialects(registry);
  return mlir::asMainReturnCode(
      mlir::MlirOptMain(argc, argv, "PNP carrier-wave optimizer\n", registry));
}

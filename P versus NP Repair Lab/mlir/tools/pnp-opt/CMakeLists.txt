add_llvm_executable(pnp-opt pnp-opt.cpp)
llvm_update_compile_flags(pnp-opt)
target_link_libraries(pnp-opt PRIVATE MLIROptLib PNPRegistration)
mlir_check_all_link_libraries(pnp-opt)

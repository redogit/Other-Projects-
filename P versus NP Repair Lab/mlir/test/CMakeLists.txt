configure_lit_site_cfg(
  ${CMAKE_CURRENT_SOURCE_DIR}/lit.site.cfg.py.in
  ${CMAKE_CURRENT_BINARY_DIR}/lit.site.cfg.py
  MAIN_CONFIG
  ${CMAKE_CURRENT_SOURCE_DIR}/lit.cfg.py
)

set(PNPMLIR_TEST_DEPENDS FileCheck count not)
if(TARGET pnp-opt)
  list(APPEND PNPMLIR_TEST_DEPENDS pnp-opt)
endif()

add_lit_testsuite(check-pnp-mlir "Running PNP MLIR tests"
  ${CMAKE_CURRENT_BINARY_DIR}
  DEPENDS ${PNPMLIR_TEST_DEPENDS}
)
set_target_properties(check-pnp-mlir PROPERTIES FOLDER "Tests")

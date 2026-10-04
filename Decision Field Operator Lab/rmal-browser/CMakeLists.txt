cmake_minimum_required(VERSION 3.25)
project(RMALBrowserBootstrap VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 23)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

include(FetchContent)

# Canonical authority remains redogit/DnD. Do not vendor or silently float.
# The JSON pin is the single source of toolchain identity for docs + build.
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/RMAL_TOOLCHAIN_PIN.json" RMAL_PIN_JSON)
string(JSON RMAL_AUTHORITY_REPOSITORY GET "${RMAL_PIN_JSON}" authority_repository)
string(JSON RMAL_AUTHORITY_COMMIT GET "${RMAL_PIN_JSON}" authority_commit)
string(JSON RMAL_PIN_LANGUAGE_VERSION GET "${RMAL_PIN_JSON}" language_version)
string(JSON RMAL_PIN_COMPILER_VERSION GET "${RMAL_PIN_JSON}" compiler_version)

if(NOT RMAL_PIN_LANGUAGE_VERSION STREQUAL "3.1" OR
   NOT RMAL_PIN_COMPILER_VERSION STREQUAL "3.1")
  message(FATAL_ERROR "Browser bootstrap currently requires RMAL/RMALC 3.1")
endif()

# Do not import the upstream test matrix into this component build.
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(RMAL_BUILD_DECISION_FIELD OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
  rmal_authority
  GIT_REPOSITORY ${RMAL_AUTHORITY_REPOSITORY}
  GIT_TAG ${RMAL_AUTHORITY_COMMIT}
  GIT_SHALLOW FALSE
)
FetchContent_MakeAvailable(rmal_authority)

execute_process(
  COMMAND git -C "${rmal_authority_SOURCE_DIR}" rev-parse HEAD
  OUTPUT_VARIABLE RMAL_FETCHED_COMMIT
  OUTPUT_STRIP_TRAILING_WHITESPACE
  RESULT_VARIABLE RMAL_GIT_RESULT
)
if(NOT RMAL_GIT_RESULT EQUAL 0)
  message(FATAL_ERROR "Could not verify fetched RMAL authority commit")
endif()
if(NOT RMAL_FETCHED_COMMIT STREQUAL RMAL_AUTHORITY_COMMIT)
  message(FATAL_ERROR
    "RMAL authority drift: expected ${RMAL_AUTHORITY_COMMIT}, got ${RMAL_FETCHED_COMMIT}")
endif()

add_executable(browser_rmal_host browser_rmal_host.c)
target_link_libraries(browser_rmal_host PRIVATE rmal)

add_executable(browser_rmal_http_plan_host browser_rmal_http_plan_host.c)
target_link_libraries(browser_rmal_http_plan_host PRIVATE rmal)

add_executable(browser_rmal_http_response_host browser_rmal_http_response_host.c)
target_link_libraries(browser_rmal_http_response_host PRIVATE rmal)

add_executable(browser_rmal_url_host browser_rmal_url_host.c)
target_link_libraries(browser_rmal_url_host PRIVATE rmal)

add_executable(browser_rmal_input_host browser_rmal_input_host.c)
target_link_libraries(browser_rmal_input_host PRIVATE rmal)

if(CMAKE_C_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(browser_rmal_host PRIVATE -Wall -Wextra -Wpedantic -Werror)
  target_compile_options(browser_rmal_http_plan_host PRIVATE -Wall -Wextra -Wpedantic -Werror)
  target_compile_options(browser_rmal_http_response_host PRIVATE -Wall -Wextra -Wpedantic -Werror)
  target_compile_options(browser_rmal_url_host PRIVATE -Wall -Wextra -Wpedantic -Werror)
  target_compile_options(browser_rmal_input_host PRIVATE -Wall -Wextra -Wpedantic -Werror)
elseif(MSVC)
  target_compile_options(browser_rmal_host PRIVATE /W4 /WX)
  target_compile_options(browser_rmal_http_plan_host PRIVATE /W4 /WX)
  target_compile_options(browser_rmal_http_response_host PRIVATE /W4 /WX)
  target_compile_options(browser_rmal_url_host PRIVATE /W4 /WX)
  target_compile_options(browser_rmal_input_host PRIVATE /W4 /WX)
endif()

set(BROWSER_BOOTSTRAP "${CMAKE_CURRENT_SOURCE_DIR}/browser_bootstrap.rmal")
set(BROWSER_HTTP_PLAN "${CMAKE_CURRENT_SOURCE_DIR}/browser_http_plan.rmal")
set(BROWSER_HTTP_RESPONSE "${CMAKE_CURRENT_SOURCE_DIR}/browser_http_response.rmal")
set(BROWSER_URL_RESOLVE "${CMAKE_CURRENT_SOURCE_DIR}/browser_url_resolve.rmal")
set(BROWSER_INPUT_ACTIVATE "${CMAKE_CURRENT_SOURCE_DIR}/browser_input_activate.rmal")

# Re-enable tests only for this integration after upstream has been added.
enable_testing()

add_test(
  NAME browser_rmalc_check
  COMMAND $<TARGET_FILE:rmalc> check "${BROWSER_BOOTSTRAP}"
)
add_test(
  NAME browser_rmalc_compile
  COMMAND $<TARGET_FILE:rmalc> compile "${BROWSER_BOOTSTRAP}"
)
add_test(
  NAME browser_rmal_native_host
  COMMAND $<TARGET_FILE:browser_rmal_host> "${BROWSER_BOOTSTRAP}"
)
set_tests_properties(
  browser_rmal_native_host
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAL_BROWSER_RECEIPT handoffs=21 python_runtime_used=false"
)

add_test(
  NAME browser_rmal_http_plan_check
  COMMAND $<TARGET_FILE:rmalc> check "${BROWSER_HTTP_PLAN}"
)
add_test(
  NAME browser_rmal_http_plan_compile
  COMMAND $<TARGET_FILE:rmalc> compile "${BROWSER_HTTP_PLAN}"
)
add_test(
  NAME browser_rmal_http_plan_native
  COMMAND $<TARGET_FILE:browser_rmal_http_plan_host> "${BROWSER_HTTP_PLAN}"
)
set_tests_properties(
  browser_rmal_http_plan_native
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAL_HTTP_PLAN_RECEIPT calls=2 python_runtime_used=false"
)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

add_test(
  NAME browser_rmapl_http_plan_lowering_check
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/lower_rmapl_http_plan.py"
    --profile
    "${CMAKE_CURRENT_SOURCE_DIR}/browser_http_plan.lowering.json"
    --check
)
set_tests_properties(
  browser_rmapl_http_plan_lowering_check
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAPL_RMAL_HTTP_PLAN_LOWERING_CHECK PASS"
)

add_test(
  NAME browser_rmapl_rmal_http_plan_equivalence
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/verify_http_plan_equivalence.py"
    $<TARGET_FILE:browser_rmal_http_plan_host>
    "${BROWSER_HTTP_PLAN}"
)
set_tests_properties(
  browser_rmapl_rmal_http_plan_equivalence
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAPL_RMAL_HTTP_PLAN_EQUIVALENCE PASS"
)

add_test(
  NAME browser_rmal_http_response_check
  COMMAND $<TARGET_FILE:rmalc> check "${BROWSER_HTTP_RESPONSE}"
)
add_test(
  NAME browser_rmal_http_response_compile
  COMMAND $<TARGET_FILE:rmalc> compile "${BROWSER_HTTP_RESPONSE}"
)
add_test(
  NAME browser_rmal_http_response_native
  COMMAND $<TARGET_FILE:browser_rmal_http_response_host> "${BROWSER_HTTP_RESPONSE}"
)
set_tests_properties(
  browser_rmal_http_response_native
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAL_HTTP_RESPONSE_RECEIPT fixtures=4 policy_in_rmal=true python_runtime_used=false"
)

add_test(
  NAME browser_rmapl_http_response_lowering_check
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/lower_rmapl_http_response.py"
    --profile
    "${CMAKE_CURRENT_SOURCE_DIR}/browser_http_response.lowering.json"
    --check
)
set_tests_properties(
  browser_rmapl_http_response_lowering_check
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAPL_RMAL_HTTP_RESPONSE_LOWERING_CHECK PASS"
)

add_test(
  NAME browser_rmapl_rmal_http_response_equivalence
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/verify_http_response_equivalence.py"
    $<TARGET_FILE:browser_rmal_http_response_host>
    "${BROWSER_HTTP_RESPONSE}"
)
set_tests_properties(
  browser_rmapl_rmal_http_response_equivalence
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAPL_RMAL_HTTP_RESPONSE_EQUIVALENCE PASS"
)

add_test(
  NAME browser_rmal_url_check
  COMMAND $<TARGET_FILE:rmalc> check "${BROWSER_URL_RESOLVE}"
)
add_test(
  NAME browser_rmal_url_compile
  COMMAND $<TARGET_FILE:rmalc> compile "${BROWSER_URL_RESOLVE}"
)
add_test(
  NAME browser_rmal_url_native
  COMMAND $<TARGET_FILE:browser_rmal_url_host> "${BROWSER_URL_RESOLVE}"
)
set_tests_properties(
  browser_rmal_url_native
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAL_URL_RECEIPT fixtures=7 policy_in_rmal=true python_runtime_used=false"
)

add_test(
  NAME browser_rmapl_url_lowering_check
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/lower_rmapl_url_resolve.py"
    --profile
    "${CMAKE_CURRENT_SOURCE_DIR}/browser_url_resolve.lowering.json"
    --check
)
set_tests_properties(
  browser_rmapl_url_lowering_check
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAPL_RMAL_URL_RESOLVE_LOWERING_CHECK PASS"
)

add_test(
  NAME browser_rmapl_rmal_url_equivalence
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/verify_url_resolve_equivalence.py"
    $<TARGET_FILE:browser_rmal_url_host>
    "${BROWSER_URL_RESOLVE}"
)
set_tests_properties(
  browser_rmapl_rmal_url_equivalence
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAPL_RMAL_URL_RESOLVE_EQUIVALENCE PASS"
)

add_test(
  NAME browser_rmal_input_check
  COMMAND $<TARGET_FILE:rmalc> check "${BROWSER_INPUT_ACTIVATE}"
)
add_test(
  NAME browser_rmal_input_compile
  COMMAND $<TARGET_FILE:rmalc> compile "${BROWSER_INPUT_ACTIVATE}"
)
add_test(
  NAME browser_rmal_input_native
  COMMAND $<TARGET_FILE:browser_rmal_input_host> "${BROWSER_INPUT_ACTIVATE}"
)
set_tests_properties(
  browser_rmal_input_native
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAL_INPUT_RECEIPT fixtures=8 policy_in_rmal=true python_runtime_used=false"
)

add_test(
  NAME browser_rmapl_input_lowering_check
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/lower_rmapl_input_activation.py"
    --profile
    "${CMAKE_CURRENT_SOURCE_DIR}/browser_input_activate.lowering.json"
    --check
)
set_tests_properties(
  browser_rmapl_input_lowering_check
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAPL_RMAL_INPUT_ACTIVATION_LOWERING_CHECK PASS"
)

add_test(
  NAME browser_rmapl_rmal_input_equivalence
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/verify_input_activation_equivalence.py"
    $<TARGET_FILE:browser_rmal_input_host>
    "${BROWSER_INPUT_ACTIVATE}"
)
set_tests_properties(
  browser_rmapl_rmal_input_equivalence
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "RMAPL_RMAL_INPUT_ACTIVATION_EQUIVALENCE PASS"
)

# FKDB direct-successor layer. Historical Independent Browser targets above remain unchanged.
add_executable(fkdb_rmal_host fkdb_rmal_host.c)
target_link_libraries(fkdb_rmal_host PRIVATE rmal)

add_executable(fkdb_query_host fkdb_query_host.c)
target_link_libraries(fkdb_query_host PRIVATE rmal)

if(CMAKE_C_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(fkdb_rmal_host PRIVATE -Wall -Wextra -Wpedantic -Werror)
  target_compile_options(fkdb_query_host PRIVATE -Wall -Wextra -Wpedantic -Werror)
elseif(MSVC)
  target_compile_options(fkdb_rmal_host PRIVATE /W4 /WX)
  target_compile_options(fkdb_query_host PRIVATE /W4 /WX)
endif()

set(FKDB_BOOTSTRAP "${CMAKE_CURRENT_SOURCE_DIR}/fkdb_bootstrap.rmal")
set(FKDB_QUERY "${CMAKE_CURRENT_SOURCE_DIR}/fkdb_query.rmal")

add_test(
  NAME fkdb_rmalc_check
  COMMAND $<TARGET_FILE:rmalc> check "${FKDB_BOOTSTRAP}"
)
add_test(
  NAME fkdb_rmalc_compile
  COMMAND $<TARGET_FILE:rmalc> compile "${FKDB_BOOTSTRAP}"
)
add_test(
  NAME fkdb_native_host
  COMMAND $<TARGET_FILE:fkdb_rmal_host> "${FKDB_BOOTSTRAP}"
)
set_tests_properties(
  fkdb_native_host
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "FKDB_BROWSER_RECEIPT handoffs=27 direct_successor=true python_runtime_used=false"
)

add_test(
  NAME fkdb_query_rmalc_check
  COMMAND $<TARGET_FILE:rmalc> check "${FKDB_QUERY}"
)
add_test(
  NAME fkdb_query_rmalc_compile
  COMMAND $<TARGET_FILE:rmalc> compile "${FKDB_QUERY}"
)
add_test(
  NAME fkdb_query_native
  COMMAND $<TARGET_FILE:fkdb_query_host> "${FKDB_QUERY}"
)
set_tests_properties(
  fkdb_query_native
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "FKDB_QUERY_RECEIPT policy_in_rmal=true python_runtime_used=false"
)

add_test(
  NAME fkdb_local_surface
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_surface.py"
)
set_tests_properties(
  fkdb_local_surface
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)

add_test(
  NAME fkdb_page_manifest
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_manifest.py"
)
set_tests_properties(
  fkdb_page_manifest
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)

add_test(
  NAME fkdb_page_build_check
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../tools/build_fkdb_pages.py"
    --check
)
set_tests_properties(
  fkdb_page_build_check
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "FKDB_PAGE_BUILD_CHECK PASS"
)

add_executable(fkdb_live_query_host fkdb_live_query_host.c)
target_link_libraries(fkdb_live_query_host PRIVATE rmal)

if(CMAKE_C_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(fkdb_live_query_host PRIVATE -Wall -Wextra -Wpedantic -Werror)
elseif(MSVC)
  target_compile_options(fkdb_live_query_host PRIVATE /W4 /WX)
endif()

set(FKDB_LIVE_QUERY "${CMAKE_CURRENT_SOURCE_DIR}/fkdb_live_query.rmal")

add_test(
  NAME fkdb_live_query_check
  COMMAND $<TARGET_FILE:rmalc> check "${FKDB_LIVE_QUERY}"
)
add_test(
  NAME fkdb_live_query_compile
  COMMAND $<TARGET_FILE:rmalc> compile "${FKDB_LIVE_QUERY}"
)

add_test(
  NAME fkdb_live_query_history
  COMMAND $<TARGET_FILE:fkdb_live_query_host> "${FKDB_LIVE_QUERY}" HISTORY
)
set_tests_properties(
  fkdb_live_query_history
  PROPERTIES PASS_REGULAR_EXPRESSION
    "FKDB_LIVE_QUERY_RECEIPT status=MATCH route=history cost=2 source_preserved=true"
)

add_test(
  NAME fkdb_live_query_recover
  COMMAND $<TARGET_FILE:fkdb_live_query_host> "${FKDB_LIVE_QUERY}" RECOVER
)
set_tests_properties(
  fkdb_live_query_recover
  PROPERTIES PASS_REGULAR_EXPRESSION
    "FKDB_LIVE_QUERY_RECEIPT status=MATCH route=recover cost=4 source_preserved=true"
)

add_test(
  NAME fkdb_live_query_lineage
  COMMAND $<TARGET_FILE:fkdb_live_query_host> "${FKDB_LIVE_QUERY}" LINEAGE
)
set_tests_properties(
  fkdb_live_query_lineage
  PROPERTIES PASS_REGULAR_EXPRESSION
    "FKDB_LIVE_QUERY_RECEIPT status=MATCH route=lineage cost=6 source_preserved=true"
)

add_test(
  NAME fkdb_live_query_home
  COMMAND $<TARGET_FILE:fkdb_live_query_host> "${FKDB_LIVE_QUERY}" FKDB
)
set_tests_properties(
  fkdb_live_query_home
  PROPERTIES PASS_REGULAR_EXPRESSION
    "FKDB_LIVE_QUERY_RECEIPT status=MATCH route=fkdb cost=7 source_preserved=true"
)

add_test(
  NAME fkdb_live_query_empty
  COMMAND $<TARGET_FILE:fkdb_live_query_host> "${FKDB_LIVE_QUERY}"
)
set_tests_properties(
  fkdb_live_query_empty
  PROPERTIES PASS_REGULAR_EXPRESSION
    "FKDB_LIVE_QUERY_RECEIPT status=NO_MATCH route=fkdb cost=1 source_preserved=true"
)

add_test(
  NAME fkdb_live_query_unresolved
  COMMAND $<TARGET_FILE:fkdb_live_query_host> "${FKDB_LIVE_QUERY}" "WHAT IS THIS"
)
set_tests_properties(
  fkdb_live_query_unresolved
  PROPERTIES PASS_REGULAR_EXPRESSION
    "FKDB_LIVE_QUERY_RECEIPT status=UNRESOLVED route=fkdb cost=7 source_preserved=true"
)

add_test(
  NAME fkdb_live_query_decay
  COMMAND $<TARGET_FILE:fkdb_live_query_host> "${FKDB_LIVE_QUERY}" DECAY
)
set_tests_properties(
  fkdb_live_query_decay
  PROPERTIES PASS_REGULAR_EXPRESSION
    "FKDB_LIVE_QUERY_RECEIPT status=MATCH route=decay cost=3 source_preserved=true"
)

add_test(
  NAME fkdb_live_query_relate
  COMMAND $<TARGET_FILE:fkdb_live_query_host> "${FKDB_LIVE_QUERY}" RELATE
)
set_tests_properties(
  fkdb_live_query_relate
  PROPERTIES PASS_REGULAR_EXPRESSION
    "FKDB_LIVE_QUERY_RECEIPT status=MATCH route=relate cost=5 source_preserved=true"
)

add_test(
  NAME fkdb_source_index
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_index.py"
)
set_tests_properties(
  fkdb_source_index
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)

add_test(
  NAME fkdb_result_projection
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_result_projection.py"
)
set_tests_properties(
  fkdb_result_projection
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)


add_test(
  NAME fkdb_wasm_hif_contract
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_wasm_hif.py"
)
set_tests_properties(
  fkdb_wasm_hif_contract
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)

find_program(FKDB_NODE_EXECUTABLE NAMES node nodejs)
if(FKDB_NODE_EXECUTABLE)
  add_test(
    NAME fkdb_web_host_node
    COMMAND
      "${FKDB_NODE_EXECUTABLE}"
      "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_web_host.mjs"
  )
  set_tests_properties(
    fkdb_web_host_node
    PROPERTIES
      PASS_REGULAR_EXPRESSION
        "FKDB_WASM_HIF_NODE PASS"
  )
else()
  message(STATUS "Node.js not found: FKDB Web host behavioral test skipped; Python contract test remains active")
endif()


add_test(
  NAME fkdb_tool_carrier
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_tool_carrier.py"
)
set_tests_properties(
  fkdb_tool_carrier
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)


add_test(
  NAME fkdb_local_tool_bridge
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_local_tool_bridge.py"
)
set_tests_properties(
  fkdb_local_tool_bridge
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)


add_test(
  NAME fkdb_local_adapters
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_local_adapters.py"
)
set_tests_properties(
  fkdb_local_adapters
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)


add_test(
  NAME fkdb_adapter_mathbox
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_adapter_mathbox.py"
)
set_tests_properties(
  fkdb_adapter_mathbox
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)


add_test(
  NAME fkdb_adapter_superpowers
  COMMAND
    "${Python3_EXECUTABLE}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../test_fkdb_adapter_superpowers.py"
)
set_tests_properties(
  fkdb_adapter_superpowers
  PROPERTIES
    PASS_REGULAR_EXPRESSION
      "OK"
)

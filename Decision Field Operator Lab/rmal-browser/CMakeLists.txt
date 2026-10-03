cmake_minimum_required(VERSION 3.25)
project(RMALBrowserBootstrap VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 23)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

include(FetchContent)

# Canonical authority remains redogit/DnD. Do not vendor or silently float.
set(RMAL_AUTHORITY_REPOSITORY "https://github.com/redogit/DnD.git")
set(RMAL_AUTHORITY_COMMIT "57786dd85cb13c4a8f657ae4a66ca6d4058854fa")

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

if(CMAKE_C_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(browser_rmal_host PRIVATE -Wall -Wextra -Wpedantic -Werror)
elseif(MSVC)
  target_compile_options(browser_rmal_host PRIVATE /W4 /WX)
endif()

set(BROWSER_BOOTSTRAP "${CMAKE_CURRENT_SOURCE_DIR}/browser_bootstrap.rmal")

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

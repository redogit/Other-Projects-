cmake_minimum_required(VERSION 3.20)
project(PNPMLIR LANGUAGES C CXX)

set(PNP_LLVM_VERSION "23.1.1" CACHE STRING "Required LLVM/MLIR release")
set(CMAKE_CXX_STANDARD 17 CACHE STRING "C++ standard")
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(MLIR ${PNP_LLVM_VERSION} EXACT REQUIRED CONFIG)
find_package(LLVM ${PNP_LLVM_VERSION} EXACT REQUIRED CONFIG)

if(NOT LLVM_PACKAGE_VERSION VERSION_EQUAL PNP_LLVM_VERSION)
  message(FATAL_ERROR "PNP MLIR requires LLVM ${PNP_LLVM_VERSION}; found ${LLVM_PACKAGE_VERSION}")
endif()

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using MLIRConfig.cmake: ${MLIR_DIR}")

list(APPEND CMAKE_MODULE_PATH "${MLIR_CMAKE_DIR}" "${LLVM_CMAKE_DIR}")
include(TableGen)
include(AddLLVM)
include(AddMLIR)
include(HandleLLVMOptions)

separate_arguments(LLVM_DEFINITIONS_LIST NATIVE_COMMAND ${LLVM_DEFINITIONS})
add_definitions(${LLVM_DEFINITIONS_LIST})

include_directories(${LLVM_INCLUDE_DIRS})
include_directories(${MLIR_INCLUDE_DIRS})
include_directories(${PROJECT_SOURCE_DIR}/include)
include_directories(${PROJECT_BINARY_DIR}/include)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
set(PNPMLIR_SOURCE_DIR "${PROJECT_SOURCE_DIR}")
set(PNPMLIR_BINARY_DIR "${PROJECT_BINARY_DIR}")

add_subdirectory(include/pnp)
add_subdirectory(lib)
if(EXISTS "${PROJECT_SOURCE_DIR}/tools/pnp-opt/CMakeLists.txt")
  add_subdirectory(tools/pnp-opt)
endif()
add_subdirectory(test)

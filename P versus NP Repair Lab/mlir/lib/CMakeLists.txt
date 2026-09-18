add_mlir_dialect_library(PNPCore
  Core/CoreDialect.cpp
  PARTIAL_SOURCES_INTENDED
  ADDITIONAL_HEADER_DIRS ${PROJECT_SOURCE_DIR}/include
  DEPENDS
    MLIRCoreOpsIncGen
    MLIRCoreAttributesIncGen
  LINK_LIBS PUBLIC MLIRIR
)

add_mlir_dialect_library(PNPCarrier
  Carrier/CarrierDialect.cpp
  PARTIAL_SOURCES_INTENDED
  ADDITIONAL_HEADER_DIRS ${PROJECT_SOURCE_DIR}/include
  DEPENDS MLIRCarrierOpsIncGen
  LINK_LIBS PUBLIC MLIRIR
)

add_mlir_dialect_library(PNPEvidence
  Evidence/EvidenceDialect.cpp
  PARTIAL_SOURCES_INTENDED
  ADDITIONAL_HEADER_DIRS ${PROJECT_SOURCE_DIR}/include
  DEPENDS MLIREvidenceOpsIncGen
  LINK_LIBS PUBLIC MLIRIR
)

add_mlir_library(PNPRegistration
  RegisterDialects.cpp
  ADDITIONAL_HEADER_DIRS ${PROJECT_SOURCE_DIR}/include
  LINK_LIBS PUBLIC
    MLIRIR
    PNPCore
    PNPCarrier
    PNPEvidence
)

add_library(PNPMLIR INTERFACE)
target_link_libraries(PNPMLIR INTERFACE PNPRegistration)

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class LLVM23BuildContractTests(unittest.TestCase):
    def test_core_attribute_tablegen_is_explicit_and_depended_on(self):
        cmake = read("include/pnp/CMakeLists.txt")
        self.assertIn("CoreOpsAttributes.h.inc", cmake)
        self.assertIn("-gen-attrdef-decls", cmake)
        self.assertIn("CoreOpsAttributes.cpp.inc", cmake)
        self.assertIn("-gen-attrdef-defs", cmake)
        self.assertIn("MLIRCoreAttrsIncGen", cmake)
        headers = cmake.split("add_custom_target(PNPMLIRHeaders", 1)[1]
        self.assertIn("MLIRCoreAttrsIncGen", headers)

    def test_generated_definition_translation_units_include_required_support(self):
        expected_op_defs = {
            "lib/Core/CoreDialect.cpp": "pnp/CoreOps.cpp.inc",
            "lib/Carrier/CarrierDialect.cpp": "pnp/CarrierOps.cpp.inc",
            "lib/Evidence/EvidenceDialect.cpp": "pnp/EvidenceOps.cpp.inc",
        }
        for relative, generated in expected_op_defs.items():
            text = read(relative)
            with self.subTest(relative=relative):
                self.assertIn('"mlir/IR/Builders.h"', text)
                self.assertIn('"llvm/ADT/TypeSwitch.h"', text)
                self.assertIn("#define GET_OP_CLASSES", text)
                self.assertIn(f'#include "{generated}"', text)

    def test_generated_op_headers_expose_required_llvm23_interfaces(self):
        for relative in (
            "include/pnp/CoreOps.h",
            "include/pnp/CarrierOps.h",
            "include/pnp/EvidenceOps.h",
        ):
            text = read(relative)
            with self.subTest(relative=relative):
                self.assertIn('"mlir/Bytecode/BytecodeOpInterface.h"', text)
                self.assertIn('"mlir/IR/OpImplementation.h"', text)
                self.assertIn('"mlir/Interfaces/SideEffectInterfaces.h"', text)

    def test_dialect_libraries_keep_source_ownership_explicit_and_link_interfaces(self):
        cmake = read("lib/CMakeLists.txt")
        self.assertGreaterEqual(cmake.count("PARTIAL_SOURCES_INTENDED"), 3)
        self.assertGreaterEqual(cmake.count("MLIRSideEffectInterfaces"), 3)
        self.assertIn("MLIRCoreAttrsIncGen", cmake)

    def test_ods_helpers_avoid_shadowed_mnemonics_and_use_supported_type_match_trait(self):
        core = read("include/pnp/CoreDialect.td")
        carrier_types = read("include/pnp/CarrierTypes.td")
        evidence_types = read("include/pnp/EvidenceTypes.td")
        carrier_ops = read("include/pnp/CarrierOps.td")
        self.assertIn("string attrMnemonic", core)
        self.assertIn("let mnemonic = attrMnemonic;", core)
        self.assertIn("string typeMnemonic", carrier_types)
        self.assertIn("let mnemonic = typeMnemonic;", carrier_types)
        self.assertIn("string typeMnemonic", evidence_types)
        self.assertIn("let mnemonic = typeMnemonic;", evidence_types)
        self.assertIn('AllTypesMatch<["input", "result"]>', carrier_ops)
        self.assertNotIn("SameOperandsAndResultType", carrier_ops)

    def test_generated_dialect_class_names_are_used_consistently(self):
        expectations = {
            "lib/Core/CoreDialect.cpp": "PNPCoreDialect",
            "lib/Carrier/CarrierDialect.cpp": "PNPCarrierDialect",
            "lib/Evidence/EvidenceDialect.cpp": "PNPEvidenceDialect",
        }
        for relative, class_name in expectations.items():
            with self.subTest(relative=relative):
                self.assertIn(f"void {class_name}::initialize()", read(relative))
        registry = read("lib/RegisterDialects.cpp")
        self.assertIn("pnp::core::PNPCoreDialect", registry)
        self.assertIn("pnp::carrier::PNPCarrierDialect", registry)
        self.assertIn("pnp::evidence::PNPEvidenceDialect", registry)

    def test_lit_config_imports_the_llvm_config_it_uses(self):
        lit_cfg = read("test/lit.cfg.py")
        self.assertIn("from lit.llvm import llvm_config", lit_cfg)
        self.assertIn("llvm_config.use_default_substitutions()", lit_cfg)

    def test_reproduction_docs_match_ci_bootstrap_targets(self):
        readme = read("README.md")
        self.assertIn("MLIROptLib MLIRIR FileCheck not count", readme)
        self.assertNotIn("mlir-tblgen mlir-opt FileCheck not", readme)


if __name__ == "__main__":
    unittest.main()

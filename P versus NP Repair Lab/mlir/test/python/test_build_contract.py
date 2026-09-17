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
        for relative in (
            "lib/Core/CoreDialect.cpp",
            "lib/Carrier/CarrierDialect.cpp",
            "lib/Evidence/EvidenceDialect.cpp",
        ):
            text = read(relative)
            with self.subTest(relative=relative):
                self.assertIn('"mlir/IR/Builders.h"', text)
                self.assertIn('"llvm/ADT/TypeSwitch.h"', text)

    def test_pure_operation_headers_make_side_effect_interfaces_visible(self):
        for relative in (
            "include/pnp/CoreOps.h",
            "include/pnp/CarrierOps.h",
            "include/pnp/EvidenceOps.h",
        ):
            text = read(relative)
            with self.subTest(relative=relative):
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


if __name__ == "__main__":
    unittest.main()

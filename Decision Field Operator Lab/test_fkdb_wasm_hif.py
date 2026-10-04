from pathlib import Path
import json
import unittest


HERE = Path(__file__).resolve().parent
WEB = HERE / "fkdb" / "web"
WASM = HERE / "fkdb" / "wasm" / "wit"


class FkdbWasmHifContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capabilities = json.loads(
            (WEB / "capabilities.json").read_text(encoding="utf-8")
        )
        cls.host_js = (WEB / "fkdb-host.mjs").read_text(encoding="utf-8")
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.wit03 = (WASM / "0.3" / "fkdb-hif.wit").read_text(encoding="utf-8")
        cls.wit02 = (WASM / "0.2" / "fkdb-hif.wit").read_text(encoding="utf-8")
        cls.spec = (WEB / "WASM_HIF.md").read_text(encoding="utf-8")

    def test_modern_first_fallback_tiers_are_ordered(self):
        self.assertEqual(
            self.capabilities["tiers"],
            [
                "WASM_COMPONENT_0_3",
                "WASM_JSPI",
                "WASM_PROMISE_HANDOFF",
                "WASM_LEGACY_WEB",
                "JS_MODERN_FALLBACK",
                "JS_LEGACY_FALLBACK",
                "NATIVE_RMAL_FALLBACK",
            ],
        )
        self.assertEqual(
            self.capabilities["policy"],
            "FEATURE_DETECT_DONT_UA_SNIFF",
        )

    def test_component_capabilities_distinguish_native_and_browser_transpiled(self):
        capabilities = self.capabilities["capabilities"]
        self.assertIn("componentNative03", capabilities)
        self.assertIn("componentBrowserTranspiled03", capabilities)
        self.assertNotIn("componentModel03", capabilities)
        self.assertIn("WASM_COMPONENT_0_3", self.capabilities["tiers"])

    def test_no_user_agent_sniffing(self):
        lowered = self.host_js.lower()
        self.assertNotIn("useragent", lowered)
        self.assertNotIn("navigator.useragent", lowered)

    def test_wasi03_contract_is_native_async(self):
        self.assertIn("async func", self.wit03)
        self.assertIn("stream<u8>", self.wit03)
        self.assertIn("future<result<_, host-error>>", self.wit03)
        self.assertIn("world fkdb-browser", self.wit03)

    def test_wasi03_local_tools_are_native_async(self):
        for required in (
            "enum tool-locality",
            "record tool-descriptor",
            "record tool-carrier",
            "record import-request",
            "record local-run-request",
            "interface local-tools",
            "import-artifact: async func",
            "run-local: async func",
            "import local-tools;",
        ):
            self.assertIn(required, self.wit03)

    def test_wasi02_local_tools_use_explicit_operation_resources(self):
        for required in (
            "enum tool-locality",
            "record tool-descriptor",
            "record tool-carrier",
            "record import-request",
            "record local-run-request",
            "resource tool-operation",
            "interface local-tools",
            "begin-import: func",
            "begin-run: func",
            "import local-tools;",
        ):
            self.assertIn(required, self.wit02)
        self.assertNotIn("import-artifact: async func", self.wit02)
        self.assertNotIn("run-local: async func", self.wit02)

    def test_wasi02_contract_is_explicit_poll_compatibility(self):
        self.assertNotIn("async func", self.wit02)
        self.assertIn("resource query-operation", self.wit02)
        self.assertIn("poll: func()", self.wit02)
        self.assertIn("resource byte-reader", self.wit02)
        self.assertIn("world fkdb-browser-compat", self.wit02)

    def test_browser_surface_uses_progressive_module_loading(self):
        self.assertIn('type="module"', self.html)
        self.assertIn('name="viewport"', self.html)
        self.assertIn("<noscript>", self.html)
        self.assertIn("detectCapabilities", self.html)
        self.assertIn("selectHostProfile", self.html)

    def test_capability_contract_preserves_fkdb_invariants(self):
        invariants = set(self.capabilities["invariants"])
        self.assertIn("FALLBACK != SILENT_SEMANTIC_WEAKENING", invariants)
        self.assertIn("CANONICAL_ABI_TRANSLATION != EVIDENCE_TRANSFER", invariants)
        self.assertIn("UNRESOLVED != NEGATIVE", invariants)
        self.assertIn("RETURN UNRESOLVED", self.spec)


if __name__ == "__main__":
    unittest.main()

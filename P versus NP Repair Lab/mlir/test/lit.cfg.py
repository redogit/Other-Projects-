import os

import lit.formats
from lit.llvm import llvm_config

config.name = "PNPMLIR"
config.test_format = lit.formats.ShTest(False)
config.suffixes = [".mlir"]
config.excludes = ["CMakeLists.txt", "lit.cfg.py", "lit.site.cfg.py.in"]
config.test_source_root = os.path.dirname(__file__)
config.test_exec_root = os.path.dirname(config.pnpmlir_site_config)

llvm_config.use_default_substitutions()
llvm_config.with_environment("PATH", config.llvm_tools_dir, append_path=True)
llvm_config.with_environment("PATH", os.path.join(config.pnpmlir_binary_dir, "bin"), append_path=True)

tool_dirs = [config.llvm_tools_dir, os.path.join(config.pnpmlir_binary_dir, "bin")]
tools = ["FileCheck", "count", "not"]
llvm_config.add_tool_substitutions(tools, tool_dirs)

pnp_opt = os.path.join(config.pnpmlir_binary_dir, "bin", "pnp-opt")
if os.path.exists(pnp_opt):
    config.substitutions.append(("%pnp-opt", pnp_opt))

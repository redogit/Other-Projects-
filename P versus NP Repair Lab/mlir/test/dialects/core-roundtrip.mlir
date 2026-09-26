// RUN: %pnp-opt "%s" | FileCheck "%s"

module {
  %src = "pnp_core.source"() <{source_id = "compiler_0", obligation = "sat"}> : () -> !pnp_carrier.carrier<"cnf">
  "pnp_core.return"(%src) <{status = #pnp_core.status<"UNKNOWN">}> : (!pnp_carrier.carrier<"cnf">) -> ()
}

// CHECK: pnp_core.source
// CHECK: #pnp_core.status<"UNKNOWN">

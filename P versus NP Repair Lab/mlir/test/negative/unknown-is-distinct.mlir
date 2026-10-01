// RUN: not %pnp-opt "%s" 2>&1 | FileCheck "%s"

module {
  %src = "pnp_core.source"() <{source_id = "bad", obligation = "sat"}> : () -> !pnp_carrier.carrier<"cnf">
  "pnp_core.return"(%src) <{status = #pnp_core.status<"0">}> : (!pnp_carrier.carrier<"cnf">) -> ()
}

// CHECK: expected status SAT, UNSAT, UNKNOWN, or BOUND

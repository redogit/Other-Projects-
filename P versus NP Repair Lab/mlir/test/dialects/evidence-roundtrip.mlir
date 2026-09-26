// RUN: %pnp-opt "%s" | FileCheck "%s"

module {
  %src = "pnp_core.source"() <{source_id = "compiler_1", obligation = "sat"}> : () -> !pnp_carrier.carrier<"cnf">
  %cert = "pnp_evidence.certificate"(%src) <{verifier = "legacy.check", reference = "node_0.json"}> : (!pnp_carrier.carrier<"cnf">) -> !pnp_evidence.certificate
  "pnp_evidence.record_cost"(%cert) <{costs = {planning_row_operations = 2312 : i64, states_evaluated = 3 : i64}}> : (!pnp_evidence.certificate) -> ()
}

// CHECK: pnp_evidence.certificate
// CHECK: planning_row_operations = 2312
// CHECK: states_evaluated = 3

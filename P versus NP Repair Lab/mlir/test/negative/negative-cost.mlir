// RUN: not %pnp-opt %s 2>&1 | FileCheck %s

module {
  %src = "pnp_core.source"() <{source_id = "bad-cost", obligation = "sat"}> : () -> !pnp_carrier.carrier<"cnf">
  %cert = "pnp_evidence.certificate"(%src) <{verifier = "legacy.check", reference = "node.json"}> : (!pnp_carrier.carrier<"cnf">) -> !pnp_evidence.certificate
  "pnp_evidence.record_cost"(%cert) <{costs = {planning = -1 : i64}}> : (!pnp_evidence.certificate) -> ()
}

// CHECK: cost dimension 'planning' must be nonnegative

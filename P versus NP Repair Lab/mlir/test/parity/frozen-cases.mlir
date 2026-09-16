// RUN: %pnp-opt %s | FileCheck %s

module {
  %c0 = "pnp_core.source"() <{source_id = "compiler_0:k4", obligation = "sat", states_evaluated = 7 : i64, maximum_depth = 2 : i64}> : () -> !pnp_carrier.carrier<"cnf">
  "pnp_core.return"(%c0) <{status = #pnp_core.status<"UNSAT">}> : (!pnp_carrier.carrier<"cnf">) -> ()

  %c1 = "pnp_core.source"() <{source_id = "compiler_1:k4", obligation = "sat", states_evaluated = 3 : i64, maximum_depth = 2 : i64}> : () -> !pnp_carrier.carrier<"cnf">
  "pnp_core.return"(%c1) <{status = #pnp_core.status<"SAT">}> : (!pnp_carrier.carrier<"cnf">) -> ()

  %b0 = "pnp_core.source"() <{source_id = "balanced_0:k4", obligation = "sat", states_evaluated = 6 : i64, maximum_depth = 2 : i64}> : () -> !pnp_carrier.carrier<"cnf">
  "pnp_core.return"(%b0) <{status = #pnp_core.status<"SAT">}> : (!pnp_carrier.carrier<"cnf">) -> ()

  %b4 = "pnp_core.source"() <{source_id = "balanced_4:k4", obligation = "sat", states_evaluated = 7 : i64, maximum_depth = 2 : i64}> : () -> !pnp_carrier.carrier<"cnf">
  "pnp_core.return"(%b4) <{status = #pnp_core.status<"UNSAT">}> : (!pnp_carrier.carrier<"cnf">) -> ()

  %o0 = "pnp_core.source"() <{source_id = "compiler_0:one_round", obligation = "sat", states_evaluated = 29 : i64, maximum_depth = 5 : i64}> : () -> !pnp_carrier.carrier<"cnf">
  "pnp_core.return"(%o0) <{status = #pnp_core.status<"UNSAT">}> : (!pnp_carrier.carrier<"cnf">) -> ()

  %o1 = "pnp_core.source"() <{source_id = "compiler_1:one_round", obligation = "sat", states_evaluated = 3 : i64, maximum_depth = 2 : i64}> : () -> !pnp_carrier.carrier<"cnf">
  "pnp_core.return"(%o1) <{status = #pnp_core.status<"SAT">}> : (!pnp_carrier.carrier<"cnf">) -> ()
}

// CHECK-COUNT-6: pnp_core.return
// CHECK: #pnp_core.status<"UNSAT">
// CHECK: #pnp_core.status<"SAT">

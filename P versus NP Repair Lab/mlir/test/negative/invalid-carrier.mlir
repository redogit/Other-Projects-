// RUN: not %pnp-opt %s 2>&1 | FileCheck %s

module {
  %src = "pnp_core.source"() <{source_id = "bad-carrier", obligation = "sat"}> : () -> !pnp_carrier.carrier<"magic_answer">
}

// CHECK: unknown carrier kind 'magic_answer'

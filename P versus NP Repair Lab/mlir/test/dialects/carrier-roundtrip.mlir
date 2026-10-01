// RUN: %pnp-opt "%s" | FileCheck "%s"

module {
  %src = "pnp_core.source"() <{source_id = "xor-native", obligation = "sat"}> : () -> !pnp_carrier.carrier<"gf2">
  %same = "pnp_carrier.identity"(%src) : (!pnp_carrier.carrier<"gf2">) -> !pnp_carrier.carrier<"gf2">
}

// CHECK: !pnp_carrier.carrier<"gf2">
// CHECK: pnp_carrier.identity

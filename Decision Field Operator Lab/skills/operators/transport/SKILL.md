---
name: operator-transport
version: 0.1.0
description: Audit load-bearing transformations for preservation, reflection, recoverability, and grounded scope.
---

# TRANSPORT Skill

## Purpose
Determine whether a measurement, parser, abstraction, serializer, compiler, surrogate, reconstruction, or other carrier preserves the distinctions the obligation requires.

## Contract
For target equivalence `~T` and transport `f`, test within the declared domain:

- preservation: `x ~T y -> f(x) ~ f(y)`
- reflection/separation: `f(x) ~ f(y) -> x ~T y`

Equivalent shorthand when justified: `ker(f) = ~T`.

## Procedure
1. Freeze source domain, target representation, target equivalence, and admissible observations.
2. Test collapse: distinct source states become indistinguishable.
3. Test fracture: source-equivalent states become spuriously distinct.
4. Test escape: reasoning depends on objects/states outside the grounded admitted image.
5. Ask the reverse question: what source distinction becomes unrecoverable after transport?
6. Record whether raw evidence or an injective/reversible encoding remains available.
7. Bound all conclusions to the tested universe.

## Output
`TRANSPORT_AUDIT`: transport identity, source/target contracts, preservation result, reflection result, collapse/fracture/escape witnesses, recoverability status, unresolved cases, and claim ceiling.

## Stop / handoff
- suspected failure needs a discriminating witness -> `ATTACK`
- witnessed residual needs minimal correction -> `REPAIR`
- transport passes but downstream claim remains open -> return to the owning operator; transport success is not global certification.

# Mutable adjective aspects

September 14, 2026 · bounded sidecar experiment

`aspects.mjs` adds a deliberately narrow aspect-oriented sidecar around the compiled Garden executor. The aspect profile describes behavior with adjectives instead of giving the aspect authority to rewrite the compiled plan.

## Descriptor axes

- `scope`: local, task-wide, project-wide, cross-cutting, boundary-only, execution-only
- `effect`: observational, validating, annotative, measuring, decorative, protective
- `mutation`: immutable, bounded-mutable, reversible
- `persistence`: ephemeral, session-lived, checkpointed
- `predictability`: deterministic, seeded, reactive
- `purpose`: diagnostic, exploratory, adversarial, educational, playful, accessibility-oriented
- `temperament`: curious, conservative, whimsical, quiet, skeptical, experimental

Two fields are not mutable adjectives:

- `authority = sidecar-only`
- `semantics = preserved`

A profile that attempts to change either field is rejected.

## Mutation boundary

`mutateAspect(profile, seed, generation)` changes one permitted descriptive axis deterministically. The same input profile, seed and generation reproduces the same mutation. A mutation receipt retains the before/after adjective and can reconstruct the prior profile with `revertAspectMutation()`.

The current runtime does not accept arbitrary aspect hooks. It can observe calls, describe itself, mutate its own bounded adjective profile and record sidecar events, but executor outputs are forwarded unchanged. Routing/filtering are intentionally absent from the current effect vocabulary because those labels would imply semantic authority that this experiment does not grant.

## Evidence boundary

The standalone mutation tests exercise 1,000 deterministic/reversible generations. The repository test also wraps the real compiled Garden fixture executor and compares node, detail, hierarchy, relation, capability and search outputs before and after adjective mutation.

Passing these bounded checks would establish only that this sidecar implementation preserves the tested executor outputs. It would not establish general AOP safety, arbitrary hook safety, universal semantic preservation, or optimality.

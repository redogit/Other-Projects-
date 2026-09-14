# Operator Agents

Each operator skill has a paired bounded Agent. The Agent executes method; the Skill stores method; evidence decides truth.

## Common agent contract

Every Agent must:
1. load its paired `SKILL.md`;
2. validate the shared invocation envelope;
3. preserve source revision, provenance, authority scope, and claim ceiling;
4. distinguish observation from interpretation;
5. keep unknowns explicit;
6. write only the output packet authorized by its skill;
7. hand off missing obligations rather than silently absorbing another role;
8. never self-ratify or treat agreement as proof.

Agents are **role-separated reviewers**, not automatically independent reviewers. Independence requires a separate validated contract because shared model lineage, runtime, prompt lineage, filesystem, or evidence exposure can correlate them.

Use the smallest effective agent society. Add agents for speed, specialization, adversarial pressure, or role separation when marginal value exceeds coordination/usage cost.

## Root coordination

The owning/root orchestrator may decompose work and issue bounded contracts, but it cannot manufacture missing verification, economic, sentinel, or ratification authority. Cross-project work uses `COORDINATION.md` and must preserve each project's own admission boundary.

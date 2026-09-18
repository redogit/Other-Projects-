# RIPPING MANY ARMS OFF — Massive 3D Roguelike MMORPG

**World ID:** `rmao-world`  
**Status:** active successor design + bounded implementation seed.  
**Current renderer:** 2D transition prototype.  
**Target runtime:** massive chunk-streamed 3D world with server-authoritative shared state.

## World equation

`World = Stream3D(Seed, Space, PersistentDelta) + Runs + Entities + LimbGraphs + Authority`

Canonical spatial hierarchy:

`WorldSeed → Region → Sector → Chunk → Cell → Entity`

A client loads only the chunks needed for its current observation/control neighborhood. The world identity and durable deltas are larger than the loaded set.

## 3D streaming

Each chunk has:
- stable integer 3D coordinate;
- generator version;
- world seed;
- deterministic base hash;
- admitted persistent deltas;
- transient simulation set;
- render/physics LOD state.

The current pure-core seed implements deterministic 3D chunk addressing. Actual 3D rendering, collision streaming, floating-origin precision, server persistence and measured scale are still required before promotion.

## Roguelike runs

A run has:
- `runId`;
- `runSeed`;
- run-scoped inventory/state;
- encounter/event state;
- explicit persistent outputs.

Defeat may destroy/reset run-scoped state but must not silently erase admitted player/world history.

## Many-arm body graph

Bodies are arbitrary graphs. Arms are ordinary graph nodes with stable IDs.

Minimum states:

`attached → damaged → disabled → detached`

Detachment is a gameplay transition. It removes the detached subtree's capabilities/equipment slots and emits an authoritative event in a networked build.

Examples of capability consequences:
- fewer weapon/tool slots;
- reduced reach or simultaneous actions;
- loss of a shield/parry limb;
- loss of carrying/manipulation capability;
- boss phase changes;
- mutations/regrowth creating new arm nodes.

No fixed two-arm assumption is allowed in the successor core.

## Presentation

The title is intentionally violent fiction, but gameplay state must not depend on graphic depiction. A non-graphic mode maps the same limb-state transitions to disarm/disable/break visuals and textual cues.

`GAME_LIMB_GRAPH != REAL_ANATOMY`

## MMO authority

A live MMORPG requires authoritative services for identity, shard membership, movement reconciliation, combat, limb transitions, inventory, loot, persistent progression, moderation and durable world deltas.

Browser-local simulation and BroadcastChannel remain useful test carriers only.

`LOCAL_SHARD_SIMULATION != SERVER_AUTHORITY`

## Promotion ladder

1. Pure deterministic 3D spatial + limb-graph tests.
2. Local 3D renderer with streamed chunks.
3. Deterministic roguelike run lifecycle + persistence scopes.
4. Local combat driven by limb graph.
5. Authoritative server vertical slice.
6. Multi-client reconciliation/reconnect/recovery tests.
7. Scale/load evidence for declared shard/world budgets.
8. Accessibility and non-graphic parity checks.
9. Only then promote corresponding “massive 3D MMORPG” claims.

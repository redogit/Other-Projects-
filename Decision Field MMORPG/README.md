# RIPPING MANY ARMS OFF — Decision Field MMORPG Transition Runtime

**Successor target:** massive chunk-streamed 3D roguelike MMORPG.  
**Current executable truth:** this directory still contains a 2D browser transition prototype; it is not yet an authoritative massive 3D MMO.

The successor world contract is [`RMAO_WORLD.md`](RMAO_WORLD.md) with the machine-readable [`rmao-world-contract.json`](rmao-world-contract.json).

`CURRENT_2D_PROTOTYPE != MASSIVE_3D_WORLD`  
`LOCAL_SHARD_SIMULATION != SERVER_AUTHORITY`

A no-build browser MMORPG-style research world where the environment mutates constantly and every interaction can become a bounded gameplay observation.

This is currently a **client-side MMO prototype**, not an internet-scale authoritative MMO server. Same-browser tabs see each other through `BroadcastChannel`; NPC populations and world events simulate a larger shard. A production MMO still needs an authoritative server for identity, persistence, matchmaking, moderation, economy consistency and anti-cheat.

## Run it

From the repository root:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/Decision%20Field%20MMORPG/
```

Do not rely on opening `index.html` directly from `file://`; the game uses browser modules.

Run the deterministic core checks with:

```bash
node "Decision Field MMORPG/tests/core.test.mjs"
node "Decision Field MMORPG/tests/rmao-world.test.mjs"
```

## Controls

- WASD / arrow keys — move
- Pointer / touch drag — steer
- Space or double-click/tap — pulse attack
- E — interact with a nearby signal
- Q — phase shift
- R — local-shard shout
- 1 / 2 / 3 — geometry / semantic / rhythm carrier lens
- M — optional device-motion steering
- V — optional speech controls

Motion and speech are permission-gated. Browser speech recognition may use a browser/vendor service when enabled.

## RMAO implementation seed

The pure core now includes deterministic 3D chunk addressing and a data-driven limb graph. A creature can have arbitrary arm counts; detaching an arm produces a new immutable graph state and removes only capabilities supplied by the detached subtree. These functions are locally testable and are not yet wired into the 2D renderer or a server-authoritative combat loop.

## What now works

- combat grants XP and removes defeated actors;
- defeated populations replenish so the world does not empty;
- signals can be collected and respawn;
- level progression and reform-on-defeat work;
- world mutations alter chaos and spawn actors/signals;
- pointer/touch steering works alongside keyboard movement;
- optional motion and speech inputs are wired back in;
- same-browser tabs exchange player position/name/level and local shouts;
- the coarse local learning profile persists and can be reset;
- Fuzzball discovery persists across reloads;
- Quantum Frontier encounters reopen as the explorer collects signals.

## Character visual pipeline

The Ripping Many Arms Off visual work now has a five-deliverable production specification in [`CHARACTER_VISUAL_PIPELINE.md`](CHARACTER_VISUAL_PIPELINE.md): reference dossier, canonical fictional character sheet, material/texture specification, reversible shapeshifter states, and integration/acceptance gates.

The visual target is high-quality photorealistic / real-life imagery with scene-specific resolutions and formats rather than a fixed aspect-ratio family. Asset numbering is intentionally open-ended and generation can be batched at whatever scale is practical while preserving stable IDs, source masters and reproducibility metadata.

The complete motion/image scene set and failed-render recovery rules are in [`RMAO_WORLD.md`](RMAO_WORLD.md).

Reference imagery is treated as visual input, not evidence of identity. Generated concept art remains concept evidence until production assets are implemented and tested.

## Fuzzball

There is a deliberately obscure code-hidden artifact named **Fuzzball**. It is not shown in the normal HUD or item list. Its unlock logic is defined separately in `core.mjs`, where it can be tested without running the renderer.

Once found, it opens **Quantum Frontier** encounters based on genuine unresolved physics questions. Each encounter carries an open question, current boundary, proposed discriminating probe and explicit `UNRESOLVED` state.

Fuzzball never claims to solve those problems. A finite computation, game event, analogy, carrier or player action is not promoted into physical truth.

## Decision-field direction

The field is modeled as an action-sensitive partition of observations:

1. Observe a state.
2. Ask which available action would actually change.
3. Merge states only while the protected action remains equivalent.
4. When a counterexample appears, split the field, add a discriminator, weaken the claim, or remain unresolved.
5. Reuse carriers that reduce search/planning cost without calling the carrier truth.
6. Preserve failed actions and unresolved remainder.

The MMORPG turns that into gameplay. Hostiles, other explorers, signals, world mutations and Quantum Frontier prompts are distinct carriers through which the game can test whether its present state description is sufficient.

Local adaptation is visible and limited to coarse gameplay parameters such as world-event tempo. It does not infer identity, health, personality, politics or other sensitive traits.

## Current test boundary

The deterministic `core.mjs` tests cover profile migration, the hidden unlock sequence, interrupted-sequence rejection, Quantum Frontier `UNRESOLVED` state and bounded event pacing. The client bundle also passes JavaScript syntax checking and a local stubbed initialization smoke test. This is not yet a full cross-browser, multiplayer-server, accessibility or production-security certification.

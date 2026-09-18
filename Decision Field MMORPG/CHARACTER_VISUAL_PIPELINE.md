# Character Visual Pipeline — Five Deliverables

Status: design specification. This document does not claim that generated concept art is a production-ready texture set or that a depicted person has any real-world identity.

The recurring woman in the Ripping Many Arms Off concept work is treated as a **fictional shapeshifter character**. Reference images are visual inputs only; identity inference is out of scope.

## Global image target

- High-quality photorealistic / real-life visual output
- Natural camera, lens, depth-of-field and lighting behavior
- Physically plausible skin, hair, fabric, glass, metal, water, rain and reflections
- No fixed output count, aspect-ratio family or numbering ceiling
- Choose dimensions and file format per scene and destination
- Maintain open-ended sequential asset IDs and batch generation at whatever scale storage and compute permit
- Preserve high-resolution source masters and derive game/web/mobile variants from them

## Deliverable 1 — Reference dossier

Build a provenance-aware reference set separating:
- user-supplied reference imagery;
- generated concept imagery;
- game screenshots / world context;
- observations from interpretations.

Record only visible design features needed for the fictional character: silhouette, hair treatment, clothing layers, material response, pose language, lighting and recurring motifs.

## Deliverable 2 — Canonical character sheet

Create a stable fictional base design rather than attempting biometric replication. Required coverage: portrait, front, side, rear, three-quarter, neutral silhouette and representative rainy-night lighting. Add further views whenever they improve continuity or production use. Preserve intentional variability as part of the shapeshifter mechanic.

## Deliverable 3 — Material and texture specification

Production material families:
- skin: base color, normal, roughness, subsurface mask;
- hair: base color, strand/alpha, normal, roughness;
- clothing: fabric/leather base color, normal, roughness, masks;
- hardware: metallic/roughness, scratches and wetness response;
- overlays: rain, grime, wear, damage and emissive accents.

Prefer reusable masks and material instances over duplicated texture sets.

## Multi-arm creature production rule

RMAO creatures use a body/limb graph rather than a fixed humanoid rig. Visual production must support zero-to-many arm nodes, stable limb IDs, attached/damaged/disabled/detached presentation states, detachable equipment bindings, LOD-safe limb visibility, and a non-graphic presentation that communicates the same mechanics without gore.

Rigging/animation assets do not own gameplay state; the authoritative limb graph does.

## Deliverable 4 — Shapeshifter state system

Represent transformations as authored fictional states rather than claims about a real person. Each state has:
- stable character ID;
- state ID;
- silhouette delta;
- material overrides;
- wardrobe configuration;
- animation/VFX hooks;
- gameplay meaning;
- transition constraints.

Transformations should be reversible, testable and independent of real-world identity attributes.

## Deliverable 5 — Integration and acceptance gate

Integrate the character into the Decision Field MMORPG only after checks for:
- asset provenance;
- licensing/permission boundaries;
- age-appropriate base-game presentation;
- optional mature content isolated behind a separate gate if ever implemented;
- texture budgets and LODs;
- wet/dry readability;
- accessibility/readability against dark scenes;
- deterministic state transitions;
- graceful fallback when high-resolution assets are absent.

## RMAO world motion set

The old scene list is superseded. Use [`RMAO_WORLD.md`](RMAO_WORLD.md) for world-scale 3D motion, creature, combat and camera requirements. Inherited companion/night-city material is reference-only and does not define the successor world.
- companion reveal;
- night-city walk;
- private-room scene;
- in-game phone clips;
- living-world moments;
- memory videos.

## Image generation recovery

- Keep the selected source/reference intact.
- Request one verified edited variant first.
- Treat generation as complete only when a render exists.
- Retry when output is empty or missing while preserving scene intent.
- Preserve failed requests as pending instead of marking them complete.
- Choose output size and aspect ratio per asset rather than forcing presets.
- Verify a replacement asset before overwriting a working image.
- Preserve reproducible generation intent alongside each result.
- Validate face, hair, wardrobe, hands, reflections, lighting direction and continuity before promotion.
- Batch large runs and retain stable asset numbering/index metadata.

### Evidence boundary

Concept images demonstrate visual direction only. They do not establish a real person's identity, measurements, biography, or canonical game geometry. Production readiness requires implementation and executed tests.
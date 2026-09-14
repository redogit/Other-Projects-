# Character Visual Pipeline — Five Deliverables

Status: design specification. This document does not claim that generated concept art is a production-ready texture set or that a depicted person has any real-world identity.

The recurring woman in the Red Wilds concept work is treated as a **fictional shapeshifter character**. Reference images are visual inputs only; identity inference is out of scope.

## Deliverable 1 — Reference dossier

Build a provenance-aware reference set separating:
- user-supplied reference imagery;
- generated concept imagery;
- game screenshots / world context;
- observations from interpretations.

Record only visible design features needed for the fictional character: silhouette, hair treatment, clothing layers, material response, pose language, lighting and recurring motifs.

## Deliverable 2 — Canonical character sheet

Create a stable fictional base design rather than attempting biometric replication. Required views: portrait, front, side, rear, three-quarter, neutral silhouette and representative rainy-night lighting. Preserve intentional variability as part of the shapeshifter mechanic.

## Deliverable 3 — Material and texture specification

Production material families:
- skin: base color, normal, roughness, subsurface mask;
- hair: base color, strand/alpha, normal, roughness;
- clothing: fabric/leather base color, normal, roughness, masks;
- hardware: metallic/roughness, scratches and wetness response;
- overlays: rain, grime, wear, damage and emissive accents.

Prefer reusable masks and material instances over duplicated texture sets.

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

### Evidence boundary

Concept images demonstrate visual direction only. They do not establish a real person's identity, measurements, biography, or canonical game geometry. Production readiness requires implementation and executed tests.
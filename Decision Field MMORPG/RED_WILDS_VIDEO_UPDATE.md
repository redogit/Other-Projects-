# RED WILDS — VIDEO + IMAGE UPDATE

## MASTER VISUAL RULE

- High-quality photorealistic / real-life visual target
- Natural skin, hair, fabric, glass, metal, rain, reflections and environmental light
- Cinematic camera behavior and physically plausible depth of field
- Preserve the same fictional companion identity across scene variants unless a shapeshifter state explicitly changes it
- No fixed image count
- No fixed aspect-ratio family
- No fixed numbered range
- Use sequential asset IDs (`1`, `2`, `3`, …) for as many variants as the project needs
- Generation/storage can be batched while the logical asset sequence remains open-ended
- Choose resolution and format per scene instead of forcing every asset into the same dimensions

## VIDEO SET

### 01 — COMPANION REVEAL
- Slow turn toward camera
- Direct eye contact
- Hair adjustment
- Close framing
- Red evening dress
- Warm interior lighting
- Alternate face-angle takes
- Short and long takes

### 02 — NIGHT-CITY WALK
- Neon street environment
- Handheld follow shot
- Over-the-shoulder tracking
- Look-back moments
- Crowd movement
- Reflections in wet pavement
- City signage and ambient traffic

### 03 — PRIVATE-ROOM SCENE
- Warm bedside lamps
- Black sleepwear
- Close conversational framing
- Playful body language
- Sitting / standing transitions
- Window-light variation
- Camera push-in
- Alternate endings and camera positions

### 04 — IN-GAME PHONE CLIPS
- Selfie video
- Voice-message video
- “Come find me” location clip
- Outfit-change clip
- Mirror clip
- Walking clip
- Passenger-seat clip
- Rooftop clip
- Hotel / apartment clip
- Portrait, square, landscape, ultrawide and custom crops as needed

### 05 — LIVING-WORLD MOMENTS
- Dancing
- Rooftop rain
- Nightclub sequence
- Restaurant sequence
- Road-trip sequence
- Swimming sequence
- Sunset walk
- Sunrise sequence
- City overlook
- Arcade / game-night moment

### 06 — MEMORY VIDEOS
- Quiet breakfast
- Laughing in the kitchen
- Train-window ride
- City lights from a balcony
- Rain against an apartment window
- Walking home after an event
- Photo-booth sequence
- Shared map / trip planning
- Short home-video fragments

## RED WILDS VISUAL DIRECTION

- Bolder wardrobe and silhouette choices
- Direct eye contact
- Close camera distance
- Strong red / black night styling
- Confident poses
- Natural movement in hair and clothing
- Neon, rain, glass, mirrors and reflections
- Dramatic warm-vs-cool lighting
- Realistic pores, flyaway hairs, fabric weave, jewelry reflections and environmental bounce light when visible at the chosen shot distance
- Avoid plastic skin, over-smoothed faces, impossible anatomy, duplicated accessories, broken hands and inconsistent reflections

## IMAGE GENERATION RECOVERY

Generation is complete only when an actual image asset exists and can be displayed.

1. Preserve the selected reference image and composition target.
2. Generate one verified variant first.
3. Confirm the render exists and is visually valid.
4. Retry failed or empty outputs without changing the intended scene unless the failure requires a repair.
5. Keep failed requests pending rather than marking them complete.
6. Choose dimensions and aspect ratio per asset; do not constrain the project to preset ratios.
7. Do not overwrite a working source image until the replacement render is verified.
8. Store generation intent, seed/state where available, source references and resulting asset ID separately.
9. Run consistency checks for face, hair, wardrobe, hands, reflections, lighting direction and scene continuity.
10. Batch large variant runs and keep deterministic numbering/index metadata so the set can scale from a few images to very large collections.

## OUTPUT FAMILIES

- Dashboard concepts
- Cinematic stills
- Phone clips / thumbnails
- Companion portraits
- Full-body character shots
- Outfit / silhouette variants
- Night-city environments
- Private-room environments
- Memory scenes
- Contact sheets
- Storyboard frames
- Background plates
- UI art
- Promotional key art
- High-resolution source masters
- Derived web/game/mobile versions

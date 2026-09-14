# RED WILDS — VIDEO + IMAGE UPDATE

## VIDEO SET

### 01 — COMPANION REVEAL
- Slow turn toward camera
- Direct eye contact
- Hair adjustment
- Close framing
- Red evening dress
- Warm interior lighting
- Alternate face-angle takes
- 6–12 second loop

### 02 — NIGHT-CITY WALK
- Neon street environment
- Handheld follow shot
- Over-the-shoulder tracking
- Look-back moments
- Crowd movement
- Reflections in wet pavement
- City signage and ambient traffic
- 10–20 second loop

### 03 — PRIVATE-ROOM SCENE
- Warm bedside lamps
- Black sleepwear
- Close conversational framing
- Playful body language
- Sitting / standing transitions
- Window-light variation
- Camera push-in
- Fade / cut ending
- 8–18 second loop

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
- Vertical 9:16 format
- 4–12 seconds each

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

- Slightly bolder wardrobe and silhouette choices
- More direct eye contact
- Closer camera distance
- Stronger red / black night styling
- More confident poses
- More movement in hair and clothing
- Neon, rain, glass, mirrors, reflections
- More dramatic warm-vs-cool lighting
- Keep the same recognizable fictional companion across variants

## IMAGE GENERATION RECOVERY

Generation is considered successful only when an actual image asset is returned and can be displayed.

Pipeline:
1. Preserve the selected reference image and composition target.
2. Generate a single edited variant first.
3. Verify that a render exists before advancing.
4. Retry once with the same visual intent if the render is empty or missing.
5. If the second attempt fails, preserve the request as pending instead of silently treating it as complete.
6. Keep output dimensions and aspect ratio explicit for dashboard and in-game-phone assets.
7. Do not overwrite a working source image until the replacement render is verified.
8. Store prompt intent separately from the resulting asset so generation can be reproduced.

## TARGET OUTPUTS

- Dashboard concept update
- 16:9 cinematic stills
- 9:16 phone clips / thumbnails
- Companion portrait variants
- Outfit / silhouette variants
- Night-city environment variants
- Private-room environment variants
- Memory-scene variants

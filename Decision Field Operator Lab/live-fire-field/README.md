# FIRE + Music + Dance — Live Field

A no-build browser interface for the executable FIRE + Music + Dance control carrier.

## Open it

From the repository root:

```sh
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/Decision%20Field%20Operator%20Lab/live-fire-field/
```

The page is local-first and persists its state in browser `localStorage`.

## What is live

- DARK / MIDDLE / LIGHT triad;
- current FIRE stage;
- ASH / SMOKE / EMBER / SURVIVOR bins;
- one-degree mutation controls;
- Music cadence and beat/bar pulses;
- Dance over ALL WAYS;
- HOMEWARD, SLEEP and WAKE;
- learned route preference and habituation;
- `DELTA_ZERO -> NO_CHANGE -> CLOSE`;
- exact trace display;
- state export/import.

## ChatGPT bridge

The page exposes a bounded shared-state bridge.

**Human -> ChatGPT**

Use **Copy state for ChatGPT** or **Download state JSON**. The exported packet uses:

```text
fire-music-dance-bridge-state/v1
```

That lets the chat operate on the exact visible state rather than reconstructing it from prose.

**ChatGPT -> Human**

Paste a command packet into the Command Packet box:

```json
{
  "schema": "fire-music-dance-command/v1",
  "commands": [
    {
      "command": "DANCE",
      "direction": "INWARD"
    },
    {
      "command": "MUTATE",
      "path": "system.depth",
      "after": 3,
      "operator": "DEEPEN",
      "direction": "INWARD"
    }
  ]
}
```

Supported commands:

`SET_TRIAD`, `DANCE`, `MUTATE`, `BURN`, `SURVIVOR`,
`RECONSTITUTE`, `HOMEWARD`, `SLEEP`, `WAKE`, `COMPARE`.

The browser does **not** call an AI API and does not upload state automatically.

## Inspectable browser API

For debugging/automation in the page console:

```js
window.FireMusicDanceLive.getState()
window.FireMusicDanceLive.bridgeSnapshot()
window.FireMusicDanceLive.applyCommandPacket(packet)
```

## Test

The repository-native Python contract test is discovered by the existing Decision Field Operator Lab suite:

```sh
python -m unittest "Decision Field Operator Lab/test_fire_music_dance_live_ui.py" -v
```

A separate local static smoke check was also run against the implementation before push, including JavaScript syntax validation.

## Boundary

```text
LIVE_UI != DOMAIN_EVIDENCE
GENERATE != VERIFY != ADMIT
MUSIC != TRUTH
DANCE != TRUTH
METHOD_TRANSFER != EVIDENCE_TRANSFER
DELTA_ZERO_IS_LOCAL_NOT_GLOBAL
```

# Hodge Compass API

A fast, local, provenance-first API connecting the Eye-of-the-Storm / Compass observer lineage to the existing Hodge research spine **without transferring evidence across domains**.

## Why this exists

The research already has several useful but separate surfaces:

- `redogit/conscience64/research/hodge/` — target-native Hodge research and W114 work;
- `redogit/conscience64#99` — current W114 matrix-factorization proof obligation;
- `Hodge Span Lab/` — exact rational span/separation and an explicit deformation-signature bridge;
- Compass / Five-Eyes / observer work — multiple views, blind spots, residuals and reprojection;
- Normal + Work history — redundant provenance carriers for important ideas.

This API makes those surfaces queryable through one local interface while preserving their authority and claim ceilings.

## Hard boundaries

- `NORMAL_OCCURRENCE + WORK_OCCURRENCE != INDEPENDENT_CORROBORATION`
- `METHOD_TRANSFER != EVIDENCE_TRANSFER`
- `OBSERVABLE_REMAINDER != ALGEBRAIC_REALIZATION`
- `PROJECTION != FULL_STATE`
- `NONZERO_TARGET_COEFFICIENT != FULL_HODGE_PROOF`
- `FAILED_ANSATZ != NONALGEBRAIC_CLASS`

Private chat/work-history text is **not bundled**. Local clients may ingest their own authorized occurrences into the local SQLite database.

## Start

Python 3.10+, standard library only.

```sh
python "Hodge Compass API/hodge_compass_api.py" \
  --db .hodge-compass/index.sqlite3 \
  ingest "Hodge Compass API/bootstrap_manifest.json"

python "Hodge Compass API/hodge_compass_api.py" \
  --db .hodge-compass/index.sqlite3 \
  --repo-root . serve --port 8765
```

Then:

```sh
python "Hodge Compass API/client.py" health
python "Hodge Compass API/client.py" w114
python "Hodge Compass API/client.py" sources W114
python "Hodge Compass API/client.py" search "Compass remainder"
```

## API

| Endpoint | Role |
|---|---|
| `GET /v1/health` | health, counts, hard boundaries |
| `GET /v1/hodge/w114` | frozen W114 target contract |
| `GET /v1/hodge/sources` | revision-pinned Hodge/source catalog |
| `POST /v1/hodge/sources/search` | fast path/repo/role filtering |
| `POST /v1/records` | ingest private/local provenance records |
| `POST /v1/search` | FTS5 occurrence search with fallback |
| `GET /v1/objects/{SemanticObjectID}` | object + occurrences + relations |
| `POST /v1/hodge/span` | existing exact Hodge Span Lab in-process |
| `POST /v1/hodge/bridge` | existing exact deformation→span bridge |
| `POST /v1/observer/remainder` | exact controlled observer/remainder experiment |

See `openapi.json`.

## All-Hodge source catalog

`source_catalog.json` is generated from exact repository trees and pins:

- the current `conscience64` revision containing the target-native Hodge spine;
- the current `Other-Projects-` revision containing Hodge tools and connected method surfaces.

A catalog entry means **discoverable source**, not verified theorem or promoted evidence.

## Normal + Work history

Use one stable `SemanticObjectID` for the idea/object and a separate `OccurrenceID` for each exact occurrence.

Example:

```json
{
  "semantic_object_id": "compass:observer-return-loop",
  "kind": "observer-framework",
  "domain": "compass",
  "title": "Eye of the Storm observer-return loop",
  "claim_ceiling": "METHOD_ONLY",
  "occurrence": {
    "surface": "work",
    "source_ref": "work:<authorized-reference>",
    "authority": "private-lineage",
    "status": "CURRENT",
    "text": "authorized local text or compact summary",
    "provenance": ["work-history"]
  }
}
```

A matching Normal-history occurrence gets a new `OccurrenceID`, not a second semantic object and not another scientific vote.

## Controlled remainder

`/v1/observer/remainder` uses exact rational matrices. It answers:

- which observer sees the injected remainder;
- combined observer rank;
- collective blind dimension;
- whether the remainder is collectively detected.

Floats are rejected so calibration inputs remain exact.

## W114

The frozen target is:

```text
alpha = (1,7,78,79,86,91)
M_W114 = x1^6 x2^77 x3^78 x4^85 x5^90
degree = 336
```

The API preserves issue #99's success criterion and claim ceiling. It does not upgrade a coefficient hit into a Hodge proof.

## Tests

```sh
python -m unittest discover -s "Hodge Compass API" -p 'test_*.py' -v
python -m unittest discover -s "Hodge Span Lab" -p 'test_*.py' -v
```

CI runs both suites on API/Hodge-Span changes.

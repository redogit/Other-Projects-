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
python "Hodge Compass API/client.py" batch-search "Hodge Compass API/w114_query_pack.json"
```

## Index the actual Hodge source contents

The revision-pinned catalog is a navigation layer. For millisecond full-text search over the **contents** of local source trees, ingest the checked-out repositories:

```sh
# From Other-Projects-
python "Hodge Compass API/hodge_compass_api.py" \
  --db .hodge-compass/index.sqlite3 \
  ingest-tree \
  --root ../conscience64 \
  --repo redogit/conscience64 \
  --prefix research/hodge \
  --root-object hodge:conscience64:research-spine

python "Hodge Compass API/hodge_compass_api.py" \
  --db .hodge-compass/index.sqlite3 \
  ingest-tree \
  --root . \
  --repo redogit/Other-Projects- \
  --prefix "Hodge Span Lab" \
  --prefix "Hodge Compass API" \
  --prefix "Decision Field Operator Lab"
```

Every file becomes one stable source semantic object. A changed file creates a new occurrence under that object; re-indexing unchanged bytes is idempotent. UTF-8 text is hashed before ingestion, binary/oversized files are skipped, and every generated relation still defaults to `evidence_transfer=DENY`.

## API

| Endpoint | Role |
|---|---|
| `GET /v1/health` | health, counts, hard boundaries |
| `GET /v1/hodge/w114` | frozen W114 target contract |
| `GET /v1/hodge/sources` | revision-pinned Hodge/source catalog |
| `POST /v1/hodge/sources/search` | fast path/repo/role filtering |
| `POST /v1/records` | ingest private/local provenance records |
| `POST /v1/search` | FTS5 occurrence/source-content search with fallback |
| `POST /v1/batch/search` | up to 64 searches in one request |
| `POST /v1/graph/traverse` | bounded typed relation traversal; gates preserved |
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

The local content index is deliberately separate from the catalog: the catalog says *what source snapshot exists*; the local FTS index makes its text fast to search. This prevents a convenient search index from becoming the source of truth.

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

## Batch proof-work queries

`w114_query_pack.json` bundles the current high-value search channels—W114, matrix factorization, primitive Chern character, Favero–Kelly, Shioda/coset screens, Jacobian target, observer remainder, monodromy bridge and span separation—into one API round trip.

```sh
python "Hodge Compass API/client.py" batch-search "Hodge Compass API/w114_query_pack.json"
```

## Relation traversal

Traverse the typed graph without dropping evidence gates:

```sh
python "Hodge Compass API/client.py" traverse \
  hodge:w114:alpha:1-7-78-79-86-91 \
  --max-depth 3 --direction both
```

Returned edges retain `permission` and `evidence_transfer`; traversal itself never promotes either.

## v1.1 speed model

The fast path is now:

```text
local source bytes
→ exact SHA-256 occurrence
→ stable SemanticObjectID
→ SQLite WAL
→ FTS5
→ batch query
→ typed relation traversal
→ exact Hodge/observer probe
```

Network discovery remains useful for refresh, but routine proof-work queries can stay entirely local once the source trees are indexed.

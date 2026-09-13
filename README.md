# Other Projects

Implementation home for the Human Expression Archive, 1,024-byte section carriers, and bounded learning-compression tools, explicitly selected by the user on September 13, 2026.

## Projects

- [ChatGPT and Conscience](ChatGPT%20and%20Conscience/README.md) — the existing cooperation lab. Its code, patches, evidence and source locks are unchanged by the archive publication.
- [Human Expression Archive](Human%20Expression%20Archive/README.md) — the complete 91-record accession, source register, qualified relations, explicit gaps, and a searchable offline viewer.
- [S1024 Compression Lab](S1024%20Compression%20Lab/README.md) — exact 1,024-byte cuts, UTF-8 boundary states, finite-float transport, exact UTF-8 indexing, constrained bit repair, and a frozen-pattern compression example.

## Run locally

Python 3.10 or newer; standard library only. No API keys, downloads, or package installation are needed for these two new projects.

```sh
python "Human Expression Archive/build.py"
python "S1024 Compression Lab/demo.py"
python -m unittest discover -s "Human Expression Archive/tests" -v
python -m unittest discover -s "S1024 Compression Lab/tests" -v
```

Open `Human Expression Archive/public/index.html` after the first command. The page is searchable offline. The committed, hash-locked accession expands to ordinary UTF-8 JSON/JSONL files under `public/data/`.

## Boundaries

The archive is a bounded accession, not all human expression. Preservation is not endorsement. Source-specific rights and cultural protocols remain attached; no blanket training permission is granted. Compression results are synthetic and task-relative, not a law of human learning. Private Library snapshots and complete third-party media are excluded.

This repository is the implementation home. Earlier `conscience64/research` notes are historical cross-references, not the source-of-truth repository for these projects. No GitHub Pages deployment or workflow activation is part of this publication.

See [publication evidence](evidence/PUBLICATION_CHECKS.json) for fresh checks and [routing](PROJECT_ROUTING.md) for project boundaries.

## Context Discovery — systemic continuation

[Context Discovery](Context%20Discovery/README.md) adds an exact finite question planner, selected SQLite/zlib context-dependency probes, counterexamples, source notes and reproducible evidence. Python 3.11+; run `python "Context Discovery/systemic.py" --out context-output`. The existing projects and workflows are unchanged. This is bounded research, not an automated cultural-meaning or universal idea detector.

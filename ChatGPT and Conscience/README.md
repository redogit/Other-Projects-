# ChatGPT and Conscience

A cooperation lab for **ChatGPT + Conscience64**, directed by the human project owner.

**I — What do we have?** Research claims, typed project records, explicit finite tables and recorded experiments.  
**R — What difference matters?** Preserve source identity, distinguish a receipt from endorsement, and measure useful work rather than a flattering counter.  
**P — What should we do next?** Reproduce a bounded result, challenge it, repair one consequential boundary and compare costs.  
**O — What happened?** Keep the result, failures, provenance and unresolved remainder together.

## Start here

From the repository root:

```bash
cd "ChatGPT and Conscience"
python demo.py
python -m unittest discover -s tests -v
```

The Python demo and tests use the standard library. The two research implementation files in `src/` are copied byte-for-byte from Cooperation Pass 002. They detect domain-and-label-preserving XOR translations of explicitly listed Boolean tables; they are not general-purpose intelligence or a solution to an open complexity problem.

## Run the local Conscience64 API sandbox

The repository stores two reviewable patches and a SHA-256 source lock, not a duplicate of the entire upstream research corpus. Python and Git build the sandbox; Node 22 or newer runs the inherited checker and the additional smoke tests.

```bash
python tools/materialize_sandbox.py --download
node tests/api_smoke.mjs
python -m http.server 8765 --bind 127.0.0.1 --directory build/site
```

Open `http://127.0.0.1:8765/`. The page exposes `window.Conscience64API`.

The download option explicitly retrieves fourteen runtime/checker files from commit `3f8889e17cecd7bd865e33f70201c703163df405` of `redogit/conscience64`. Every file is checked against `source-lock.json`. Both patches are then applied in order, and the resulting `app.js` and `API.md` must match the recorded **1.2.0-coop.2** hashes. It does not alter a Git branch or deploy anything. The sandbox is not a mirror of every upstream document or playground tool.

An offline alternative accepts a local copy of the exact original 1.2.0 source:

```bash
python tools/materialize_sandbox.py --source-dir /path/to/original/site
```

An existing `build/site` is never overwritten. Use a fresh `--output` directory for another build. Review all code before running it; this is a research candidate, not a production security certification.

## What is here

| Area | Contents |
|---|---|
| `src/` and `demo.py` | Matched anchor/reuse controls and adaptive symmetry implementation |
| `patches/` | Endpoint/method/argument guard, then I/R/P/O history snapshot repair |
| `evidence/` | Historical acceptance record and explicitly derived benchmark summary |
| `CLAIMS.json` | Scope-qualified claim index, including source-only entries |
| `PROVENANCE.json` | Original archive identities, exact-copy mapping and import boundary |
| `source-lock.json` | Pinned upstream runtime assets, patches and expected candidate identities |
| `tests/` | New packaging-level correctness and API smoke checks |
| `docs/COOPERATION.md` | Chronology, roles, limitations and continuation target |
| `VALIDATION.json` | Checks actually performed for this publication, distinct from prior results |

## Boundaries

ChatGPT authors implementation and interpretation; Conscience64 supplies structured navigation and carries records. The human sets goals and authorizes publication. These roles do not merge identities, authorship or evidence. Conscience64's structured API is not a generative chat endpoint.

Historical benchmark results are imported observations, not a new benchmark or independent replication. A hash establishes bytes, not truth. History is a rolling 512-record in-memory window, not a durable archive. Knowledge Decay remains active: recheck source identity, runtime versions and availability before reuse.

This is a **new project publication**, not deployment of the candidate into `redogit/conscience64`. Only selected project material is included; private Library material and raw conversation exports are excluded. No new license grant for upstream material is inferred by this import. Prior scoped notices remain applicable; the project name does not imply official OpenAI affiliation or endorsement.

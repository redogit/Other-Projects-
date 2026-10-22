# FKDB Knowledge Workbench — bounded first integration

This increment introduces a browser-side, dependency-aware source and claim registry without changing the existing FKDB transport, RMAL routing, local tool permissions, or native fallback.

## Capabilities
- Captures exact UTF-8 text with separate occurrence identities and SHA-256 content digests.
- Records source purpose, origin, context, and immutable event sequence.
- Tracks evidence excerpts and claim dependencies; changing a source marks dependent claims for review.
- Checks evidence presence without promoting source content to mathematical truth.
- Exports and imports a portable JSON archive with source-digest checks.

## Limits and known gaps
- Local in-memory only; save the exported archive externally. No automatic crawling, IndexedDB migration, or network sync.
- Source limit 2 MB per capture; no quota on total records yet.
- Event history is not cryptographically authenticated and archive import does not prove event authenticity.
- Source revision currently preserves old digests in events but not old source bytes; therefore full historical recovery is NOT yet guaranteed.
- Evidence checks confirm exact excerpt presence, not factual correctness, contextual sufficiency, or independent corroboration.
- Source impact detection currently covers direct claim dependencies only, not arbitrary transitive claims.
- Browser integration is a new optional surface, not replacement of the existing host entry.

## Test
Run `node web/knowledge-workbench/test.mjs` from the FKDB project root. This requires Node.js 20+.

## Research alignment
The immediate next boundary is append-only versioned source snapshots with integrity-checked historical restoration, followed by a typed transitive justification graph and crash-safe persistence.

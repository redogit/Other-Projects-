# Knowledge Garden

A place to wander through connected work, follow a useful trail and leave with a small working set.

The Garden brings source-reviewed Library, Orbit, Master, companion, research and practical-project summaries into **Other Projects**. It adds a browser explorer and a local HTTP API. Every project keeps its own evidence, state and next action.

## Take a walk

Requires Node.js 22 or later. No package installation is needed.

```sh
cd knowledge-garden
npm start
```

Open <http://127.0.0.1:4317>. The server listens on loopback by default. `PORT` selects another port; exposing it on another host requires an explicit `HOST` setting. Stop it with Ctrl+C.

Search a name or topic, open a branch, or choose an expedition. Each entry shows its next action, sources, capabilities and typed connections. **Surprise me** offers another way in. Gather entries into a working set and describe the task they belong to: subject, motivator, request, obligation, surface and output definition. Blank fields stay blank.

Download a portable JSON proposal, or save a named checkpoint in this browser. Import and checkpoint review show changed or missing entries before you restore; restored selections use the current catalog. There is one in-memory undo for restore. Nothing is automatically saved or restored on reload.

**Clear active work** releases the task, selections, pending import and undo. **Save and clear** clears only after the checkpoint write succeeds. Remove a checkpoint individually or review **Clear saved checkpoints** to remove the Garden's own history while keeping active work. Checkpoints are limited to twelve and 2 MiB in total; imports to 1 MiB. Browser storage can be cleared by the browser, so download anything you need to keep independently. See [execution and recovery](docs/EXECUTION.md).

The interface uses native buttons, links, headings, lists and expandable details. It supports keyboard use and reduced-motion preferences. API and static UI checks are recorded in [verification](docs/VERIFICATION.md). Rendered browser, assistive-technology and participant acceptance remain open.

## What grows here

| Branch | Includes |
| --- | --- |
| Workspace & memory | Library, Orbit and its source roles, Master 2.0 / Plan 2.2 / learning route 2.6, Conscience64 and its separate cooperation lab |
| Methods & meaning | R³, CSOL, One Level Up, working-set and attribution distinctions, freshness, accessibility, Blank Page Lab |
| Research clearings | Moonshot, TBCL, SHADOW, Cross-Carrier, numeric carriers, Coordinate Space, streaming memory, physics, Recursive Survivor, unresolved fractal source, Context Discovery, SPrime Search, Hodge Span Lab |
| Practical workshop | Excel Report Assistant, Accessible WorkMate, Jira gadget, RIVIR SDK |
| Expression & learning | Human Expression Archive, 1,024-byte section carriers, bounded learning compression |

This is a selected catalog, not an exhaustive inventory or a complete record of a person's knowledge. The September 14 refresh links the now-published expression and cooperation projects, Context Discovery, SPrime Search, Blank Page Lab and Hodge Span Lab at a pinned repository revision. Garden files are additive under this directory.

## API

```sh
curl 'http://127.0.0.1:4317/api/projects?limit=10'
curl 'http://127.0.0.1:4317/api/hierarchy?root=workspace'
curl 'http://127.0.0.1:4317/api/relations?node_id=master-librarian'
curl 'http://127.0.0.1:4317/api/search?q=carriers'
```

[OpenAPI contract](openapi.json) documents the endpoints, parameters, schemas and error responses. It is also served at `/api/openapi.json`. `/api/catalog` provides the complete selected catalog; `/api/nodes/{id}` bundles one node with its immediate children, connections, source summaries and capabilities.

The API is read-only and makes no outgoing requests. Capability records distinguish new local HTTP behavior, inspected external browser interfaces and historical source contracts. Listing Conscience64 or Master does not start them. The companion's graph and lesson searches remain distinct.

## How connections work

`parent_id` forms the navigation hierarchy. A separate relation has a type, scope, status and source references. `related_to` proposes a useful connection; `depends_on` records a scoped requirement. `supports` is reserved for a source-described, explicitly scoped basis. The initial catalog makes no new scientific support claim.

Sources label public references and owner-held summaries. The public dataset contains newly authored technical summaries, not raw private documents, personal conversations or proprietary API payloads. Historical verification reports and local candidates retain those labels. The coop.2 history repair now has a published candidate carrier in ChatGPT and Conscience; deployment into the inspected Conscience64 1.3.0 source remains separate.

## Maintain the map

The editable source is [data/catalog.json](data/catalog.json), with [catalog.schema.json](catalog.schema.json) as its format contract. Follow [the catalog guide](docs/CATALOG_GUIDE.md) to add a node, source, capability or trail. The server checks identities, references and hierarchy before accepting the catalog.

Every `npm start` first compiles a query plan for the exact catalog. Startup checks its version, content fingerprint and derived relationships before listening. Direct `node server.mjs` requires a current plan from `npm run build`. Generated plans live in the ignored `build/` directory.

```sh
npm test
npm run benchmark
```

These checks exercise the Garden's data and API. They do not replay the source projects' scientific or integration tests. See [source review](docs/SOURCE_REVIEW.md) for what was inspected and what remains unresolved.

Compilation prepares lookup indices and search text, not native machine code or executable task instructions. The [measurement record](docs/EXECUTION.md#measured-costs) reports build costs, query timings and memory limits; it does not establish universal optimality.

# Grow the catalog

Edit `data/catalog.json`, update `catalog_version` and `reviewed_on`, and run `npm test` before proposing a change. Keep a change small enough that its sources can be inspected.

## Add a source, then a node

Give a source a stable lowercase ID, a descriptive title, its source date when known, the review date, evidence kind and the exact scope of what it establishes. Use a pinned public HTTPS reference where available. For an owner-held source, set `access` to `owner-held` and `url` to `null`; publish only a newly authored technical summary. Unknown dates remain `null`.

Then add a node with a stable ID and one `parent_id`. Roots use `null`. Use `group` for navigation, `project` for independent work, `component` for a project part, and `role` for a source-defined organizational role. A node must include its source references, plain-language status, evidence status, summary, tags and bounded next action.

Changing an ID is a migration: update all child, relation, capability and trail references. A display-name change does not need a new ID. A newer filename or version number alone does not establish supersession.

## Keep different relations different

| Type | Meaning in this catalog |
| --- | --- |
| `parent_id` | Navigation containment; no scientific or supervisory authority |
| `related_to` | Scoped useful connection; often an integration proposal |
| `depends_on` | The source node needs the target within the stated scope |
| `supports` | The source node provides a specifically described evidential basis for the target; requires `source-described` status and source references |
| `derived_from` | The source node adapts an idea or artifact from the target within the stated scope |
| `predecessor` | The source node is an earlier state of the target; chronology needs evidence |

Relation records always carry a scope and source IDs. `proposal` means an integration suggestion; `source-described` attributes the relation to inspected source material. Neither status independently verifies an experimental result. The initial release contains no `supports` or `predecessor` edge because the integration does not need to establish either.

## Declare what can actually be called

Capabilities use one of three transports:

- `local-http` with `implemented`: an endpoint implemented by this project.
- `external-browser` with `source-inspected`: an interface found in a pinned external browser implementation; availability and connection are separate.
- `source-contract` with `described`: a historical design or package contract that this API does not execute.

Record the invocation, input, output and limitations. Never turn a catalog declaration into a claim that a companion is connected, a service is available or a historical runtime has been exercised. New transports or status semantics require a schema and server update.

## Curate an expedition

A trail contains existing node IDs, a title, a short purpose and one next action. Its status is `proposal`. A browser working-set export similarly records a selection and catalog version; it does not import raw sources, execute tools or change project authority.

## Review source changes

When a source changes, inspect the affected node and capability before updating its status. Keep reported results, static inspection, executed checks and participant acceptance distinct. If the exact original is missing, preserve the gap in the next action. A zero-result search means no match in this catalog, not absence of knowledge in the wider world.

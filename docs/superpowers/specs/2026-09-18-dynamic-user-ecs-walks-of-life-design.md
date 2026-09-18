# Dynamic User-Language ECS Client + Walks of Life — Design

**Date:** 2026-09-18  
**Status:** APPROVED DESIGN / NOT YET IMPLEMENTED  
**Canonical design home:** `redogit/Other-Projects-`  
**Related designs:** RMAPL/Ω domain-derived repair/fitting; Decision Field; S'1; GSFL; RMAO/RMAOS directions

## 1. Purpose

Build the main client around a dynamic, local-first ECS world that is continuously remade through the user's own talking, searching, doing, making, saving, playing, and returning.

The client must:

- use the user's own language as the visible language;
- let apps/games emerge from repeated conversation/search instead of forcing fixed applications;
- keep ECS as the principal client state/composition model;
- keep privacy, provenance, accessibility, evidence, safety, rollback, and authority protections behind every client;
- preserve continuity locally so `JUST LOAD IT` can reconstruct the current path without loading irrelevant history;
- represent all walks of life without forcing stereotypes or flattening different forms of wisdom into one universal view;
- keep wisdom contextual, reconstructible, attributable, revisable, and non-authoritative by default.

This design is human-centered and domain-specialized. It does not create a universal ontology over people.

## 2. Core rule: user language owns the visible surface

The internal runtime may use terms such as:

```text
entity
component
system
archetype
state
relation
provenance
evidence
privacy boundary
repair
```

The visible client must instead prefer the exact language the user actually uses.

Examples:

```text
internal entity: research_project_17
user-visible: "Hodge"

internal restore operation
user-visible: "Just Load It"

internal next_action
user-visible: "what do I do next"

internal app capsule
user-visible: whatever the user called the thing
```

Required boundaries:

```text
USER_LANGUAGE != SYSTEM_LANGUAGE
SYSTEM_LANGUAGE_STAYS_BEHIND_CLIENT
NEW_SYSTEM_TERM != USER_TERM
```

If the user has not named a concept, the system should:

1. reuse the nearest existing user-authored wording when faithful; or
2. ask the user what they want to call it when naming materially affects meaning.

It must not silently force a system ontology into the visible client.

## 3. Main client view = dynamic ECS world

ECS is the primary client composition and inspection model.

The client world contains things the user has chosen, searched for, made, saved, learned, or is currently doing.

Example internal classes may include:

```text
Goal
Quest
Project
Search
Tool
Game
Routine
KnowledgeItem
Artifact
PersonRelation
EvidenceItem
UnresolvedItem
WisdomItem
```

These are internal roles. The visible surface uses the user's own words.

The runtime relationship is:

```text
USER
 -> talk / search / do / play / make
 -> local discovery
 -> ECS structural change
 -> protected transition
 -> local save/checkpoint
 -> next client view
```

The client is not a fixed dashboard. It is a projection of what matters now.

```text
WHAT USER WANTS NOW
+ WHAT USER IS DOING NOW
+ WHAT USER NEEDS TO SEE NOW
= CURRENT CLIENT VIEW
```

## 4. Dynamicalization

Everything non-protected may change through explicit user-driven evolution:

```text
names
groups
views
game layers
app layers
search lenses
controls
presentation
task structure
quest structure
relationship between things
```

Structural ECS events are explicit and reversible where possible.

Adding a component requires declared initialization.

Removing a component requires declared projection/transfer/loss behavior.

No structural change may silently erase protected state.

```text
DYNAMIC != HISTORY_ERASURE
REFIT != SILENT_MUTATION
```

## 5. Local-first continuity and JUST LOAD IT

The client persists enough local structure to reconstruct:

```text
what the user was doing
what they wanted
what they had finished
what remained unresolved
what failed
what mattered
what was next
```

`JUST LOAD IT` means:

```text
recover current relevant state
-> widen locally only as necessary
-> restore user-language view
-> restore active path
-> restore unresolved distinctions
-> continue
```

Retrieval widens progressively:

```text
current active state
-> current project
-> local checkpoints
-> local retained artifacts
-> older relevant history
```

Stop when the current obligation is reconstructible.

```text
ALL_REACHABLE != ALL_ACTIVE
```

## 6. Client protection stack

Every state-changing app, game, search, agent, plugin, server, or system request passes through a client protection boundary.

Minimum layers:

```text
LOCAL OWNERSHIP
PRIVACY
CONSENT / CAPABILITY
ACCESSIBILITY
DOMAIN AUTHORITY
EVIDENCE / CLAIM
PROVENANCE / INTEGRITY
SAFETY / HUMAN BURDEN
COST / RESOURCE
VERSION / ROLLBACK
SYNC / SERVER AUTHORITY
```

No generated app or game may bypass these layers.

## 7. Privacy protection and temporary privacy violations

Privacy protection is ON by default.

The special authorization discussed here is not ordinary app permission. It is permission from the user to temporarily allow a specific action that would otherwise violate the user's privacy boundary.

Default behavior:

```text
privacy protection = ON
temporary privacy-violation window = 5 minutes
```

The 5-minute value is an internal parameter that does not clutter the normal UI.

The user may change the duration using ordinary language, for example:

```text
"only for one minute"
"for ten minutes"
"until I finish this"
"stop now"
```

The parameter is hidden from normal presentation but never hidden from the user. The user can ask what it is and inspect active exceptions.

Each exception is scoped to:

```text
which user
which client
which action
which data
which destination
which recipient/system
which duration
which mutation/share operation
```

Required boundaries:

```text
TEMPORARY_PRIVACY_EXCEPTION != PRIVACY_OFF
USER_EXCEPTION != APP_AUTHORITY
EXCEPTION_SCOPE_A != EXCEPTION_SCOPE_B
EXPIRED != RENEWED
```

Exceptions do not auto-renew or transfer.

## 8. Parent boundary

For a child/minor client, the global setting that disables the privacy protection layer itself is parent/guardian-only.

This does not create silent parent access to all child data.

Required boundary:

```text
PARENT_CONTROL != SILENT_ACCESS
```

The design intent is:

- the child/user retains a protected client surface;
- temporary user-level privacy exceptions remain scoped and time-bounded within the applicable parent policy;
- changing the existence of the privacy protection layer itself requires the parent/guardian role;
- parental control actions remain inspectable and attributable.

This design is a technical policy model, not a statement of legal sufficiency in every jurisdiction.

## 9. Walks of Life

The client must support people across all walks of life without reducing them to fixed profiles.

The system may represent user/parent-declared ranges such as:

```text
age/life stage
activity range
social context
location context
ability/accessibility needs
duration
effort
experience duration
role
craft/trade
family/caregiving context
education
community
interests
```

These ranges are descriptive context, not identity conclusions.

```text
AGE != WISDOM
AGE != ABILITY
ROLE != PERSON
ACTIVITY != IDENTITY
PROFILE != DESTINY
```

Sensitive characteristics are not inferred from behavior merely to personalize the client.

## 10. Open-ended activities

The activity catalog is open.

Examples may include:

```text
play
games
learning
school
reading
research
making
programming
art
music
writing
exercise
walking
sports
outdoors
travel
shopping
cooking
home
cleaning
gardening
family
caregiving
friends
community
communication
appointments
planning
work
business
projects
finance
accessibility
health routines
rest
entertainment
hobbies
exploration
search
discovery
building
repair
volunteering
cultural/spiritual activity
life administration
```

But:

```text
ACTIVITY_CATALOG != CLOSED_LIST
```

If the user says "bird watching", "fix my tractor", "help my grandmother", "build a robot", "research Hodge", or anything else, the client can form around that exact user-authored activity.

## 11. Activity ranges

Activities may carry explicit ranges such as:

```text
NOW
TODAY
DAILY
WEEKLY
OCCASIONAL
SEASONAL
PROJECT_LENGTH
LONG_TERM
LIFELONG
ONE_TIME
```

and effort/difficulty when useful:

```text
tiny
short
normal
deep
all-day
multi-day
ongoing

easy
comfortable
challenging
hard
expert
unknown
```

These are internal dimensions only when supported by explicit user context. They are not stereotypes inferred from age or role.

## 12. Accessibility and alternate ways of doing

A goal must not be hard-coded to one body action or one presentation mode.

Example:

```text
movement goal
 -> outdoor walking
 -> indoor walking
 -> wheelchair route
 -> assisted movement
 -> seated movement
 -> another equivalent activity chosen by user
```

```text
GOAL != ONE_REQUIRED_BODY_ACTION
```

Client state can be rendered through multiple carriers:

```text
graphical
game
cards
text
voice
audio/sonification
large type
reduced motion
keyboard-only
switch input
other future carriers
```

Different view does not create different truth:

```text
DIFFERENT_VIEW != DIFFERENT_CLIENT_TRUTH
```

## 13. Apps and games emerge from use

The user need not design an app formally.

The interaction loop is:

```text
"I want ..."
-> search / understand
-> produce something usable
-> user uses it
-> user changes it
-> ECS refits
-> local save
-> continue
```

Apps/games become domain-specialized ECS capsules.

Examples:

```text
learning -> learning quest
exercise -> movement game
research -> investigation world
shopping -> comparison/search tool
household task -> cooperative quest
programming -> build/test/debug loop
travel -> exploration structure
```

The game layer is optional.

```text
GAME_GOAL != HUMAN_GOAL_AUTHORITY
REWARD != OBLIGATION
STREAK != AUTHORITY
```

The underlying app remains usable without the game layer.

## 14. Search is part of the world

Search is not external to the generated client.

```text
NEED
-> SEARCH
-> DISCOVER
-> COMPARE
-> CHOOSE
-> ACT
-> VERIFY
-> KEEP
```

Search results become local entities only when the user/system admits them under the current rules.

```text
SEARCH_RESULT != LOCAL_AUTHORITY
FOUND != VERIFIED
```

## 15. Walks-of-Life wisdom

Wisdom is condensed from paths without flattening different walks into one model.

A wisdom record may preserve:

```text
user/community wording
source walk/context
who expressed or experienced it
conditions
activities
attempts
successes
failures
counterexamples
corrections
provenance
unresolved limitations
```

Condensation flow:

```text
experience
-> distinction
-> repeated pattern
-> counterexample search
-> bounded condensation
-> shareable wisdom
```

Required boundaries:

```text
ONE_WALK != ALL_WALKS
AGE != WISDOM
EXPERTISE_ONE_DOMAIN != EXPERTISE_ANOTHER
POPULAR_WISDOM != UNIVERSAL_TRUTH
INHERITED_WISDOM != LIVED_EXPERIENCE
CONDENSED != CONTEXT_REMOVED
```

Multiple contradictory wisdoms may coexist when they arise from different conditions.

The system must preserve:

```text
COMMON_WISDOM
LOCAL_WISDOM
PERSONAL_WISDOM
CONTRADICTORY_WISDOM
UNRESOLVED_WISDOM
```

rather than averaging them into one answer.

## 16. Wisdom transfer

Wisdom can travel between people, families, communities, teachers, crafts, and generations while preserving lineage.

```text
Walker/Person A lived/expressed it
-> condensed wisdom
-> Person B receives it
```

For Person B:

```text
RECEIVED_WISDOM != LIVED_EXPERIENCE
```

If B later tests or uses it, that creates B's own path attached to the inherited item.

Parent or elder wisdom is not automatically a child's obligation:

```text
PARENT_WISDOM != CHILD_OBLIGATION
ELDER_WISDOM != UNQUESTIONABLE_TRUTH
```

## 17. ECS inspection view

The main client may render a simple human view using only the user's words.

An advanced inspection view may expose:

```text
entity
current components
relations
systems touching it
who/what may mutate it
last transition
source
evidence
privacy scope
failures
rollback points
unresolved state
```

The advanced view is optional and does not replace the user-language surface.

## 18. Protected client transition

Conceptual transition:

```text
REQUEST
-> resolve affected client/domain/state
-> check privacy/capability/accessibility/authority
-> propose transition
-> verify provenance/evidence/reversibility/cost
-> admit or reject
-> apply atomically
-> observe consequence
-> counterprobe when required
-> record before/operation/after/residual
-> checkpoint
```

Rejected transitions preserve client state and return an inspectable reason.

## 19. Multi-client and multiplayer boundaries

Each client's private local state remains independently protected.

```text
CONNECTED_CLIENTS != MERGED_CLIENT_STATE
SHARED_APP != SHARED_PRIVATE_MEMORY
MULTIPLAYER != LOSS_OF_LOCAL_AUTHORITY
```

A live shared game may have server-authoritative shared-world state while private client preferences, local history, and private user data remain separately scoped.

Every bridge declares:

```text
what is shared
why
with whom
which version
what may be changed
what returns
what is retained
what can be revoked
```

## 20. Relation to existing ECS research

This design incorporates, without erasing their separate evidence:

```text
data-driven ECS
configuration-indexed ECS
archetype / SoA ECS
solver ECS
evidence ECS
cooperative ECS
relation ECS
observer ECS
render/video ECS
RMAO world ECS
Decision Field
RMAPL/Ω repair/fitting
GSFL semantic fitting
```

The important architectural change is:

> ECS is both the principal client-visible world model and the execution substrate, while every client is wrapped by mandatory protection layers.

Native domain systems remain authoritative for their own semantics.

## 21. Relation to RMAO and RMAOS/MINGX direction

RMAO remains its own game-world specialization with its server/world authority rules.

The broader life-runtime direction uses the same ECS family for user-created games/apps, but:

```text
RMAO_WORLD != USER_PRIVATE_WORLD
GAME_SERVER_AUTHORITY != PRIVATE_CLIENT_AUTHORITY
```

The design does not require every user app to become an MMORPG.

## 22. Data-driven, domain-specialized quality rule

Each generated app/game must derive from its actual domain data and declared user need.

```text
USER_NEED
+ DOMAIN_DATA
+ DOMAIN_RULES
+ CLIENT_PROTECTION
-> DOMAIN-SPECIALIZED CAPSULE
```

Do not force a generic app template when domain distinctions materially differ.

Inspectability remains mandatory:

```text
what changed
why
what was preserved
what was lost
what was shared
who/what authorized it
what evidence supports it
what remains unresolved
how to undo/repair it
```

## 23. Acceptance criteria for future implementation

A future implementation must prove at least:

1. visible client naming uses user-authored terms for fixtures where those terms exist;
2. internal ECS/system names are not exposed as required user vocabulary;
3. structural ECS changes preserve history and declare loss when removing state;
4. `JUST LOAD IT` reconstructs the current user-language path from local state without loading unrelated history;
5. every state-changing subsystem passes through the client protection gate;
6. privacy protection defaults ON;
7. a temporary privacy exception defaults to 5 minutes, is scoped, expires, does not auto-renew, and can be revoked early;
8. changing the exception duration through ordinary user language updates the hidden duration parameter without exposing implementation syntax;
9. one privacy exception cannot authorize a different privacy action;
10. for a child/minor fixture, global privacy-protection disable requires the parent/guardian role;
11. parent control does not create silent unlogged access;
12. activity/range handling is open-ended and does not infer age/ability/identity from unrelated behavior;
13. alternate accessibility carriers preserve the same protected underlying state;
14. wisdom retains source context, provenance, failures/counterexamples, and uncertainty;
15. inherited wisdom remains distinct from lived experience;
16. contradictory wisdoms remain separately inspectable;
17. search results do not become local authority merely by retrieval;
18. multiplayer/shared-world state does not expose private client state without an explicit bridge;
19. RMAO authority boundaries remain intact;
20. existing native domain tests remain green unless a separately evidenced defect is found.

## 24. Rollout boundary

First implementation should be narrow:

```text
Phase 1:
  local client root
  user-language naming map
  ECS structural event ledger
  client protection gate
  privacy exception window
  JUST LOAD IT local reconstruction
  inspection view
  exact tests

Phase 2:
  dynamic app/game capsules
  activity ranges
  accessibility carrier switching
  search-to-local admission

Phase 3:
  Walks-of-Life wisdom records
  wisdom condensation
  inheritance/testing lineage
  contradictory-wisdom inspection

Phase 4:
  multi-client bridges
  shared-world/game integration
  RMAO/RMAOS specializations
```

No phase may weaken client privacy or native domain authority to simplify integration.

## 25. Final design statement

The client belongs to the user.

The visible language belongs to the user.

The world changes around what the user actually says, searches, does, makes, and keeps.

ECS is the dynamic state/composition substrate.

Protection is mandatory behind every client.

Privacy exceptions are narrow, temporary, inspectable, and user-controlled; global protection-disable for child/minor clients is parent/guardian-controlled without becoming silent access.

Walks-of-Life wisdom remains plural, contextual, reconstructible, and revisable.

```text
USER WORDS
-> USER THINGS
-> USER PATH
-> DYNAMIC ECS CLIENT
-> PROTECTED TRANSITIONS
-> LOCAL SAVE
-> JUST LOAD IT
-> CONTINUE
```

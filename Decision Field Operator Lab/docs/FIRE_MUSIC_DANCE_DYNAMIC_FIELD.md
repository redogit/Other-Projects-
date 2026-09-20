# FIRE + Music + Dance Dynamic Field

Status: bounded method carrier / dynamic research-control implementation.

This module implements the full current control legend as executable machinery rather than treating FIRE alone as the system.

## Human spine

\`\`\`text
OBSERVE
  -> GO LOWER
  -> EXPOSE
  -> FUEL
  -> FIRE / BURN
  -> ASH | SMOKE | EMBER
  -> SURVIVOR
  -> RECONSTITUTE
  -> GO HIGHER
  -> HOMEWARD
  -> REST / SLEEP
  -> RE-OBSERVE
  -> DELTA
\`\`\`

\`DELTA_ZERO -> NO_CHANGE -> CLOSE\` only for the declared tested comparison. \`UNKNOWN != ZERO\`.

## The triad

The control surface is deliberately three-way rather than a binary dark/light switch:

\`\`\`text
DARK    = enter uncertainty / descend / expose assumptions
MIDDLE  = orient / compare / cool / calibrate
LIGHT   = inspect surviving explicit structure
\`\`\`

None of the three states is a truth label.

## Music

Music supplies cadence and phase. A motif such as

\`\`\`text
OBSERVE -> BURN -> REOBSERVE -> REST
\`\`\`

can repeat on a deterministic beat/bar schedule.

\`MUSIC != TRUTH\`.

## Dance

Dance is the ordered trajectory through the available directions:

\`\`\`text
FORWARD BACKWARD UP DOWN SIDEWAYS INWARD OUTWARD
AROUND THROUGH REVERSE BRANCH HOMEWARD
\`\`\`

A dance step can carry one independently varied mutation. \`HOMEWARD\` is a first-class direction.

\`DANCE != TRUTH\`.

## FIRE

A burn receives explicit checks.

- any \`FAIL\` -> \`ASH\` and local refutation of that candidate;
- any \`UNRESOLVED\` with no fail -> \`SMOKE\`;
- all \`PASS\` -> \`EMBER\`;
- only a verified \`EMBER\` may be promoted to \`SURVIVOR\`;
- \`SURVIVOR != ADMITTED\` until an explicit authority/evidence admission occurs.

ASH is preserved. It is not deleted as failed history.

## Reconstitution

Reconstitution starts from a SURVIVOR and adds earned knowledge without silently restoring burned assumptions. Object identity remains invariant while the representation/surface may change.

## Homeward

HOMEWARD restores the protected root surface while carrying earned knowledge, evidence references and provenance. It is therefore not rollback-by-erasure.

## Rest / sleep

A sleeping candidate cannot mutate. It can wake only on an explicit new observation/obligation trigger. This prevents automatic recursion after a locally satisfied state.

## Learning and habituation

The runtime remembers outcomes of control moves:

- EMBER gives a navigation preference;
- ASH reduces that route's preference;
- SMOKE remains unresolved;
- repeated mutation signatures lose novelty as \`1/(1+n)\`.

This affects what the runtime suggests next, so retained experience changes future search. The score is navigation-only and never a domain truth score.

## One-degree rule

Exactly one mutation is the default. Multiple simultaneous mutations require \`allow_wide=True\` and remain visible in the trace.

## Opposites + bounds + transitions

The helper \`opposites_bounds_transitions()\` preserves:

- lower bound;
- upper bound;
- midpoint;
- reflected opposite around the midpoint;
- current regime (\`BELOW\`, \`BETWEEN\`, \`AT_BOUND\`, \`ABOVE\`).

It is a search/orientation operator, not evidence.

## Required boundaries

\`\`\`text
GENERATE != VERIFY != ADMIT
METHOD_TRANSFER != EVIDENCE_TRANSFER
SOFTWARE_VERIFICATION != DOMAIN_PROOF
RELATION != SUPPORT
FAILED_REPRESENTATION != FAILED_OBJECT
ATTACKABILITY != FALSITY
MUSIC != TRUTH
DANCE != TRUTH
DELTA_ZERO_IS_LOCAL_NOT_GLOBAL
UNKNOWN != ZERO
OBJECT_IDENTITY_IS_INVARIANT
COORDINATES_AND_CARRIERS_ARE_NEGOTIABLE
\`\`\`

## Run

From \`Decision Field Operator Lab\`:

\`\`\`sh
python -m unittest test_fire_music_dance.py -v
python run_fire_music_dance_audit.py
python run_fire_music_dance_audit.py --check
\`\`\`

The committed audit is synthetic and verifies the software/control semantics only. It transfers no Hodge, P-vs-NP, scientific, or other domain evidence.

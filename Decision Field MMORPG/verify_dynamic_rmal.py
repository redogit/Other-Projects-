from pathlib import Path

ROOT = Path(__file__).resolve().parent
RMAL = ROOT / "DYNAMIC_RMAL_CHARACTERS.rmal"

REQUIRED = [
    'RMAL DYNAMIC 0.1',
    'WORLD "rmao-world"',
    'ENTITY SuperSeraphine',
    'TYPE Sproutling',
    'GAME_CHARACTER != PRIVATE_PERSON',
    'SPROUTLING != REAL_CHILD',
    'TRICKSTER_ROLE != ADMIN_AUTHORITY',
    'PRESENTATION_SPOOF != SERVER_STATE',
    'authority_ceiling = GAME_ENTITY',
    'private_person    = NONE',
    'family_proxy      = NONE',
    'IMPERSONATE_REAL_PERSON()',
    'MINT_SERVER_AUTHORITY()',
]

text = RMAL.read_text(encoding="utf-8")
missing = [token for token in REQUIRED if token not in text]
if missing:
    raise SystemExit("FAIL missing Dynamic RMAL obligations: " + ", ".join(missing))

if text.count("ENTITY SuperSeraphine") != 1:
    raise SystemExit("FAIL canonical Super Seraphine entity must appear exactly once")

if text.count("TYPE Sproutling") != 1:
    raise SystemExit("FAIL canonical Sproutling type must appear exactly once")

print("PASS Dynamic RMAL character contract")
print("PASS privacy/authority invariants")

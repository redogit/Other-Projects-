from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from itertools import permutations, product
import json
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

BOOL_INPUTS = ((0, 0), (0, 1), (1, 0), (1, 1))
A_MASK = 0b1100
B_MASK = 0b1010

BOOLEAN_NAMES = {
    0: "FALSE",
    1: "NOR",
    2: "B_AND_NOT_A",
    3: "NOT_A",
    4: "A_AND_NOT_B",
    5: "NOT_B",
    6: "XOR",
    7: "NAND",
    8: "AND",
    9: "XNOR",
    10: "B",
    11: "A_IMPLIES_B",
    12: "A",
    13: "B_IMPLIES_A",
    14: "OR",
    15: "TRUE",
}

FAMILY_HINTS = {
    "FALSE": "constant",
    "TRUE": "constant",
    "A": "projection",
    "B": "projection",
    "NOT_A": "negation",
    "NOT_B": "negation",
    "AND": "conjunction",
    "NAND": "conjunction",
    "OR": "disjunction",
    "NOR": "disjunction",
    "XOR": "difference",
    "XNOR": "difference",
    "A_AND_NOT_B": "directional_difference",
    "B_AND_NOT_A": "directional_difference",
    "A_IMPLIES_B": "directional",
    "B_IMPLIES_A": "directional",
}


@dataclass(frozen=True)
class Operator:
    id: str
    family: str
    arity: int
    domain: str
    codomain: str
    truth_mask: int | None = None
    commutative: bool | None = None
    associative: bool | None = None
    idempotent: bool | None = None
    identity: int | None = None
    absorbing: int | None = None
    converse: str | None = None
    output_complement: str | None = None
    demorgan_dual: str | None = None
    invertible_each_argument: bool | None = None
    executable: bool = True
    notes: str = ""


@dataclass(frozen=True)
class NandStep:
    left: int
    right: int
    output: int


@dataclass(frozen=True)
class Certificate:
    target_mask: int
    primitive: str
    gates: tuple[NandStep, ...]
    verified: bool


@dataclass(frozen=True)
class CompassHeading:
    vector: tuple[int, int, int, int]
    support: int
    opposite: tuple[int, int, int, int]
    canonical: tuple[int, int, int, int]


@dataclass(frozen=True)
class SPrimeScore:
    gain: int
    loss: int
    magnitude: int
    signed: float
    representation_only: bool
    computational_cost: int
    unresolved: bool


@dataclass(frozen=True)
class AdmissionRecord:
    key: str
    status: str
    certificate: str | None
    provenance: str


class AlgorithmicBuilder:
    """Minimal admission protocol: PROPOSE -> VERIFY -> ADMIT_UNIQUE -> PROMOTE."""

    def __init__(self) -> None:
        self.records: dict[str, AdmissionRecord] = {}
        self.semantic_keys: set[str] = set()

    def propose(self, key: str, *, provenance: str = "") -> AdmissionRecord:
        record = AdmissionRecord(key, "PROPOSED", None, provenance)
        self.records[key] = record
        return record

    def verify(
        self,
        key: str,
        verifier: Callable[[], bool],
        *,
        certificate: str | None = None,
    ) -> AdmissionRecord:
        previous = self.records.get(key)
        if previous is None:
            raise KeyError(f"proposal not found: {key}")
        status = "VERIFIED" if verifier() else "REJECTED"
        record = AdmissionRecord(key, status, certificate, previous.provenance)
        self.records[key] = record
        return record

    def admit_unique(self, key: str, *, semantic_key: str) -> AdmissionRecord:
        previous = self.records.get(key)
        if previous is None or previous.status != "VERIFIED":
            raise ValueError("only VERIFIED proposals may be admitted")
        if semantic_key in self.semantic_keys:
            record = AdmissionRecord(key, "DUPLICATE", previous.certificate, previous.provenance)
        else:
            self.semantic_keys.add(semantic_key)
            record = AdmissionRecord(key, "ADMITTED_UNIQUE", previous.certificate, previous.provenance)
        self.records[key] = record
        return record

    def promote(self, key: str) -> AdmissionRecord:
        previous = self.records.get(key)
        if previous is None or previous.status != "ADMITTED_UNIQUE":
            raise ValueError("only ADMITTED_UNIQUE records may be promoted")
        record = AdmissionRecord(key, "PROMOTED_PRIMITIVE", previous.certificate, previous.provenance)
        self.records[key] = record
        return record


def bit(mask: int, a: int, b: int) -> int:
    return (mask >> BOOL_INPUTS.index((a, b))) & 1


def apply_mask(mask: int, a: int, b: int) -> int:
    return bit(mask, a, b)


def swap_mask(mask: int) -> int:
    result = 0
    for index, (a, b) in enumerate(BOOL_INPUTS):
        result |= apply_mask(mask, b, a) << index
    return result


def output_complement_mask(mask: int) -> int:
    return mask ^ 0b1111


def demorgan_dual_mask(mask: int) -> int:
    result = 0
    for index, (a, b) in enumerate(BOOL_INPUTS):
        value = 1 - apply_mask(mask, 1 - a, 1 - b)
        result |= value << index
    return result


def identity_value(mask: int) -> int | None:
    for e in (0, 1):
        if all(apply_mask(mask, x, e) == x and apply_mask(mask, e, x) == x for x in (0, 1)):
            return e
    return None


def absorbing_value(mask: int) -> int | None:
    for z in (0, 1):
        if all(apply_mask(mask, x, z) == z and apply_mask(mask, z, x) == z for x in (0, 1)):
            return z
    return None


def is_associative(mask: int) -> bool:
    return all(
        apply_mask(mask, apply_mask(mask, a, b), c)
        == apply_mask(mask, a, apply_mask(mask, b, c))
        for a, b, c in product((0, 1), repeat=3)
    )


def invertible_each_argument(mask: int) -> bool:
    # For every fixed value of either argument, the remaining unary map is bijective.
    return all(
        {apply_mask(mask, a, b) for a in (0, 1)} == {0, 1}
        and {apply_mask(mask, a, b) for b in (0, 1)} == {0, 1}
        for a, b in ((0, 0), (1, 1))
    )


def boolean_registry() -> list[Operator]:
    operators: list[Operator] = []
    by_mask = BOOLEAN_NAMES
    for mask in range(16):
        name = by_mask[mask]
        swapped = swap_mask(mask)
        converse = by_mask[swapped]
        complement = by_mask[output_complement_mask(mask)]
        dual = by_mask[demorgan_dual_mask(mask)]
        operators.append(
            Operator(
                id=name,
                family=FAMILY_HINTS[name],
                arity=2,
                domain="bool×bool",
                codomain="bool",
                truth_mask=mask,
                commutative=swapped == mask,
                associative=is_associative(mask),
                idempotent=all(apply_mask(mask, x, x) == x for x in (0, 1)),
                identity=identity_value(mask),
                absorbing=absorbing_value(mask),
                converse=converse,
                output_complement=complement,
                demorgan_dual=dual,
                invertible_each_argument=invertible_each_argument(mask),
            )
        )
    return operators


def structural_registry() -> list[Operator]:
    return [
        Operator("PRESERVE", "state", 1, "state", "state", executable=False, notes="Identity on a declared state space."),
        Operator("PERMUTE", "symmetry", 1, "state", "state", executable=False, notes="Lateral orbit motion when obligations are preserved."),
        Operator("CANONICALIZE", "symmetry", 1, "orbit", "representative", executable=False, notes="Choose one representative per certified orbit."),
        Operator("SPLIT", "structural", 1, "partition", "partition", executable=False, notes="Refinement candidate; S' direction is obligation-relative."),
        Operator("MERGE", "structural", 1, "partition", "partition", executable=False, notes="Coarsening candidate; S' direction is obligation-relative."),
        Operator("REPAIR", "transform", 1, "state", "state", executable=False, notes="Move toward an obligation-satisfying state under a declared cost."),
        Operator("MUX", "selection", 3, "bool×bool×bool", "bool", executable=False, notes="Three-input conditional selector; outside binary calibration."),
        Operator("FILTER", "selection", 2, "set×predicate", "set", executable=False, notes="Structural selection operator; not a Boolean truth-table competitor here."),
        Operator("THRESHOLD_K", "counting", -1, "bool^n", "bool", executable=False, notes="Parameterized counting family."),
        Operator("EXACTLY_K", "counting", -1, "bool^n", "bool", executable=False, notes="Parameterized counting family."),
    ]


def operator_registry() -> list[Operator]:
    return boolean_registry() + structural_registry()


def nand_mask(left: int, right: int) -> int:
    result = 0
    for index in range(4):
        value = 1 - (((left >> index) & 1) & ((right >> index) & 1))
        result |= value << index
    return result


def execute_nand_certificate(certificate: Certificate) -> bool:
    available = {A_MASK, B_MASK}
    for step in certificate.gates:
        if step.left not in available or step.right not in available:
            return False
        if nand_mask(step.left, step.right) != step.output:
            return False
        available.add(step.output)
    return certificate.target_mask in available


def synthesize_nand(
    target_mask: int,
    *,
    max_gates: int = 5,
    beam: int | None = None,
    total_candidate_cap: int = 100_000,
) -> Certificate:
    if target_mask in {A_MASK, B_MASK}:
        return Certificate(target_mask, "NAND", (), True)

    start = frozenset({A_MASK, B_MASK})
    queue: deque[tuple[frozenset[int], tuple[NandStep, ...]]] = deque([(start, ())])
    seen = {start}
    expanded = 0

    while queue:
        available, program = queue.popleft()
        if len(program) >= max_gates:
            continue
        generated: list[tuple[frozenset[int], tuple[NandStep, ...]]] = []
        ordered = sorted(available)
        for i, left in enumerate(ordered):
            for right in ordered[i:]:
                output = nand_mask(left, right)
                if output in available:
                    continue
                next_available = frozenset((*available, output))
                if next_available in seen:
                    continue
                next_program = program + (NandStep(left, right, output),)
                seen.add(next_available)
                expanded += 1
                if expanded > total_candidate_cap:
                    raise RuntimeError("total candidate cap exceeded")
                if output == target_mask:
                    certificate = Certificate(target_mask, "NAND", next_program, False)
                    return Certificate(target_mask, "NAND", next_program, execute_nand_certificate(certificate))
                generated.append((next_available, next_program))

        generated.sort(key=lambda item: (-len(item[0]), tuple(sorted(item[0]))))
        if beam is not None:
            generated = generated[:beam]
        queue.extend(generated)

    raise LookupError(f"truth mask {target_mask} not reached within {max_gates} NAND gates")


def all_boolean_certificates(max_gates: int = 5) -> dict[int, Certificate]:
    return {mask: synthesize_nand(mask, max_gates=max_gates) for mask in range(16)}


def canonical_heading(vector: Sequence[int]) -> tuple[int, int, int, int]:
    support = sum(value != 0 for value in vector)
    return tuple([1] * support + [0] * (4 - support))  # type: ignore[return-value]


def compass_headings() -> list[CompassHeading]:
    headings = []
    for vector in product((-1, 0, 1), repeat=4):
        if vector == (0, 0, 0, 0):
            continue
        support = sum(value != 0 for value in vector)
        opposite = tuple(-value for value in vector)
        headings.append(CompassHeading(vector, support, opposite, canonical_heading(vector)))
    return headings


def orbit_from_template(support: int) -> set[tuple[int, int, int, int]]:
    if support not in {1, 2, 3, 4}:
        raise ValueError("support must be 1..4")
    seed = tuple([1] * support + [0] * (4 - support))
    vectors: set[tuple[int, int, int, int]] = set()
    for perm in set(permutations(seed)):
        nonzero_positions = [i for i, value in enumerate(perm) if value]
        for signs in product((-1, 1), repeat=support):
            vector = list(perm)
            for index, sign in zip(nonzero_positions, signs):
                vector[index] = sign
            vectors.add(tuple(vector))  # type: ignore[arg-type]
    return vectors


def compass_audit() -> dict:
    headings = compass_headings()
    support_counts = {support: sum(h.support == support for h in headings) for support in range(1, 5)}
    independent = {support: len(orbit_from_template(support)) for support in range(1, 5)}
    all_independent = set().union(*(orbit_from_template(support) for support in range(1, 5)))
    heading_vectors = {h.vector for h in headings}
    return {
        "heading_count": len(headings),
        "support_counts": support_counts,
        "canonical_templates": {
            support: list(canonical_heading([1] * support + [0] * (4 - support)))
            for support in range(1, 5)
        },
        "independent_orbit_counts": independent,
        "coverage_verified": all_independent == heading_vectors,
        "opposites_verified": all(h.opposite in heading_vectors for h in headings),
    }


def score_sprime(
    before: Iterable[str],
    after: Iterable[str],
    *,
    representation_changed: bool = False,
    cost: int = 0,
    unresolved: bool = False,
) -> SPrimeScore:
    before_set, after_set = set(before), set(after)
    gain = len(after_set - before_set)
    loss = len(before_set - after_set)
    magnitude = gain + loss
    signed = (gain - loss) / magnitude if magnitude else 0.0
    return SPrimeScore(
        gain=gain,
        loss=loss,
        magnitude=magnitude,
        signed=signed,
        representation_only=representation_changed and magnitude == 0,
        computational_cost=cost,
        unresolved=unresolved,
    )


def rank_boolean_operators(
    required_rows: Mapping[tuple[int, int], int],
    *,
    max_nand_gates: int = 5,
) -> list[dict]:
    certificates = all_boolean_certificates(max_nand_gates)
    registry = {op.truth_mask: op for op in boolean_registry()}
    rows: list[dict] = []
    for mask in range(16):
        violations = sum(apply_mask(mask, *inputs) != expected for inputs, expected in required_rows.items())
        operator = registry[mask]
        rows.append(
            {
                "id": operator.id,
                "truth_mask": mask,
                "violations": violations,
                "nand_gates": len(certificates[mask].gates),
                "ones": mask.bit_count(),
                "commutative": operator.commutative,
                "associative": operator.associative,
            }
        )
    return sorted(rows, key=lambda row: (row["violations"], row["nand_gates"], row["id"]))


COUNTING_ALIASES = {
    "THRESHOLD_1_OF_2": "OR",
    "THRESHOLD_2_OF_2": "AND",
    "EXACTLY_0_OF_2": "NOR",
    "EXACTLY_1_OF_2": "XOR",
    "EXACTLY_2_OF_2": "AND",
}


def balance_report() -> dict:
    fixtures = {
        "exclusive_change": {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 0},
        "agreement": {(0, 0): 1, (0, 1): 0, (1, 0): 0, (1, 1): 1},
        "intersection": {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 1},
        "coverage": {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 1},
        "endpoint_preserving_symmetric": {(0, 0): 0, (1, 1): 1},
    }
    result: dict[str, dict] = {}
    for name, requirements in fixtures.items():
        ranking = rank_boolean_operators(requirements)
        if name == "endpoint_preserving_symmetric":
            ranking = [row for row in ranking if row["commutative"]]
            ranking.sort(key=lambda row: (row["violations"], row["nand_gates"], row["id"]))
        result[name] = {
            "requirements": {f"{a}{b}": expected for (a, b), expected in requirements.items()},
            "winner": ranking[0]["id"],
            "ranking": ranking,
            "cost_rule": ["violations", "nand_gates", "id"],
        }
    result["structural_comparison"] = {
        op.id: "INCOMPARABLE_ON_BOOLEAN_FIXTURES"
        for op in structural_registry()
    }
    return {
        "fixtures": result,
        "counting_aliases": COUNTING_ALIASES,
        "interpretation": (
            "Winner is fixture-relative under an explicit lexicographic cost vector. "
            "XOR is a discriminator on exclusive-change obligations, not a universal balance law."
        ),
    }


def bounded_audit() -> dict:
    certificates = all_boolean_certificates()

    xnor_four_gate_reachable = True
    try:
        synthesize_nand(9, max_gates=4)
    except LookupError:
        xnor_four_gate_reachable = False

    builder = AlgorithmicBuilder()
    proposed = builder.propose("xor-candidate", provenance="binary Boolean calibration")
    verified = builder.verify("xor-candidate", lambda: execute_nand_certificate(certificates[6]), certificate="NAND witness")
    admitted = builder.admit_unique("xor-candidate", semantic_key="truth-mask:6")
    promoted = builder.promote("xor-candidate")

    builder.propose("xor-alternate", provenance="same semantic truth mask")
    builder.verify("xor-alternate", lambda: True, certificate="independent truth-table check")
    duplicate = builder.admit_unique("xor-alternate", semantic_key="truth-mask:6")

    equal_gain_loss = score_sprime({"a"}, {"b"}, representation_changed=True, cost=1)

    return {
        "schema": "decision-field-operator-lab/audit-v1",
        "boolean": {
            "operator_count": 16,
            "all_masks_present": sorted(certificates) == list(range(16)),
            "all_certificates_verified": all(c.verified and execute_nand_certificate(c) for c in certificates.values()),
            "max_nand_gate_count": max(len(c.gates) for c in certificates.values()),
            "gate_counts": {BOOLEAN_NAMES[mask]: len(certificates[mask].gates) for mask in range(16)},
        },
        "compass": compass_audit(),
        "negative_controls": {
            "xnor_reachable_within_four_nand_gates": xnor_four_gate_reachable,
            "expected": False,
        },
        "admission_protocol": {
            "proposed": asdict(proposed),
            "verified": asdict(verified),
            "admitted": asdict(admitted),
            "promoted": asdict(promoted),
            "duplicate": asdict(duplicate),
        },
        "equal_gain_loss_control": asdict(equal_gain_loss),
        "balance": balance_report(),
    }


def periodic_table() -> dict:
    certificates = all_boolean_certificates()
    rows = []
    for operator in boolean_registry():
        cert = certificates[operator.truth_mask]  # type: ignore[index]
        row = asdict(operator)
        row["nand_gate_count"] = len(cert.gates)
        row["certificate"] = [asdict(step) for step in cert.gates]
        row["certificate_verified"] = cert.verified and execute_nand_certificate(cert)
        rows.append(row)

    return {
        "schema": "decision-field-operator-lab/operator-table-v1",
        "boolean_operators": rows,
        "structural_operators": [asdict(op) for op in structural_registry()],
        "compass": compass_audit(),
        "enumeration_contracts": [
            {
                "space": "binary Boolean operators",
                "status": "FINITE_EXHAUSTIVE",
                "count": 16,
                "deterministic": True,
                "total": True,
            },
            {
                "space": "signed 4D compass headings in {-1,0,1}^4 minus zero",
                "status": "FINITE_EXHAUSTIVE",
                "count": 80,
                "deterministic": True,
                "total": True,
            },
            {
                "space": "NAND straight-line programs",
                "status": "FINITE_BOUNDED_SEARCH",
                "max_gates": 5,
                "semantic_state_deduplication": True,
                "coverage_claim": "exact only for the declared Boolean calibration and stated gate bound when no beam truncation occurs",
            },
        ],
        "balance": balance_report(),
        "boundaries": [
            "XOR is a discriminator, not a universal decision law.",
            "Permutation/symmetry is lateral motion (S'=0) only when declared obligations are preserved.",
            "Equal consequential gain and loss may project to signed zero while magnitude remains nonzero.",
            "Iterable/enumerable does not imply decidable.",
            "Finite exhaustive calibration is not a universal novelty detector.",
            "Structural operators registered here are incomparable on binary Boolean fixtures unless a domain bridge is explicitly supplied.",
        ],
    }


def write_periodic_table(path: str | Path) -> None:
    Path(path).write_text(json.dumps(periodic_table(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

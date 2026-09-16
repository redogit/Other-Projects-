"""Bounded proverbial fixture generation for GSFL v0.1.

The fixture layer is intentionally non-authoritative: a proverb can carry several
human/machine/alternate readings, provenance, partner/tool traces, corollaries,
and confounds without promoting any reading into a universal or singular truth.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import random
from typing import Any, Iterable

import gsfl

SOURCE_STATUSES = {"TRADITIONAL_OR_COMMON", "SYNTHETIC", "QUOTED_SOURCE", "TRANSLATED_SOURCE"}


@dataclass(frozen=True)
class ProverbProvenance:
    source_kind: str
    source_detail: str
    evidence_group: str

    def __post_init__(self) -> None:
        if not self.source_kind or not self.source_detail or not self.evidence_group:
            raise ValueError("proverb provenance fields are required")


@dataclass(frozen=True)
class ProverbTool:
    tool_id: str
    purpose: str
    provenance: str
    evidence_group: str

    def __post_init__(self) -> None:
        if not all((self.tool_id, self.purpose, self.provenance, self.evidence_group)):
            raise ValueError("proverb tool id, purpose, provenance, and evidence_group are required")


@dataclass(frozen=True)
class ProverbCooperationStep:
    partner_kind: str
    action: str
    detail: str
    tools: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.partner_kind not in {"HUMAN", "MACHINE"}:
            raise ValueError("proverb cooperation partner must be HUMAN or MACHINE")
        if not self.action or not self.detail:
            raise ValueError("proverb cooperation action and detail are required")


@dataclass(frozen=True)
class ProverbFixture:
    fixture_id: str
    source_text: str
    source_status: str
    context: str
    provenance: ProverbProvenance
    human_interpretations: tuple[str, ...]
    machine_interpretations: tuple[str, ...]
    alternate_interpretations: tuple[str, ...]
    invariant_meanings: tuple[str, ...]
    cooperation_trace: tuple[ProverbCooperationStep, ...]
    tools: tuple[ProverbTool, ...]
    human_understanding_evidence: str = "NONE"
    claims_single_true_meaning: bool = False

    def __post_init__(self) -> None:
        if not self.fixture_id or not self.source_text or not self.context:
            raise ValueError("fixture id, source text, and context are required")
        if self.source_status not in SOURCE_STATUSES:
            raise ValueError(f"unknown source status {self.source_status!r}")
        if not self.human_interpretations or not self.machine_interpretations:
            raise ValueError("human and machine interpretations are both required")
        if not self.invariant_meanings:
            raise ValueError("at least one invariant meaning/boundary is required")
        tool_ids = {t.tool_id for t in self.tools}
        if len(tool_ids) != len(self.tools):
            raise ValueError("proverb tool IDs must be unique")
        for step in self.cooperation_trace:
            unknown = set(step.tools) - tool_ids
            if unknown:
                raise ValueError(f"unknown proverb tool reference {sorted(unknown)[0]!r}")
        if self.claims_single_true_meaning:
            raise ValueError("proverb fixtures may not claim one universal true meaning")


PROVERB_COROLLARIES = (
    {
        "id": "MULTIPLE_READINGS_REMAIN_DISTINCT",
        "statement": "Human, machine, and alternate readings can coexist without being collapsed into one authoritative meaning.",
        "boundary": "preserving alternatives does not establish that every reading is equally supported",
    },
    {
        "id": "SOURCE_STATUS_PRESERVES_LINEAGE",
        "statement": "Traditional/common, quoted, translated, and synthetic sayings can remain distinguishable through transport.",
        "boundary": "a source label does not establish exact historical origin",
    },
    {
        "id": "SYNTHETIC_FIXTURES_CAN_CALIBRATE",
        "statement": "Synthetic proverb-like fixtures can test cooperation and semantic transport without pretending to be cultural tradition.",
        "boundary": "synthetic usefulness does not create cultural provenance",
    },
    {
        "id": "PARTNER_DISAGREEMENT_IS_RETAINABLE",
        "statement": "Human and machine partners can preserve disagreement as data for review instead of forcing premature consensus.",
        "boundary": "retained disagreement does not by itself resolve the interpretation",
    },
    {
        "id": "PROVERB_IS_SURFACE_NOT_EVIDENCE",
        "statement": "A proverb can be a compact reasoning surface while remaining separate from empirical or factual evidence.",
        "boundary": "memorable wording is not proof",
    },
    {
        "id": "TOOL_TRACE_SUPPORTS_RECONSTRUCTION",
        "statement": "Tool and partner traces make the generation/review path reconstructible.",
        "boundary": "reconstructible process does not certify output truth",
    },
)


PROVERB_CONFOUND_REGISTRY = (
    {"id": "TRANSLATION_LOSS", "control": "retain source language/text when available and treat translations as interpretations rather than identity"},
    {"id": "CULTURAL_FLATTENING", "control": "retain context and do not replace local meanings with one generic global gloss"},
    {"id": "FALSE_UNIVERSALITY", "control": "label applicability as contextual rather than universal"},
    {"id": "ATTRIBUTION_UNCERTAINTY", "control": "separate common/traditional status from exact author, date, or culture claims"},
    {"id": "LITERAL_FIGURATIVE_COLLAPSE", "control": "retain literal and figurative readings as separate candidate interpretations"},
    {"id": "MACHINE_PARAPHRASE_AS_HUMAN_UNDERSTANDING", "control": "require human-side evidence such as teach-back or task performance before claiming human understanding"},
    {"id": "POPULARITY_AS_TRUTH", "control": "do not convert repetition, familiarity, or popularity into factual truth"},
    {"id": "PRESERVATION_AS_ENDORSEMENT", "control": "preserve sayings without treating preservation as moral or factual endorsement"},
    {"id": "SYNTHETIC_PROVENANCE_LAUNDERING", "control": "keep generator provenance attached and reject relabeling synthetic sayings as traditional"},
    {"id": "LEXICAL_SIMILARITY_AS_CROSS_CULTURAL_EQUIVALENCE", "control": "require contextual evidence before calling similar wording or themes culturally equivalent"},
    {"id": "FAMILIARITY_BIAS", "control": "compare unfamiliar and familiar fixtures without ranking familiarity as semantic quality"},
    {"id": "SURVIVORSHIP_OF_SAYINGS", "control": "remember that preserved/popular proverbs are not a representative sample of human experience"},
    {"id": "PROVERB_AS_EMPIRICAL_EVIDENCE", "control": "keep proverbial guidance separate from empirical observation and scientific evidence"},
)


def _finding(confound_id: str, trigger: str) -> dict[str, str]:
    row = next(r for r in PROVERB_CONFOUND_REGISTRY if r["id"] == confound_id)
    return {"id": confound_id, "trigger": trigger, "control": row["control"]}


def _default_tools(source_kind: str) -> tuple[ProverbTool, ...]:
    return (
        ProverbTool(
            "source-card",
            "retain source/status/context",
            f"fixture provenance:{source_kind}",
            "source-lineage",
        ),
        ProverbTool(
            "semantic-audit",
            "compare interpretations without declaring one universal meaning",
            "GSFL v0.1 local deterministic audit",
            "semantic-audit",
        ),
    )


def _default_trace(source_text: str) -> tuple[ProverbCooperationStep, ...]:
    return (
        ProverbCooperationStep("HUMAN", "frame", f"human partner supplies or reviews the proverb surface: {source_text}", ("source-card",)),
        ProverbCooperationStep("MACHINE", "propose", "machine partner proposes a provisional paraphrase and alternative reading", ("semantic-audit",)),
        ProverbCooperationStep("HUMAN", "review", "human partner may accept, reject, revise, or preserve disagreement", ("source-card", "semantic-audit")),
    )


def traditional_fixture(fixture_id: str, source_text: str, context: str) -> ProverbFixture:
    provenance = ProverbProvenance(
        "traditional_or_common_unverified_origin",
        "fixture records common/traditional status only; exact author/date/origin not established here",
        "source-lineage",
    )
    return ProverbFixture(
        fixture_id=fixture_id,
        source_text=source_text,
        source_status="TRADITIONAL_OR_COMMON",
        context=context,
        provenance=provenance,
        human_interpretations=(
            "Human reading: treat the saying as context-dependent practical guidance rather than a literal law.",
        ),
        machine_interpretations=(
            "Machine reading: offer a provisional paraphrase while preserving uncertainty about origin, applicability, and intended scope.",
        ),
        alternate_interpretations=(
            "Literal and figurative readings may diverge.",
            "A different social or cultural context may reverse, narrow, or reject the advice.",
        ),
        invariant_meanings=(
            "source text remains unchanged",
            "context remains attached",
            "no universal truth claim",
            "no exact-origin claim",
        ),
        cooperation_trace=_default_trace(source_text),
        tools=_default_tools(provenance.source_kind),
    )


def synthetic_fixture(fixture_id: str, source_text: str, context: str) -> ProverbFixture:
    provenance = ProverbProvenance(
        "synthetic_generator",
        "generated as a GSFL v0.1 proverb-like cooperation fixture; not a traditional attribution",
        "synthetic-fixture",
    )
    return ProverbFixture(
        fixture_id=fixture_id,
        source_text=source_text,
        source_status="SYNTHETIC",
        context=context,
        provenance=provenance,
        human_interpretations=(
            "Human reading: use the invented saying to discuss cooperation, limits, and context without treating it as inherited wisdom.",
        ),
        machine_interpretations=(
            "Machine reading: paraphrase the invented saying as a cooperation pattern while keeping its synthetic provenance explicit.",
        ),
        alternate_interpretations=(
            "The metaphor can support more than one reading.",
            "A human partner can disagree with the machine paraphrase without invalidating the fixture.",
        ),
        invariant_meanings=(
            "synthetic provenance remains attached",
            "human and machine readings remain distinct",
            "no universal truth claim",
        ),
        cooperation_trace=_default_trace(source_text),
        tools=_default_tools(provenance.source_kind),
    )


def replace_source_status(fixture: ProverbFixture, source_status: str) -> ProverbFixture:
    """Return a deliberately altered fixture for counterprobe testing.

    Provenance is not rewritten. This makes status/provenance disagreement visible
    to the confound detector instead of laundering the original source kind.
    """
    return replace(fixture, source_status=source_status)


_SYNTHETIC_TEMPLATES = (
    ("Shared lanterns shorten the dark road.", "shared observation can reduce individual uncertainty"),
    ("A bridge remembered by both banks carries more than feet.", "cooperation should retain both endpoints and their histories"),
    ("Two maps compared reveal the road neither map could name alone.", "different representations can expose complementary distinctions"),
    ("A thread kept labeled can leave the loom and still find its pattern.", "provenance supports reconstruction across transport"),
    ("The tool that shows the mark does not own the meaning of the mark.", "tool use should remain separate from semantic authority"),
    ("A question shared before an answer travels farther than a verdict alone.", "joint framing can improve cooperative understanding"),
    ("When one partner remembers the source and another tests the path, the return journey is easier.", "partner specialization can support recoverability"),
    ("Many windows can face one field without moving the field.", "multiple observations need not modify the observed state"),
    ("A repaired sentence should still know the words it came from.", "semantic repair should preserve lineage"),
    ("The clearest machine answer still needs a human place to land.", "human usefulness and machine output are distinct"),
)


def generate_synthetic_fixtures(seed: int, count: int) -> tuple[ProverbFixture, ...]:
    if count < 0:
        raise ValueError("count must be nonnegative")
    rng = random.Random(seed)
    order = list(range(len(_SYNTHETIC_TEMPLATES)))
    rng.shuffle(order)
    fixtures: list[ProverbFixture] = []
    for i in range(count):
        template_index = order[i % len(order)]
        if i and i % len(order) == 0:
            rng.shuffle(order)
            template_index = order[i % len(order)]
        text, theme = _SYNTHETIC_TEMPLATES[template_index]
        cycle = i // len(_SYNTHETIC_TEMPLATES)
        rendered = text if cycle == 0 else text[:-1] + f" ({cycle + 1})."
        fixture = synthetic_fixture(
            fixture_id=f"synthetic-{seed}-{i:03d}",
            source_text=rendered,
            context=f"synthetic proverb-like fixture; theme={theme}; seed={seed}; index={i}",
        )
        fixtures.append(fixture)
    return tuple(fixtures)


def detect_proverb_confounds(fixture: ProverbFixture) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    findings.append(_finding("FALSE_UNIVERSALITY", "proverbial wording can sound broader than its context warrants"))
    findings.append(_finding("LITERAL_FIGURATIVE_COLLAPSE", "fixture contains compact metaphorical/proverbial wording"))
    findings.append(_finding("PRESERVATION_AS_ENDORSEMENT", "fixture is preserved for analysis"))
    findings.append(_finding("PROVERB_AS_EMPIRICAL_EVIDENCE", "proverb is present as a reasoning surface, not empirical evidence"))
    findings.append(_finding("LEXICAL_SIMILARITY_AS_CROSS_CULTURAL_EQUIVALENCE", "surface similarity could be overread during comparisons"))

    if fixture.machine_interpretations and fixture.human_understanding_evidence == "NONE":
        findings.append(_finding("MACHINE_PARAPHRASE_AS_HUMAN_UNDERSTANDING", "machine interpretation exists without human comprehension evidence"))
    if fixture.source_status == "TRADITIONAL_OR_COMMON":
        findings.append(_finding("ATTRIBUTION_UNCERTAINTY", "fixture records traditional/common status without exact-origin proof"))
        findings.append(_finding("POPULARITY_AS_TRUTH", "common/traditional status may be mistaken for truth"))
        findings.append(_finding("FAMILIARITY_BIAS", "a common saying may receive extra trust from familiarity"))
        findings.append(_finding("SURVIVORSHIP_OF_SAYINGS", "surviving sayings are not a representative sample of human experience"))
        findings.append(_finding("CULTURAL_FLATTENING", "common-language fixture may hide local/contextual variation"))
    if fixture.source_status == "TRANSLATED_SOURCE" or "translat" in fixture.context.lower():
        findings.append(_finding("TRANSLATION_LOSS", "fixture is explicitly translated or translation-scoped"))
    synthetic_kind = fixture.provenance.source_kind.startswith("synthetic")
    if synthetic_kind and fixture.source_status != "SYNTHETIC":
        findings.append(_finding("SYNTHETIC_PROVENANCE_LAUNDERING", "synthetic provenance conflicts with non-synthetic source status"))
    return sorted(findings, key=lambda row: row["id"])


def _semantic_rotation_checks(fixture: ProverbFixture) -> list[dict[str, Any]]:
    source = gsfl.SemanticObject(
        object_id=f"proverb:{fixture.fixture_id}",
        meaning={
            "source_text": fixture.source_text,
            "source_status": fixture.source_status,
            "context": fixture.context,
            "provenance_kind": fixture.provenance.source_kind,
        },
        invariants=("source_text", "source_status", "provenance_kind"),
    )
    surfaces = (
        ("human", fixture.human_interpretations[0]),
        ("machine", fixture.machine_interpretations[0]),
        ("alternate", fixture.alternate_interpretations[0] if fixture.alternate_interpretations else fixture.machine_interpretations[0]),
    )
    results = []
    for candidate_id, surface in surfaces:
        candidate = gsfl.Candidate(
            candidate_id=candidate_id,
            meaning=dict(source.meaning),
            surface=surface,
            metrics=gsfl.Metrics(0.8, 0.8, 0.9, 0.3, 0.2, 0.0),
            reconstructed_meaning=dict(source.meaning),
        )
        results.append(asdict(gsfl.evaluate_candidate(source, candidate)))
    return results


def audit_fixture(fixture: ProverbFixture) -> dict[str, Any]:
    interpretations = (
        tuple(fixture.human_interpretations)
        + tuple(fixture.machine_interpretations)
        + tuple(fixture.alternate_interpretations)
    )
    return {
        "fixture_id": fixture.fixture_id,
        "source_text": fixture.source_text,
        "source_status": fixture.source_status,
        "context": fixture.context,
        "provenance": asdict(fixture.provenance),
        "human_understanding_evidence": fixture.human_understanding_evidence,
        "interpretation_count": len(interpretations),
        "human_interpretation_count": len(fixture.human_interpretations),
        "machine_interpretation_count": len(fixture.machine_interpretations),
        "alternate_interpretation_count": len(fixture.alternate_interpretations),
        "claims_single_true_meaning": fixture.claims_single_true_meaning,
        "semantic_rotation_checks": _semantic_rotation_checks(fixture),
        "corollaries": list(PROVERB_COROLLARIES),
        "confounds": detect_proverb_confounds(fixture),
        "boundaries": [
            "PROVERB != EMPIRICAL_EVIDENCE",
            "MACHINE_PARAPHRASE != HUMAN_UNDERSTANDING",
            "POPULARITY != TRUTH",
            "PRESERVATION != ENDORSEMENT",
            "LEXICAL_SIMILARITY != CROSS_CULTURAL_EQUIVALENCE",
            "SYNTHETIC != TRADITIONAL",
        ],
    }


def audit_corpus(fixtures: Iterable[ProverbFixture]) -> dict[str, Any]:
    fixtures = tuple(fixtures)
    ids = [f.fixture_id for f in fixtures]
    if len(ids) != len(set(ids)):
        raise ValueError("fixture IDs must be unique")
    audits = [audit_fixture(f) for f in fixtures]
    confound_ids = sorted({c["id"] for audit in audits for c in audit["confounds"]})
    source_counts: dict[str, int] = {}
    for fixture in fixtures:
        source_counts[fixture.source_status] = source_counts.get(fixture.source_status, 0) + 1
    return {
        "fixture_count": len(fixtures),
        "source_status_counts": dict(sorted(source_counts.items())),
        "observations": [
            "every fixture preserves source status and provenance as separate fields",
            "every fixture preserves human and machine interpretations separately",
            "synthetic and traditional/common fixtures remain distinguishable",
        ],
        "corollaries": list(PROVERB_COROLLARIES),
        "confounds": [row for row in PROVERB_CONFOUND_REGISTRY if row["id"] in confound_ids],
        "confound_count": len(confound_ids),
        "universal_meaning_claim": any(f.claims_single_true_meaning for f in fixtures),
        "fixture_audits": audits,
        "claim_ceiling": [
            "generated proverb fixtures are bounded semantic/cooperation test surfaces",
            "traditional/common labels do not establish exact origin",
            "synthetic fixtures do not acquire cultural provenance",
            "interpretation preservation does not prove interpretation truth",
            "machine paraphrase does not establish human understanding",
        ],
    }

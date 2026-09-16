"""GSFL v0.1 human-machine cooperation profile.

This module is additive. It delegates semantic classification and fitting to the
GSFL v0 kernel while making human understanding, machine-learning claim
boundaries, partner contributions, and tool provenance first-class records.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import shlex
from typing import Any

import gsfl

PARTNER_KINDS = {"HUMAN", "MACHINE"}
LEARNING_STATES = {
    "NO_LEARNING_CLAIM",
    "IN_CONTEXT_ADAPTATION",
    "OBSERVED_BEHAVIOR_CHANGE",
    "EXTERNAL_TRAINING_EVIDENCE",
}
UNDERSTANDING_EVIDENCE_KINDS = {
    "NONE",
    "APPROVAL_ONLY",
    "TEACH_BACK",
    "TASK_COMPLETION",
    "PARTICIPANT_REPORT",
}

VOCABULARY_FAMILIES: dict[str, str] = {
    "HUMAN": "HUMAN", "HUMAN_PARTNER": "HUMAN", "HUMAN_INTENT": "HUMAN",
    "HUMAN_REVIEW": "HUMAN", "HUMAN_CHOICE": "HUMAN",
    "UNDERSTAND": "UNDERSTANDING", "UNDERSTANDING": "UNDERSTANDING",
    "UNDERSTANDING_GOAL": "UNDERSTANDING", "UNDERSTANDING_EVIDENCE": "UNDERSTANDING",
    "EXPLAIN": "UNDERSTANDING", "TEACH": "UNDERSTANDING", "TEACH_BACK": "UNDERSTANDING",
    "COMPREHEND": "UNDERSTANDING",
    "MACHINE": "MACHINE_LEARNING", "MACHINE_PARTNER": "MACHINE_LEARNING",
    "MACHINE_LEARNING": "MACHINE_LEARNING", "LEARN": "MACHINE_LEARNING",
    "LEARNING": "MACHINE_LEARNING", "LEARNING_CLAIM": "MACHINE_LEARNING",
    "MODEL": "MACHINE_LEARNING", "MODEL_OUTPUT": "MACHINE_LEARNING",
    "ADAPT": "MACHINE_LEARNING", "ADAPTATION": "MACHINE_LEARNING",
    "COOPERATE": "COOPERATION", "COOPERATION": "COOPERATION",
    "CONTRIBUTE": "COOPERATION", "CONTRIBUTION": "COOPERATION",
    "SHARE": "COOPERATION", "HANDOFF": "COOPERATION", "ASK": "COOPERATION",
    "ANSWER": "COOPERATION", "PROPOSE": "COOPERATION", "REVIEW_TOGETHER": "COOPERATION",
    "VERIFY_TOGETHER": "COOPERATION", "REPAIR_TOGETHER": "COOPERATION",
    "PARTNER": "PARTNER", "PARTNERS": "PARTNER", "ROLE": "PARTNER", "ACTOR": "PARTNER",
    "TOOL": "TOOL", "TOOLS": "TOOL", "TOOL_USE": "TOOL", "TOOL_PURPOSE": "TOOL",
    "TOOL_PROVENANCE": "TOOL", "TRACE_TOOL": "TOOL", "VERIFY_TOOL": "TOOL",
    "OBJECT": "SEMANTIC_CORE", "MEANING": "SEMANTIC_CORE", "PRESERVE": "SEMANTIC_CORE",
    "ROTATE": "SEMANTIC_CORE", "SURFACE": "SEMANTIC_CORE", "SET": "SEMANTIC_CORE",
    "DROP": "SEMANTIC_CORE", "METRIC": "SEMANTIC_CORE", "RECONSTRUCT": "SEMANTIC_CORE",
    "FIT": "SEMANTIC_CORE", "END": "SEMANTIC_CORE",
}
RESERVED_VOCABULARY = tuple(VOCABULARY_FAMILIES)
COOPERATION_FAMILIES = {"HUMAN", "MACHINE_LEARNING", "UNDERSTANDING", "COOPERATION", "PARTNER", "TOOL"}

COROLLARIES = (
    {"id": "ATTRIBUTION_RECONSTRUCTIBLE", "statement": "Preserved partner IDs and cooperation steps make bounded contribution attribution reconstructible.", "boundary": "trace reconstruction is not moral or causal responsibility proof"},
    {"id": "TOOL_PROVENANCE_SEPARABLE", "statement": "Tool use can be audited separately from semantic or truth authority.", "boundary": "tool provenance does not certify tool output"},
    {"id": "ADMISSION_PRECEDES_OPTIMIZATION", "statement": "Higher human-use fit cannot admit a v0 mutation or invariant failure.", "boundary": "fit remains task-relative"},
    {"id": "USEFUL_MACHINE_CONTRIBUTION_WITHOUT_LEARNING_CLAIM", "statement": "Machine contribution can be useful without asserting training or weight change.", "boundary": "usefulness is not machine-learning evidence"},
    {"id": "UNDERSTANDING_REMAINS_SEPARATE", "statement": "Machine reconstruction and human-facing fit can coexist with no human-understanding evidence.", "boundary": "machine reconstruction is not human comprehension"},
    {"id": "PARTNER_DISTINCTIONS_SURVIVE_COMPOSITION", "statement": "Cooperation can compose contributions while retaining human and machine identities and roles.", "boundary": "composition does not imply equivalent agency"},
    {"id": "LINEAGE_FIELDS_REMAIN_REVERSIBLE", "statement": "Source meaning, selected surface, partner/tool trace, and claim boundaries remain separately reconstructible fields.", "boundary": "field recovery does not prove semantic universality"},
)

CONFOUND_REGISTRY = (
    {"id": "APPROVAL_AS_UNDERSTANDING", "control": "require separate understanding evidence such as teach-back or task completion"},
    {"id": "APPROVAL_AS_TRUTH", "control": "keep human approval distinct from factual or semantic truth"},
    {"id": "OUTPUT_AS_LEARNING_EVIDENCE", "control": "do not infer learning from output differences alone"},
    {"id": "IN_CONTEXT_AS_WEIGHT_UPDATE", "control": "label in-context adaptation separately from persistent parameter updates"},
    {"id": "TOOL_RESULT_AS_AUTHORITY", "control": "retain source/provenance and independent verification requirements"},
    {"id": "CORRELATED_TOOLS_AS_INDEPENDENT_VERIFICATION", "control": "track evidence groups and do not count shared-source tools as independent"},
    {"id": "LEXICAL_MAJORITY_AS_COMPREHENSION", "control": "treat vocabulary ratio as lexical emphasis only"},
    {"id": "FIT_SCORE_AS_TRUTH", "control": "semantic admission and external evidence remain prior to fit selection"},
    {"id": "PARTNER_ROLE_COLLAPSE", "control": "require distinct human and machine partner identities"},
    {"id": "PROVENANCE_LAUNDERING", "control": "require nonempty tool provenance and preserve original source identity"},
    {"id": "AUTOMATION_BIAS", "control": "preserve human review and disagreement as independent actions"},
    {"id": "SYNTHETIC_FIXTURE_GENERALIZATION", "control": "keep conclusions bounded to the declared fixture"},
    {"id": "SELECTION_BIAS_IN_HUMAN_VALIDATION", "control": "record participant population and sampling before generalizing"},
    {"id": "VERBOSITY_AS_CLARITY", "control": "measure task comprehension separately from surface length"},
)

@dataclass(frozen=True)
class Partner:
    partner_id: str
    kind: str
    role: str
    def __post_init__(self) -> None:
        if self.kind not in PARTNER_KINDS:
            raise ValueError(f"partner kind must be HUMAN or MACHINE, got {self.kind!r}")
        if not self.partner_id or not self.role:
            raise ValueError("partner id and role are required")

@dataclass(frozen=True)
class ToolUse:
    tool_id: str
    purpose: str
    provenance: str
    evidence_group: str
    def __post_init__(self) -> None:
        if not all((self.tool_id, self.purpose, self.provenance, self.evidence_group)):
            raise ValueError("tool id, purpose, provenance, and evidence_group are required")

@dataclass(frozen=True)
class CooperationStep:
    actor_partner_id: str
    action: str
    detail: str
    tools: tuple[str, ...]

@dataclass(frozen=True)
class UnderstandingEvidence:
    kind: str
    detail: str
    def __post_init__(self) -> None:
        if self.kind not in UNDERSTANDING_EVIDENCE_KINDS:
            raise ValueError(f"unknown understanding evidence kind {self.kind!r}")

@dataclass(frozen=True)
class LearningClaim:
    state: str
    evidence: str
    def __post_init__(self) -> None:
        if self.state not in LEARNING_STATES:
            raise ValueError(f"unknown machine learning state {self.state!r}")
        if self.state != "NO_LEARNING_CLAIM" and not self.evidence.strip():
            raise ValueError(f"machine learning state {self.state} requires explicit evidence")

@dataclass(frozen=True)
class CooperationContext:
    human_partner: Partner
    machine_partner: Partner
    tools: tuple[ToolUse, ...]
    steps: tuple[CooperationStep, ...]
    understanding_goal: str
    understanding_evidence: UnderstandingEvidence
    learning_claim: LearningClaim
    def __post_init__(self) -> None:
        if self.human_partner.kind != "HUMAN" or self.machine_partner.kind != "MACHINE":
            raise ValueError("cooperation context requires HUMAN and MACHINE partners")
        if self.human_partner.partner_id == self.machine_partner.partner_id:
            raise ValueError("human and machine partner IDs must be distinct")
        if not self.understanding_goal.strip():
            raise ValueError("understanding goal is required")
        tool_ids = [t.tool_id for t in self.tools]
        if len(tool_ids) != len(set(tool_ids)):
            raise ValueError("tool IDs must be unique")
        partners = {self.human_partner.partner_id, self.machine_partner.partner_id}
        known_tools = set(tool_ids)
        for step in self.steps:
            if step.actor_partner_id not in partners:
                raise ValueError(f"unknown partner actor {step.actor_partner_id!r}")
            unknown = set(step.tools) - known_tools
            if unknown:
                raise ValueError(f"unknown tool reference: {sorted(unknown)[0]}")

def vocabulary_audit() -> dict[str, Any]:
    cooperation = [t for t, family in VOCABULARY_FAMILIES.items() if family in COOPERATION_FAMILIES]
    semantic = [t for t, family in VOCABULARY_FAMILIES.items() if family == "SEMANTIC_CORE"]
    ratio = len(cooperation) / len(RESERVED_VOCABULARY)
    family_counts = {family: sum(1 for f in VOCABULARY_FAMILIES.values() if f == family) for family in sorted(set(VOCABULARY_FAMILIES.values()))}
    return {
        "reserved_terms": len(RESERVED_VOCABULARY),
        "cooperation_terms": len(cooperation),
        "semantic_core_terms": len(semantic),
        "ratio": round(ratio, 12),
        "passes": ratio > 0.5,
        "family_counts": family_counts,
        "cooperation_families": sorted(COOPERATION_FAMILIES),
    }

def _parse_value(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text

def _assignment(text: str) -> tuple[str, Any]:
    if "=" not in text:
        raise ValueError(f"expected key=value, got {text!r}")
    key, value = text.split("=", 1)
    if not key.strip():
        raise ValueError("empty key")
    return key.strip(), _parse_value(value)

def _tokens(rest: str) -> list[str]:
    return shlex.split(rest)

def _kv(tokens: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for token in tokens:
        key, value = _assignment(token)
        if key in result:
            raise ValueError(f"duplicate field {key!r}")
        result[key] = value
    return result

def parse_cooperation(program: str) -> tuple[gsfl.SemanticObject, list[gsfl.Candidate], CooperationContext]:
    lines = [raw.strip() for raw in program.splitlines() if raw.strip() and not raw.strip().startswith("#")]
    if not lines or lines[0] != "GSFL 0.1":
        raise ValueError("cooperation program must start with 'GSFL 0.1'")
    object_id: str | None = None
    meaning: dict[str, Any] = {}
    invariants: list[str] = []
    human: Partner | None = None
    machine: Partner | None = None
    tools: list[ToolUse] = []
    steps: list[CooperationStep] = []
    understanding_goal = ""
    understanding_evidence = UnderstandingEvidence("NONE", "")
    learning_claim = LearningClaim("NO_LEARNING_CLAIM", "")
    candidates: list[gsfl.Candidate] = []
    candidate_ids: set[str] = set()
    current: dict[str, Any] | None = None
    saw_fit = False
    after_fit = False
    for line in lines[1:]:
        if after_fit:
            raise ValueError("FIT must be terminal")
        op, _, rest = line.partition(" ")
        op = op.upper(); rest = rest.strip()
        if current is None:
            if op == "OBJECT":
                if object_id is not None: raise ValueError("OBJECT may appear only once")
                object_id = rest
            elif op == "MEANING":
                key, value = _assignment(rest)
                if key in meaning: raise ValueError(f"duplicate MEANING key {key!r}")
                meaning[key] = value
            elif op == "PRESERVE":
                invariants.append(rest)
            elif op in {"HUMAN", "MACHINE"}:
                toks = _tokens(rest)
                if not toks: raise ValueError(f"{op} requires partner id")
                fields = _kv(toks[1:]); partner = Partner(toks[0], op, str(fields.get("role", "")))
                if op == "HUMAN":
                    if human is not None: raise ValueError("HUMAN may appear only once")
                    human = partner
                else:
                    if machine is not None: raise ValueError("MACHINE may appear only once")
                    machine = partner
            elif op == "TOOL":
                toks = _tokens(rest)
                if not toks: raise ValueError("TOOL requires tool id")
                fields = _kv(toks[1:])
                tools.append(ToolUse(toks[0], str(fields.get("purpose", "")), str(fields.get("provenance", "")), str(fields.get("evidence_group", ""))))
            elif op == "UNDERSTANDING_GOAL":
                understanding_goal = str(_parse_value(rest))
            elif op == "UNDERSTANDING_EVIDENCE":
                toks = _tokens(rest)
                if not toks: raise ValueError("UNDERSTANDING_EVIDENCE requires kind")
                fields = _kv(toks[1:]); understanding_evidence = UnderstandingEvidence(toks[0], str(fields.get("detail", "")))
            elif op == "MACHINE_LEARNING":
                toks = _tokens(rest)
                if not toks: raise ValueError("MACHINE_LEARNING requires state")
                fields = _kv(toks[1:]); learning_claim = LearningClaim(toks[0], str(fields.get("evidence", "")))
            elif op == "COOPERATE":
                toks = _tokens(rest)
                if not toks: raise ValueError("COOPERATE requires partner id")
                fields = _kv(toks[1:]); raw_tools = str(fields.get("tools", "none"))
                step_tools = () if raw_tools.lower() == "none" else tuple(t for t in raw_tools.split(",") if t)
                steps.append(CooperationStep(toks[0], str(fields.get("action", "")), str(fields.get("detail", "")), step_tools))
            elif op == "ROTATE":
                if rest in candidate_ids: raise ValueError(f"duplicate candidate id {rest!r}")
                candidate_ids.add(rest); current = {"candidate_id": rest, "meaning": dict(meaning), "surface": "", "metrics": {}, "reconstructed_meaning": {}}
            elif op == "FIT":
                saw_fit = True; after_fit = True
            else:
                raise ValueError(f"unknown top-level operation {op!r}")
        else:
            if op == "SURFACE":
                value = _parse_value(rest)
                if not isinstance(value, str): raise ValueError("SURFACE must decode to a string")
                current["surface"] = value
            elif op == "SET":
                key, value = _assignment(rest); current["meaning"][key] = value
            elif op == "DROP":
                current["meaning"].pop(rest, None)
            elif op == "METRIC":
                current["metrics"].update({k: float(v) for k, v in _kv(_tokens(rest)).items()})
            elif op == "RECONSTRUCT":
                key, value = _assignment(rest); current["reconstructed_meaning"][key] = value
            elif op == "END":
                required=("clarity","usefulness","recoverability","cognitive_effort","ambiguity","semantic_loss")
                missing=[n for n in required if n not in current["metrics"]]
                if missing: raise ValueError(f"candidate {current['candidate_id']!r} missing metrics: {', '.join(missing)}")
                candidates.append(gsfl.Candidate(current["candidate_id"],dict(current["meaning"]),current["surface"],gsfl.Metrics(**current["metrics"]),dict(current["reconstructed_meaning"])))
                current = None
            else:
                raise ValueError(f"unknown candidate operation {op!r}")
    if current is not None: raise ValueError("unterminated ROTATE block")
    if not object_id: raise ValueError("OBJECT is required")
    if not saw_fit: raise ValueError("FIT is required")
    if human is None or machine is None: raise ValueError("HUMAN and MACHINE partners are required")
    for key in invariants:
        if key not in meaning: raise ValueError(f"PRESERVE refers to absent meaning key {key!r}")
    source = gsfl.SemanticObject(object_id, meaning, tuple(dict.fromkeys(invariants)))
    context = CooperationContext(human,machine,tuple(tools),tuple(steps),understanding_goal,understanding_evidence,learning_claim)
    return source,candidates,context

def _finding(confound_id: str, trigger: str) -> dict[str, str]:
    row = next(r for r in CONFOUND_REGISTRY if r["id"] == confound_id)
    return {"id": confound_id, "trigger": trigger, "control": row["control"]}

def detect_confounds(context: CooperationContext, semantic_result: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if context.understanding_evidence.kind == "APPROVAL_ONLY":
        findings.append(_finding("APPROVAL_AS_UNDERSTANDING", "understanding evidence is approval-only"))
        findings.append(_finding("APPROVAL_AS_TRUTH", "approval is present without independent truth evidence"))
    if context.learning_claim.state == "IN_CONTEXT_ADAPTATION":
        findings.append(_finding("IN_CONTEXT_AS_WEIGHT_UPDATE", "learning state is in-context adaptation"))
    elif context.learning_claim.state == "OBSERVED_BEHAVIOR_CHANGE":
        findings.append(_finding("OUTPUT_AS_LEARNING_EVIDENCE", "behavior change is observed without training proof"))
    groups: dict[str, list[str]] = {}
    for tool in context.tools:
        groups.setdefault(tool.evidence_group, []).append(tool.tool_id)
    correlated = [ids for ids in groups.values() if len(ids) > 1]
    if correlated:
        findings.append(_finding("CORRELATED_TOOLS_AS_INDEPENDENT_VERIFICATION", f"shared evidence group: {','.join(correlated[0])}"))
    if context.tools:
        findings.append(_finding("TOOL_RESULT_AS_AUTHORITY", "tools participate in the cooperation trace"))
    findings.append(_finding("LEXICAL_MAJORITY_AS_COMPREHENSION", "vocabulary-majority audit is lexical only"))
    findings.append(_finding("FIT_SCORE_AS_TRUTH", "semantic candidates are ranked by a fit score after admission"))
    if "observer" in str(semantic_result.get("object_id", "")).lower():
        findings.append(_finding("SYNTHETIC_FIXTURE_GENERALIZATION", "the bounded example is an observer fixture"))
    return sorted(findings, key=lambda x: x["id"])

def execute_cooperation(program: str) -> dict[str, Any]:
    source,candidates,context=parse_cooperation(program)
    selected,evaluations=gsfl.fit(source,candidates)
    semantic_result={
        "gsfl_version": "0.1", "object_id": source.object_id, "source_meaning": source.meaning,
        "invariants": list(source.invariants), "selected_candidate": selected.candidate_id,
        "selected_surface": selected.surface, "evaluations": [asdict(e) for e in evaluations],
    }
    cooperation={
        "human_partner": asdict(context.human_partner), "machine_partner": asdict(context.machine_partner),
        "tools": [asdict(t) for t in context.tools], "steps": [asdict(s) for s in context.steps],
        "understanding_goal": context.understanding_goal, "understanding_evidence": asdict(context.understanding_evidence),
        "machine_learning_claim": asdict(context.learning_claim),
    }
    return {**semantic_result, "cooperation": cooperation, "vocabulary_audit": vocabulary_audit(),
            "corollaries": list(COROLLARIES), "confound_registry": list(CONFOUND_REGISTRY),
            "confound_findings": detect_confounds(context, semantic_result)}

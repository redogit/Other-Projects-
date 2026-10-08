from __future__ import annotations

import json
import re
from typing import Any

from fkdb_tool_carrier import validate_tool_carrier


TOKEN=re.compile(r"[A-Za-z0-9]+")
MAX_PAYLOAD_BYTES=1_048_576


def _tokens(value: Any) -> list[str]:
    text=json.dumps(value,ensure_ascii=False) if not isinstance(value,str) else value
    return [x.upper() for x in TOKEN.findall(text)]


def admit_tool_carriers(values: list[dict[str,Any]]) -> dict[str,Any]:
    if not isinstance(values,list):
        raise ValueError("tool carriers must be a list")
    seen=set(); records=[]
    for value in values:
        validated=validate_tool_carrier(value,max_payload_bytes=MAX_PAYLOAD_BYTES)
        cid=validated["carrier_id"]
        if cid in seen: raise ValueError(f"duplicate carrier_id: {cid}")
        seen.add(cid)
        provenance=validated["provenance"]
        records.append({
            "source_carrier_id":cid,
            "tool_id":validated["tool_id"],
            "source_identity":validated["source_identity"],
            "source_version":validated["source_version"],
            "authority_scope":validated["authority_scope"],
            "evidence_status":validated["evidence_status"],
            "recovery_path":validated["recovery_path"],
            "relations":list(validated["relations"]),
            "payload_type":validated["payload_type"],
            "payload":validated["payload"],
            "provenance":dict(provenance),
            "evidence_promoted":False,
        })

    contradictions=[]
    by_subject={}
    for rec in records:
        subject=rec["provenance"].get("subject_key")
        claim=rec["provenance"].get("claim_value")
        if not isinstance(subject,str) or not subject or claim is None: continue
        prior=by_subject.setdefault(subject,[])
        for other in prior:
            if other["claim"] != claim:
                contradictions.append({
                    "subject_key":subject,
                    "carrier_ids":[other["carrier_id"],rec["source_carrier_id"]],
                    "claim_values":[other["claim"],claim],
                    "status":"UNRESOLVED_CONTRADICTION",
                })
        prior.append({"carrier_id":rec["source_carrier_id"],"claim":claim})

    remainder=[]
    if contradictions: remainder.append("CONTRADICTION_REQUIRES_INSPECTION")
    return {
        "schema":"fkdb/cross-carrier-admission/v1",
        "status":"ADMITTED_WITH_CONTRADICTIONS" if contradictions else "ADMITTED",
        "records":records,
        "contradictions":contradictions,
        "remainder":remainder,
        "invariants":[
            "TOOLCARRIER_ADMISSION != EVIDENCE_PROMOTION",
            "CONTRADICTION != AUTOMATIC_RESOLUTION",
            "EXTERNAL_RECORD != CANONICAL_STATIC_RECORD",
        ],
    }


def build_external_index_records(records: list[dict[str,Any]], *, max_terms: int=32) -> list[dict[str,Any]]:
    if type(max_terms) is not int or max_terms<1: raise ValueError("max_terms must be positive")
    output=[]
    for rec in records:
        payload=rec["payload"]
        try: parsed=json.loads(payload) if rec["payload_type"]=="application/json" else payload
        except json.JSONDecodeError: parsed=payload
        terms=[]
        for value in (rec["tool_id"],rec["source_identity"],parsed):
            for token in _tokens(value):
                if token not in terms:
                    terms.append(token)
                    if len(terms)>=max_terms: break
            if len(terms)>=max_terms: break
        cid=rec["source_carrier_id"]
        output.append({
            "id":"EXT-"+cid,
            "title":rec["source_identity"],
            "kind":"EXTERNAL_TOOL_CARRIER",
            "state":"IMPORTED",
            "domain":"CROSS_CARRIER",
            "carrier":"TOOL_CARRIER",
            "source_refs":[rec["source_identity"]],
            "provenance":{
                "relation":"IMPORTED_FROM_TOOL_CARRIER",
                "target":cid,
                "status":"SOURCE_PRESERVED",
                "tool_id":rec["tool_id"],
                "authority_scope":rec["authority_scope"],
            },
            "evidence_status":rec["evidence_status"],
            "recovery_path":rec["recovery_path"],
            "recovery_display":"INSPECT IMPORTED SOURCE",
            "relations":[],
            "terms":terms,
        })
    return output

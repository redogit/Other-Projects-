from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
LAB = HERE.parent
INDEX_PATH = LAB / "fkdb" / "index" / "records.json"
TOKEN = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [part.upper() for part in TOKEN.findall(text)]


def record_tokens(record: dict) -> set[str]:
    tokens = set(tokenize(record.get("id", "")))
    tokens.update(tokenize(record.get("title", "")))
    tokens.update(tokenize(record.get("kind", "")))
    tokens.update(tokenize(record.get("domain", "")))
    tokens.update(tokenize(record.get("carrier", "")))
    for term in record.get("terms", []):
        tokens.update(tokenize(term))
    return tokens


def load_index(path: Path = INDEX_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "fkdb/source-index/v1":
        raise ValueError("unsupported FKDB source-index schema")
    if data.get("project") != "FKDB":
        raise ValueError("source index project identity is not FKDB")
    records = data.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("FKDB source index requires records")

    ids = set()
    for record in records:
        rid = record.get("id")
        if not isinstance(rid, str) or not rid:
            raise ValueError("FKDB source record requires id")
        if rid in ids:
            raise ValueError(f"duplicate FKDB source record id: {rid}")
        ids.add(rid)
        for field in ("title", "kind", "state", "domain", "carrier", "evidence_status", "recovery_path"):
            if not record.get(field):
                raise ValueError(f"FKDB source record {rid} requires {field}")
        if not record.get("source_refs"):
            raise ValueError(f"FKDB source record {rid} requires source_refs")
        provenance = record.get("provenance")
        if not isinstance(provenance, dict) or not provenance.get("relation") or not provenance.get("status"):
            raise ValueError(f"FKDB source record {rid} requires provenance")
    for record in records:
        for target in record.get("relations", []):
            if target not in ids:
                raise ValueError(f"FKDB source record {record['id']} relates to unknown id {target}")
    return data


def search_index(query: str, data: dict | None = None) -> dict:
    if data is None:
        data = load_index()
    raw_query = query
    tokens = tokenize(raw_query)
    stripped = "".join(TOKEN.findall(raw_query))
    source_alnum = "".join(ch for ch in raw_query if ch.isascii() and ch.isalnum())
    dropped = bool(raw_query) and stripped.upper() != source_alnum.upper()

    records = data["records"]
    cost = len(records) * max(1, len(tokens))
    remainder = []

    if raw_query == "":
        status = "NO_MATCH"
        matches = []
        remainder.append("EMPTY_QUERY")
    elif not tokens:
        status = "UNRESOLVED"
        matches = []
        remainder.append("NO_SUPPORTED_QUERY_TOKENS")
    else:
        query_set = set(tokens)
        matches = [record for record in records if query_set.issubset(record_tokens(record))]
        matches.sort(key=lambda record: record["id"])
        status = "MATCH" if matches else "NO_MATCH"
        if not matches:
            remainder.append("NO_LOCAL_BOUNDED_MATCH")
        elif len(matches) > 1:
            remainder.append("MULTIPLE_CANDIDATES_REMAIN")

    if dropped:
        remainder.append("NORMALIZATION_DROPPED_CHARACTERS")

    candidates = []
    for record in matches:
        candidates.append(
            {
                "id": record["id"],
                "title": record["title"],
                "kind": record["kind"],
                "state": record["state"],
                "domain": record["domain"],
                "carrier": record["carrier"],
                "source_refs": record["source_refs"],
                "provenance": record["provenance"],
                "evidence_status": record["evidence_status"],
                "recovery_path": record["recovery_path"],
                "relations": record.get("relations", []),
                "matched_tokens": tokens,
            }
        )

    return {
        "schema": "fkdb/source-query-result/v1",
        "raw_query": raw_query,
        "normalized_tokens": tokens,
        "normalization": data["normalization"],
        "status": status,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "scan_cost": {
            "records_scanned": len(records),
            "query_tokens": len(tokens),
            "comparison_units": cost,
        },
        "remainder": remainder,
        "claim_ceiling": data["claim_ceiling"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the bounded FKDB local source index.")
    parser.add_argument("--query", default="")
    parser.add_argument("--index", type=Path, default=INDEX_PATH)
    args = parser.parse_args()
    result = search_index(args.query, load_index(args.index))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


class PortableProviderAdapter:
    def __init__(self, provider: str, authority_scope: str) -> None:
        if provider not in {"scispace","consensus","exa","linear"}:
            raise ValueError("unsupported portable provider")
        self.tool_id=provider
        self.authority_scope=authority_scope

    def descriptor(self, context) -> dict[str,Any]:
        return {
            "tool_id":self.tool_id,
            "locality":"PORTABLE_IMPORT",
            "state":"AVAILABLE",
            "capabilities":["COLLECT","IMPORT_PORTABLE_PROVIDER"],
            "unresolved_requirements":["LIVE_REMOTE_SYNC_NOT_ENABLED"],
        }

    def collect(self, request_value, context) -> dict[str,Any]:
        if context.resolved_root is None:
            raise ValueError("portable provider collection requires a root")
        options=request_value.get("options",{})
        value=options.get("path")
        if not isinstance(value,str) or not value:
            raise ValueError("portable provider path is required")
        candidate=Path(value)
        if not candidate.is_absolute():
            candidate=context.resolved_root/candidate
        path=context.resolve_read_path(candidate)
        if not path.is_file():
            raise ValueError("portable provider path must reference a file")
        size=path.stat().st_size
        if size>context.max_bytes:
            return {"status":"PARTIAL","carriers":[],"remainder":["PORTABLE_PROVIDER_BYTE_LIMIT_REACHED"],"cost":{"files_scanned":0,"bytes_read":0}}
        raw=path.read_bytes()
        try: data=json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError,json.JSONDecodeError) as exc:
            raise ValueError("portable provider artifact must be UTF-8 JSON") from exc
        if not isinstance(data,dict) or data.get("schema")!="fkdb/portable-provider/v1":
            raise ValueError("unsupported portable provider schema")
        if data.get("provider")!=self.tool_id:
            raise ValueError("portable provider identity mismatch")
        exported_at=data.get("exported_at")
        if not isinstance(exported_at,str) or not exported_at:
            raise ValueError("portable provider exported_at is required")
        records=data.get("records")
        if not isinstance(records,list):
            raise ValueError("portable provider records must be a list")
        max_records=options.get("max_records",context.max_files)
        if type(max_records) is not int or max_records<1:
            raise ValueError("portable provider max_records must be positive")
        max_records=min(max_records,context.max_files)

        carriers=[]; remainder=[]
        for index,record in enumerate(records):
            if len(carriers)>=max_records:
                remainder.append("PORTABLE_PROVIDER_RECORD_LIMIT_REACHED"); break
            if not isinstance(record,dict):
                remainder.append(f"PORTABLE_PROVIDER_MALFORMED_RECORD:{index}"); continue
            record_raw=json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
            digest=hashlib.sha256(record_raw).hexdigest()
            external=record.get("external_id")
            identity=str(external) if external is not None else f"record-{index}"
            carriers.append({
                "schema":"fkdb/tool-carrier/v1",
                "carrier_id":f"{self.tool_id}-"+hashlib.sha256((identity+"\0"+digest).encode()).hexdigest()[:32],
                "tool_id":self.tool_id,
                "tool_version":"portable-provider-v1",
                "adapter_kind":"PORTABLE_IMPORT",
                "locality":"PORTABLE_IMPORT",
                "source_identity":f"{path.name}#{identity}",
                "source_version":digest,
                "retrieved_at":datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z"),
                "payload_type":"application/json",
                "payload":record_raw.decode("utf-8"),
                "content_hash":digest,
                "provenance":{
                    "provider":self.tool_id,
                    "exported_at":exported_at,
                    "external_id":external,
                    "source_file":path.name,
                    "remote_sync_performed":False,
                },
                "authority_scope":self.authority_scope,
                "evidence_status":"PORTABLE_PROVIDER_RECORD_UNVERIFIED",
                "obligation":"IMPORT_PORTABLE_PROVIDER_RECORD",
                "relations":[],
                "cost":{"bytes_read":len(record_raw)},
                "loss":[],
                "remainder":[],
                "recovery_path":f"re-read {path.name} record {identity}; no remote provider was queried",
            })
        return {
            "status":"PARTIAL" if remainder else "COLLECTED",
            "carriers":carriers,
            "remainder":remainder,
            "cost":{"files_scanned":1,"bytes_read":len(raw)},
        }

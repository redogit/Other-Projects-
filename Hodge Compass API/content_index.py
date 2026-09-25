"""Local UTF-8 source-tree to Hodge Compass records.

This indexes source text for retrieval. A source occurrence is not a verified claim.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

TEXT_EXTENSIONS={
    ".md",".txt",".json",".jsonl",".py",".mjs",".js",".ts",".html",".htm",
    ".rmal",".yml",".yaml",".toml",".csv",".tsv",".xml",".tex"
}
DEFAULT_MAX_BYTES=2_000_000
SKIP_DIRS={".git",".hodge-compass","node_modules","__pycache__",".venv","venv"}

def _semantic_id(repo, rel):
    return f"source:{repo}:{rel}"

def records_for_tree(*, root, repo, prefixes=None, domain="hodge",
                     surface="local-repo", root_object_id=None,
                     max_bytes=DEFAULT_MAX_BYTES):
    root=Path(root).resolve()
    if not root.is_dir(): raise ValueError(f"source root is not a directory: {root}")
    prefixes=[p.replace("\\","/").strip("/") for p in (prefixes or []) if p]
    records=[]; skipped={"extension":0,"size":0,"encoding":0,"directory":0}
    scanned=0
    for path in sorted(root.rglob("*")):
        if not path.is_file(): continue
        rel=path.relative_to(root).as_posix()
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            skipped["directory"]+=1; continue
        if prefixes and not any(rel==p or rel.startswith(p+"/") for p in prefixes):
            continue
        scanned+=1
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            skipped["extension"]+=1; continue
        data=path.read_bytes()
        if len(data)>max_bytes:
            skipped["size"]+=1; continue
        try:text=data.decode("utf-8")
        except UnicodeDecodeError:
            skipped["encoding"]+=1; continue
        digest=hashlib.sha256(data).hexdigest()
        relations=[]
        if root_object_id:
            relations.append({
                "target_object_id":root_object_id,
                "type":"PART_OF_RESEARCH_SURFACE",
                "permission":"ALLOW",
                "evidence_transfer":"DENY",
                "provenance":[f"repo:{repo}",f"path:{rel}",f"sha256:{digest}"],
            })
        records.append({
            "semantic_object_id":_semantic_id(repo,rel),
            "kind":"source-file",
            "domain":domain,
            "title":rel,
            "claim_ceiling":"SOURCE_TEXT != VERIFIED_CLAIM",
            "occurrence":{
                "surface":surface,
                "source_ref":f"{repo}:{rel}#sha256={digest}",
                "authority":"source-text-only",
                "status":"CURRENT",
                "text":text,
                "provenance":[f"repo:{repo}",f"path:{rel}",f"sha256:{digest}"],
            },
            "relations":relations,
        })
    return records,{
        "root":str(root),"repo":repo,"prefixes":prefixes,"scanned":scanned,
        "accepted":len(records),"skipped":skipped,"max_bytes":max_bytes,
        "boundary":"SOURCE_TEXT != VERIFIED_CLAIM",
    }

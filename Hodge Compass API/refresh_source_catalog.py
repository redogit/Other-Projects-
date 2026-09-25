#!/usr/bin/env python3
"""Refresh source_catalog.json from exact public GitHub trees."""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from urllib.request import Request, urlopen

API="https://api.github.com/repos"
REPOS=("redogit/conscience64","redogit/Other-Projects-")
SELF_CATALOG="Hodge Compass API/source_catalog.json"

def get_json(url, token=None):
    headers={"Accept":"application/vnd.github+json","User-Agent":"hodge-compass-api"}
    if token: headers["Authorization"]=f"Bearer {token}"
    with urlopen(Request(url,headers=headers),timeout=30) as r:
        return json.load(r)

def select(repo,path):
    if repo=="redogit/conscience64":
        return path.startswith("research/hodge/") or (
            path.startswith(".github/workflows/") and "hodge" in path.lower()
        )
    if path==SELF_CATALOG:
        return False
    return (
        "hodge" in path.lower()
        or path.startswith("Decision Field Operator Lab/")
        or path=="BIDIRECTIONAL_HANDOFF_ADAPTER_2026-09-20.json"
    )

def role(repo,path):
    if repo=="redogit/conscience64":
        return "target-native-hodge" if path.startswith("research/hodge/") else "hodge-ci"
    if path.startswith("Hodge Span Lab/"): return "hodge-method-tool"
    if path.startswith("Hodge Compass API/"): return "hodge-query-api"
    return "related-method-surface"

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",default=str(Path(__file__).with_name("source_catalog.json")))
    p.add_argument("--token",default=os.environ.get("GITHUB_TOKEN"));a=p.parse_args()
    sources=[]; generated={}
    for repo in REPOS:
        meta=get_json(f"{API}/{repo}",a.token); branch=meta["default_branch"]
        tree=get_json(f"{API}/{repo}/git/trees/{branch}?recursive=1",a.token)
        files=[x for x in tree["tree"] if x.get("type")=="blob" and select(repo,x["path"])]
        generated["conscience64" if repo.endswith("/conscience64") else "other_projects"]={
            "repo":repo,"sha":tree["sha"],"count":len(files)
        }
        sources.extend({
            "repo":repo,"path":x["path"],"blob_sha":x["sha"],"size":x.get("size",0),"role":role(repo,x["path"])
        } for x in files)
    out={
        "schema":"hodge-compass-source-catalog/v1",
        "generated_from":generated,
        "boundaries":[
            "CATALOG_ENTRY != VERIFIED_CLAIM",
            "METHOD_TRANSFER != EVIDENCE_TRANSFER",
            "SOURCE_PATH != AUTHORITY_PROMOTION",
            "CATALOG_EXCLUDES_SELF_TO_AVOID_RECURSIVE_PIN"
        ],
        "sources":sources,
    }
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"out":a.out,"sources":len(sources),"generated_from":generated},indent=2))

if __name__=="__main__":main()

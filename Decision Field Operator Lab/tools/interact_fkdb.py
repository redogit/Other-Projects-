from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
PAGES = LAB / "fkdb" / "pages"
MANIFEST = PAGES / "manifest.json"
LIVE_QUERY_RMAL = LAB / "rmal-browser" / "fkdb_live_query.rmal"
PREDECESSOR = HERE / "interact_independent_browser.py"
QUERY_RECEIPT = re.compile(
    r"FKDB_LIVE_QUERY_RECEIPT status=(\S+) route=(\S+) cost=(\S+) source_preserved=true"
)


def load_manifest() -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("schema") != "fkdb/page-manifest/v1":
        raise ValueError("unsupported FKDB page manifest schema")
    if data.get("project") != "FKDB":
        raise ValueError("manifest project identity is not FKDB")
    lineage = data.get("lineage", {})
    if lineage.get("kind") != "DIRECT_SUCCESSOR" or lineage.get("predecessor") != "Independent Browser":
        raise ValueError("FKDB direct-successor lineage is missing")

    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("FKDB manifest requires pages")
    ids = set()
    for page in pages:
        page_id = page.get("id")
        filename = page.get("file")
        if not isinstance(page_id, str) or not page_id:
            raise ValueError("FKDB page requires non-empty id")
        if page_id in ids:
            raise ValueError(f"duplicate FKDB page id: {page_id}")
        ids.add(page_id)
        if not isinstance(filename, str) or not filename:
            raise ValueError(f"FKDB page {page_id} requires file")
        if not (PAGES / filename).is_file():
            raise FileNotFoundError(PAGES / filename)
        if not page.get("provenance"):
            raise ValueError(f"FKDB page {page_id} requires provenance")
        if not page.get("recovery_path"):
            raise ValueError(f"FKDB page {page_id} requires recovery_path")

    start = data.get("start_page")
    if start not in ids:
        raise ValueError("FKDB start_page is not registered")
    for page in pages:
        for target in page.get("relations", []):
            if target not in ids:
                raise ValueError(f"FKDB page relation targets unknown page: {target}")
    return data


def route_query(query_host: Path, query: str, manifest: dict) -> tuple[str, str, str]:
    if not query_host.is_file():
        raise FileNotFoundError(query_host)
    completed = subprocess.run(
        [str(query_host), str(LIVE_QUERY_RMAL), query],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"FKDB live query host exited with {completed.returncode}: {completed.stderr.strip()}"
        )
    match = QUERY_RECEIPT.search(completed.stdout)
    if match is None:
        raise RuntimeError("FKDB live query host emitted no parseable receipt")
    status, route, cost = match.groups()
    page_ids = {page["id"] for page in manifest["pages"]}
    if route not in page_ids:
        raise RuntimeError(f"FKDB live query routed to unknown page: {route}")
    if status not in {"MATCH", "NO_MATCH", "UNRESOLVED"}:
        raise RuntimeError(f"FKDB live query returned invalid status: {status}")
    return status, route, cost


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch FKDB through the Independent Browser live driver."
    )
    parser.add_argument("--presenter", type=Path, required=True)
    parser.add_argument("--http-carrier", type=Path)
    parser.add_argument("--tls-carrier", type=Path)
    parser.add_argument("--query", default=None)
    parser.add_argument("--query-host", type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path(".fkdb"))
    parser.add_argument("--max-interactions", type=int, default=64)
    parser.add_argument("--max-transitions", type=int, default=64)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_manifest()
    start_page = manifest["start_page"]
    if args.query is not None:
        if args.query_host is None:
            raise ValueError("--query requires --query-host")
        status, route, cost = route_query(args.query_host, args.query, manifest)
        start_page = route if status == "MATCH" else manifest["start_page"]
        print(
            json.dumps(
                {
                    "fkdbQueryStatus": status,
                    "fkdbQueryRoute": route,
                    "fkdbQueryCost": cost,
                    "sourcePreserved": True,
                },
                sort_keys=True,
            )
        )

    command = [sys.executable, str(PREDECESSOR)]
    for page in manifest["pages"]:
        command.extend(["--page", f"{page['id']}={PAGES / page['file']}"])
    command.extend([
        "--start", start_page,
        "--presenter", str(args.presenter),
        "--work-dir", str(args.work_dir),
        "--max-interactions", str(args.max_interactions),
        "--max-transitions", str(args.max_transitions),
    ])
    if args.http_carrier is not None:
        command.extend(["--http-carrier", str(args.http_carrier)])
    if args.tls_carrier is not None:
        command.extend(["--tls-carrier", str(args.tls_carrier)])

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

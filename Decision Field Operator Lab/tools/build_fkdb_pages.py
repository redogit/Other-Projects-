from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
LAB = HERE.parent
FKDB = LAB / "fkdb"
STATE = FKDB / "state" / "current_query.json"
PAGES = FKDB / "pages"
DISPLAY = re.compile(r"^[A-Z ]+$")


def display(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or not DISPLAY.fullmatch(value):
        raise ValueError(f"{field} must contain uppercase A-Z and spaces only")
    if len(value) > 25:
        raise ValueError(f"{field} exceeds bounded FKDB line width")
    return value


def load_state() -> dict:
    data = json.loads(STATE.read_text(encoding="utf-8"))
    if data.get("schema") != "fkdb/query-state/v1":
        raise ValueError("unsupported FKDB query-state schema")
    if data.get("project") != "FKDB":
        raise ValueError("query state project identity is not FKDB")
    lineage = data.get("lineage", {})
    if lineage.get("predecessor") != "Independent Browser":
        raise ValueError("query state lost Independent Browser predecessor")
    if lineage.get("successor") != "FKDB" or lineage.get("kind") != "DIRECT_SUCCESSOR":
        raise ValueError("query state lost FKDB direct-successor identity")
    for field in (
        "need",
        "history",
        "decay",
        "recover",
        "relate",
        "return_state",
        "lineage_display",
    ):
        display(data.get(field), field)
    return data


def build_pages(data: dict) -> dict[str, str]:
    return {
        "fkdb.html": (
            f"<h1>FKDB</h1><p>{data['need']}</p>"
            '<a href="history">HISTORY</a>'
            '<a href="recover">RECOVER</a>'
            '<a href="lineage">LINEAGE</a>'
        ),
        "history.html": (
            f"<h1>HISTORY</h1><p>{data['history']}</p>"
            '<a href="fkdb">HOME</a>'
        ),
        "recover.html": (
            f"<h1>RECOVER</h1><p>{data['decay']}</p>"
            f"<p>{data['recover']}</p>"
            '<a href="fkdb">HOME</a>'
        ),
        "lineage.html": (
            f"<h1>LINEAGE</h1><p>{data['lineage_display']}</p>"
            '<a href="fkdb">HOME</a>'
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = build_pages(load_state())
    mismatches = []
    for filename, content in expected.items():
        path = PAGES / filename
        if args.check:
            actual = path.read_text(encoding="utf-8") if path.is_file() else None
            if actual != content:
                mismatches.append(filename)
        else:
            path.write_text(content, encoding="utf-8")

    if mismatches:
        raise SystemExit("FKDB_PAGE_BUILD_DRIFT " + " ".join(mismatches))
    if args.check:
        print("FKDB_PAGE_BUILD_CHECK PASS")
    else:
        print("FKDB_PAGE_BUILD PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

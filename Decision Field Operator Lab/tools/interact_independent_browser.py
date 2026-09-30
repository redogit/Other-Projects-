"""Interactive bootstrap for the bounded RMAPL local-navigation browser.

Browser semantics remain in examples/independent_browser_navigation.rmapl.
This host loop only:
1. supplies a finite local page table,
2. materializes the admitted P5 camera stream,
3. invokes our native presenter,
4. reads a CLICK x y carrier,
5. rebuilds Omega with that pointer event,
6. executes RMAPL again.

BOOTSTRAP_LOOP != BROWSER_SEMANTICS
LOCAL_PAGE_TABLE != NETWORK
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program

PROGRAM_PATH = LAB / "examples" / "independent_browser_keyboard.rmapl"


def parse_page(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--page requires id=path")
    page_id, raw_path = value.split("=", 1)
    if not page_id or not raw_path:
        raise argparse.ArgumentTypeError("--page requires non-empty id and path")
    return page_id, Path(raw_path)


def load_pages(items: list[tuple[str, Path]]) -> list[dict]:
    seen = set()
    pages = []
    for page_id, path in items:
        if page_id in seen:
            raise ValueError(f"duplicate page id: {page_id}")
        seen.add(page_id)
        pages.append(
            {
                "id": page_id,
                "source": path.read_text(encoding="utf-8"),
            }
        )
    return pages


def initial_omega(pages: list[dict], start: str) -> dict:
    by_id = {page["id"]: page for page in pages}
    if start not in by_id:
        raise ValueError(f"start page {start!r} is not in the local page table")

    return make_omega(
        native_type="independent-browser-navigation/v0",
        native_identity="bootstrap:independent-browser-navigation:1",
        source_refs=tuple(f"local-page:{page['id']}" for page in pages),
        state={
            "source": by_id[start]["source"],
            "resources": {"pages": pages},
            "navigation": {
                "currentPage": start,
                "pendingHref": "",
                "history": [],
                "focusIndex": -1,
                "focusedHref": "",
            },
            "input": {
                "pointer": {"x": 0, "y": 0},
                "keyboard": "",
                "lastHit": "",
            },
            "html": {"tokens": []},
            "dom": {"nodes": []},
            "layout": {"boxes": []},
            "hitMap": [],
            "camera": {
                "width": 160,
                "height": 64,
                "pixels": [],
                "verified": False,
                "admitted": False,
                "blackPixels": 0,
                "pgm": [],
            },
        },
        path=(),
        frame={"obligation": "interactive-bounded-local-navigation"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "html-tokenization-pending", "detail": "bootstrap"},
        ),
        decision_field={"goal": "human-pointer-local-navigation"},
        provenance=(
            {"kind": "bootstrap-loop", "ref": "interact_independent_browser.py"},
        ),
        evidence=(),
        claim_ceiling=(
            "LOCAL_PAGE_NAVIGATION != NETWORK_BROWSING",
            "POINTER_EVENT_CARRIER != BROWSER_SEMANTICS",
            "BOOTSTRAP_LOOP != SELF_HOSTED_RUNTIME",
            "SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 10},
        domain_remainder={
            "unsupported": [
                "network",
                "tls",
                "css",
                "javascript",
                "images",
                "forms",
                "text-input",
                "scrolling",
                "full-html-error-recovery",
            ]
        },
    )


def pointer_omega(omega: dict, x: int, y: int) -> dict:
    construction = deepcopy(omega["construction"])
    construction["state"]["input"]["pointer"] = {"x": x, "y": y}
    construction["state"]["input"]["lastHit"] = ""
    construction["residuals"] = [
        {"kind": "pointer-activation-pending", "detail": "native-click-carrier"}
    ]
    return make_omega(**construction)


def keyboard_omega(omega: dict, key: str) -> dict:
    if key not in {"TAB", "ENTER"}:
        raise ValueError(f"unsupported native key carrier: {key}")
    construction = deepcopy(omega["construction"])
    construction["state"]["input"]["keyboard"] = key
    construction["state"]["input"]["lastHit"] = ""
    construction["residuals"] = [
        {"kind": "keyboard-activation-pending", "detail": "native-key-carrier"}
    ]
    return make_omega(**construction)


def execute_success(program, registry, omega: dict) -> dict:
    result = run_program(program, omega, registry)
    if result["stopReason"] != "SUCCESS" or len(result["branches"]) != 1:
        raise RuntimeError(
            "RMAPL browser did not reach one admitted success branch: "
            + json.dumps(
                {
                    "stopReason": result["stopReason"],
                    "stopFacts": result["stopFacts"],
                    "generation": result["generation"],
                },
                sort_keys=True,
            )
        )
    branch = result["branches"][0]
    camera = branch["omega"]["state"]["camera"]
    if not branch["admitted"] or not camera["verified"] or not camera["admitted"]:
        raise RuntimeError("RMAPL browser returned a non-admitted camera")
    return branch["omega"]


def parse_event(path: Path):
    if not path.exists():
        return None
    parts = path.read_text(encoding="ascii").strip().split()
    if len(parts) == 3 and parts[0] == "CLICK":
        x = int(parts[1], 10)
        y = int(parts[2], 10)
        if not (0 <= x < 160 and 0 <= y < 64):
            raise ValueError(f"click carrier outside framebuffer: {x},{y}")
        return ("CLICK", x, y)
    if len(parts) == 2 and parts[0] == "KEY" and parts[1] in {"TAB", "ENTER"}:
        return ("KEY", parts[1])
    raise ValueError("invalid native input carrier")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", action="append", type=parse_page, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--presenter", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, default=Path(".rmapl-browser"))
    parser.add_argument("--max-interactions", type=int, default=64)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_interactions < 1 or args.max_interactions > 10000:
        raise ValueError("--max-interactions must be in [1,10000]")
    if not args.presenter.is_file():
        raise FileNotFoundError(args.presenter)

    pages = load_pages(args.page)
    program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
    registry = native_registry(program)

    current = execute_success(program, registry, initial_omega(pages, args.start))
    args.work_dir.mkdir(parents=True, exist_ok=True)
    frame_path = args.work_dir / "frame.pgm"
    event_path = args.work_dir / "event.txt"

    for interaction in range(args.max_interactions):
        camera = current["state"]["camera"]
        frame_path.write_bytes(bytes(camera["pgm"]))
        event_path.unlink(missing_ok=True)

        completed = subprocess.run(
            [
                str(args.presenter),
                str(frame_path),
                "--event-out",
                str(event_path),
            ],
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"native presenter exited with code {completed.returncode}"
            )

        event = parse_event(event_path)
        if event is None:
            print("window closed without an input event")
            return 0

        if event[0] == "CLICK":
            _, x, y = event
            candidate = pointer_omega(current, x, y)
            event_summary = {"click": [x, y]}
        else:
            _, key = event
            candidate = keyboard_omega(current, key)
            event_summary = {"key": key}

        result = run_program(program, candidate, registry)

        if result["stopReason"] == "SUCCESS" and len(result["branches"]) == 1:
            current = result["branches"][0]["omega"]
            nav = current["state"]["navigation"]
            print(
                json.dumps(
                    {
                        "interaction": interaction + 1,
                        **event_summary,
                        "currentPage": nav["currentPage"],
                        "history": nav["history"],
                        "focusIndex": nav["focusIndex"],
                        "focusedHref": nav["focusedHref"],
                        "lastHit": current["state"]["input"]["lastHit"],
                    },
                    sort_keys=True,
                )
            )
            continue

        # A miss, unsupported transition, or unresolved local target does not
        # discard the last admitted visual state.
        print(
            json.dumps(
                {
                    "interaction": interaction + 1,
                    **event_summary,
                    "navigation": "no-admitted-transition",
                    "stopReason": result["stopReason"],
                },
                sort_keys=True,
            )
        )

    print("interaction bound reached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

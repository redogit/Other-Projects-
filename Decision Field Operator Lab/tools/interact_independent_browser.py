"""Interactive bootstrap for the RMAPL independent browser.

All browser semantics remain in RMAPL:
- render semantics: examples/independent_browser_native.rmapl
- pointer hit testing + local navigation: examples/independent_browser_interaction.rmapl

This host only:
1. supplies local document bytes/state,
2. materializes admitted camera bytes,
3. launches the native camera presenter,
4. reads raw framebuffer-space pointer coordinates,
5. invokes the RMAPL interaction program,
6. invokes the RMAPL render program after admitted navigation.

HOST_ORCHESTRATION != BROWSER_SEMANTICS
LOCAL_DOCUMENT_STORE != NETWORK_FETCH
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
from tools.render_independent_browser import browser_omega

RENDER_PATH = LAB / "examples" / "independent_browser_native.rmapl"
INTERACTION_PATH = LAB / "examples" / "independent_browser_interaction.rmapl"


def rebuild(omega: dict, *, state=None, residuals=None) -> dict:
    construction = deepcopy(omega["construction"])
    if state is not None:
        construction["state"] = state
    if residuals is not None:
        construction["residuals"] = residuals
    return make_omega(**construction)


def initial_omega(documents: dict[str, str], start: str) -> dict:
    if start not in documents:
        raise KeyError(f"start document {start!r} is not present")
    omega = browser_omega(documents[start])
    state = deepcopy(omega["state"])
    state["documents"] = deepcopy(documents)
    state["location"] = start
    state["history"] = []
    return rebuild(omega, state=state)


def run_render(program, omega: dict) -> dict:
    result = run_program(program, omega, native_registry(program))
    if result["stopReason"] != "SUCCESS" or len(result["branches"]) != 1:
        raise RuntimeError(
            "render did not produce one admitted branch: "
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
    state = branch["omega"]["state"]
    camera = state["camera"]
    if not branch["admitted"] or not camera["verified"] or not camera["admitted"]:
        raise RuntimeError("render branch did not contain verified admitted camera")
    return branch["omega"]


def pointer_omega(omega: dict, x: int, y: int) -> dict:
    state = deepcopy(omega["state"])
    state["input"] = {"clickX": int(x), "clickY": int(y), "consumed": False}
    return rebuild(
        omega,
        state=state,
        residuals=(
            {"kind": "pointer-input-pending", "detail": "native-camera-event"},
        ),
    )


def run_pointer(program, omega: dict, x: int, y: int) -> tuple[dict, bool]:
    before_location = omega["state"]["location"]
    result = run_program(
        program,
        pointer_omega(omega, x, y),
        native_registry(program),
    )
    if len(result["branches"]) != 1:
        raise RuntimeError(
            "pointer program did not expose exactly one branch: "
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
    if not branch["admitted"]:
        raise RuntimeError("pointer navigation proposal was rejected")
    after = branch["omega"]
    return after, after["state"]["location"] != before_location


def write_camera(omega: dict, path: Path) -> None:
    camera = omega["state"]["camera"]
    if not camera["verified"] or not camera["admitted"]:
        raise RuntimeError("refusing to present unverified/unadmitted camera")
    payload = bytes(camera["pgm"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def read_pointer_event(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    fields = path.read_text(encoding="ascii").strip().split()
    if len(fields) != 2:
        raise ValueError("pointer event must contain exactly: x y")
    x = int(fields[0])
    y = int(fields[1])
    if x < 0 or y < 0:
        raise ValueError("pointer coordinates must be non-negative")
    return x, y


def load_documents(path: Path) -> dict[str, str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not value:
        raise ValueError("documents file must be a non-empty JSON object")
    documents: dict[str, str] = {}
    for key, source in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("document ids must be non-empty strings")
        if not isinstance(source, str):
            raise ValueError(f"document {key!r} must contain HTML text")
        documents[key] = source
    return documents


def session(
    *,
    presenter: Path,
    documents: dict[str, str],
    start: str,
    workdir: Path,
    max_events: int,
) -> dict:
    render_program = parse_rmapl(RENDER_PATH.read_text(encoding="utf-8"))
    interaction_program = parse_rmapl(
        INTERACTION_PATH.read_text(encoding="utf-8")
    )

    omega = run_render(render_program, initial_omega(documents, start))
    frame_path = workdir / "frame.pgm"
    event_path = workdir / "pointer.txt"
    workdir.mkdir(parents=True, exist_ok=True)

    event_count = 0
    navigation_count = 0

    while event_count < max_events:
        write_camera(omega, frame_path)
        if event_path.exists():
            event_path.unlink()

        completed = subprocess.run(
            [str(presenter), str(frame_path), "--event", str(event_path)],
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"native camera exited with {completed.returncode}"
            )

        event = read_pointer_event(event_path)
        if event is None:
            break

        event_count += 1
        omega, navigated = run_pointer(
            interaction_program,
            omega,
            event[0],
            event[1],
        )
        if navigated:
            navigation_count += 1
            omega = run_render(render_program, omega)

    return {
        "schema": "rmapl-independent-browser-session-receipt/v0",
        "location": omega["state"]["location"],
        "history": list(omega["state"]["history"]),
        "events": event_count,
        "navigations": navigation_count,
        "cameraVerified": omega["state"]["camera"]["verified"],
        "cameraAdmitted": omega["state"]["camera"]["admitted"],
        "claimCeiling": list(omega["claimCeiling"]),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--presenter", type=Path, required=True)
    parser.add_argument("--documents", type=Path, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--max-events", type=int, default=32)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_events < 1 or args.max_events > 10000:
        raise SystemExit("--max-events must be in [1,10000]")
    receipt = session(
        presenter=args.presenter,
        documents=load_documents(args.documents),
        start=args.start,
        workdir=args.workdir,
        max_events=args.max_events,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

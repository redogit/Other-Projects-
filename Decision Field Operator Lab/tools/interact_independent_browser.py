"""Interactive bootstrap for the bounded RMAPL independent browser.

Browser semantics remain in RMAPL:
- URL/render/input semantics: examples/independent_browser_url.rmapl
- bounded HTTP request/response semantics: examples/independent_browser_http.rmapl

The host is an obligation router only. It:
1. supplies finite local pages,
2. presents admitted P5 camera bytes,
3. reads native CLICK/KEY carriers,
4. executes exactly one admitted RMAPL transition at a time,
5. routes native-http-transport-pending to the raw WinSock carrier,
6. injects returned bytes as http-response-parse-pending,
7. resumes RMAPL until a verified admitted camera exists.

HOST_ROUTING != BROWSER_SEMANTICS
TRANSPORT_SUCCESS != RESPONSE_ADMISSION
URL_PARSE_RESOLVE != NETWORK_FETCH
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from rmapl_runtime import run_program

URL_PROGRAM_PATH = LAB / "examples" / "independent_browser_url.rmapl"
HTTP_PROGRAM_PATH = LAB / "examples" / "independent_browser_http.rmapl"

TransportFn = Callable[[dict], bytes]


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
                "url": f"rmapl://local/{page_id}",
                "source": path.read_text(encoding="utf-8"),
            }
        )
    return pages


def empty_url() -> dict:
    return {
        "raw": "",
        "scheme": "",
        "authority": "",
        "path": "",
        "canonical": "",
        "kind": "",
        "pageId": "",
        "networkRequired": False,
    }


def initial_omega(pages: list[dict], start: str) -> dict:
    by_id = {page["id"]: page for page in pages}
    if start not in by_id:
        raise ValueError(f"start page {start!r} is not in the local page table")

    return make_omega(
        native_type="independent-browser-live-network/v0",
        native_identity="bootstrap:independent-browser-live-network:1",
        source_refs=tuple(f"local-page:{page['id']}" for page in pages),
        state={
            "source": by_id[start]["source"],
            "resources": {"pages": pages},
            "navigation": {
                "currentPage": start,
                "currentUrl": {
                    "raw": f"rmapl://local/{start}",
                    "scheme": "rmapl",
                    "authority": "local",
                    "path": f"/{start}",
                    "canonical": f"rmapl://local/{start}",
                    "kind": "local",
                    "pageId": start,
                    "networkRequired": False,
                },
                "pendingHref": "",
                "pendingUrl": empty_url(),
                "history": [],
                "focusIndex": -1,
                "focusedHref": "",
            },
            "input": {
                "pointer": {"x": 0, "y": 0},
                "keyboard": "",
                "lastHit": "",
            },
            "network": {
                "request": {
                    "host": "",
                    "port": 0,
                    "bytes": [],
                    "maxResponseBytes": 0,
                },
                "responseBytes": [],
                "response": {
                    "status": 0,
                    "bodyBytes": [],
                },
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
        frame={"obligation": "interactive-url-http-tls-gated-navigation"},
        invariants=("sourceRefs", "claim-ceiling"),
        observations=(),
        residuals=(
            {"kind": "html-tokenization-pending", "detail": "bootstrap"},
        ),
        decision_field={"goal": "verified-interactive-local-or-http-navigation"},
        provenance=(
            {"kind": "bootstrap-loop", "ref": "interact_independent_browser.py"},
        ),
        evidence=(),
        claim_ceiling=(
            "URL_PARSE_RESOLVE != NETWORK_FETCH",
            "TRANSPORT_SUCCESS != RESPONSE_ADMISSION",
            "HTTP11_CLOSE_PROFILE != GENERAL_HTTP",
            "PLAINTEXT_HTTP != TLS_TRANSPORT",
            "TLS_TRANSPORT_SUCCESS != RESPONSE_ADMISSION",
            "INPUT_EVENT_CARRIER != BROWSER_SEMANTICS",
            "BOOTSTRAP_LOOP != SELF_HOSTED_RUNTIME",
            "SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION",
        ),
        resource_bounds={"maxCandidates": 1, "maxSteps": 1},
        domain_remainder={
            "unsupported": [
                "redirects",
                "chunked-transfer",
                "compression",
                "cookies",
                "authentication",
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


def rebuild(omega: dict, *, state=None, residuals=None) -> dict:
    construction = deepcopy(omega["construction"])
    if state is not None:
        construction["state"] = state
    if residuals is not None:
        construction["residuals"] = residuals
    # Interactive orchestration intentionally exposes one admitted transition
    # per RMAPL run so carrier boundaries cannot be skipped.
    construction["resource_bounds"]["maxSteps"] = 1
    return make_omega(**construction)


def pointer_omega(omega: dict, x: int, y: int) -> dict:
    state = deepcopy(omega["state"])
    state["input"]["pointer"] = {"x": x, "y": y}
    state["input"]["lastHit"] = ""
    return rebuild(
        omega,
        state=state,
        residuals=(
            {"kind": "pointer-activation-pending", "detail": "native-click-carrier"},
        ),
    )


def keyboard_omega(omega: dict, key: str) -> dict:
    if key not in {"TAB", "ENTER"}:
        raise ValueError(f"unsupported native key carrier: {key}")
    state = deepcopy(omega["state"])
    state["input"]["keyboard"] = key
    state["input"]["lastHit"] = ""
    return rebuild(
        omega,
        state=state,
        residuals=(
            {"kind": "keyboard-activation-pending", "detail": "native-key-carrier"},
        ),
    )


def response_omega(omega: dict, payload: bytes) -> dict:
    request = omega["state"]["network"]["request"]
    maximum = request["maxResponseBytes"]
    if type(maximum) is not int or maximum < 1:
        raise ValueError("RMAPL request did not declare a positive response bound")
    if not payload or len(payload) > maximum:
        raise ValueError(
            f"native response length {len(payload)} outside declared bound {maximum}"
        )
    state = deepcopy(omega["state"])
    state["network"]["responseBytes"] = list(payload)
    return rebuild(
        omega,
        state=state,
        residuals=(
            {"kind": "http-response-parse-pending", "detail": "native-transport-complete"},
        ),
    )


def residual_kind(omega: dict) -> str | None:
    residuals = omega["residuals"]
    if not residuals:
        return None
    if len(residuals) != 1:
        raise RuntimeError("interactive browser requires exactly one active residual")
    kind = residuals[0].get("kind")
    if not isinstance(kind, str) or not kind:
        raise RuntimeError("active residual is missing a non-empty kind")
    return kind


def execute_one(program, registry, omega: dict) -> tuple[dict | None, dict]:
    limited = rebuild(omega)
    result = run_program(program, limited, registry)
    branches = result["branches"]
    if len(branches) != 1:
        return None, result
    branch = branches[0]
    if not branch["admitted"]:
        return None, result
    return branch["omega"], result


def subprocess_network_transport(
    omega: dict,
    *,
    carrier: Path,
    work_dir: Path,
    carrier_name: str,
) -> bytes:
    request = omega["state"]["network"]["request"]
    host = request["host"]
    port = request["port"]
    payload = bytes(request["bytes"])
    maximum = request["maxResponseBytes"]

    if not isinstance(host, str) or not host:
        raise RuntimeError("RMAPL network request is missing host")
    if type(port) is not int or not (1 <= port <= 65535):
        raise RuntimeError("RMAPL network request port is outside [1,65535]")
    if not payload:
        raise RuntimeError("RMAPL network request payload is empty")
    if type(maximum) is not int or maximum < 1:
        raise RuntimeError("RMAPL network request response bound is invalid")

    work_dir.mkdir(parents=True, exist_ok=True)
    request_path = work_dir / "request.bin"
    response_path = work_dir / "response.bin"
    request_path.write_bytes(payload)
    response_path.unlink(missing_ok=True)

    completed = subprocess.run(
        [
            str(carrier),
            "--host",
            host,
            "--port",
            str(port),
            "--request",
            str(request_path),
            "--out",
            str(response_path),
            "--max",
            str(maximum),
        ],
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"native {carrier_name} carrier exited with code {completed.returncode}"
        )
    if not response_path.is_file():
        raise RuntimeError(f"native {carrier_name} carrier produced no response file")
    response = response_path.read_bytes()
    if not response or len(response) > maximum:
        raise RuntimeError(f"native {carrier_name} carrier violated response byte bound")
    return response


def drive_browser(
    omega: dict,
    *,
    url_program,
    url_registry,
    http_program,
    http_registry,
    transport: TransportFn | None = None,
    tls_transport: TransportFn | None = None,
    max_transitions: int = 64,
) -> tuple[dict, str]:
    """Drive admitted RMAPL transitions until presentation or external residual.

    The function never interprets URL, HTTP, DOM, layout, or hit-map semantics.
    It routes only declared residual kinds to their owning RMAPL program or to
    the native byte carrier.
    """
    if max_transitions < 1:
        raise ValueError("max_transitions must be positive")

    current = rebuild(omega)

    for _ in range(max_transitions):
        kind = residual_kind(current)

        if kind is None:
            camera = current["state"]["camera"]
            if camera["verified"] and camera["admitted"] and camera["pgm"]:
                return current, "presentable"
            return current, "terminal-without-camera"

        if kind == "native-http-transport-pending":
            if transport is None:
                return current, "http-carrier-missing"
            current = response_omega(current, transport(current))
            continue

        if kind == "native-tls-transport-pending":
            if tls_transport is None:
                return current, "tls-carrier-missing"
            current = response_omega(current, tls_transport(current))
            continue

        if kind in {"network-transport-pending", "http-response-parse-pending"}:
            program = http_program
            registry = http_registry
        elif kind == "tls-transport-pending":
            return current, "tls-transport-pending"
        else:
            program = url_program
            registry = url_registry

        next_omega, result = execute_one(program, registry, current)
        if next_omega is None:
            return current, f"no-admitted-transition:{result['stopReason']}"
        current = next_omega

    return current, "transition-bound"


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
    parser.add_argument("--http-carrier", type=Path)
    parser.add_argument("--tls-carrier", type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path(".rmapl-browser"))
    parser.add_argument("--max-interactions", type=int, default=64)
    parser.add_argument("--max-transitions", type=int, default=64)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_interactions < 1 or args.max_interactions > 10000:
        raise ValueError("--max-interactions must be in [1,10000]")
    if args.max_transitions < 1 or args.max_transitions > 10000:
        raise ValueError("--max-transitions must be in [1,10000]")
    if not args.presenter.is_file():
        raise FileNotFoundError(args.presenter)
    if args.http_carrier is not None and not args.http_carrier.is_file():
        raise FileNotFoundError(args.http_carrier)
    if args.tls_carrier is not None and not args.tls_carrier.is_file():
        raise FileNotFoundError(args.tls_carrier)

    pages = load_pages(args.page)
    url_program = parse_rmapl(URL_PROGRAM_PATH.read_text(encoding="utf-8"))
    url_registry = native_registry(url_program)
    http_program = parse_rmapl(HTTP_PROGRAM_PATH.read_text(encoding="utf-8"))
    http_registry = native_registry(http_program)

    transport = None
    if args.http_carrier is not None:
        transport = lambda omega: subprocess_network_transport(
            omega,
            carrier=args.http_carrier,
            work_dir=args.work_dir / "http",
            carrier_name="HTTP",
        )

    tls_transport = None
    if args.tls_carrier is not None:
        tls_transport = lambda omega: subprocess_network_transport(
            omega,
            carrier=args.tls_carrier,
            work_dir=args.work_dir / "tls",
            carrier_name="TLS",
        )

    current, status = drive_browser(
        initial_omega(pages, args.start),
        url_program=url_program,
        url_registry=url_registry,
        http_program=http_program,
        http_registry=http_registry,
        transport=transport,
        tls_transport=tls_transport,
        max_transitions=args.max_transitions,
    )
    if status != "presentable":
        raise RuntimeError(f"initial browser state did not become presentable: {status}")

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

        proposed, status = drive_browser(
            candidate,
            url_program=url_program,
            url_registry=url_registry,
            http_program=http_program,
            http_registry=http_registry,
            transport=transport,
            tls_transport=tls_transport,
            max_transitions=args.max_transitions,
        )

        if status == "presentable":
            current = proposed
            nav = current["state"]["navigation"]
            print(
                json.dumps(
                    {
                        "interaction": interaction + 1,
                        **event_summary,
                        "status": status,
                        "currentPage": nav["currentPage"],
                        "currentUrl": nav["currentUrl"]["canonical"],
                        "history": nav["history"],
                        "focusIndex": nav["focusIndex"],
                        "focusedHref": nav["focusedHref"],
                        "lastHit": current["state"]["input"]["lastHit"],
                    },
                    sort_keys=True,
                )
            )
            continue

        # Failed/unavailable external transitions do not replace the last
        # admitted visual state. The unresolved obligation remains observable
        # in the proposed Omega returned by drive_browser.
        print(
            json.dumps(
                {
                    "interaction": interaction + 1,
                    **event_summary,
                    "status": status,
                    "activeResidual": residual_kind(proposed),
                    "currentUrl": current["state"]["navigation"]["currentUrl"]["canonical"],
                },
                sort_keys=True,
            )
        )

    print("interaction bound reached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

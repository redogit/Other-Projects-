"""Differential evidence for browser_http_response_admit.

The native RMAL host executes response policy without Python. This script uses
the current RMAPL operator only as an oracle and compares the observable
admission + transition contract for identical byte fixtures.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys

LAB = Path(__file__).resolve().parents[1]
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

from omega import make_omega
from rmapl import parse_rmapl
from rmapl_native import native_registry
from tools.plan_independent_browser_http import omega_for


PROGRAM_PATH = LAB / "examples" / "independent_browser_http.rmapl"

FIXTURES = {
    "valid": (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html\r\n"
        b"Connection: close\r\n"
        b"\r\n"
        b"<h1>FETCHED</h1>"
    ),
    "not_found": b"HTTP/1.1 404 Not Found\r\n\r\n<h1>NO</h1>",
    "missing_delimiter": (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html\r\n"
        b"<h1>NO</h1>"
    ),
    "empty_body": (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html\r\n"
        b"\r\n"
    ),
}


def parse_line(line: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for token in line.split()[1:]:
        key, value = token.split("=", 1)
        fields[key] = value
    return fields


def inject_response(base: dict, raw: bytes) -> dict:
    construction = deepcopy(base["construction"])
    construction["state"]["network"]["responseBytes"] = list(raw)
    construction["residuals"] = [
        {"kind": "http-response-parse-pending", "detail": "differential-oracle"}
    ]
    return make_omega(**construction)


def cleared_url(value: dict) -> bool:
    return value == {
        "raw": "",
        "scheme": "",
        "authority": "",
        "path": "",
        "canonical": "",
        "kind": "",
        "pageId": "",
        "networkRequired": False,
    }


def dirty_base() -> dict:
    base = omega_for("example.com", "/docs", "https")
    construction = deepcopy(base["construction"])
    state = construction["state"]
    state["navigation"]["history"] = ["rmapl://local/older"]
    state["navigation"]["pendingHref"] = "https://example.com/docs"
    state["navigation"]["currentPage"] = "stale-page"
    state["html"]["tokens"] = [{"kind": "stale"}]
    state["dom"]["nodes"] = [{"kind": "stale"}]
    state["layout"]["boxes"] = [{"kind": "stale"}]
    state["hitMap"] = [{"kind": "stale"}]
    state["camera"]["pixels"] = [1]
    state["camera"]["pgm"] = [1]
    state["camera"]["verified"] = True
    state["camera"]["admitted"] = True
    state["camera"]["blackPixels"] = 1
    return make_omega(**construction)


def oracle_result(operator, raw: bytes) -> dict[str, object]:
    base = dirty_base()
    before = deepcopy(base["state"])
    proposal = operator(inject_response(base, raw))
    omega = proposal["omega"]
    state = omega["state"]
    residual = omega["residuals"][0]

    admitted = proposal["consequenceKey"] == "http-response-admitted"
    append_history = (
        state["navigation"]["history"]
        == before["navigation"]["history"]
        + [before["navigation"]["currentUrl"]["canonical"]]
    )
    promote_pending = (
        state["navigation"]["currentUrl"]
        == before["navigation"]["pendingUrl"]
    )
    clear_navigation = (
        state["navigation"]["pendingHref"] == ""
        and state["navigation"]["currentPage"] == ""
        and cleared_url(state["navigation"]["pendingUrl"])
    )
    clear_render = (
        state["html"]["tokens"] == []
        and state["dom"]["nodes"] == []
        and state["layout"]["boxes"] == []
        and state["hitMap"] == []
        and state["camera"]["pixels"] == []
        and state["camera"]["pgm"] == []
        and state["camera"]["verified"] is False
        and state["camera"]["admitted"] is False
        and state["camera"]["blackPixels"] == 0
    )

    return {
        "admitted": admitted,
        "status": state["network"]["response"]["status"],
        "body": bytes(state["network"]["response"]["bodyBytes"]),
        "residual": residual["kind"],
        "detail": residual["detail"],
        "consequence": proposal["consequenceKey"],
        "history": append_history,
        "promote": promote_pending,
        "clear_nav": clear_navigation,
        "clear_render": clear_render,
    }


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: verify_http_response_equivalence.py "
            "<browser_rmal_http_response_host> <browser_http_response.rmal>"
        )

    completed = subprocess.run(
        [sys.argv[1], sys.argv[2]],
        capture_output=True,
        text=True,
        check=True,
    )
    actual = {
        row["fixture"]: row
        for row in (
            parse_line(line)
            for line in completed.stdout.splitlines()
            if line.startswith("RMAL_HTTP_RESPONSE ")
        )
    }
    if set(actual) != set(FIXTURES):
        raise AssertionError(
            f"RMAL response fixture set mismatch: {sorted(actual)}\n"
            + completed.stdout
        )

    program = parse_rmapl(PROGRAM_PATH.read_text(encoding="utf-8"))
    operator = native_registry(program)["browser_http_response_admit"]

    for name, raw in FIXTURES.items():
        expected = oracle_result(operator, raw)
        row = actual[name]

        assert row["admitted"] == bool_text(bool(expected["admitted"])), (name, row, expected)
        assert int(row["status"]) == expected["status"], (name, row, expected)
        assert bytes.fromhex(row["body_hex"]) == expected["body"], (name, row, expected)
        assert row["residual"] == expected["residual"], (name, row, expected)
        assert row["detail"] == expected["detail"], (name, row, expected)
        assert row["consequence"] == expected["consequence"], (name, row, expected)
        assert row["history"] == bool_text(bool(expected["history"])), (name, row, expected)
        assert row["promote"] == bool_text(bool(expected["promote"])), (name, row, expected)
        assert row["clear_nav"] == bool_text(bool(expected["clear_nav"])), (name, row, expected)
        assert row["clear_render"] == bool_text(bool(expected["clear_render"])), (name, row, expected)

    receipt = (
        "RMAL_HTTP_RESPONSE_RECEIPT "
        f"fixtures={len(FIXTURES)} policy_in_rmal=true python_runtime_used=false"
    )
    if receipt not in completed.stdout:
        raise AssertionError("native RMAL response receipt missing")

    print("RMAPL_RMAL_HTTP_RESPONSE_EQUIVALENCE PASS")
    print("BYTE_MECHANICS_CALLBACKS != HTTP_POLICY")
    print("PYTHON_DIFFERENTIAL_ORACLE != RMAL_RUNTIME_DEPENDENCY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

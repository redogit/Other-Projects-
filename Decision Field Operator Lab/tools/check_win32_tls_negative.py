"""Controlled Windows TLS evidence; no external host, ignore flag or client CA option.

The Python/OpenSSL server is a test peer only. The client under test is the
unmodified production SChannel executable. Certificate-rejection fixtures stay
on TLS 1.2 so exact policy errors remain isolated. A separate trusted TLS 1.3
positive control requires bounded post-handshake continuation evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.plan_independent_browser_http import plan


RESPONSE = b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n<h1>LOCAL TLS</h1>"
# Literal Windows policy and SChannel status oracles; transport errors do not pass.
CASES = (
    ("positive-control", "valid", "localhost", "0", None, "tls12", False),
    ("post-handshake-tls13", "valid", "localhost", "0", None, "tls13", True),
    ("hostname-mismatch", "valid", "127.0.0.1", "800b010f", "80090322", "tls12", False),
    ("untrusted-chain", "untrusted", "localhost", "800b0109", "80090325", "tls12", False),
    ("expired", "expired", "localhost", "800b0101", "80090328", "tls12", False),
)


def check_case(
    args,
    name,
    fixture,
    host,
    policy_error,
    handshake_error,
    protocol,
    require_post_handshake,
):
    policy = subprocess.run([str(args.policy_probe), str(args.fixtures / f"{fixture}.cer"),
                             host, policy_error], capture_output=True, text=True, timeout=15)
    record = {"case": name, "policy_exit": policy.returncode,
              "policy_stdout": policy.stdout, "policy_stderr": policy.stderr}
    # Write partial results even when an assertion below fails.
    args.records.append(record)
    assert policy.returncode == 0, record
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    if protocol == "tls13":
        if not getattr(ssl, "HAS_TLSv1_3", False):
            raise AssertionError("controlled TLS 1.3 evidence requires Python/OpenSSL TLS 1.3")
        context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_3
        # OpenSSL sends TLS 1.3 NewSessionTicket post-handshake messages.
        context.num_tickets = 2
    else:
        context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(args.fixtures / f"{fixture}.pem", args.fixtures / f"{fixture}.key")
    observed = {"connections": 0, "prefixes": [], "requests": [], "errors": []}
    stop = threading.Event()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(4)
        listener.settimeout(0.2)
        port = listener.getsockname()[1]

        def serve():
            while not stop.is_set():
                try:
                    raw, _ = listener.accept()
                except socket.timeout:
                    continue
                with raw:
                    raw.settimeout(5)
                    observed["connections"] += 1
                    try:
                        prefix = raw.recv(5, socket.MSG_PEEK)
                        observed["prefixes"].append(prefix.hex())
                        with context.wrap_socket(raw, server_side=True) as peer:
                            request = b""
                            observed["requests"].append("")
                            while b"\r\n\r\n" not in request and len(request) < 4096:
                                chunk = peer.recv(4096)
                                if not chunk:
                                    break
                                request += chunk
                                observed["requests"][-1] = request.hex()
                            if request:
                                peer.sendall(RESPONSE)
                                # Send close_notify; the client does not send a reciprocal
                                # alert, so unwrap may report EOF after the response.
                                try:
                                    peer.unwrap().close()
                                except (ssl.SSLError, OSError):
                                    pass
                    except (ssl.SSLError, OSError) as exc:
                        observed["errors"].append(str(exc))

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        request_path = args.fixtures / f"{name}-request.bin"
        output_path = args.fixtures / f"{name}-response.bin"
        request, _ = plan(host=host, path="/test", scheme="https")
        request_path.write_bytes(request)
        sentinel = b"prior-output-must-survive-certificate-failure"
        output_path.write_bytes(sentinel)
        try:
            completed = subprocess.run([
                str(args.carrier), "--host", host, "--port", str(port),
                "--request", str(request_path), "--out", str(output_path), "--max", "262144",
            ], capture_output=True, text=True, timeout=20)
        finally:
            stop.set()
            worker.join(7)
        record.update(
            exit=completed.returncode,
            stderr=completed.stderr,
            peer=observed,
            protocol=protocol,
            require_post_handshake=require_post_handshake,
            output_sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),
        )
        assert not worker.is_alive(), "local peer did not stop"
    assert observed["connections"] == 1, record
    assert all(prefix.startswith("1603") for prefix in observed["prefixes"]), record
    if handshake_error is None:
        assert completed.returncode == 0, record
        assert observed["requests"] == [request.hex()], record
        assert output_path.read_bytes() == RESPONSE, record
        if require_post_handshake:
            marker = "TLS post-handshake continuations: "
            assert marker in completed.stderr, record
            count_text = completed.stderr.split(marker, 1)[1].splitlines()[0].strip()
            assert int(count_text) >= 1, record
    else:
        assert completed.returncode == 68, record
        assert f"TLS handshake failed: 0x{handshake_error}" in completed.stderr, record
        assert not observed["requests"], record
        assert output_path.read_bytes() == sentinel, record
    record["passed"] = True
    print(json.dumps(record, sort_keys=True), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--carrier", type=Path, required=True)
    parser.add_argument("--policy-probe", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    args.records = []
    try:
        for case in CASES:
            check_case(args, *case)
    finally:
        args.receipt.write_text(json.dumps({
            "schema": "rmapl-controlled-tls-evidence/v2",
            "commit": os.environ.get("VERIFY_SHA"), "cases": args.records,
            "evidence_scope": "local Windows policy, TLS 1.2 rejection fixtures, and trusted TLS 1.3 post-handshake control",
            "claim_ceiling": ["TLS_HANDSHAKE_SUCCESS != RESPONSE_ADMISSION",
                              "CERTIFICATE_POLICY_PASS != TRUSTED_PAGE_CONTENT",
                              "SOFTWARE_VERIFICATION != SECURITY_CERTIFICATION"],
        }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

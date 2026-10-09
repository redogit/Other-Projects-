#!/usr/bin/env python3
"""Resolve frozen artifacts from the canonical Hodge repository.

Network access is explicit (`fetch`); readers only verify local pinned bytes.
The ignored checkout is a disposable dependency, never a research authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "dependencies/hodge.lock.json"
DEFAULT_CHECKOUT = ROOT / ".dependencies/hodge"
FETCH_URL = "https://github.com/redogit/hodge.git"


class DependencyError(RuntimeError):
    """An absent or altered dependency must not be admitted."""


def _lock():
    try:
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DependencyError(f"Cannot read Hodge dependency lock: {exc}") from exc
    if (not isinstance(lock, dict) or lock.get("schema") != "hodge-dependency/v1"
            or lock.get("repository") != "redogit/hodge"
            or not isinstance(lock.get("revision"), str)
            or not re.fullmatch(r"[0-9a-f]{40}", lock.get("revision", ""))
            or not isinstance(lock.get("artifacts"), dict) or not lock["artifacts"]):
        raise DependencyError("Invalid canonical Hodge dependency lock")
    for artifact in lock["artifacts"].values():
        if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str):
            raise DependencyError("Artifact must declare a relative path string")
        path = PurePosixPath(artifact.get("path", ""))
        if (path.is_absolute() or ".." in path.parts or not path.parts
                or "\\" in str(path)):
            raise DependencyError("Artifact must use a safe relative path")
        if (not isinstance(artifact.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"])):
            raise DependencyError("Artifact requires a frozen SHA-256")
    return lock


def _checkout():
    return Path(os.environ.get("HODGE_REPOSITORY_ROOT", str(DEFAULT_CHECKOUT))).resolve()


def _run_git(checkout, *args):
    try:
        return subprocess.run(
            ["git", "-C", str(checkout), *args], check=True, capture_output=True,
            text=True, timeout=120, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise DependencyError(f"Hodge dependency Git operation failed: {exc}") from exc


def _verify_revision(checkout, lock):
    if not (checkout / ".git").exists():
        raise DependencyError(
            f"Hodge checkout missing at {checkout}. Run python3 tools/hodge_dependency.py fetch"
        )
    actual = _run_git(checkout, "rev-parse", "HEAD")
    if actual != lock["revision"]:
        raise DependencyError(f"Hodge revision mismatch: expected {lock['revision']}, found {actual}")


def _verified_artifact(key, checkout, lock):
    if key not in lock["artifacts"]:
        raise DependencyError(f"Unknown artifact: {key}")
    artifact = lock["artifacts"][key]
    path = (checkout / artifact["path"]).resolve()
    if not path.is_relative_to(checkout):
        raise DependencyError(f"Hodge artifact resolves outside canonical checkout: {key}")
    try:
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise DependencyError(f"Hodge artifact missing: {key} ({path})") from exc
    if actual != artifact["sha256"]:
        raise DependencyError(f"Hodge artifact SHA-256 mismatch: {key} ({path})")
    return path


def resolve_artifact(key):
    """Return a verified canonical path; never fetch or fall back to old paths."""
    lock = _lock()
    checkout = _checkout()
    _verify_revision(checkout, lock)
    return _verified_artifact(key, checkout, lock)


def verify_dependency():
    lock = _lock()
    checkout = _checkout()
    _verify_revision(checkout, lock)
    for key in lock["artifacts"]:
        _verified_artifact(key, checkout, lock)
    return checkout


def fetch_dependency():
    """Materialize the exact canonical revision once; never overwrite a checkout."""
    checkout = _checkout()
    if checkout.exists():
        return verify_dependency()
    lock = _lock()
    checkout.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hodge-fetch-", dir=checkout.parent) as temp:
        staging = Path(temp) / "checkout"
        staging.mkdir()
        _run_git(staging, "init", "-q")
        _run_git(staging, "remote", "add", "origin", FETCH_URL)
        _run_git(staging, "fetch", "--depth=1", "origin", lock["revision"])
        _run_git(staging, "checkout", "--detach", "FETCH_HEAD")
        _verify_revision(staging, lock)
        for key in lock["artifacts"]:
            _verified_artifact(key, staging, lock)
        staging.rename(checkout)
    return verify_dependency()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("fetch", "verify", "path"))
    parser.add_argument("artifact", nargs="?")
    args = parser.parse_args(argv)
    try:
        if args.command == "path":
            if not args.artifact:
                parser.error("path requires an artifact key")
            print(resolve_artifact(args.artifact))
        else:
            if args.artifact:
                parser.error("artifact key is only valid with path")
            checkout = fetch_dependency() if args.command == "fetch" else verify_dependency()
            lock = _lock()
            print(f"HODGE_DEPENDENCY=PASS repository={lock['repository']} "
                  f"revision={lock['revision']} artifacts={len(lock['artifacts'])} checkout={checkout}")
    except DependencyError as exc:
        print(f"HODGE_DEPENDENCY=FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

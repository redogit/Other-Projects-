"""Build a pinned local API sandbox. No Git branch or deployment is modified."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 2_000_000


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_path(name: str) -> Path:
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or "\\" in name or not p.parts:
        raise ValueError(f"Unsafe path: {name!r}")
    return Path(*p.parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-dir", type=Path, help="Exact original 1.2.0 source, offline")
    group.add_argument("--download", action="store_true", help="Explicitly fetch pinned public assets")
    parser.add_argument("--output", type=Path, default=ROOT / "build/site")
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists():
        raise SystemExit(f"Refusing to overwrite {target}; use a fresh --output directory.")
    if not shutil.which("git"):
        raise SystemExit("Git is required to check and apply the two local patches.")
    lock = json.loads((ROOT / "source-lock.json").read_text(encoding="utf-8"))
    if lock["repository"] != "redogit/conscience64" or lock["commit"] != "3f8889e17cecd7bd865e33f70201c703163df405":
        raise SystemExit("Unexpected source identity; review the lock before changing this guard.")
    source = args.source_dir.resolve() if args.source_dir else None
    # Stage outside the project Git tree so git apply cannot inherit its path prefix.
    with tempfile.TemporaryDirectory(prefix="chatgpt-conscience-") as tmp:
        stage = Path(tmp)
        for entry in lock["files"]:
            rel = relative_path(entry["path"])
            if source is not None:
                input_file = (source / rel).resolve()
                if not input_file.is_relative_to(source):
                    raise ValueError(f"Source escapes directory: {rel}")
                data = input_file.read_bytes()
            else:
                url = f"https://raw.githubusercontent.com/{lock['repository']}/{lock['commit']}/{entry['path']}"
                request = Request(url, headers={"User-Agent": "ChatGPT-Conscience-local-builder/0.1"})
                with urlopen(request, timeout=30) as response:
                    data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES or len(data) != entry["bytes"] or digest(data) != entry["sha256"]:
                raise ValueError(f"Source identity mismatch: {rel}")
            output = stage / rel
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
        for entry in lock["patches"]:
            patch = ROOT / relative_path(entry["path"])
            if digest(patch.read_bytes()) != entry["sha256"]:
                raise ValueError(f"Patch identity mismatch: {patch.name}")
            subprocess.run(["git", "apply", "--check", str(patch)], cwd=stage, check=True)
            subprocess.run(["git", "apply", str(patch)], cwd=stage, check=True)
        for name, expected in lock["expected_after_patch"].items():
            if digest((stage / relative_path(name)).read_bytes()) != expected:
                raise ValueError(f"Candidate identity mismatch: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(stage, target)  # Also refuses a target created concurrently.
    print(json.dumps({"status": "BUILT_LOCAL_ONLY", "version": lock["candidate_version"],
                      "runtime_assets": len(lock["files"]), "output": str(target)}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate MiniGX assets from verified canonical Hodge inputs; never fetch implicitly."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "tools"))
from hodge_dependency import resolve_artifact
import minigxc

IR_ASSET = "minigx/w114_perturbation.minigx.json"
VERTEX_ASSET = "shaders/fullscreen.vert"
FRAGMENT_ASSET = "shaders/w114_field.frag"
JAVA_SOURCE = "java/org/rmaos/mingx/generated/MiniGXGraph.java"


def canonical_source() -> Path:
    return resolve_artifact("w114_circuit")


def canonical_shader() -> Path:
    return resolve_artifact("w114_shader")


def canonical_assets():
    ir = minigxc.canonical_ir(canonical_source())
    field = next(node for node in ir["nodes"] if node["op"] == "W114_FIELD")
    if field["params"]["vertex_shader"] != VERTEX_ASSET or field["params"]["shader"] != FRAGMENT_ASSET:
        raise ValueError("canonical circuit shader paths do not match the MiniGX asset contract")
    return ir, {
        VERTEX_ASSET: (ROOT / VERTEX_ASSET).read_bytes(),
        FRAGMENT_ASSET: canonical_shader().read_bytes(),
    }


def build(generated_root: Path):
    ir, shaders = canonical_assets()
    assets = generated_root / "assets"
    # These directories belong to this generator. Remove stale competing inputs.
    for path in (assets / "minigx", assets / "shaders", (generated_root / JAVA_SOURCE).parent):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)
    (assets / IR_ASSET).write_text(json.dumps(ir, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (generated_root / JAVA_SOURCE).write_text(minigxc.java_source(ir), encoding="utf-8")
    for name, data in shaders.items():
        (assets / name).write_bytes(data)
    print(ir["digest"])


def parity(apk: Path):
    ir, shaders = canonical_assets()
    expected_names = {"assets/" + name for name in (*shaders, IR_ASSET)}
    with ZipFile(apk) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate APK ZIP entries")
        actual_names = {name for name in names if name.startswith(("assets/shaders/", "assets/minigx/")) and not name.endswith("/")}
        unexpected = actual_names - expected_names
        if unexpected:
            raise ValueError("unexpected MiniGX asset: " + ", ".join(sorted(unexpected)))
        for name, data in shaders.items():
            if archive.read("assets/" + name) != data:
                raise ValueError("shader asset mismatch: " + name)
        if json.loads(archive.read("assets/" + IR_ASSET)) != ir:
            raise ValueError("circuit asset mismatch, including canonical source provenance")
    print("MINIGX_APK_SOURCE_PARITY=PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    generator = commands.add_parser("build")
    generator.add_argument("--generated-root", required=True, type=Path)
    checker = commands.add_parser("parity")
    checker.add_argument("apk", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "build":
            build(args.generated_root)
        else:
            parity(args.apk)
    except Exception as error:
        print("MINIGX_DEPENDENCY_ERROR: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run a GSFL v0 program and emit canonical JSON."""

from __future__ import annotations

import argparse
from pathlib import Path

import gsfl


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute a GSFL v0 program")
    parser.add_argument("program", type=Path, help="path to a .gsfl program")
    parser.add_argument("--out", type=Path, help="write canonical JSON to this path")
    args = parser.parse_args()

    result = gsfl.execute(args.program.read_text(encoding="utf-8"))
    payload = gsfl.canonical_json(result)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

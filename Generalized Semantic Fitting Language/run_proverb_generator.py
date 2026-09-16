#!/usr/bin/env python3
"""Generate deterministic synthetic proverbial GSFL v0.1 fixtures."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path

import gsfl
import gsfl_proverbs as proverbs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate GSFL v0.1 synthetic proverb fixtures")
    parser.add_argument("--seed", type=int, default=20260916)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    fixtures = proverbs.generate_synthetic_fixtures(seed=args.seed, count=args.count)
    payload = gsfl.canonical_json({
        "artifact": "GSFL-v0.1-synthetic-proverbial-fixtures",
        "seed": args.seed,
        "fixture_count": len(fixtures),
        "fixtures": [asdict(fixture) for fixture in fixtures],
        "boundaries": [
            "SYNTHETIC != TRADITIONAL",
            "PROVERB != EMPIRICAL_EVIDENCE",
            "MACHINE_PARAPHRASE != HUMAN_UNDERSTANDING",
            "POPULARITY != TRUTH",
        ],
    })
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

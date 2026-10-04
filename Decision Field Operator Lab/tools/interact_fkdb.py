from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
PAGES = LAB / "fkdb" / "pages"
PREDECESSOR = HERE / "interact_independent_browser.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch FKDB through the Independent Browser live driver."
    )
    parser.add_argument("--presenter", type=Path, required=True)
    parser.add_argument("--http-carrier", type=Path)
    parser.add_argument("--tls-carrier", type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path(".fkdb"))
    parser.add_argument("--max-interactions", type=int, default=64)
    parser.add_argument("--max-transitions", type=int, default=64)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    command = [
        sys.executable,
        str(PREDECESSOR),
        "--page", f"fkdb={PAGES / 'fkdb.html'}",
        "--page", f"history={PAGES / 'history.html'}",
        "--page", f"recover={PAGES / 'recover.html'}",
        "--page", f"lineage={PAGES / 'lineage.html'}",
        "--start", "fkdb",
        "--presenter", str(args.presenter),
        "--work-dir", str(args.work_dir),
        "--max-interactions", str(args.max_interactions),
        "--max-transitions", str(args.max_transitions),
    ]
    if args.http_carrier is not None:
        command.extend(["--http-carrier", str(args.http_carrier)])
    if args.tls_carrier is not None:
        command.extend(["--tls-carrier", str(args.tls_carrier)])

    completed = subprocess.run(command, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())

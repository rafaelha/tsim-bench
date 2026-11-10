"""Command line: ``python -m tsim_bench list|check|run``.

    list   the selected circuits with arXiv id, width and postselection
    check  validate the manifests (see check.py); needs Tsim
    run    time each selected circuit in a fresh process of this Python (see worker.py)

Selection: ``--suite NAME`` (from suites.toml; default the whole corpus), ``--max-width K``
with ``--width-of tsim|clifft`` (drops circuits wider than K, or with no recorded width),
``--only TEXT`` (substring of the id).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from . import check
from .manifest import ROOT, cases, mask_indices


def add_selection(parser):
    parser.add_argument("--suite", default=None)
    parser.add_argument("--max-width", type=int, default=None)
    parser.add_argument("--width-of", default="tsim")
    parser.add_argument("--only", default=None)


def list_cases(args) -> int:
    for case in cases(args.suite, max_width=args.max_width, width_of=args.width_of, only=args.only):
        masked = len(mask_indices(case))
        print(
            f"{case.id:<90} arXiv:{case.arxiv:<11} k={case.width(args.width_of)!s:>4} "
            f"postselect={case.postselect} ({masked}/{case.num_detectors})"
        )
    return 0


def run(args) -> int:
    errors = 0
    for case in cases(args.suite, max_width=args.max_width, width_of=args.width_of, only=args.only):
        command = [sys.executable, str(ROOT / "tsim_bench" / "worker.py"), "--case", case.id]
        if args.no_postselect:
            command.append("--no-postselect")
        done = subprocess.run(command, capture_output=True, text=True)
        lines = [line for line in done.stdout.splitlines() if line.startswith("RESULT ")]
        if done.returncode or not lines:
            errors += 1
            print(f"ERROR {case.id}: {(done.stderr.strip().splitlines() or ['?'])[-1][:200]}")
            continue
        result = json.loads(lines[-1][len("RESULT ") :])
        print(
            f"{case.id:<90} k={result['active_width']!s:>3} {result['shots_per_s']:>12.4g} shots/s "
            f"acceptance={result['acceptance']:.3g}",
            flush=True,
        )
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m tsim_bench")
    commands = parser.add_subparsers(dest="command", required=True)
    add_selection(commands.add_parser("list"))
    checking = commands.add_parser("check")
    checking.add_argument("--suite", default=None)
    checking.add_argument("--only", default=None)
    checking.add_argument("--max-width", type=int, default=20)
    checking.add_argument("--shots", type=int, default=1024)
    running = commands.add_parser("run")
    add_selection(running)
    running.add_argument("--no-postselect", action="store_true")
    args = parser.parse_args()
    return {"list": list_cases, "check": check.main, "run": run}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())

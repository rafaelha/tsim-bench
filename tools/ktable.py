"""Print a markdown table of k_max results from k_max.json files.

Usage: uv run python tools/ktable.py papers/<folder>/k_max.json [...]
"""

import json
import re
import pathlib
import sys


def cell(r, key):
    if r.get(f"{key}_k") is not None:
        return str(r[f"{key}_k"])
    error = r.get(f"{key}_error", "")
    if "timeout" in error:
        return "timeout"
    overflow = re.search(r"active width would reach (\d+)", error)
    if overflow:
        return f"≥{overflow.group(1)} (overflow)"
    return "error"


print("| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |")
print("|---|---|---|---|---|")
for path in sys.argv[1:]:
    for r in json.loads(pathlib.Path(path).read_text()):
        gates = ", ".join(f"{n} {g}" for g, n in r["non_clifford_gates"].items()) or "none"
        name = pathlib.Path(r["file"]).name
        print(f"| `{name}` | {gates} | {cell(r, 'tsim')} | {cell(r, 'clifft')} | {cell(r, 'clifft_noschedule')} |")

"""Measure the peak active width k_max of Stim circuits in Tsim and Clifft.

Tsim: ``compile_detector_sampler()`` with its default strategy
(``active_statevector``); k is the largest statevector component width (0 if
the circuit has no statevector component).

Clifft: ``clifft.compile`` with ``default_hir_pass_manager()`` plus
``ActiveWidthSchedulePass()`` (default settings); k is ``peak_active_width``.
The width without the scheduler is reported as ``clifft_k_noschedule``.

Each measurement runs in a child process with a timeout.

Usage:
    uv run python tools/measure_k.py FILE.stim [FILE.stim ...] [--timeout S] [--json OUT]
"""

import argparse
import json
import multiprocessing as mp
import sys
import time
import traceback
from pathlib import Path


def _tsim(text):
    import tsim

    sampler = tsim.Circuit(text).compile_detector_sampler()
    widths = [c.width for c in sampler._program.components if hasattr(c, "width")]
    return max(widths, default=0)


def _clifft(text, schedule):
    import clifft

    pm = clifft.default_hir_pass_manager()
    if schedule:
        pm.add(clifft.ActiveWidthSchedulePass())
    return int(clifft.compile(text, hir_passes=pm).peak_active_width)


def _worker(kind, text, queue):
    t0 = time.perf_counter()
    try:
        if kind == "tsim":
            k = _tsim(text)
        else:
            k = _clifft(text, schedule=(kind == "clifft"))
        queue.put({"k": k, "seconds": time.perf_counter() - t0})
    except Exception as error:  # noqa: BLE001
        queue.put({"error": f"{type(error).__name__}: {error}"[:500],
                   "trace": traceback.format_exc()[-1500:]})


def run(kind, text, timeout):
    queue = mp.Queue()
    proc = mp.Process(target=_worker, args=(kind, text, queue))
    proc.start()
    proc.join(timeout)
    if proc.is_alive():
        proc.kill()
        proc.join()
        return {"error": f"timeout after {timeout}s"}
    if queue.empty():
        return {"error": f"process died (exit code {proc.exitcode})"}
    return queue.get()


NON_CLIFFORD_ARITY = {"T": 1, "T_DAG": 1, "R_X": 1, "R_Y": 1, "R_Z": 1, "U3": 1,
                      "CCZ": 3, "CCX": 3, "R_XX": 2, "R_YY": 2, "R_ZZ": 2}


def gate_counts(text):
    """Count non-Clifford gate applications (REPEAT bodies counted once)."""
    import collections

    counts = collections.Counter()
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        name = line.split("(")[0].split()[0]
        if name in NON_CLIFFORD_ARITY:
            targets = line.split(")")[-1].split() if "(" in line else line.split()[1:]
            counts[name] += len(targets) // NON_CLIFFORD_ARITY[name]
    return dict(counts)


def measure(path, timeout):
    text = Path(path).read_text()
    result = {"file": str(path), "non_clifford_gates": gate_counts(text)}
    for kind, key in (("tsim", "tsim"), ("clifft", "clifft"),
                      ("clifft_noschedule", "clifft_noschedule")):
        r = run(kind, text, timeout)
        result[f"{key}_k"] = r.get("k")
        if "seconds" in r:
            result[f"{key}_seconds"] = round(r["seconds"], 2)
        if "error" in r:
            result[f"{key}_error"] = r["error"]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--json", default=None)
    args = parser.parse_args()
    results = []
    for path in args.files:
        r = measure(path, args.timeout)
        results.append(r)
        print(json.dumps(r), flush=True)
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    mp.set_start_method("spawn")
    sys.exit(main())

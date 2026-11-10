"""Time one corpus circuit in a fresh process and print ``RESULT <json>``.

Run by path, or with ``-m``, from the Python environment of the Tsim under test (Tsim 1.1 or
later): it uses only the standard library, numpy, Tsim's public API and this package.

    python -m tsim_bench.worker --case <id> [--no-postselect] [--sampler detector|measurement]
                                [--mode bench|prime|inspect|profile] [--bit-packed]
    python -m tsim_bench.worker --circuit FILE.stim [--postselect all|none]
    python -m tsim_bench.worker --mode width --case ID [--case ID ...] [--circuit FILE ...]

A case uses the sampler its manifest records unless ``--sampler`` names one; a measurement
sampler of a postselected case samples every shot (the mask is of detectors). The result says
which device sampled (``sampler.stats.device`` where Tsim has it, else ``cpu``), the output
format and the numba thread count, since each changes the rate severalfold.

``serve`` compiles and warms up once, then times calls on request (``serve``), so that a
comparison's rounds share one process per side.

``width`` compiles each circuit, samples nothing, and prints ``START <name>`` then
``RESULT <json>`` for each, in one process; the caller enforces time limits. A circuit that Tsim refuses as too wide reports
the width in the error as a lower bound (``"refused": true``).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

if __package__ in (None, ""):  # run by path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tsim_bench.manifest import load, mask_indices  # noqa: E402


def phase_import():
    """Import Tsim (a named frame, so profiles can tell the phases apart)."""
    import tsim

    return tsim


def phase_compile(tsim, path, kind, args):
    """Parse the circuit and compile the sampler."""
    circuit = tsim.Circuit.from_file(str(path))
    if kind == "auto":
        kind = "detector" if circuit.num_detectors + circuit.num_observables else "measurement"
    kwargs = {"seed": args.seed}
    if args.strategy:
        kwargs["strategy"] = args.strategy
    if kind == "detector":
        sampler = circuit.compile_detector_sampler(**kwargs)
    else:
        sampler = circuit.compile_sampler(**kwargs)
    return circuit, kind, sampler


def make_sample(kind, sampler, mask, references, args):
    """Return ``sample(shots) -> rows returned`` with the requested options."""
    kwargs = {}
    if args.batch_size:
        kwargs["batch_size"] = args.batch_size
    if args.bit_packed:
        kwargs["bit_packed"] = True
    if kind == "detector":
        kwargs["append_observables"] = True
        detector_ref, observable_ref = references
        if detector_ref:
            kwargs["use_detector_reference_sample"] = True
        if observable_ref:
            kwargs["use_observable_reference_sample"] = True
    if mask is not None:
        if kind != "detector":
            raise ValueError("postselection needs the detector sampler")
        kwargs["postselection_mask"] = mask

    def sample(shots):
        return len(sampler.sample(shots, **kwargs))

    return sample


REFUSED = re.compile(r"needs (\d+) active qubits")


def widths(tsim, items, args) -> None:
    """Compile each ``(name, path, sampler)`` and print its active width; sample nothing."""
    for name, path, kind in items:
        print(f"START {name}", flush=True)
        result = {"name": name}
        start = time.perf_counter()
        try:
            circuit, kind, sampler = phase_compile(tsim, path, kind, args)
            result.update(width=sampler.active_width, sampler=kind)
            result["components"] = len(sampler.stats.component_widths)
        except Exception as error:  # noqa: BLE001
            refused = REFUSED.search(str(error))
            if refused:
                result.update(width=int(refused.group(1)), refused=True)
            else:
                result["error"] = f"{type(error).__name__}: {error}"[:300]
        result["compile_s"] = time.perf_counter() - start
        print("RESULT " + json.dumps(result), flush=True)


def phase_sample(sample, shots, seconds):
    """Sample repeatedly for about ``seconds`` (the phase that profiles look at)."""
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        sample(shots)


def calibrate(sample, min_seconds, max_shots):
    """Find a shot count and a number of calls that together take ``min_seconds``.

    The shot count grows until one call is long enough, up to ``max_shots``, which bounds the
    size of the returned array; faster circuits are timed over several calls instead.
    """
    shots = 16
    while True:
        start = time.perf_counter()
        sample(shots)
        elapsed = time.perf_counter() - start
        if elapsed >= min_seconds:
            return shots, 1
        if shots >= max_shots:
            return shots, max(1, round(min_seconds / max(elapsed, 1e-6)))
        grow = min(16.0, max(2.0, 1.2 * min_seconds / max(elapsed, 1e-6)))
        shots = min(max_shots, int(shots * grow))


def main(argv=None):
    """Run the requested mode and print ``RESULT <json>``."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", default=[], help="corpus circuit id")
    parser.add_argument("--circuit", action="append", default=[], help="a .stim file")
    parser.add_argument("--root", default=None, help="tsim-bench checkout (default: this one)")
    parser.add_argument("--mode", default="bench", choices=["bench", "prime", "inspect", "profile", "width", "serve"])
    parser.add_argument(
        "--sampler", default="auto", help="detector, measurement, or auto (a case: its manifest's)"
    )
    parser.add_argument("--postselect", default="none", choices=["all", "none"], help="for --circuit only")
    parser.add_argument("--no-postselect", action="store_true", help="ignore the recorded mask")
    parser.add_argument("--strategy", default="")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--bit-packed", action="store_true")
    parser.add_argument("--min-seconds", type=float, default=0.5)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)
    corpus = None
    if args.case:
        corpus = load(Path(args.root)) if args.root else load()

    if args.mode == "width":
        items = [(c, corpus[c].path, corpus[c].sampler) for c in args.case]
        items += [(f, Path(f), args.sampler) for f in args.circuit]
        widths(phase_import(), items, args)
        return
    if len(args.case) + len(args.circuit) != 1:
        parser.error("give exactly one --case or --circuit")
    args.case = args.case[0] if args.case else None
    args.circuit = args.circuit[0] if args.circuit else None

    import numpy as np

    references = (False, False)
    if args.case:
        case = corpus[args.case]
        path, kind = case.path, case.sampler
        if args.sampler != "auto":
            kind = args.sampler
        indices = [] if args.no_postselect or kind != "detector" else mask_indices(case)
        if kind == "detector":
            references = (case.detector_reference, case.observable_reference)
    else:
        path, kind, indices = Path(args.circuit), args.sampler, None

    start = time.perf_counter()
    tsim = phase_import()
    imported = time.perf_counter()
    circuit, kind, sampler = phase_compile(tsim, path, kind, args)
    compiled = time.perf_counter()

    if indices is None:  # --circuit
        indices = list(range(circuit.num_detectors)) if args.postselect == "all" else []
    if args.case and circuit.num_detectors != case.num_detectors:
        raise ValueError(f"{case.id}: {circuit.num_detectors} detectors, manifest says {case.num_detectors}")
    mask = None
    if indices:
        mask = np.zeros(circuit.num_detectors, dtype=np.bool_)
        mask[indices] = True

    import numba

    result = {
        "tsim_version": getattr(tsim, "__version__", "?"),
        "sampler": kind,
        "device": getattr(sampler.stats, "device", "cpu"),
        "bit_packed": args.bit_packed,
        "threads": numba.get_num_threads(),
        "postselected_detectors": len(indices),
        "import_s": imported - start,
        "compile_s": compiled - imported,
        "active_width": sampler.active_width,
        "qubits": circuit.num_qubits,
        "detectors": circuit.num_detectors,
        "measurements": circuit.num_measurements,
        "tcount": circuit.tcount(),
    }
    if args.mode == "inspect":
        result["stats"] = str(sampler.stats)
        print("RESULT " + json.dumps(result))
        return

    sample = make_sample(kind, sampler, mask, references, args)
    warm = time.perf_counter()
    sample(16)
    result["warmup_s"] = time.perf_counter() - warm
    result["cache_misses"] = cache_misses()
    if args.mode == "prime":
        print("RESULT " + json.dumps(result))
        return

    outputs = circuit.num_detectors + circuit.num_observables
    if kind == "measurement":
        outputs = circuit.num_measurements
    # NOTE: one call returns at most about 256 MB of unpacked samples.
    max_shots = (1 << 28) // max(1, outputs)
    if args.mode == "serve":
        serve(sample, result, max_shots)
        return
    shots, calls = calibrate(sample, args.min_seconds, max_shots)
    if args.mode == "profile":
        phase_sample(sample, shots, args.min_seconds * 10)
        result["shots"] = shots
        print("RESULT " + json.dumps(result))
        return

    result.update(timed(sample, shots, calls, args.repeats))
    print("RESULT " + json.dumps(result))


def cache_misses() -> int:
    """Return how many of Tsim's numba kernels were compiled here, not loaded from the cache.

    Kernels loaded from numba's on-disk cache have run differently from freshly compiled
    ones, so a timing is valid only once the cache is warm.
    """
    import gc

    from numba.core.dispatcher import Dispatcher

    return sum(
        sum(obj.stats.cache_misses.values())
        for obj in gc.get_objects()
        if isinstance(obj, Dispatcher) and obj.py_func.__module__.startswith("tsim")
    )


def timed(sample, shots, calls, repeats) -> dict:
    """Time ``repeats`` runs of ``calls`` calls of ``shots`` shots; keep the fastest."""
    times, kept = [], 0
    for _ in range(repeats):
        start = time.perf_counter()
        for _ in range(calls):
            kept += sample(shots)
        times.append(time.perf_counter() - start)
    total = shots * calls
    # shots_per_s counts requested shots, kept or not; acceptance is the kept fraction.
    return {
        "shots": total,
        "seconds": min(times),
        "shots_per_s": total / min(times),
        "acceptance": kept / (total * repeats),
    }


def serve(sample, result, max_shots) -> None:
    """Answer timing requests on stdin, one per line, after ``READY <json>``.

    ``calibrate SECONDS`` prints ``SHOTS {"shots": n, "calls": c}``, a call size and count
    that together take about SECONDS; ``time SHOTS CALLS REPEATS`` prints
    ``RESULT <json>``: the compile-time fields of ``result`` and the timing. The process
    compiles once, so the rounds of a comparison skip the import and the compile.
    ``cache_misses`` counts the kernels compiled in this process (``READY``: by the warmup).
    """
    print("READY " + json.dumps(result), flush=True)
    for line in sys.stdin:
        words = line.split()
        if not words:
            continue
        if words[0] == "calibrate":
            shots, calls = calibrate(sample, float(words[1]), max_shots)
            print("SHOTS " + json.dumps({"shots": shots, "calls": calls}), flush=True)
        elif words[0] == "time":
            shots, calls, repeats = (int(w) for w in words[1:4])
            timing = timed(sample, shots, calls, repeats)
            print("RESULT " + json.dumps({**result, **timing, "cache_misses": cache_misses()}), flush=True)
        else:
            print(f"ERROR unknown request {words[0]!r}", flush=True)


if __name__ == "__main__":
    main()

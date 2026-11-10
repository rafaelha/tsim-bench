"""Time one corpus circuit in a fresh process and print ``RESULT <json>``.

Run by path, or with ``-m``, from the Python environment of the Tsim under test, which may be an
older Tsim: it uses only the standard library, numpy, Tsim's public API and this package.

    python -m tsim_bench.worker --case <id> [--no-postselect] [--mode bench|prime|inspect|profile]
    python -m tsim_bench.worker --circuit FILE.stim [--postselect all|none]
"""

from __future__ import annotations

import argparse
import json
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
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--case", help="corpus circuit id")
    source.add_argument("--circuit", help="a .stim file outside the corpus")
    parser.add_argument("--root", default=None, help="tsim-bench checkout (default: this one)")
    parser.add_argument("--mode", default="bench", choices=["bench", "prime", "inspect", "profile"])
    parser.add_argument("--sampler", default="auto", help="for --circuit only")
    parser.add_argument("--postselect", default="none", choices=["all", "none"], help="for --circuit only")
    parser.add_argument("--no-postselect", action="store_true", help="ignore the recorded mask")
    parser.add_argument("--strategy", default="")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=0)
    parser.add_argument("--bit-packed", action="store_true")
    parser.add_argument("--min-seconds", type=float, default=0.5)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args(argv)

    import numpy as np

    references = (False, False)
    if args.case:
        root = Path(args.root) if args.root else None
        case = (load(root) if root else load())[args.case]
        path, kind = case.path, case.sampler
        indices = [] if args.no_postselect else mask_indices(case)
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

    result = {
        "tsim_version": getattr(tsim, "__version__", "?"),
        "sampler": kind,
        "postselected_detectors": len(indices),
        "import_s": imported - start,
        "compile_s": compiled - imported,
        "active_width": getattr(sampler, "active_width", None),
        "qubits": circuit.num_qubits,
        "detectors": circuit.num_detectors,
        "measurements": circuit.num_measurements,
        "tcount": circuit.tcount(),
    }
    if args.mode == "inspect":
        result["stats"] = str(getattr(sampler, "stats", ""))
        print("RESULT " + json.dumps(result))
        return

    sample = make_sample(kind, sampler, mask, references, args)
    warm = time.perf_counter()
    sample(16)
    result["warmup_s"] = time.perf_counter() - warm
    if args.mode == "prime":
        print("RESULT " + json.dumps(result))
        return

    outputs = circuit.num_detectors + circuit.num_observables
    if kind == "measurement":
        outputs = circuit.num_measurements
    # NOTE: one call returns at most about 256 MB of unpacked samples.
    shots, calls = calibrate(sample, args.min_seconds, (1 << 28) // max(1, outputs))
    if args.mode == "profile":
        phase_sample(sample, shots, args.min_seconds * 10)
        result["shots"] = shots
        print("RESULT " + json.dumps(result))
        return

    times, kept = [], 0
    for _ in range(args.repeats):
        start = time.perf_counter()
        for _ in range(calls):
            kept += sample(shots)
        times.append(time.perf_counter() - start)
    total = shots * calls
    # shots_per_s counts requested shots, kept or not; acceptance is the kept fraction.
    result.update(
        shots=total,
        seconds=min(times),
        shots_per_s=total / min(times),
        acceptance=kept / (total * args.repeats),
    )
    print("RESULT " + json.dumps(result))


if __name__ == "__main__":
    main()

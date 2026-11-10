"""Check the manifests: files, detector counts, and that each mask keeps noiseless shots.

    python -m tsim_bench check [--max-width 20] [--only TEXT] [--shots 1024]

For every circuit: the file exists and has ``num_detectors`` detectors. For circuits whose
recorded Tsim width is at most ``--max-width``, the noiseless circuit is sampled with the
manifest's reference flags, and no postselected detector may ever fire. A detector that fires
without noise would discard error-free shots. Needs Tsim and numpy.
"""

from __future__ import annotations

import numpy as np

from .manifest import Case, cases, mask_indices, parse_ranges


def check_case(case: Case, shots: int, max_width: int) -> tuple[str, str]:
    """Return ``(status, detail)``: status is "ok", "skip" (too wide to sample) or "FAIL"."""
    import tsim

    if not case.path.exists():
        return "FAIL", f"missing file {case.path}"
    circuit = tsim.Circuit.from_file(str(case.path))
    if circuit.num_detectors != case.num_detectors:
        return "FAIL", f"{circuit.num_detectors} detectors, manifest says {case.num_detectors}"
    indices = mask_indices(case)
    if case.postselect != "none" and case.sampler != "detector":
        return "FAIL", "postselection needs the detector sampler"
    width = case.width("tsim")
    if not indices:
        return "ok", "no mask"
    if width is None or width > max_width:
        return "skip", f"width {width}: mask of {len(indices)} not sampled"
    quiet = circuit.without_noise().compile_detector_sampler(seed=0)
    dets = quiet.sample(
        shots,
        use_detector_reference_sample=case.detector_reference,
        use_observable_reference_sample=case.observable_reference,
    )
    random = set(parse_ranges(case.random_detectors))
    if not random <= set(indices):
        return "FAIL", "random_detectors must be masked detectors"
    quiet_ones = [i for i in indices if i not in random]
    fired = np.flatnonzero(dets[:, quiet_ones].any(axis=0))
    if fired.size:
        shown = [quiet_ones[i] for i in fired[:10]]
        return "FAIL", f"{fired.size} masked detectors fire without noise, e.g. {shown}"
    means = dets[:, sorted(random)].mean(axis=0) if random else np.array([])
    fixed = [i for i, m in zip(sorted(random), means) if m in (0.0, 1.0)]
    if fixed:
        return "FAIL", f"random_detectors {fixed[:10]} are deterministic without noise"
    kept = int((~dets[:, indices].any(axis=1)).sum())
    detail = f"mask of {len(indices)}/{case.num_detectors}, {kept}/{shots} noiseless shots kept"
    if random:
        detail += f" ({len(random)} detectors random by design)"
    return "ok", detail


def main(args) -> int:
    failures = 0
    for case in cases(args.suite, only=args.only):
        try:
            status, detail = check_case(case, args.shots, args.max_width)
        except Exception as error:  # noqa: BLE001
            status, detail = "FAIL", f"{type(error).__name__}: {error}"[:300]
        failures += status == "FAIL"
        print(f"{status:<4} {case.id}: {detail}", flush=True)
    print(f"SUMMARY: {failures} failed")
    return 1 if failures else 0

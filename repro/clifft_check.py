"""Independent check of selected non-Clifford points with Clifft (CPU), run in ``.venvs/clifft``.

    .venvs/clifft/bin/python repro/clifft_check.py [--shots 4e7]

Clifft (unitaryfoundation, exact near-Clifford simulator) samples the same circuit files; results go
to ``repro/results_clifft/<study>/<point>.json`` and are quoted in the captions (e.g. the Wan study,
where the paper's post-selection rate differs from the GPU kernel's). ``run_all`` calls this after
sampling. The points are listed in ``POINTS``; the postselection rule is every detector (relative to
the noiseless reference, which is all zeros for these circuits).
"""

import argparse
import json
import pathlib
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
POINTS = [("wan_few_clifford_terms", "d3_p0.001_t"), ("wan_few_clifford_terms", "d3_p0.001_s"),
          ("wan_few_clifford_terms", "d3_p0.0005_t"), ("wan_few_clifford_terms", "d3_p0.0005_s")]


def main():
    import clifft

    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", type=float, default=4e7)
    ap.add_argument("--threads", type=int, default=16)
    args = ap.parse_args()
    for study, point in POINTS:
        out = ROOT / "repro" / "results_clifft" / study / f"{point}.json"
        circ = ROOT / "repro" / "circuits" / study / f"{point}.stim"
        if out.exists() or not circ.exists():
            continue
        pm = clifft.default_hir_pass_manager()
        pm.add(clifft.ActiveWidthSchedulePass())
        prog = clifft.compile(circ.read_text(), hir_passes=pm)
        kept = errors = tot = 0
        t0 = time.perf_counter()
        while tot < args.shots:
            r = clifft.sample(prog, 1_000_000, threads=args.threads)
            d = np.asarray(r.detectors).astype(bool)
            o = np.asarray(r.observables).astype(bool)
            keep = ~d.any(1)
            kept += int(keep.sum())
            errors += int(o[keep].any(1).sum()) if o.size else 0
            tot += len(d)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dict(study=study, point=point, shots=tot, kept=kept, errors=errors,
                                       seconds=round(time.perf_counter() - t0, 1), clifft=clifft.__version__)))
        print(f"{study}/{point}: acceptance {kept / tot:.6f} ({tot:.3g} shots)", flush=True)


def load(study):
    d = ROOT / "repro" / "results_clifft" / study
    return {f.stem: json.loads(f.read_text()) for f in d.glob("*.json")} if d.exists() else {}


if __name__ == "__main__":
    main()

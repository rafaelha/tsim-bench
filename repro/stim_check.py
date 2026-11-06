"""Cross-check the GPU kernel against Stim on every Clifford-proxy point (CPU, independent of Tsim).

    uv run python -m repro.stim_check [--shots 1e9] [--jobs 8] [--only study ...]

For each sampled point with ``variant == "clifford"`` (the circuit is Clifford, so Stim can sample
it), draws ``--shots`` shots with Stim's detector sampler, applies the same postselection and error
rule, and writes ``results_stim/<study>/<point>.json``. ``make_report`` puts GPU-vs-Stim z-scores for
acceptance and LER in the report. Stim reports detectors and observables relative to a noiseless
reference, which equals the GPU worker's reference handling for every Clifford point here.
"""

import argparse
import concurrent.futures as cf
import json
import time

from repro import common

OUT = common.REPRO / "results_stim"
CHUNK_BYTES = 1 << 28  # 256 MB of detector data per sample() call and job


def run(study, point, circuit, postselect, shots, seed):
    import numpy as np
    import stim

    c = stim.Circuit(common.circuit_path(study, circuit).read_text())
    nd, no = c.num_detectors, c.num_observables
    s = c.compile_detector_sampler(seed=seed)
    mask = np.zeros(nd, bool)
    if postselect == "all":
        mask[:] = True
    elif isinstance(postselect, list):
        mask[postselect] = True
    kept = errors = done = 0
    t0 = time.perf_counter()
    # Bounded memory per job: the detector array is shots x detectors bytes (bool), plus the masked copy.
    chunk = int(max(10_000, min(10_000_000, CHUNK_BYTES // max(1, nd + no))))
    while done < shots:
        n = int(min(chunk, shots - done))
        det, obs = s.sample(n, separate_observables=True)
        keep = ~(det[:, mask].any(1))
        kept += int(keep.sum())
        errors += int(obs[keep].any(1).sum()) if no else 0
        done += n
    out = dict(study=study, point=point, shots=done, kept=kept, errors=errors, seconds=round(time.perf_counter() - t0, 1),
               stim=stim.__version__)
    path = OUT / study / f"{point}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", type=float, default=1e9)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()
    todo = []
    for st in args.only or common.STUDY_ORDER:
        try:
            mod = common.study_module(st)
        except ModuleNotFoundError:
            continue
        pts = {p.name: p for p in mod.points()}
        for name, r in common.load_results(st).items():
            p = pts.get(name)
            if p is None or p.variant != "clifford" or p.mode != "ler":
                continue
            if (OUT / st / f"{name}.json").exists():
                continue
            todo.append((st, name, p.circuit, p.postselect, args.shots, hash(name) & 0xFFFF))
    print(f"{len(todo)} Clifford points to cross-check with Stim", flush=True)
    with cf.ProcessPoolExecutor(args.jobs) as ex:
        for out in ex.map(run, *zip(*todo)) if todo else []:
            print(f"  {out['study']}/{out['point']}: acc {out['kept'] / out['shots']:.5f}, {out['errors']} errors ({out['seconds']} s)", flush=True)


def load(study):
    d = OUT / study
    return {f.stem: json.loads(f.read_text()) for f in d.glob("*.json")} if d.exists() else {}


if __name__ == "__main__":
    main()

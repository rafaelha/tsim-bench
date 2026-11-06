r"""Generate all circuits, sample all study points on the GPU, and rebuild the report.

    uv run python -m repro.run_all                      # everything, cheap points first
    uv run python -m repro.run_all --tier 1             # only cheap points (tier <= 1)
    uv run python -m repro.run_all --only soft_d5 gidney_cultivation
    uv run python -m repro.run_all --circuits-only      # just (re)generate circuits
    uv run python -m repro.run_all --regenerate         # regenerate circuits even if cached
    uv run python -m repro.run_all --fresh              # discard earlier results of the selected points
    uv run python -m repro.run_all --max-hours 20       # stop starting new points after this much wall time
    uv run python -m repro.run_all --scale 0.1          # scale every point's budget (quick smoke test)

Points run one at a time, each in its own process (``repro/gpu_worker.py`` in ``.venvs/tsim-gpu``)
inside a systemd scope with a hard memory cap. Results accumulate in ``repro/results/<study>/``:
re-running continues a point until its stopping rule (errors / shots / GPU seconds) is met, so
raising a budget in a study file and re-running only samples the difference. A changed circuit or
Tsim build restarts the point (the old result is kept as ``*.stale-*.json``).

After sampling, the CPU cross-checks run (``repro/stim_check.py`` on every Clifford point, ``repro/clifft_check.py``
on selected non-Clifford points; skip with ``--no-crosscheck``), and ``repro.make_report`` rebuilds figures and the
PDF (skip with ``--no-report``). Published inputs are fetched by ``repro/data_sources.py`` (pinned URLs, sha256).
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
import time

from repro import common

MEMORY_MAX = os.environ.get("REPRO_MEMORY_MAX", "24G")
LOG = common.RESULTS / "run_log.jsonl"


def log(entry):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    entry["time"] = datetime.datetime.now().isoformat(timespec="seconds")
    with LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def generate(study, mod, regenerate):
    makers = mod.circuits()
    d = common.CIRCUITS / study
    d.mkdir(parents=True, exist_ok=True)
    for name, make in makers.items():
        path = common.circuit_path(study, name)
        if path.exists() and not regenerate:
            continue
        t0 = time.perf_counter()
        text = make()
        path.write_text(text.rstrip() + "\n")
        print(f"  circuit {study}/{name} ({time.perf_counter() - t0:.1f} s)", flush=True)


def capped(cmd):
    """``cmd`` inside a systemd user scope with the memory cap (no swap), so a runaway job is killed alone."""
    return ["systemd-run", "--user", "--scope", "-q", "-p", f"MemoryMax={MEMORY_MAX}", "-p", "MemorySwapMax=0", *cmd]


def run_point(study, pt, scale, fresh):
    out = common.result_path(study, pt.name)
    out.parent.mkdir(parents=True, exist_ok=True)
    if fresh and out.exists():
        out.rename(out.with_name(out.stem + f".stale-{datetime.datetime.now():%Y%m%d-%H%M%S}.json"))
    spec = {
        "study": study, "point": pt.name, "spec_key": pt.spec_key(), "circuit": pt.circuit,
        "circuit_path": str(common.circuit_path(study, pt.circuit)), "result_path": str(out),
        "params": dict(pt.params, variant=pt.variant), "postselect": pt.postselect, "mode": pt.mode,
        "detector_reference": pt.detector_reference, "observable_reference": pt.observable_reference,
        "accept_hint": pt.accept_hint,
        "stop": {"target_errors": pt.target_errors * (scale if scale < 1 else 1), "max_shots": pt.max_shots * scale,
                 "max_seconds": pt.max_seconds * scale},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(spec, f)
    cmd = capped([str(common.GPU_PYTHON), str(common.REPRO / "gpu_worker.py"), f.name])
    t0 = time.perf_counter()
    timeout = pt.max_seconds * scale * 1.3 + 1800
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        status = p.returncode
        tail = (p.stdout.strip().splitlines() or [""])[-1]
        err = "\n".join(l for l in p.stderr.splitlines() if "jaxlib" not in l and "Falling back" not in l)[-1500:]
    except subprocess.TimeoutExpired:
        status, tail, err = "timeout", "", ""
    wall = time.perf_counter() - t0
    log({"study": study, "point": pt.name, "status": status, "wall": round(wall, 1), "stdout": tail, "stderr": err if status else ""})
    print(f"  [{study}] {pt.name}: {tail or status} ({wall:.0f} s wall)" + (f"\n{err}" if status else ""), flush=True)
    os.unlink(f.name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--tier", type=int, default=3)
    ap.add_argument("--min-tier", type=int, default=1)
    ap.add_argument("--variant", choices=["clifford", "t"], default=None)
    ap.add_argument("--points", nargs="*", default=None, help="only points whose name contains one of these strings")
    ap.add_argument("--circuits-only", action="store_true")
    ap.add_argument("--regenerate", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--no-report", action="store_true")
    ap.add_argument("--no-crosscheck", action="store_true", help="skip the Stim / Clifft CPU cross-checks after sampling")
    ap.add_argument("--max-hours", type=float, default=float("inf"))
    ap.add_argument("--scale", type=float, default=1.0)
    args = ap.parse_args()

    studies = args.only or common.STUDY_ORDER
    mods = {}
    for s in studies:
        try:
            mods[s] = common.study_module(s)
        except ModuleNotFoundError as e:
            if e.name and e.name.endswith(s):
                print(f"{s}: no study module yet, skipped", flush=True)
                continue
            raise
    for s, mod in mods.items():
        print(f"circuits: {s}", flush=True)
        generate(s, mod, args.regenerate)
    if args.circuits_only:
        return

    queue = []
    for s, mod in mods.items():
        for pt in mod.points():
            if not (args.min_tier <= pt.tier <= args.tier):
                continue
            if args.variant and pt.variant != args.variant:
                continue
            if args.points and not any(x in pt.name for x in args.points):
                continue
            queue.append((pt.tier, studies.index(s), s, pt))
    queue.sort(key=lambda x: (x[0], x[1]))
    print(f"{len(queue)} points queued", flush=True)
    start = time.perf_counter()
    for tier, _, s, pt in queue:
        if (time.perf_counter() - start) / 3600 > args.max_hours:
            print("max-hours reached; stopping", flush=True)
            break
        run_point(s, pt, args.scale, args.fresh)
    if not args.no_crosscheck:
        # Independent CPU cross-checks (skip points already checked): Stim on every Clifford point, Clifft on selected T points.
        subprocess.run(capped([sys.executable, "-m", "repro.stim_check"] + (["--only", *args.only] if args.only else [])))
        clifft_py = common.ROOT / ".venvs" / "clifft" / "bin" / "python"
        if clifft_py.exists():
            subprocess.run(capped([str(clifft_py), str(common.REPRO / "clifft_check.py")]))
    if not args.no_report:
        subprocess.run(capped([sys.executable, "-m", "repro.make_report"] + (["--only", *args.only] if args.only else [])))


if __name__ == "__main__":
    main()

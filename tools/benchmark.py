"""Throughput and k_max of every circuit in papers/*/stim, and the README table.

Steps (each writes/updates results/benchmark.json; rerunning a step overwrites its fields):

    uv run python tools/benchmark.py setup         # build the two venvs below
    uv run python tools/benchmark.py kmax  [--jobs 8]
    uv run python tools/benchmark.py cpu   [--jobs 8]
    uv run python tools/benchmark.py gpu
    uv run python tools/benchmark.py table         # rewrite the table in README.md
    uv run python tools/benchmark.py all           # everything above

Environments (in .venvs/, git-ignored):
- tsim-cpu: bloqade-tsim==1.0.0 (PyPI) and clifft==0.13.0. Used for k_max and the CPU throughput.
- tsim-gpu: Tsim draft PR #219 (``cuda-statevector-executor``, head a2af975f) with its ``gpu`` extra
  (CuPy for CUDA 13).

k_max: Tsim ``compile_detector_sampler()`` (default ``active_statevector``), largest statevector
component width; Clifft ``default_hir_pass_manager()`` + ``ActiveWidthSchedulePass()`` (default
settings), ``peak_active_width``.

Throughput (tools/bench_worker.py): detector sampler, ``sample(n, append_observables=True,
bit_packed=True)``, no postselection, every shot returned to the host, compilation and warm-up
excluded.
- CPU: one core. ``NUMBA_NUM_THREADS=1`` and the process pinned with ``taskset`` to one physical
  core; with ``--jobs J`` up to J circuits run at once, on distinct physical cores 0..J-1.
  Only circuits with Tsim k_max <= 15.
- GPU: one circuit at a time, only circuits with Tsim k_max <= 11 (the CUDA executor's limit).
  Calls are capped at 2 GiB of output, so for circuits with many detectors the rate is bounded by
  the device-to-host copy. The worker lets the draft's packing kernels use more than 48 KB of shared
  memory (see ``allow_large_shared_memory`` in bench_worker.py); without that, circuits with more than
  ~6000 output columns fail to launch.
"""

import argparse
import concurrent.futures as cf
import json
import os
import pathlib
import queue
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VENVS = ROOT / ".venvs"
RESULTS = ROOT / "results" / "benchmark.json"
WORKER = ROOT / "tools" / "bench_worker.py"
REPO_URL = "https://github.com/rafaelha/tsim-bench/blob/master"
ENVS = {
    "tsim-cpu": ["bloqade-tsim==1.0.0", "clifft==0.13.0"],
    "tsim-gpu": ["bloqade-tsim[gpu] @ git+https://github.com/QuEraComputing/tsim@a2af975f"],
}
CPU_MAX_K, GPU_MAX_K = 15, 11
TIMEOUT = {"kmax": 1800, "cpu": 1200, "gpu": 900}
BEGIN, END = "<!-- benchmark-table:begin -->", "<!-- benchmark-table:end -->"


def setup():
    for name, packages in ENVS.items():
        venv = VENVS / name
        subprocess.run(["uv", "venv", "-q", "--allow-existing", "-p", "3.12", str(venv)], check=True)
        subprocess.run(["uv", "pip", "install", "-q", "-p", str(venv), *packages], check=True)
        print(f"ready: {venv}")


def circuits():
    return sorted(str(p.relative_to(ROOT)) for p in ROOT.glob("papers/*/stim/*.stim"))


def load():
    return json.loads(RESULTS.read_text()) if RESULTS.exists() else {}


def save(results):
    RESULTS.parent.mkdir(exist_ok=True)
    RESULTS.write_text(json.dumps(dict(sorted(results.items())), indent=1) + "\n")


def run_worker(mode, path, core=None):
    venv = "tsim-gpu" if mode == "gpu" else "tsim-cpu"
    cmd = [str(VENVS / venv / "bin" / "python"), str(WORKER), mode, str(ROOT / path)]
    env = dict(os.environ)
    if mode == "cpu":
        env.update(NUMBA_NUM_THREADS="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MKL_NUM_THREADS="1", XLA_FLAGS="--xla_force_host_platform_device_count=1")
        cmd = ["taskset", "-c", str(core), *cmd]
    if mode != "gpu":
        env["CUDA_VISIBLE_DEVICES"] = ""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=TIMEOUT[mode])
    except subprocess.TimeoutExpired:
        return {"error": f"timeout after {TIMEOUT[mode]}s"}
    lines = [l for l in proc.stdout.splitlines() if l.startswith("{")]
    if not lines:
        return {"error": f"exit {proc.returncode}: {proc.stderr.strip()[-400:]}"}
    return json.loads(lines[-1])


def run_step(mode, jobs, only_errors=False):
    results = load()
    paths = circuits()
    if mode in ("cpu", "gpu"):
        limit = CPU_MAX_K if mode == "cpu" else GPU_MAX_K
        todo = []
        for p in paths:
            k = results.get(p, {}).get("tsim", {}).get("k")
            if k is not None and k <= limit:
                todo.append(p)
            else:
                results.setdefault(p, {})[mode] = {"skipped": f"Tsim k_max {k} > {limit}" if k is not None
                                                   else "no Tsim k_max"}
    else:
        todo = paths
    if only_errors:
        todo = [p for p in todo if "error" in results.get(p, {}).get(mode if mode != "kmax" else "tsim", {"error": 1})]
    jobs = 1 if mode == "gpu" else jobs
    cores = queue.Queue()
    for c in range(jobs):
        cores.put(c)

    def task(p):
        core = cores.get()
        try:
            return p, run_worker(mode, p, core)
        finally:
            cores.put(core)

    with cf.ThreadPoolExecutor(jobs) as pool:
        for i, fut in enumerate(cf.as_completed([pool.submit(task, p) for p in todo]), 1):
            p, r = fut.result()
            entry = results.setdefault(p, {})
            if mode == "kmax":
                entry["tsim"], entry["clifft"] = r.get("tsim", r), r.get("clifft", r)
            else:
                entry[mode] = r
            save(results)
            short = {k: v for k, v in r.items() if k in ("tsim", "clifft", "shots_per_s", "error")}
            print(f"[{i}/{len(todo)}] {mode} {p}: {json.dumps(short)}", flush=True)


def rate(r):
    if r is None:
        return "–"
    if "skipped" in r:
        return "–"
    if "error" in r:
        return "error"
    x = r["shots_per_s"]
    for unit, scale in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if x >= scale:
            return f"{x / scale:.3g} {unit}"
    return f"{x:.3g}"


def kcell(r, simulator):
    if r is None:
        return "–"
    if r.get("k") is not None:
        return str(r["k"])
    error = r.get("error", "")
    m = re.search(r"active width would reach (\d+)", error)
    if m:
        return f"≥{m.group(1)} (overflow)"
    m = re.search(r"needs (\d+) active qubits", error)
    if m:
        return f"{m.group(1)} (refused, limit 30)"
    return "timeout" if "timeout" in error else "error"


def table():
    results = load()
    lines = [
        "| arXiv / circuit | Tsim single-core CPU (shots/s) | Tsim GPU (shots/s) | Tsim k_max | Clifft k_max |",
        "|---|---|---|---|---|",
    ]
    for p, r in sorted(results.items()):
        if not (ROOT / p).exists():
            continue
        arxiv = pathlib.Path(p).parts[1].split("_")[0]
        name = pathlib.Path(p).stem
        lines.append(f"| [{arxiv}](https://arxiv.org/abs/{arxiv}) / [`{name}`]({REPO_URL}/{p}) | "
                     f"{rate(r.get('cpu'))} | {rate(r.get('gpu'))} | {kcell(r.get('tsim'), 'tsim')} | "
                     f"{kcell(r.get('clifft'), 'clifft')} |")
    block = "\n".join([BEGIN, *lines, END])
    readme = (ROOT / "README.md").read_text()
    if BEGIN in readme:
        readme = re.sub(re.escape(BEGIN) + ".*?" + re.escape(END), lambda _: block, readme, flags=re.S)
    else:
        raise SystemExit(f"README.md has no {BEGIN} marker")
    (ROOT / "README.md").write_text(readme)
    print(f"wrote table with {len(lines) - 2} rows to README.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["setup", "kmax", "cpu", "gpu", "table", "all"])
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--only-errors", action="store_true", help="rerun only circuits whose last result was an error")
    args = parser.parse_args()
    steps = ["setup", "kmax", "cpu", "gpu", "table"] if args.step == "all" else [args.step]
    for step in steps:
        if step == "setup":
            setup()
        elif step == "table":
            table()
        else:
            run_step(step, args.jobs, args.only_errors)


if __name__ == "__main__":
    sys.exit(main())

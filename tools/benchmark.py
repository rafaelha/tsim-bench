"""Throughput and k_max of every circuit in papers/*/stim, and the README table.

Steps (each writes/updates results/benchmark.json; rerunning a step overwrites its fields):

    uv run python tools/benchmark.py setup         # build the two venvs below
    uv run python tools/benchmark.py kmax  [--jobs 8]
    uv run python tools/benchmark.py cpu   --jobs 1    # throughput: one circuit at a time
    uv run python tools/benchmark.py gpu
    uv run python tools/benchmark.py clifft --jobs 1   # Clifft single-core CPU throughput
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
  core; with ``--jobs J`` up to J circuits run at once, on distinct physical cores 0..J-1. Use
  ``--jobs 1`` for the published numbers: concurrent jobs share memory bandwidth, which halved Tsim's
  rate on d=5 end-to-end cultivation (and slowed Clifft by 1.2x).
  Only circuits with Tsim k_max <= 15.
- Clifft CPU: Clifft 0.13.0, ``compile`` with ``default_hir_pass_manager()`` + ``ActiveWidthSchedulePass()``,
  then ``clifft.sample(program, n, threads=1)`` (returns measurements, detectors and observables as
  byte arrays); pinned like the Tsim CPU runs. Only circuits with Clifft k_max <= 15.
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
    # Tsim PR #270 (sparse error basis): same samples and k as 1.0.0, far less compile memory. Used
    # with --tsim-env tsim-sparse only for circuits that 1.0.0 cannot compile; marked in the tables.
    "tsim-sparse": ["bloqade-tsim @ git+https://github.com/QuEraComputing/tsim@96b86e8b", "clifft==0.13.0"],
}
BUILD_LABEL = {"tsim-sparse": "Tsim PR #270 (96b86e8b)"}
TSIM_ENV = "tsim-cpu"  # set by --tsim-env
CPU_MAX_K, GPU_MAX_K = 15, 11
TIMEOUT = {"kmax": 1800, "cpu": 1200, "gpu": 900, "clifft_cpu": 3600}
# Memory: every worker runs in its own systemd scope with a hard MemoryMax (no swap), so a worker that
# blows up is killed alone instead of exhausting the machine (60 GB). Parallel workers share
# MEMORY_BUDGET_GB; circuits whose file is at least LARGE_BYTES run afterwards, one at a time, with
# the whole budget.
MEMORY_BUDGET_GB = 40
LARGE_BYTES = 2_000_000
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


def run_worker(mode, path, core=None, extra=(), memory_gb=MEMORY_BUDGET_GB):
    tsim_run = mode == "cpu" or (mode == "kmax" and list(extra) == ["tsim"])
    venv = "tsim-gpu" if mode == "gpu" else (TSIM_ENV if tsim_run else "tsim-cpu")
    cmd = [str(VENVS / venv / "bin" / "python"), str(WORKER), mode, str(ROOT / path), *extra]
    env = dict(os.environ)
    if mode in ("cpu", "clifft_cpu"):
        env.update(NUMBA_NUM_THREADS="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MKL_NUM_THREADS="1", XLA_FLAGS="--xla_force_host_platform_device_count=1")
        cmd = ["taskset", "-c", str(core), *cmd]
    if mode != "gpu":
        env["CUDA_VISIBLE_DEVICES"] = ""
    cmd = ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={memory_gb}G",
           "-p", "MemorySwapMax=0", *cmd]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=TIMEOUT[mode])
    except subprocess.TimeoutExpired:
        return {"error": f"timeout after {TIMEOUT[mode]}s"}
    lines = [l for l in proc.stdout.splitlines() if l.startswith("{")]
    if not lines:
        if proc.returncode in (137, -9):
            return {"error": f"out of memory (worker capped at {memory_gb} GB)"}
        return {"error": f"exit {proc.returncode}: {proc.stderr.strip()[-400:]}"}
    return json.loads(lines[-1])


def run_step(mode, jobs, only_errors=False, only=None, sims=("tsim", "clifft")):
    results = load()
    paths = [p for p in circuits() if not only or only in p]
    if mode in ("cpu", "gpu", "clifft_cpu"):
        limit = GPU_MAX_K if mode == "gpu" else CPU_MAX_K
        simulator = "clifft" if mode == "clifft_cpu" else "tsim"
        todo = []
        for p in paths:
            k = results.get(p, {}).get(simulator, {}).get("k")
            if k is not None and k <= limit:
                todo.append(p)
            else:
                results.setdefault(p, {})[mode] = {"skipped": f"{simulator} k_max {k} > {limit}" if k is not None
                                                   else f"no {simulator} k_max"}
    else:
        todo = paths
    if only_errors:
        todo = [p for p in todo if "error" in results.get(p, {}).get(mode if mode != "kmax" else "tsim", {"error": 1})]
    jobs = 1 if mode == "gpu" else jobs
    small = [p for p in todo if (ROOT / p).stat().st_size < LARGE_BYTES]
    large = [p for p in todo if (ROOT / p).stat().st_size >= LARGE_BYTES]
    done = 0

    def record(p, r):
        nonlocal done
        done += 1
        entry = results.setdefault(p, {})
        if mode == "kmax":
            for name in sims:
                entry[name] = r.get(name, r)
        else:
            entry[mode] = r
        save(results)
        short = {k: v for k, v in r.items() if k in ("tsim", "clifft", "shots_per_s", "error")}
        print(f"[{done}/{len(todo)}] {mode} {p}: {json.dumps(short)}", flush=True)

    def measure(p, core, memory_gb):
        if mode == "kmax":  # one process per simulator, so a Clifft timeout keeps Tsim's k
            out = {}
            for name in sims:
                r = run_worker(mode, p, core, [name], memory_gb)
                out[name] = r.get(name, r)  # a timeout or crash comes back without the key
                if name == "tsim" and TSIM_ENV in BUILD_LABEL:
                    out[name]["build"] = BUILD_LABEL[TSIM_ENV]
            return out
        r = run_worker(mode, p, core, memory_gb=memory_gb)
        if mode == "cpu" and TSIM_ENV in BUILD_LABEL:
            r["build"] = BUILD_LABEL[TSIM_ENV]
        return r

    cores = queue.Queue()
    for c in range(jobs):
        cores.put(c)
    per_job_gb = max(4, MEMORY_BUDGET_GB // jobs)

    def task(p):
        core = cores.get()
        try:
            return p, measure(p, core, per_job_gb)
        finally:
            cores.put(core)

    with cf.ThreadPoolExecutor(jobs) as pool:
        for fut in cf.as_completed([pool.submit(task, p) for p in small]):
            record(*fut.result())
    for p in large:  # one at a time, with the whole memory budget
        record(p, measure(p, 0, MEMORY_BUDGET_GB))


def rate(r):
    if r is None:
        return "–"
    if "skipped" in r:
        return "–"
    if "error" in r:
        return failure(r["error"])
    x = r["shots_per_s"]
    mark = "‡" if r.get("build") else ""
    for unit, scale in (("B", 1e9), ("M", 1e6), ("k", 1e3)):
        if x >= scale:
            return f"{x / scale:.3g} {unit}{mark}"
    return f"{x:.3g}{mark}"


def failure(error):
    """Short table label for a failed measurement."""
    if "timeout" in error:
        return "timeout"
    if "out of memory" in error or "MemoryError" in error:
        return "OOM"
    if "do not fit" in error:  # the GPU draft's noise kernel rejects rows this wide
        return "unsupported"
    return "error"


def speedup(cpu, gpu):
    """GPU rate / single-core CPU rate: an integer above 10, one decimal otherwise."""
    if not (cpu and gpu and "shots_per_s" in cpu and "shots_per_s" in gpu):
        return "–"
    x = gpu["shots_per_s"] / cpu["shots_per_s"]
    return f"{x:.0f}x" if x > 10 else f"{x:.1f}x"


def kcell(r, simulator):
    if r is None:
        return "–"
    if r.get("k") is not None:
        return str(r["k"]) + ("‡" if r.get("build") else "")
    error = r.get("error", "")
    m = re.search(r"active width would reach (\d+)", error)
    if m:
        return f"≥{m.group(1)} (overflow)"
    m = re.search(r"needs (\d+) active qubits", error)
    if m:
        return f"{m.group(1)} (refused, limit 30)"
    return failure(error)


def paper_meta(folder):
    """(title, short author list, year) from the first lines of papers/<folder>/README.md."""
    lines = (ROOT / "papers" / folder / "README.md").read_text().splitlines()
    title = lines[0].lstrip("# ").strip()
    byline = " ".join(l.strip() for l in lines[2:6] if l.strip()).split("[arXiv")[0]
    year = re.search(r"(\d{4})\)", byline)
    names = [n.strip() for n in re.split(r",| and ", byline.split(" (")[0]) if n.strip() and n.strip() != "et al."]
    last = [n.split()[-1] for n in names]
    if len(last) == 1:
        authors = last[0]
    elif len(last) == 2 and "et al." not in byline:
        authors = f"{last[0]} and {last[1]}"
    else:
        authors = f"{last[0]} et al."
    return title, authors, year.group(1) if year else ""


def table():
    results = load()
    lines = [
        "| paper / circuit | Tsim single-core CPU (shots/s) | Tsim GPU (shots/s) | GPU speedup | Tsim k_max |",
        "|---|---|---|---|---|",
    ]
    by_folder = {}
    for p, r in sorted(results.items()):
        if (ROOT / p).exists():
            by_folder.setdefault(pathlib.Path(p).parts[1], []).append((p, r))
    for folder, rows in sorted(by_folder.items()):
        arxiv = folder.split("_")[0]
        title, authors, year = paper_meta(folder)
        lines.append(f"| **[{arxiv}](https://arxiv.org/abs/{arxiv})** {authors} ({year}), *{title}* | | | | |")
        for p, r in rows:
            name = pathlib.Path(p).stem
            lines.append(f"| [`{name}`]({REPO_URL}/{p}) | {rate(r.get('cpu'))} | {rate(r.get('gpu'))} | "
                         f"{speedup(r.get('cpu'), r.get('gpu'))} | {kcell(r.get('tsim'), 'tsim')} |")
    block = "\n".join([BEGIN, *lines, END])
    readme = (ROOT / "README.md").read_text()
    if BEGIN in readme:
        readme = re.sub(re.escape(BEGIN) + ".*?" + re.escape(END), lambda _: block, readme, flags=re.S)
    else:
        raise SystemExit(f"README.md has no {BEGIN} marker")
    (ROOT / "README.md").write_text(readme)
    print(f"wrote table with {len(by_folder)} papers to README.md")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["setup", "kmax", "cpu", "gpu", "clifft", "table", "all"])
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--tsim-env", default="tsim-cpu", choices=["tsim-cpu", "tsim-sparse"],
                        help="environment for Tsim k_max and CPU throughput (default: Tsim 1.0.0)")
    parser.add_argument("--sims", default="tsim,clifft", help="kmax: which simulators to measure")
    parser.add_argument("--only", default=None, help="restrict to circuits whose path contains this substring")
    parser.add_argument("--only-errors", action="store_true", help="run only circuits without a result for this step, or whose last result was an error")
    args = parser.parse_args()
    global TSIM_ENV
    TSIM_ENV = args.tsim_env
    steps = ["setup", "kmax", "cpu", "clifft", "gpu", "table"] if args.step == "all" else [args.step]
    for step in steps:
        if step == "setup":
            setup()
        elif step == "table":
            table()
        else:
            run_step("clifft_cpu" if step == "clifft" else step, args.jobs, args.only_errors, args.only,
                     tuple(args.sims.split(",")))


if __name__ == "__main__":
    sys.exit(main())

"""One measurement on one circuit; runs inside a benchmark venv (see tools/benchmark.py).

    python bench_worker.py kmax  FILE.stim     -> {"tsim_k", "clifft_k"} (each may be an error)
    python bench_worker.py cpu   FILE.stim     -> detector-sampler throughput on the CPU executor
    python bench_worker.py gpu   FILE.stim     -> detector-sampler throughput; fails unless the CUDA executor is used

Prints one JSON line. Throughput: ``sampler.sample(n, append_observables=True, bit_packed=True)``
(no postselection, every shot returned), after a warm-up call that triggers JIT/NVRTC compilation.
``n`` doubles until a call takes at least ``--target`` seconds (or hits the output-size cap); then
the best of three calls at that size is reported. Compilation time is reported separately.
"""

import json
import sys
import time


def tsim_k(text):
    import tsim

    sampler = tsim.Circuit(text).compile_detector_sampler()
    return max((c.width for c in sampler._program.components if hasattr(c, "width")), default=0)


def clifft_k(text):
    import clifft

    pm = clifft.default_hir_pass_manager()
    pm.add(clifft.ActiveWidthSchedulePass())
    return int(clifft.compile(text, hir_passes=pm).peak_active_width)


def attempt(fn, *args):
    t0 = time.perf_counter()
    try:
        return {"k": fn(*args), "seconds": round(time.perf_counter() - t0, 2)}
    except Exception as error:  # noqa: BLE001
        return {"error": f"{type(error).__name__}: {error}"[:400]}


def allow_large_shared_memory():
    """Work around a launch failure in the GPU draft (PR #219 at a2af975f).

    For rows of more than ~6000 output columns, ``gather_columns`` needs more than the 48 KB of
    shared memory a kernel gets without opting in, and fails with CUDA_ERROR_INVALID_VALUE. This lets
    the packing kernels use the device maximum (99 KB on the RTX 5090); it changes no results.
    """
    import cupy
    from tsim.statevector.cuda import sampler as cuda_sampler

    limit = cupy.cuda.Device().attributes["MaxSharedMemoryPerBlockOptin"]
    original = cuda_sampler.CudaShotSampler._pack

    def _pack(self, module, *args, **kwargs):
        for name in ("gather_columns", "noise_kept"):
            kernel = getattr(module, name, None)
            if kernel is not None:
                kernel.max_dynamic_shared_size_bytes = limit - kernel.attributes["shared_size_bytes"]
        return original(self, module, *args, **kwargs)

    cuda_sampler.CudaShotSampler._pack = _pack


def throughput(text, mode, target, max_bytes):
    import tsim

    if mode == "gpu":
        allow_large_shared_memory()

    t0 = time.perf_counter()
    sampler = tsim.Circuit(text).compile_detector_sampler()
    compile_s = time.perf_counter() - t0
    backend = type(getattr(sampler, "_shots", None)).__name__
    if mode == "gpu" and backend != "CudaShotSampler":
        raise RuntimeError(f"not on the GPU (shot sampler: {backend})")
    c = tsim.Circuit(text)
    row_bytes = max(1, (c.num_detectors + c.num_observables + 7) // 8)
    cap = max(1024, max_bytes // row_bytes)

    def call(n):
        t = time.perf_counter()
        sampler.sample(n, append_observables=True, bit_packed=True)
        return time.perf_counter() - t

    t0 = time.perf_counter()
    call(1024)  # warm-up (JIT / NVRTC)
    warmup_s = time.perf_counter() - t0
    n = 1024
    while True:
        elapsed = call(n)
        if elapsed >= target or n >= cap:
            break
        n = min(cap, n * 2 if elapsed > target / 64 else n * 16)
    best = min([elapsed] + [call(n) for _ in range(2)])
    return {"shots_per_s": n / best, "shots": n, "seconds": round(best, 4),
            "compile_seconds": round(compile_s, 2), "warmup_seconds": round(warmup_s, 2),
            "backend": backend}


def main():
    mode, path = sys.argv[1], sys.argv[2]
    text = open(path).read()
    if mode == "kmax":
        out = {"tsim": attempt(tsim_k, text), "clifft": attempt(clifft_k, text)}
    else:
        target = 1.0 if mode == "cpu" else 0.5
        max_bytes = (1 << 28) if mode == "cpu" else (1 << 31)
        out = attempt(lambda: throughput(text, mode, target, max_bytes))
        out = out.get("k", out)
    import tsim

    out["tsim_version"] = getattr(tsim, "__version__", "?")
    print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main()

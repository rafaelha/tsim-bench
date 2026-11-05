r"""Sample one study point on the GPU and append the result to its JSON file.

Runs inside the Tsim GPU venv (``.venvs/tsim-gpu``, see ``repro/setup.sh``); ``repro/run_all.py``
calls it as ``python gpu_worker.py SPEC.json``. The spec is one point of a study (see
``repro/common.py``): a circuit file, a postselection rule, and stopping rules.

Every accepted shot is classified on the host from the bit-packed rows that Tsim returns (Tsim
postselects on the device with ``postselection_mask``, so only accepted rows are copied):

- ``kept``: shots that pass postselection;
- ``errors``: kept shots in which any observable differs from its reference value (``mode="ler"``);
- ``obs_ones``: per observable, the kept shots in which it reads 1 (used for tomography).

The point's result file accumulates *segments*, one per invocation. A new segment continues an
earlier result only if the circuit file (sha256) and the Tsim build are unchanged; otherwise the
old file is moved aside and sampling starts over. Each segment uses a fresh seed. Progress is
written every ``SAVE_EVERY`` seconds, so an interrupted run loses at most that much work.
"""

import datetime
import hashlib
import json
import pathlib
import socket
import sys
import time

import numpy as np

SAVE_EVERY = 60.0
TARGET_CALL_SECONDS = 4.0
MAX_ROW_BYTES = 1 << 30  # host memory for the kept rows of one call


def tsim_build():
    import importlib.metadata as md

    dist = md.distribution("bloqade-tsim")
    url = dist.read_text("direct_url.json")
    commit = json.loads(url).get("vcs_info", {}).get("commit_id") if url else None
    return {"version": dist.version, "commit": commit}


def gpu_name():
    try:
        import cupy

        return cupy.cuda.runtime.getDeviceProperties(0)["name"].decode()
    except Exception:  # noqa: BLE001
        return None


def allow_large_shared_memory():
    """Let the draft's packing kernels opt into the device's shared-memory maximum.

    Without this, circuits with more than ~6000 output columns fail to launch on the Tsim GPU
    draft (PR #219); it changes no results. See tools/bench_worker.py.
    """
    try:
        import cupy
        from tsim.statevector.cuda import sampler as cuda_sampler
    except ImportError:
        return
    limit = cupy.cuda.Device().attributes["MaxSharedMemoryPerBlockOptin"]
    original = cuda_sampler.CudaShotSampler._pack

    def _pack(self, module, *args, **kwargs):
        for name in ("gather_columns", "noise_kept"):
            kernel = getattr(module, name, None)
            if kernel is not None:
                kernel.max_dynamic_shared_size_bytes = limit - kernel.attributes["shared_size_bytes"]
        return original(self, module, *args, **kwargs)

    cuda_sampler.CudaShotSampler._pack = _pack


def totals(result):
    keys = ("shots", "kept", "errors", "seconds", "compile_seconds")
    out = {k: sum(s[k] for s in result["segments"]) for k in keys}
    nobs = len(result["segments"][0]["obs_ones"]) if result["segments"] else 0
    out["obs_ones"] = [sum(s["obs_ones"][i] for s in result["segments"]) for i in range(nobs)]
    return out


def done(spec, tot):
    stop = spec["stop"]
    if tot["shots"] >= stop.get("max_shots", float("inf")):
        return "max_shots"
    if tot["errors"] >= stop.get("target_errors", float("inf")):
        return "target_errors"
    if tot["seconds"] >= stop.get("max_seconds", float("inf")):
        return "max_seconds"
    return None


def main():
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text())
    out = pathlib.Path(spec["result_path"])
    circuit_path = pathlib.Path(spec["circuit_path"])
    text = circuit_path.read_text()
    sha = hashlib.sha256(text.encode()).hexdigest()
    build = tsim_build()

    result = None
    if out.exists():
        old = json.loads(out.read_text())
        if old.get("circuit_sha256") == sha and old.get("tsim") == build and old.get("spec_key") == spec["spec_key"]:
            result = old
        else:
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            out.rename(out.with_name(out.stem + f".stale-{stamp}.json"))
    if result is None:
        result = {"study": spec["study"], "point": spec["point"], "spec_key": spec["spec_key"], "circuit": spec["circuit"],
                  "circuit_sha256": sha, "tsim": build, "params": spec["params"], "segments": []}
    reason = done(spec, totals(result)) if result["segments"] else None
    if reason:
        print(json.dumps({"point": spec["point"], "status": "already done", "reason": reason}))
        return

    allow_large_shared_memory()
    import tsim

    seed = int(hashlib.sha256(f"{spec['study']}/{spec['point']}/{len(result['segments'])}".encode()).hexdigest()[:8], 16)
    t0 = time.perf_counter()
    circuit = tsim.Circuit(text)
    sampler = circuit.compile_detector_sampler(seed=seed)
    nd, no = circuit.num_detectors, circuit.num_observables
    backend = type(getattr(sampler, "_shots", None)).__name__
    post = spec["postselect"]
    mask = np.zeros(nd, bool)
    if post == "all":
        mask[:] = True
    elif isinstance(post, list):
        mask[post] = True
    kw = dict(append_observables=True, bit_packed=True,
              use_detector_reference_sample=spec.get("detector_reference", True),
              use_observable_reference_sample=spec.get("observable_reference", True),
              postselection_mask=mask if mask.any() else None)
    sampler.sample(1 << 12, **kw)  # warm-up / JIT
    compile_seconds = time.perf_counter() - t0

    obs_bytes = [(nd + i) // 8 for i in range(no)]
    obs_bits = [np.uint8(1 << ((nd + i) % 8)) for i in range(no)]
    om = np.zeros((nd + no + 7) // 8, np.uint8)
    for b, m in zip(obs_bytes, obs_bits):
        om[b] |= m
    row_bytes = max(1, (nd + no + 7) // 8)

    seg = {"seed": seed, "shots": 0, "kept": 0, "errors": 0, "obs_ones": [0] * no, "seconds": 0.0,
           "compile_seconds": round(compile_seconds, 2), "backend": backend, "gpu": gpu_name(), "host": socket.gethostname(),
           "started": datetime.datetime.now().isoformat(timespec="seconds"), "finished": None}
    result["segments"].append(seg)
    last_save = time.perf_counter()
    n = 1 << 20
    expected_accept = spec.get("accept_hint", 1.0)

    def save():
        seg["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
        result["totals"] = totals(result)
        tmp = out.with_suffix(".tmp")
        tmp.write_text(json.dumps(result, indent=1))
        tmp.replace(out)

    while True:
        tot = totals(result)
        reason = done(spec, tot)
        if reason:
            break
        stop = spec["stop"]
        n = int(min(n, stop.get("max_shots", 1e18) - tot["shots"]))
        n = max(n, 1)
        tc = time.perf_counter()
        rows = np.asarray(sampler.sample(n, **kw))
        seg["shots"] += n
        nkept = len(rows)
        seg["kept"] += nkept
        if no and nkept:
            # Column-wise: only the bytes that hold observables are touched.
            anyflip = None
            for b in sorted(set(obs_bytes)):
                col = rows[:, b] & om[b]
                anyflip = col if anyflip is None else (anyflip | col)
                for i in range(no):
                    if obs_bytes[i] == b:
                        seg["obs_ones"][i] += int(np.count_nonzero(col & obs_bits[i]))
            seg["errors"] += int(np.count_nonzero(anyflip))
        del rows
        dt = time.perf_counter() - tc  # wall time of the whole iteration (sampling + host counting)
        seg["seconds"] = round(seg["seconds"] + dt, 3)
        accept = max(nkept / n, 1e-6)
        expected_accept = accept
        # Grow the call size toward TARGET_CALL_SECONDS, bounded by host memory for kept rows.
        grow = TARGET_CALL_SECONDS / max(dt, 1e-3)
        n = int(min(n * min(grow, 4.0), MAX_ROW_BYTES / (row_bytes * expected_accept), 2**34))
        if time.perf_counter() - last_save > SAVE_EVERY:
            save()
            last_save = time.perf_counter()
    seg["stop_reason"] = reason
    save()
    t = result["totals"]
    print(json.dumps({"point": spec["point"], "status": "done", "reason": reason, "shots": t["shots"], "kept": t["kept"],
                      "errors": t["errors"], "seconds": t["seconds"]}))


if __name__ == "__main__":
    main()

"""Noiseless sanity checks of non-Clifford circuits with Tsim.

Tsim reports detector *values* (not flips against a reference sample as Stim
does), so a deterministic detector may read 1. ``check`` strips all noise,
samples the circuit, and reports

- how many detectors are random (should be 0 for a protocol whose checks are
  deterministic without noise),
- whether the deterministic values agree with those of a Clifford proxy
  circuit, when one is given,
- the mean of each observable.
"""

import re

import numpy as np

_NOISE = re.compile(
    r"^\s*(DEPOLARIZE1|DEPOLARIZE2|X_ERROR|Y_ERROR|Z_ERROR|PAULI_CHANNEL_1|PAULI_CHANNEL_2|"
    r"E|ELSE_CORRELATED_ERROR|CORRELATED_ERROR|HERALDED_ERASE|HERALDED_PAULI_CHANNEL_1|I_ERROR|II_ERROR)\b"
)
_NOISY_MEASURE = re.compile(r"^(\s*)(M|MX|MY|MZ|MR|MRX|MRY|MRZ|MPP|MXX|MYY|MZZ)\([^)]*\)", re.M)


def strip_noise(text):
    lines = [line for line in text.splitlines() if not _NOISE.match(line)]
    return _NOISY_MEASURE.sub(r"\1\2", "\n".join(lines)) + "\n"


def sample(text, shots=1024, seed=0):
    import tsim

    sampler = tsim.Circuit(strip_noise(text)).compile_detector_sampler(seed=seed)
    det, obs = sampler.sample(shots, separate_observables=True)
    return np.asarray(det, dtype=float).mean(axis=0), np.asarray(obs, dtype=float).mean(axis=0)


def check(text, proxy=None, shots=1024, seed=0):
    det, obs = sample(text, shots, seed)
    result = {
        "random_detectors": int(((det > 0) & (det < 1)).sum()),
        "num_detectors": int(det.size),
        "observable_means": [round(float(x), 4) for x in obs],
    }
    if proxy is not None:
        ref, _ = sample(proxy, shots, seed)
        deterministic = (det == 0) | (det == 1)
        result["matches_proxy"] = bool(np.array_equal(det[deterministic], ref[deterministic]))
    return result

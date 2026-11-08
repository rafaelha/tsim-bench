"""Turn a benchmark circuit into a Magna circuit and task.

Magna evaluates acceptance and error per fault draw instead of returning detector samples, so each
circuit gets one fixed task:
- acceptance: ``POSTSELECT`` on every detector that is deterministic in the noiseless circuit, at its
  noiseless value (Magna, like Tsim, reads a detector as its raw parity);
- error: any logical observable flipped from its noiseless value (``error_observables``; an observable
  whose noiseless value is 1 gets a constant register, ``CONTROL[XOR](1) -> ctrl[j]`` and
  ``OBSERVABLE_INCLUDE(k) ctrl[j]``, so that a fault-free run is correct). Circuits without observables ask for acceptance only.

The noiseless values come from Tsim's detector sampler on ``without_noise()``.
"""

from __future__ import annotations

import re

import numpy as np

# Magna's circuit syntax is Stim's with fewer gates (docs/software/circuit-format.md at e595744).
UNSUPPORTED = re.compile(r"^\s*(R_X|R_Y|R_Z|R_XX|R_YY|R_ZZ|R_PAULI|U3|HERALDED_\w+|SPP\w*|TPP\w*)\b", re.M)


def replace_mpad(text: str) -> str:
    """Magna has no MPAD: measure a fresh qubit prepared in the padded value instead (same record)."""
    if not re.search(r"^\s*MPAD\b", text, re.M):
        return text
    import tsim

    fresh = tsim.Circuit(text).num_qubits
    out = []
    for line in text.splitlines():
        m = re.match(r"^(\s*)MPAD(\([^)]*\))?\s+(.*)$", line)
        if not m:
            out.append(line)
            continue
        for bit in m.group(3).split():
            out.append(f"{m.group(1)}R {fresh}")
            if bit == "1":
                out.append(f"{m.group(1)}X {fresh}")
            out.append(f"{m.group(1)}M {fresh}")
    return "\n".join(out)


def noiseless_values(text: str, shots: int = 64):
    """Per detector and observable: 0/1 if constant over noiseless shots, else None."""
    import tsim

    c = tsim.Circuit(text).without_noise()
    nd, no = c.num_detectors, c.num_observables
    rows = c.compile_detector_sampler(seed=0).sample(shots, append_observables=True)
    const = (rows == rows[0]).all(axis=0)
    vals = [int(rows[0, i]) if const[i] else None for i in range(nd + no)]
    return vals[:nd], vals[nd:]


def build(text: str):
    """Return (magna circuit text, task dict, info) or raise ValueError if Magna can't read it."""
    m = UNSUPPORTED.search(text)
    if m:
        raise ValueError(f"unsupported by Magna: {m.group(1)}")
    text = replace_mpad(text)
    try:
        dets, obs = noiseless_values(text)
        refused = False
    except ValueError as error:  # Tsim refuses circuits above 30 active qubits: no postselection then
        if "active qubits" not in str(error):
            raise
        dets, refused = [None] * text.count("DETECTOR"), True
        obs = [None] * (1 + max((int(x) for x in re.findall(r"OBSERVABLE_INCLUDE\((\d+)\)", text)), default=-1))
    lines = [text.rstrip()]
    flips = [k for k, v in enumerate(obs) if v == 1]
    for j, k in enumerate(flips):  # a constant register 1 makes a fault-free run correct
        lines.append(f"CONTROL[XOR](1) -> ctrl[{j}]")
        lines.append(f"OBSERVABLE_INCLUDE({k}) ctrl[{j}]")
    keep = [f"{'!' if v else ''}det[{i}]" for i, v in enumerate(dets) if v is not None]
    if keep:
        lines.append("POSTSELECT " + " ".join(keep))
    task = {"schema_version": 1}
    if obs:
        task["error_observables"] = list(range(len(obs)))
    else:
        task["outputs"] = []
    info = {"reference_refused": refused, "postselected_detectors": len(keep), "detectors": len(dets), "observables": len(obs),
            "observables_noiseless_one": flips, "nondeterministic_observables": [k for k, v in enumerate(obs) if v is None]}
    return "\n".join(l for l in lines if l), task, info

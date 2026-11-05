r"""Shared definitions for the decoder-free reproduction studies.

A *study* (one module in ``repro/studies``) reproduces one figure or table of one paper. It defines:

- ``META``: arXiv id, paper, which figure/table, a one-paragraph description;
- ``circuits()``: a dict ``name -> zero-argument function returning Stim text``. They run in the
  project environment (``uv run``), usually calling the authors' generator; results are cached in
  ``repro/circuits/<study>/<name>.stim`` and only regenerated with ``--regenerate``;
- ``points()``: the list of ``Point``s to sample, each referring to one circuit;
- ``figures(results)``: makes the study's figures/tables from the sampled results (see
  ``repro/make_report.py``) and returns ``Figure`` records for the LaTeX report.

Two variants of each figure are sampled when the paper ran a Clifford proxy: ``variant="clifford"``
(the authors' proxy, to check that the GPU reproduces their published numbers) and
``variant="t"`` (the real non-Clifford circuit).
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPRO = ROOT / "repro"
PAPERS = ROOT / "papers"
CIRCUITS = REPRO / "circuits"
RESULTS = REPRO / "results"
REPORT = REPRO / "report"
GPU_PYTHON = ROOT / ".venvs" / "tsim-gpu" / "bin" / "python"

STUDY_ORDER = [
    "gidney_cultivation",
    "wan_few_clifford_terms",
    "soft_d5",
    "clifft_inject_cultivate",
    "gauging_cultivation",
    "fold_transversal",
    "chan_flags",
    "magna",
    "google_experiment",
    "star_injection",
    "rp2_ungrown",
    "erasure_injection",
    "vaknin_full_vector",
]


@dataclasses.dataclass
class Point:
    """One circuit sampled until a stopping rule triggers.

    ``postselect``: ``"all"`` (every detector), ``"none"``, or a list of detector indices.
    ``detector_reference``: XOR a noiseless reference sample into detectors before postselecting.
    Use False when some postselected detectors are random by design (e.g. STAR).
    ``observable_reference``: XOR a reference into observables (deterministic observables only;
    False for tomography, where observables are random).
    ``tier``: 1 cheap (< ~2 min), 2 medium (< ~20 min), 3 expensive.
    """

    name: str
    circuit: str
    variant: str  # "clifford" or "t"
    params: dict
    target_errors: int = 1000
    max_shots: float = 1e12
    max_seconds: float = 600.0
    tier: int = 1
    mode: str = "ler"  # "ler" or "tomo"
    postselect: object = "all"
    detector_reference: bool = True
    observable_reference: bool = True
    accept_hint: float = 1.0

    def spec_key(self):
        """Fields that define what is sampled (stopping rules excluded, so budgets can grow)."""
        d = dict(circuit=self.circuit, mode=self.mode, postselect=self.postselect,
                 detector_reference=self.detector_reference, observable_reference=self.observable_reference)
        return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


@dataclasses.dataclass
class Figure:
    """A figure or table for the report. ``path`` is a PDF (figure) or a .tex fragment (table)."""

    key: str
    path: pathlib.Path
    title: str
    caption: str
    budget: str
    kind: str = "figure"


def study_module(name):
    return importlib.import_module(f"repro.studies.{name}")


def circuit_path(study, name):
    return CIRCUITS / study / f"{name}.stim"


def result_path(study, point):
    return RESULTS / study / f"{point}.json"


def load_results(study):
    out = {}
    d = RESULTS / study
    if not d.exists():
        return out
    for f in sorted(d.glob("*.json")):
        if ".stale-" in f.name:
            continue
        r = json.loads(f.read_text())
        if r.get("segments"):
            r.setdefault("totals", {})
            out[r["point"]] = r
    return out


# ---------------------------------------------------------------------------------------------
# Circuit helpers

NOISE_NAMES = ("DEPOLARIZE1", "DEPOLARIZE2", "X_ERROR", "Y_ERROR", "Z_ERROR", "PAULI_CHANNEL_1", "PAULI_CHANNEL_2",
               "E", "ELSE_CORRELATED_ERROR", "CORRELATED_ERROR", "HERALDED_ERASE", "HERALDED_PAULI_CHANNEL_1",
               "I_ERROR", "II_ERROR")
_NOISE_RE = re.compile(r"^\s*(" + "|".join(NOISE_NAMES) + r")\b")
_MEAS_ARG_RE = re.compile(r"^(\s*(?:M|MR|MX|MY|MZ|MRX|MRY|MRZ|MPP|MXX|MYY|MZZ))\([^)]*\)")


def strip_noise(text):
    """Remove noise channels and measurement-flip arguments (for noiseless checks)."""
    return "\n".join(_MEAS_ARG_RE.sub(r"\1", line) for line in text.splitlines() if not _NOISE_RE.match(line))


def replace_gate(text, old, new):
    """Replace a gate name at the start of instruction lines (``S`` -> ``T`` etc.), keeping targets."""
    pat = re.compile(rf"^(\s*){re.escape(old)}(\s)", re.M)
    return pat.sub(rf"\g<1>{new}\g<2>", text)


def s_to_t(text):
    """The blanket d=3 rule: S -> T and S_DAG -> T_DAG."""
    text = replace_gate(text, "S_DAG", "T_DAG__")
    text = replace_gate(text, "S", "T")
    return text.replace("T_DAG__", "T_DAG")


def s_to_z(text):
    text = replace_gate(text, "S_DAG", "Z")
    return replace_gate(text, "S", "Z")


def noiseless_check(text, shots=512, require_deterministic_observables=True):
    """Sample the noiseless circuit with Tsim (CPU, project env).

    Returns (random_detectors, random_observables, reference_row). Raises if anything is random
    that should not be.
    """
    import numpy as np
    import tsim

    s = tsim.Circuit(strip_noise(text)).compile_detector_sampler(seed=1)
    a = np.asarray(s.sample(shots, append_observables=True)).astype(bool)
    c = tsim.Circuit(text)
    nd = c.num_detectors
    rd = int((a[:, :nd] != a[0, :nd]).any(0).sum())
    ro = int((a[:, nd:] != a[0, nd:]).any(0).sum())
    if rd:
        raise ValueError(f"{rd} detectors are random without noise")
    if require_deterministic_observables and ro:
        raise ValueError(f"{ro} observables are random without noise")
    return rd, ro, a[0]


# ---------------------------------------------------------------------------------------------
# Statistics


def binomial_interval(hits, shots, factor=1000.0):
    """Max-likelihood rate and the interval of rates within ``factor`` of the max likelihood (sinter convention)."""
    import sinter

    if shots <= 0:
        return float("nan"), float("nan"), float("nan")
    f = sinter.fit_binomial(num_shots=int(shots), num_hits=int(hits), max_likelihood_factor=factor)
    return f.best, f.low, f.high


def fmt_seconds(s):
    if s < 60:
        return f"{s:.0f} s" if s >= 10 else f"{s:.1f} s"
    if s < 3600:
        return f"{s / 60:.1f} min"
    return f"{s / 3600:.2f} h"


def fmt_count(n):
    if n == 0:
        return "0"
    e = int(math.floor(math.log10(n)))
    m = n / 10**e
    return f"{m:.2g}e{e}" if e >= 4 else f"{int(n)}"


def budget_line(results, points=None, label=None):
    """One-line compute budget: GPU sampling time, compile time, shots, for the given points."""
    rs = [r for k, r in results.items() if points is None or k in points]
    if not rs:
        return "not yet sampled"
    sec = sum(r["totals"]["seconds"] for r in rs)
    comp = sum(r["totals"]["compile_seconds"] for r in rs)
    shots = sum(r["totals"]["shots"] for r in rs)
    gpus = sorted({s.get("gpu") or "?" for r in rs for s in r["segments"]})
    commits = sorted({(r["tsim"].get("commit") or r["tsim"].get("version") or "?")[:8] for r in rs})
    head = f"{label}: " if label else ""
    return (f"{head}{fmt_seconds(sec)} GPU sampling + {fmt_seconds(comp)} compile, {fmt_count(shots)} shots, "
            f"{len(rs)} points ({', '.join(gpus)}, Tsim {', '.join(commits)})")

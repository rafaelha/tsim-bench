r"""Sahay et al. (2025), arXiv:2509.05212 -- Fig. app_hxy(b): fault-distance-3 fold-transversal cultivation without escape.

The paper compares $|Y\rangle$-state cultivation (Clifford, Stim) with the true $|H_{XY}\rangle = T|+\rangle$
cultivation (a state-vector simulation) on the fault-distance-3 surface-code protocol: unitary
preparation plus stabilizer round, two fold-transversal $H_{XY}$ checks with GHZ(3) ancillas, then a
noiseless decoding of the code and a logical readout; every detector postselected.

Circuits:

- Clifford proxy: the authors' ``generate_sv_cirquit(p, dfinal=7, prep="unitstab", cirq=False)``
  (kaavyas99/MSC_foldedH at 9378fd2), the circuit their state-vector handoff starts from; noiseless
  logical $Y$ readout.
- $T$: the native-$T$ reconstruction of the same circuit by Wan and Zapirain (arXiv:2609.18922,
  ``fold-d3/model.json``: CY layers -> CCZ + controlled-$SX$), exported by our ``make_circuits.py``
  at noise $p$, followed by a noiseless $T^\dagger$ and $X$ readout of the decoded logical qubit.
"""

import functools
import importlib.util
import json
import sys

from repro import common
from repro.common import Point

STUDY = "fold_transversal"
HERE = common.PAPERS / "2509.05212_fold_transversal_cultivation"
META = dict(arxiv="2509.05212", paper="Sahay et al. (2025), Fold-transversal surface code cultivation")
PS = [5e-4, 7e-4, 1e-3, 1.5e-3, 2e-3, 3e-3, 5e-3, 7e-3]  # the paper's panel: 1e-3, 3e-3, 5e-3, 7e-3


@functools.lru_cache(None)
def _mc():
    sys.path.insert(0, str(common.ROOT / "tools"))
    spec = importlib.util.spec_from_file_location("fold_make_circuits", HERE / "make_circuits.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@functools.lru_cache(None)
def _sv():
    sys.path.insert(0, str(HERE / "stim_src" / "MSC_foldedH" / "src"))
    from full_clifford_sim.main_complied_fxns import generate_sv_cirquit

    return generate_sv_cirquit


def make(p, variant):
    if variant == "y":
        c = _sv()(p, dfinal=7, prep="unitstab", cirq=False)
        text = str(c.flattened())
        common.noiseless_check(text)
        return text
    m = _mc()
    model = json.loads((HERE / "stim_src" / "exact_ler_native_T_models" / "fold-d3" / "model.json").read_text())
    body = m.export(model, p)
    q = model["logical"]
    errs = []
    for readout in ([f"T_DAG {q}", f"MX {q}"], [f"T {q}", f"MX {q}"], [f"T_DAG {q}", f"MY {q}"], [f"T {q}", f"MY {q}"]):
        text = body + "\n".join(readout) + "\nOBSERVABLE_INCLUDE(0) rec[-1]\n"
        try:
            common.noiseless_check(text)
            return text
        except ValueError as e:
            errs.append(str(e))
    raise ValueError(errs)


def circuits():
    return {f"fd3_p{p:g}_{v}": functools.partial(make, p, v) for p in PS for v in ("y", "t")}


def points():
    return [Point(f"fd3_p{p:g}_{v}", f"fd3_p{p:g}_{v}", "t" if v == "t" else "clifford", dict(p=p, gate=v),
                  target_errors=20000, max_shots=1e12, max_seconds=420, tier=1) for p in PS for v in ("y", "t")]


def figures(results):
    """The paper's ycult_v2.pdf style: LER vs expected attempts (log, 1-10), 1-sigma bars, p labels."""
    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    style = {"y": ("#ffb6c1", r"$|Y\rangle$ (Tsim GPU, Clifford)", -1), "t": ("#007f7f", r"$|H_{XY}\rangle$ (Tsim GPU, real $T$)", 1)}
    for g, (col, lab, side) in style.items():
        ser = sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["gate"] == g)
        xs, ys, es = [], [], []
        for p, t in ser:
            if not t["kept"] or not t["errors"]:
                continue
            x = t["shots"] / t["kept"]
            y = t["errors"] / t["kept"]
            xs.append(x)
            ys.append(y)
            es.append(y / np.sqrt(t["errors"]))
            ax.annotate(f"{p:g}", (x, y), xytext=(8, 4 * side), textcoords="offset points", fontsize=9)
        ax.errorbar(xs, ys, yerr=es, ls="none", marker="o", ms=4, color=col, elinewidth=2, label=lab)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 10)
    ax.set_xticks(range(1, 11), [str(k) for k in range(1, 11)])
    ax.set_xlabel("Expected attempts")
    ax.set_ylabel("Logical error rate")
    ax.grid(True, ls="--", alpha=0.6)
    ax.legend(loc="lower right", frameon=False)
    path = plotting.save(fig, out / "ycult_v2.pdf")
    return [common.Figure(
        "fold", path, "Sahay et al. Fig.~app\\_hxy(b) (\\texttt{ycult\\_v2.pdf}): $|Y\\rangle$ vs.\\ $|H_{XY}\\rangle$ cultivation, fault distance 3, no escape",
        "Same axes and style as the paper (logical error rate vs.\\ expected attempts, $\\pm1\\sigma$ bars, points labelled by $p$; "
        "the paper shows $p$ = 0.001, 0.003, 0.005, 0.007). All detectors postselected; noiseless decoding and logical readout. "
        "No numbers for this panel are released (the repository's \\texttt{all\\_paper\\_data\\_v2.csv} holds only end-to-end runs), "
        "so there is no overlay. Read off the paper's figure, its $|Y\\rangle$ stabilizer point at $p=10^{-3}$ is about $1.8\\times10^{-7}$ "
        "at 1.35 attempts, versus $5\\times10^{-8}$ at 1.25 here, so the paper's circuit for this panel has more fault locations than "
        "\\texttt{generate\\_sv\\_cirquit(prep=\"unitstab\")}; as in the paper, $|H_{XY}\\rangle$ and $|Y\\rangle$ differ once escape is excluded "
        "(here $H_{XY}$ is about $2\\times$ worse, in the paper about $2\\times$ better).",
        common.budget_line(results))]

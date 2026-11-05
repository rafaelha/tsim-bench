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
PS = [5e-4, 7e-4, 1e-3, 1.5e-3, 2e-3, 3e-3]


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
    import matplotlib.pyplot as plt

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for g, col, lab in (("t", "C3", "$|H_{XY}\\rangle$ (real T gates)"), ("y", "C0", "$|Y\\rangle$ (Clifford proxy)")):
        ser = sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["gate"] == g)
        plotting.ler_points(axes[0], ser, color=col, label=lab)
        plotting.accept_points(axes[1], ser, color=col, label=lab)
    plotting.style_ler(axes[0], "noise strength $p$")
    plotting.style_accept(axes[1], "noise strength $p$")
    axes[0].legend()
    path = plotting.save(fig, out / "fig_app_hxy_b.pdf")
    return [common.Figure(
        "fold", path, "Sahay et al. Fig.~app\\_hxy(b): $|Y\\rangle$ vs.\\ $|H_{XY}\\rangle$ cultivation, fault distance 3, no escape",
        "All detectors postselected; noiseless decoding and logical readout. The paper's figure is shown only as an image "
        "(no released numbers for this panel), so no overlay. As in the paper, the two states have different logical error rates "
        "once escape is excluded.",
        common.budget_line(results))]

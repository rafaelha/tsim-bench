r"""Hetényi, Brown, Williamson (2026), arXiv:2603.05429 -- gauging Clifford-measurement cultivation.

Fig. 4(a) compares, at $d=3$ and $p$ = 0.1--0.5%, the authors' Stim simulation of the $|{+i}\rangle$
proxy with a qiskit state-vector simulation of the $T$ circuit; Table 1 lists $P_L$ and $p_{succ}$
for fault distances 3 and 5 at $p$ = 1e-3 and 5e-4 (the $d=7$ entries are skipped here, as agreed).
Every detector is postselected, including a final noiseless stabilizer round.

Circuits: the authors' generator ``get_stim_circ_w_growing(d, basis="Y", pipeline=True)`` with
their ``utils.add_noise`` (uniform $p$), as in their notebook. Clifford proxy: as generated, final
noiseless $Y_L$ readout. $T$ version: every $S$/$S^\dagger$ becomes $T$/$T^\dagger$ (as in the authors'
qiskit check), and a noiseless logical rotation $\exp(\mp i\pi Z_L/8)$ (``repro/magic_check.py``) is
inserted before the readout so that $Y_L$ checks the $T$ state deterministically, the same
observable as the paper's per-shot $XS^\dagger$ expectation.
"""

import functools
import re
import sys

from repro import common, magic_check
from repro.common import Point

STUDY = "gauging_cultivation"
HERE = common.PAPERS / "2603.05429_gauging_clifford_cultivation"
META = dict(arxiv="2603.05429", paper="Hetényi, Brown, Williamson (2026), Constant-depth magic state cultivation with Clifford measurements by gauging")
P3 = [5e-4, 1e-3, 2e-3, 3e-3, 4e-3, 5e-3]
P5 = [5e-4, 1e-3, 2e-3]
# Table 1: (p, d) -> (P_L, err, p_succ)
TABLE = {(1e-3, 3): (8.8e-7, 0.8e-7, 0.46), (1e-3, 5): (3.2e-10, 0.4e-10, 0.04),
         (5e-4, 3): (1.2e-7, 0.2e-7, 0.65), (5e-4, 5): (1.1e-11, 0.3e-11, 0.20)}


@functools.lru_cache(None)
def _gen():
    sys.path.insert(0, str(HERE / "stim_src" / "gauging_clifford_measurement"))
    from color_code import get_stim_circ_w_growing
    from utils import add_noise

    return get_stim_circ_w_growing, add_noise


def drop_targetless(text):
    keep = ("TICK", "DETECTOR", "OBSERVABLE_INCLUDE", "SHIFT_COORDS")
    return re.sub(rf"^\s*(?!{'|'.join(keep)})[A-Z_0-9]+(\([^)]*\))?\s*$\n", "", text, flags=re.M)


def make(d, p, variant):
    get, add_noise = _gen()
    proxy = drop_targetless(str(add_noise(get(d, basis="Y", pipeline=True), CX_error=p, meas_error=p,
                                          single_qubit_error=p, gate_idle_error=p)))
    if variant == "s":
        common.noiseless_check(proxy)
        return proxy
    t = common.s_to_t(proxy)
    last_mpp = [l for l in t.splitlines() if l.startswith("MPP ")][-1].split()
    assert len(last_mpp) == 2, last_mpp
    _, zl = magic_check.split_y(magic_check.parse_product(last_mpp[1]))
    text, _ = magic_check.make_deterministic(t, zl)
    return text


def combos():
    return [(3, p, v) for p in P3 for v in ("s", "t")] + [(5, p, v) for p in P5 for v in ("s", "t")]


def name(d, p, v):
    return f"d{d}_p{p:g}_{v}"


def circuits():
    return {name(*c): functools.partial(make, *c) for c in combos()}


def points():
    pts = []
    for d, p, v in combos():
        variant = "t" if v == "t" else "clifford"
        if d == 3:
            pts.append(Point(name(d, p, v), name(d, p, v), variant, dict(d=d, p=p, gate=v), target_errors=20000,
                             max_shots=1e12, max_seconds=300, tier=1))
        else:
            sec = {5e-4: 2400, 1e-3: 1800, 2e-3: 900}[p]
            pts.append(Point(name(d, p, v), name(d, p, v), variant, dict(d=d, p=p, gate=v), target_errors=1000,
                             max_shots=2e13, max_seconds=sec, tier=2 if p == 2e-3 else 3))
    return pts


def figures(results):
    import matplotlib.pyplot as plt

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    cols = {(3, "s"): "C0", (3, "t"): "C3", (5, "s"): "C9", (5, "t"): "C1"}
    for (d, g), col in cols.items():
        ser = sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["d"] == d and r["params"]["gate"] == g)
        lab = f"d={d}, {'T' if g == 't' else '|+i> proxy'}"
        plotting.ler_points(axes[0], ser, color=col, ls="-" if g == "t" else "--", label=lab)
        plotting.accept_points(axes[1], ser, color=col, ls="-" if g == "t" else "--", label=lab)
    for (p, d), (pl, e, ps) in TABLE.items():
        plotting.published_value(axes[0], p, pl, color=cols[(d, "s")], yerr=(e, e), label="paper Table 1 (proxy)" if (p, d) == (1e-3, 3) else None)
        plotting.published_value(axes[1], p, ps, color=cols[(d, "s")])
    plotting.style_ler(axes[0], "noise strength $p$")
    plotting.style_accept(axes[1], "noise strength $p$", log=True)
    axes[0].legend()
    path = plotting.save(fig, out / "fig4_table1.pdf")
    return [common.Figure(
        "gauging", path, "Hetényi et al. Fig. 4(a,b) and Table 1: gauging cultivation, $d=3$ and $d=5$",
        "Full postselection including the final noiseless stabilizer round (counted in the success probability). "
        "Dashed: the $|{+i}\\rangle$ Clifford proxy; solid: real $T$ gates with a noiseless $T$-basis readout. "
        "Open diamonds: the paper's Table 1 (proxy, Stim). The $d=7$ point of the paper is not attempted.",
        common.budget_line(results))]


def checks(results):
    rows = []
    for (p, d), (pl, e, ps) in TABLE.items():
        r = results.get(name(d, p, "s"))
        if r:
            rows.append(common.check_row(f"d={d} p={p:g} |+i> proxy", "clifford", dict(value=pl, sigma=e), r["totals"]))
            rows.append(common.check_row(f"d={d} p={p:g} |+i> proxy", "clifford", dict(value=ps), r["totals"], quantity="acceptance"))
    return [x for x in rows if x]

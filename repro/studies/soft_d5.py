r"""Li et al. (2025), SOFT, arXiv:2512.23037 -- Fig. 2 / Table 3: d=5 injection + cultivation with T gates.

SOFT sampled the authors' own native-$T$ circuits (unitary injection, $d=3$ and $d=5$ double
checks, code growth, noiseless readout; every detector postselected) on 16 H800 GPUs for 20 days:
28.9B, 74B and 134.4B shots at $p$ = 2e-3, 1e-3, 5e-4. SOFT ran no Clifford proxy, so only the
non-Clifford version is sampled here (the $S$ proxy of the same protocol is in the Gidney study).

Circuits: SOFT's released files (``softv1_magic_state_cultivation``), used verbatim. They are
also the reference circuits of the exact-LER paper (Wan, Zapirain, arXiv:2609.18922), whose
exact values $A(p)$ and $P_L(p)$ and truncated series are overlaid.
"""

import fractions
import re

from repro import common
from repro.common import Point

STUDY = "soft_d5"
SRC = common.PAPERS / "2512.23037_soft" / "stim_src" / "softv1_magic_state_cultivation"
EXACT = common.PAPERS / "2609.18922_exact_ler_cultivation" / "tex" / "data"
META = dict(arxiv="2512.23037", paper="Li et al. (2025), SOFT: a high-performance simulator for universal fault-tolerant quantum circuits")
PS = [5e-4, 1e-3, 2e-3, 3e-3, 4e-3, 5e-3]
# Table 3: p -> (total shots, kept, errors)
PUBLISHED = {2e-3: (28.9e9, 0.60e9, 22), 1e-3: (74.0e9, 10.6e9, 49), 5e-4: (134.4e9, 50.9e9, 8)}
BUDGET = {5e-4: (3e12, 1500), 1e-3: (1.5e12, 1200), 2e-3: (1e12, 1200), 3e-3: (6e11, 900), 4e-3: (6e11, 900), 5e-3: (6e11, 900)}


def circuits():
    out = {f"d5_p{p:g}": (lambda p=p: (SRC / f"circuit_d5_p{p:g}.stim").read_text()) for p in PS}
    out["d3_p0.001"] = lambda: (SRC / "circuit_d3_p0.001.stim").read_text()
    return out


def points():
    pts = [Point(f"d5_p{p:g}", f"d5_p{p:g}", "t", dict(d=5, p=p), target_errors=100000,
                 max_shots=BUDGET[p][0], max_seconds=BUDGET[p][1], tier=3 if p <= 1e-3 else 2) for p in PS]
    pts.append(Point("d3_p0.001", "d3_p0.001", "t", dict(d=3, p=1e-3), target_errors=20000, max_shots=1e12, max_seconds=300))
    return pts


def _frac(s):
    s = s.replace("\\frac{", "").replace("}{", "/").replace("}", "").replace("$", "").strip()
    return fractions.Fraction(s)


def exact_grid():
    rows = []
    for line in (EXACT / "exact_grid.tex").read_text().splitlines():
        m = re.match(r"\$([0-9.]+)\$ & \$([0-9.]+)\$ & \$([0-9.]+)\\times10\^\{(-?\d+)\}\$", line.strip())
        if m:
            rows.append((float(m[1]), float(m[2]), float(m[3]) * 10 ** int(m[4])))
    return rows


def d5_series():
    text = (EXACT / "d5_series.tex").read_text()
    return {int(k): fractions.Fraction(int(a), int(b)) for a, b, k in re.findall(r"\\frac\{(\d+)\}\{(\d+)\}x\^\{(\d+)\}", text)}


def series_value(coeffs, p):
    x = p / (1 - p)
    return float(sum(c * x**k for k, c in coeffs.items()))


def figures(results):
    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    ser = sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["d"] == 5)
    plotting.ler_points(axes[0], ser, color="C3", label="Tsim GPU, T")
    plotting.accept_points(axes[1], ser, color="C3", label="Tsim GPU")
    pub = [dict(p=p, shots=s, kept=k, errors=e) for p, (s, k, e) in PUBLISHED.items()]
    plotting.published_ler(axes[0], pub, color="k", label="SOFT (Table 3)")
    plotting.published_accept(axes[1], pub, color="k")
    grid = exact_grid()
    axes[0].plot([g[0] for g in grid], [g[2] for g in grid], "x", color="C2", ms=6, mew=1.5, label="exact (2609.18922)", zorder=6)
    axes[1].plot([g[0] for g in grid], [g[1] for g in grid], "x", color="C2", ms=6, mew=1.5, zorder=6)
    xs = np.geomspace(4e-4, 2.2e-3, 50)
    co = d5_series()
    axes[0].plot(xs, [series_value(co, x) for x in xs], color="C2", lw=0.8, ls=":", label="exact series to $x^{10}$")
    plotting.style_ler(axes[0], "noise strength $p$")
    plotting.style_accept(axes[1], "noise strength $p$", log=True)
    axes[0].legend()
    path = plotting.save(fig, out / "fig2_d5.pdf")
    figs = [common.Figure(
        "soft", path, "SOFT Fig. 2 / Table 3: $d=5$ injection + cultivation with real $T$ gates",
        "SOFT's own circuits (verbatim), all detectors postselected, noiseless final check. Black diamonds: SOFT's published "
        "values (16 H800 GPUs, 20 days, $2.4\\times10^{11}$ shots). Green crosses and dotted line: exact values and series of "
        "Wan and Zapirain (arXiv:2609.18922) for the same circuits.",
        common.budget_line(results, [k for k, r in results.items() if r["params"]["d"] == 5]))]
    rows = []
    gmap = {round(g[0], 6): g for g in grid}
    for p in PS:
        r = results.get(f"d5_p{p:g}")
        pubc = PUBLISHED.get(p)
        cells = [f"{p:g}"]
        cells.append(f"{pubc[2] / pubc[1]:.3g} ({pubc[2]}/{common.fmt_count(pubc[1])})" if pubc else "--")
        g = gmap.get(round(p, 6))
        cells.append(f"{g[2]:.4g}, $A$={g[1]:.4f}" if g else "--")
        if r:
            t = r["totals"]
            b, lo, hi = common.binomial_interval(t["errors"], t["kept"])
            cells.append(f"{b:.3g} [{lo:.2g}, {hi:.2g}] ({t['errors']}/{common.fmt_count(t['kept'])}), $A$={t['kept'] / t['shots']:.4f}")
            cells.append(f"{common.fmt_count(t['shots'])}, {common.fmt_seconds(t['seconds'])}")
        else:
            cells += ["--", "--"]
        rows.append(" & ".join(cells) + r" \\")
    tpath = out / "table3.tex"
    tpath.write_text("\\begin{tabular}{l l l l l}\n\\toprule\n$p$ & SOFT (Table 3) & exact (2609.18922) & Tsim GPU & shots, GPU time\\\\\n\\midrule\n"
                     + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    figs.append(common.Figure("soft_table", tpath, "SOFT Table 3 vs. exact values vs. Tsim GPU",
                              "LER of kept shots (errors / kept); $A$ is the acceptance rate; Tsim brackets are 1000x likelihood intervals.",
                              common.budget_line(results), kind="table"))
    return figs

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


def _band(ax, pts, color, label, marker="o"):
    """SOFT's Fig. 2 style: line + markers, band = hypotheses within a Bayes factor of 1000 (binomial)."""
    xs, ys, lo, hi = [], [], [], []
    for p, e, k in pts:
        if not k or not e:
            continue
        b, l, h = common.binomial_interval(e, k)
        xs.append(p)
        ys.append(b)
        lo.append(l)
        hi.append(h)
    ax.plot(xs, ys, "-", marker=marker, color=color, label=label)
    ax.fill_between(xs, lo, hi, color=color, alpha=0.2, lw=0)


def figures(results):
    import matplotlib.pyplot as plt

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    figs = []
    # ---- Fig. 2 (logical_error_rate.pdf): same axes as the paper (default figure size, p in [5e-4, 2e-3], y in [1e-11, 1e-7])
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    _band(ax, [(p, e, k) for p, (s, k, e) in sorted(PUBLISHED.items())], "C0", "SOFT (paper, Table 3)")
    ours = [(r["params"]["p"], r["totals"]["errors"], r["totals"]["kept"]) for r in results.values()
            if r["params"]["d"] == 5 and r["params"]["p"] <= 2e-3]
    _band(ax, sorted(ours), "C3", "Tsim GPU", marker="s")
    grid = [g for g in exact_grid()]
    ax.plot([g[0] for g in grid], [g[2] for g in grid], "x", color="C2", ms=7, mew=1.5, label="exact (arXiv:2609.18922)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(1e-11, 1e-7)
    ax.set_xlabel("Physical Error Rate")
    ax.set_ylabel("Logical Error Rate")
    ax.grid(True, which="major", alpha=1.0, color="0.7", lw=0.8)
    ax.grid(False, which="minor")
    ax.legend(loc="lower right", fontsize=8)
    path = plotting.save(fig, out / "logical_error_rate.pdf")
    figs.append(common.Figure(
        "soft", path, "SOFT Fig. 2: logical error rate of $d=5$ magic state injection + cultivation (real $T$ gates)",
        "Same axes as the paper. Blue: SOFT's published points (16 H800 GPUs, 20 days, $2.4\\times10^{11}$ shots); red: Tsim GPU on "
        "SOFT's own circuits; green crosses: exact values of Wan and Zapirain (arXiv:2609.18922) for the same circuits. Bands: hypotheses "
        "with a Bayes factor of at most 1000 relative to the maximum-likelihood hypothesis (binomial), as in the paper. "
        "Our points at $p>2\\times10^{-3}$ are in the table below.",
        common.budget_line(results, [k for k, r in results.items() if r["params"]["d"] == 5])))

    # ---- Table 3, in the paper's format, published rows and ours
    rows = []
    for p in sorted(PS, reverse=True):
        if p in PUBLISHED:
            s, k, e = PUBLISHED[p]
            rows.append(f"{p:g} & SOFT (paper) & {s / 1e9:.1f}B & {k / 1e9:.2f}B & {100 * (1 - k / s):.2f}\\% & {e} & ${tex_sci(e / k)}$ & 16 H800, $\\sim$20 days total \\\\")
        r = results.get(f"d5_p{p:g}")
        if r:
            t = r["totals"]
            rows.append(f"{p:g} & Tsim GPU & {t['shots'] / 1e9:.1f}B & {t['kept'] / 1e9:.2f}B & {100 * (1 - t['kept'] / t['shots']):.2f}\\% & "
                        f"{t['errors']} & ${tex_sci(t['errors'] / t['kept'])}$ & 1 RTX 5090, {common.fmt_seconds(t['seconds'])} \\\\")
        g = {round(x[0], 6): x for x in exact_grid()}.get(round(p, 6))
        if g:
            rows.append(f"{p:g} & exact (2609.18922) & & & {100 * (1 - g[1]):.2f}\\% & & ${tex_sci(g[2])}$ & \\\\")
        rows.append("\\midrule")
    tpath = out / "table3.tex"
    tpath.write_text("\\begin{tabular}{c l c c c c c l}\n\\toprule\nNoise Strength & & Total Shots & Preserved Shots & Discard Rate & "
                     "Detected Logical Errors & Logical Error Rate & hardware, time\\\\\n\\midrule\n" + "\n".join(rows[:-1]) +
                     "\n\\bottomrule\n\\end{tabular}\n")
    figs.append(common.Figure("soft_table", tpath, "SOFT Table 3: performance of $d=5$ cultivation (1 B = 1 billion), paper vs.\\ Tsim GPU vs.\\ exact",
                              "Same columns as the paper's Table 3, with our rows (and the exact values) added.",
                              common.budget_line(results), kind="table"))
    return figs


def tex_sci(x):
    m, e = f"{x:.2e}".split("e")
    return f"{m}\\times 10^{{{int(e)}}}"


def checks(results):
    rows = []
    for p, (s, k, e) in PUBLISHED.items():
        r = results.get(f"d5_p{p:g}")
        if r:
            rows.append(common.check_row(f"d=5 p={p:g} T (SOFT Table 3)", "t", dict(errors=e, kept=k), r["totals"]))
    for p, a, pl in exact_grid():
        r = results.get(f"d5_p{p:g}")
        if r:
            rows.append(common.check_row(f"d=5 p={p:g} T (exact, 2609.18922)", "t", dict(value=pl, sigma=0.0), r["totals"]))
            rows.append(common.check_row(f"d=5 p={p:g} T (exact, 2609.18922)", "t", dict(value=a, sigma=0.0), r["totals"], quantity="acceptance"))
    return [x for x in rows if x]

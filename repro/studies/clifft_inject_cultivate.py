r"""Chase, Labib (2026), Clifft, arXiv:2604.27058 -- Fig. 6: inject + cultivate, $T$ vs. $S$ proxy, $d=3$ and $d=5$.

Clifft's Fig. 6 plots the logical error rate per kept shot of Gidney's unitary-injection
cultivation circuits (no escape) with real $T$ gates and with the $S$ proxy, and their ratio; its
Table 2 lists the $d=5$ $T$-gate values at three noise strengths (stratified importance sampling,
$9.6\times10^{10}$ shots, 12 machine-hours on a 16-core c6i.8xlarge).

Clifft's circuits are the same as the Gidney study's (the Clifft paper's converter, byte-identical
at $p=10^{-3}$), so this study samples nothing itself: it re-plots the Gidney study's unitary-injection
points as LER and $T/S$ ratio.
"""

from repro import common

STUDY = "clifft_inject_cultivate"
META = dict(arxiv="2604.27058", paper="Chase, Labib (2026), Clifft: fast exact simulation of near-Clifford quantum circuits")
TABLE2 = {5e-4: 1.56e-10, 1e-3: 2.67e-9, 2e-3: 5.78e-8}


def circuits():
    return {}


def points():
    return []


def figures(results):
    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting

    g = common.load_results("gidney_cultivation")
    out = common.REPORT / "figures" / STUDY
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    used = []
    for d, col in ((3, "C0"), (5, "C3")):
        ts = {}
        for gate in ("t", "s"):
            ser = sorted((r["params"]["p"], r["totals"]) for k, r in g.items()
                         if r["params"]["d"] == d and r["params"]["style"] == "unitary" and r["params"]["gate"] == gate)
            used += [k for k, r in g.items() if r["params"]["d"] == d and r["params"]["style"] == "unitary" and r["params"]["gate"] == gate]
            plotting.ler_points(axes[0], ser, color=col, ls="-" if gate == "t" else "--", marker="o" if gate == "t" else "s",
                                label=f"d={d}, {'T' if gate == 't' else 'S proxy'}")
            ts[gate] = dict(ser)
        xs, rat, lo, hi = [], [], [], []
        for p in sorted(set(ts["t"]) & set(ts["s"])):
            a, b = ts["t"][p], ts["s"][p]
            if a["errors"] and b["errors"]:
                r = (a["errors"] / a["kept"]) / (b["errors"] / b["kept"])
                e = r * np.sqrt(1 / a["errors"] + 1 / b["errors"])
                xs.append(p)
                rat.append(r)
                lo.append(e)
                hi.append(e)
        if xs:
            axes[1].errorbar(xs, rat, yerr=[lo, hi], marker="o", color=col, ms=3.5, capsize=2, label=f"d={d}")
    for p, v in TABLE2.items():
        plotting.published_value(axes[0], p, v, color="C3", label="Clifft Table 2 (d=5, T)" if p == 1e-3 else None)
    plotting.style_ler(axes[0], "noise strength $p$")
    axes[0].legend(fontsize=5.5)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("noise strength $p$")
    axes[1].set_ylabel("$T$ / $S$ logical error rate")
    axes[1].legend()
    path = plotting.save(fig, out / "fig6_t_over_s.pdf")
    return [common.Figure(
        "clifft6", path, "Clifft Fig. 6: inject + cultivate, $T$ vs.\\ $S$ proxy, and their ratio",
        "Same samples as the Gidney study (unitary injection). Error bars on the ratio are $\\pm1\\sigma$ (Poisson). "
        "Open diamonds: Clifft's Table 2 $d=5$ values (stratified importance sampling).",
        common.budget_line(g, used, label="(Gidney study points)"))]

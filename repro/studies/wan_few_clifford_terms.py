r"""Wan, Zhong, Zapirain (2025), arXiv:2509.08658 -- d=3 T-gate cultivation, Figs. 15-17 and 19.

The paper samples the native-$T$ $d=3$ cultivation circuit (injection + double check, from the
companion repo's ``d_3_circuit_definitions.py``) followed by a noiseless $T$-projection readout,
postselecting on every detector. Its Table (``tab:v3-results``) lists the exact non-Clifford
results at $2^{29}$--$2^{32}$ shots per noise strength; its red curves are the $S$-gate proxy sampled
with Stim.

Circuits: built as in the repo's ``run.py`` and our ``make_circuits.py``: $T\to S$, the vendored
``gen.NoiseModel.uniform_depolarizing(p)``, $S\to T$; the projection stays noiseless. The Clifford
proxy maps every $T$/$T^\dagger$ of the whole circuit (including the projection) to $S$/$S^\dagger$.
"""

import functools
import importlib.util
import re

from repro import common
from repro.common import Point

STUDY = "wan_few_clifford_terms"
HERE = common.PAPERS / "2509.08658_few_clifford_terms"
META = dict(arxiv="2509.08658", paper="Wan, Zhong, Zapirain (2025), Simulating magic state cultivation with few Clifford terms")
PS = [5e-4, 1e-3, 1.5e-3, 2e-3, 2.5e-3, 3e-3, 4e-3, 5e-3]
# tab:v3-results: p -> (shots, PSR, errors, kept)
PUBLISHED_T = {5e-4: (2**32, 0.807, 622, 3465069335), 1e-3: (2**29, 0.651, 351, 349529061),
               1.5e-3: (2**29, 0.525, 831, 282110746), 2e-3: (2**29, 0.424, 1540, 227748263),
               2.5e-3: (2**29, 0.343, 2373, 183908903), 3e-3: (2**29, 0.277, 3201, 148548040),
               4e-3: (2**29, 0.181, 4785, 96970177), 5e-3: (2**29, 0.118, 6193, 63357051)}


@functools.lru_cache(None)
def _mc():
    spec = importlib.util.spec_from_file_location("wan_make_circuits", HERE / "make_circuits.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def make(p, variant):
    m = _mc()
    text = m.make(p)
    if variant == "s":
        text = re.sub(r"^(\s*)T_DAG(\s)", r"\1S_DAG\2", text, flags=re.M)
        text = re.sub(r"^(\s*)T(\s)", r"\1S\2", text, flags=re.M)
    common.noiseless_check(text)
    return text


def circuits():
    return {f"d3_p{p:g}_{v}": functools.partial(make, p, v) for p in PS for v in ("t", "s")}


def points():
    return [Point(f"d3_p{p:g}_{v}", f"d3_p{p:g}_{v}", "t" if v == "t" else "clifford", dict(p=p, gate=v),
                  target_errors=20000, max_shots=1e12, max_seconds=300, tier=1) for p in PS for v in ("t", "s")]


# Discard ratios printed on the bars of the paper's Fig. 19 (bar_chart_psr.png): p -> (Y stim, T tsim+cutting, T accel.), percent.
PUBLISHED_DISCARD = {5e-4: (19.6, 19.3, 19.3), 1e-3: (35.4, 34.9, 34.9), 1.5e-3: (48.1, 47.5, 47.5), 2e-3: (58.2, 57.6, 57.6),
                     2.5e-3: (66.4, 65.8, 65.7), 3e-3: (73.0, 72.3, 72.3), 4e-3: (82.5, 81.9, 81.9), 5e-3: (88.6, 88.2, 88.2)}


def _ler_attempts(ax, ser, color, label, side):
    """The paper's style (Figs. 15/17): LER vs expected attempts per kept shot, 1-sigma band, p labels."""
    import numpy as np

    xs, ys, lo, hi = [], [], [], []
    for p, t in ser:
        if not t["kept"] or not t["errors"]:
            continue
        y = t["errors"] / t["kept"]
        s = y / np.sqrt(t["errors"])
        xs.append(t["shots"] / t["kept"])
        ys.append(y)
        lo.append(y - s)
        hi.append(y + s)
        dx, ha = (8, "left") if side == "right" else (-8, "right")
        ax.annotate(f"p={p:g}", (xs[-1], y), xytext=(dx, -6 if side == "right" else 8), textcoords="offset points",
                    color=color, fontsize=8, ha=ha)
    ax.plot(xs, ys, "-", color=color, lw=1.5)
    ax.scatter(xs, ys, color=color, s=18, zorder=3, label=label)
    ax.fill_between(xs, lo, hi, color=color, alpha=0.25, lw=0)


def _crosscheck_sentence(results):
    """Independent acceptances on the same circuit files: Clifft (repro/clifft_check.py) and Stim (repro/stim_check.py)."""
    from repro import clifft_check, stim_check

    cl, st = clifft_check.load(STUDY), stim_check.load(STUDY)
    parts = []
    for p in (1e-3, 5e-4):
        for g in ("t", "s"):
            k = f"d3_p{p:g}_{g}"
            r = results.get(k)
            ours = f"{r['totals']['kept'] / r['totals']['shots']:.5f}" if r else "--"
            if k in cl:
                c = cl[k]
                a = c["kept"] / c["shots"]
                parts.append(f"Clifft {c['clifft']} keeps ${a:.5f}\\pm{(a * (1 - a) / c['shots']) ** .5:.5f}$ of {common.fmt_count(c['shots'])} "
                             f"shots for the {'$T$ circuit' if g == 't' else '$S$ proxy'} at $p={p:g}$ (Tsim GPU {ours}"
                             + (f"; paper {PUBLISHED_T[p][3] / PUBLISHED_T[p][0]:.4f}" if g == "t" else "") + ")")
            if g == "s" and k in st:
                x = st[k]
                parts.append(f"Stim keeps {x['kept'] / x['shots']:.5f} of {common.fmt_count(x['shots'])} shots of the $S$ proxy at $p={p:g}$ (Tsim GPU {ours})")
    if not parts:
        return "(Run repro/clifft_check.py and repro/stim_check.py for independent CPU cross-checks.)"
    return "Independent CPU simulators on the same circuit files: " + "; ".join(parts) + "."


def figures(results):
    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    figs = []
    ser = {g: sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["gate"] == g) for g in ("s", "t")}

    # ---- Figs. 15/17: LER vs expected attempts per kept shot (paper style, LER_accel_improved.png)
    fig, ax = plt.subplots(figsize=(7.2, 5.8))
    _ler_attempts(ax, ser["s"], "red", r"$d=3$ $|Y\rangle$ cultivation (Tsim GPU, $S$ proxy)", "right")
    _ler_attempts(ax, ser["t"], "green", r"$d=3$ $|T\rangle$ cultivation (Tsim GPU)", "left")
    pub = sorted(PUBLISHED_T.items())
    ax.errorbar([s / k for p, (s, psr, e, k) in pub], [e / k for p, (s, psr, e, k) in pub],
                yerr=[e / k / np.sqrt(e) for p, (s, psr, e, k) in pub], ls="none", marker="D", mfc="none", mec="k", ecolor="k",
                ms=6, capsize=2, label=r"paper, $|T\rangle$ (tsim+cutting+accel., Table v3-results)", zorder=4)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("expected attempts per kept shot", fontsize=12)
    ax.set_ylabel("logical error rate (per kept shot)", fontsize=12)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    path = plotting.save(fig, out / "LER_accel_improved.pdf")
    figs.append(common.Figure(
        "wan", path, "Wan et al. Figs. 15 and 17: $d=3$ $T$ cultivation, LER vs.\\ expected attempts per kept shot",
        "Same format as the paper (shaded bands: binomial standard error). Red: the $|Y\\rangle$ ($S$-gate) proxy, which the paper "
        "sampled with Stim; green: real $T$ gates; open diamonds: the paper's exact non-Clifford results "
        "(Table v3-results, $2^{29}$--$2^{32}$ shots, Apple M4 Pro CPU). The $T$ LERs agree with the table at every $p$.", common.budget_line(results)))

    # ---- Fig. 19: discard ratio bar chart (bar_chart_psr.png), the paper's bars plus ours
    ps = [p for p in PS]
    w = 0.16
    x = np.arange(len(ps))
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = [("paper: $|Y\\rangle$ (stim)", [PUBLISHED_DISCARD[p][0] for p in ps], "#ff4d4d", None),
            ("paper: $|T\\rangle$ (tsim+cutting+accel.)", [PUBLISHED_DISCARD[p][2] for p in ps], "#4caf50", None)]
    for g, lab, col in (("s", "Tsim GPU: $|Y\\rangle$ ($S$ proxy)", "#ff4d4d"), ("t", "Tsim GPU: $|T\\rangle$", "#4caf50")):
        d = dict(ser[g])
        bars.append((lab, [100 * (1 - d[p]["kept"] / d[p]["shots"]) if p in d else np.nan for p in ps], col, "//"))
    for i, (lab, vals, col, hatch) in enumerate(bars):
        pos = x + (i - 1.5) * w
        ax.bar(pos, vals, w, label=lab, color=col, edgecolor="k", lw=0.6, hatch=hatch, alpha=0.85 if hatch is None else 0.45)
        for xx, v in zip(pos, vals):
            if v == v:
                ax.text(xx, v + 0.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=5)
    ax.set_xticks(x, [f"{p:g}" for p in ps], fontsize=7)
    ax.set_xlabel("physical error rate (circuit-level noise $p$)", fontsize=11)
    ax.set_ylabel("discard ratio (%)", fontsize=11)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(False)
    path = plotting.save(fig, out / "bar_chart_psr.pdf")
    figs.append(common.Figure(
        "wan_psr", path, "Wan et al. Fig. 19: discard ratio (1 $-$ PSR)",
        "Solid bars: the values printed on the paper's figure; hatched: Tsim GPU on the circuits built from the authors' repo. "
        "The $S$ proxy reproduces the paper's Stim bars exactly. For the $T$ circuit the paper discards 0.3--0.6 points less "
        "than for its $S$ proxy, while Tsim GPU discards only about 0.1 point less, so the two $T$ samplers (the paper's "
        "Tsim 0.1.0 with cutting, and the CUDA kernel here) disagree on the $T$ post-selection rate by a few $10^{-3}$, "
        "far beyond statistics, while their LERs agree. " + _crosscheck_sentence(results),
        common.budget_line(results)))

    rows = []
    for p in PS:
        s, psr, e, k = PUBLISHED_T[p]
        r = results.get(f"d3_p{p:g}_t")
        if r:
            t = r["totals"]
            ours = f"{t['errors'] / t['kept']:.3g} & {t['kept'] / t['shots']:.4f} & {t['errors']} & {common.fmt_count(t['shots'])} & {common.fmt_seconds(t['seconds'])}"
        else:
            ours = "-- & -- & -- & -- & --"
        rows.append(f"$" + plotting_p(p) + f"$ & $2^{{{int(round(np.log2(s)))}}}$ & {psr:.3f} & {e:,} & {k:,} & {e / k:.2g} & " + ours + " \\\\")
    tpath = out / "table.tex"
    tpath.write_text("\\begin{tabular}{cccccc|ccccc}\n\\toprule\n\\multicolumn{6}{c|}{paper (Table v3-results, $T$, Apple M4 Pro CPU)} & "
                     "\\multicolumn{5}{c}{Tsim GPU ($T$)}\\\\\n$p$ & \\textbf{Shots} & \\textbf{PSR} & \\textbf{Errors} & $n_{\\mathrm{kept}}$ & "
                     "\\textbf{LER} & LER & PSR & errors & shots & GPU time\\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    figs.append(common.Figure("wan_table", tpath, "Wan et al. Table v3-results (left, as published) vs.\\ Tsim GPU (right)", "",
                              common.budget_line(results, [f"d3_p{p:g}_t" for p in PS]), kind="table"))
    return figs


def plotting_p(p):
    m, e = f"{p:.1e}".split("e")
    return f"{float(m):g} \\times 10^{{{int(e)}}}"


def checks(results):
    rows = []
    for p, (s, psr, e, k) in PUBLISHED_T.items():
        r = results.get(f"d3_p{p:g}_t")
        if r:
            rows.append(common.check_row(f"d=3 p={p:g} T", "t", dict(errors=e, kept=k), r["totals"]))
            rows.append(common.check_row(f"d=3 p={p:g} T", "t", dict(kept=k, shots=s), r["totals"], quantity="acceptance"))
    return [x for x in rows if x]

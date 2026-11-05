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


def figures(results):
    import matplotlib.pyplot as plt

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for g, col, lab in (("t", "C3", "T (Tsim GPU)"), ("s", "C0", "S proxy (Tsim GPU)")):
        ser = sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["gate"] == g)
        plotting.ler_points(axes[0], ser, color=col, label=lab)
        plotting.accept_points(axes[1], ser, color=col, label=lab)
    pub = [dict(p=p, shots=s, kept=k, errors=e) for p, (s, psr, e, k) in PUBLISHED_T.items()]
    plotting.published_ler(axes[0], pub, color="C3", label="paper, T (tab. v3-results)")
    plotting.published_accept(axes[1], pub, color="C3")
    plotting.style_ler(axes[0], "noise strength $p$")
    plotting.style_accept(axes[1], "noise strength $p$")
    axes[0].legend()
    path = plotting.save(fig, out / "fig_ler_psr.pdf")
    figs = [common.Figure(
        "wan", path, "Wan et al. Figs. 15--17, 19: $d=3$ $T$ cultivation, LER and post-selection rate",
        "Injection + double check with a noiseless $T$-projection readout; every detector postselected. "
        "Open diamonds: the paper's exact non-Clifford results (Table v3-results, $2^{29}$--$2^{32}$ shots, Apple M4 Pro CPU). "
        "Red: real $T$ gates; blue: the $S$ proxy (the paper's Stim reference).",
        common.budget_line(results))]
    rows = []
    for p in PS:
        s, psr, e, k = PUBLISHED_T[p]
        r = results.get(f"d3_p{p:g}_t")
        if r:
            t = r["totals"]
            ours = f"{t['errors'] / t['kept']:.3g} & {t['kept'] / t['shots']:.4f} & {t['errors']} & {common.fmt_count(t['shots'])} & {common.fmt_seconds(t['seconds'])}"
        else:
            ours = "-- & -- & -- & -- & --"
        rows.append(f"{p:g} & {e / k:.2g} & {psr:.3f} & {e} & {common.fmt_count(s)} & {ours} \\\\")
    tpath = out / "table.tex"
    tpath.write_text("\\begin{tabular}{l lll l | lllll}\n\\toprule\n & \\multicolumn{4}{c|}{paper ($T$, CPU)} & \\multicolumn{5}{c}{Tsim GPU ($T$)}\\\\\n"
                     "$p$ & LER & PSR & errors & shots & LER & PSR & errors & shots & time\\\\\n\\midrule\n" + "\n".join(rows) +
                     "\n\\bottomrule\n\\end{tabular}\n")
    figs.append(common.Figure("wan_table", tpath, "Wan et al. Table v3-results vs. Tsim GPU", "",
                              common.budget_line(results, [f"d3_p{p:g}_t" for p in PS]), kind="table"))
    return figs

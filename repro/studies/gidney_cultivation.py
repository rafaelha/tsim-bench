r"""Gidney, Shutty, Jones (2024), arXiv:2409.17595 -- cultivation without the escape stage.

Two figures, both decoder-free (all detectors postselected, noiseless final logical check):

- Fig. 13 (``t-vs-s``): unitary injection + d=3 cultivation with each T gate replaced by T, S or Z,
  vs. uniform depolarizing noise p. The paper used a state-vector simulator ("vec_intercept").
- Fig. 21 (``inject-only-sampled``): bell / teleport ("degenerate") / unitary injection + d=3
  cultivation, and unitary + d=5 cultivation, at p = 5e-4, 1e-3, 2e-3. The paper sampled the S
  proxy with Stim ("perfectionist" decoder = discard on any detection event).

Circuits: the authors' generator (``cultiv.make_inject_and_cultivate_circuit``, commit 871e68f)
with their ``gen.NoiseModel.uniform_depolarizing(p)``; T circuits by the Clifft paper's converter
(``convert_circuit``: S->T, d=5 sign flips and feedforward, final Y_L wrapped in T...T_DAG). Z
variant: S/S_DAG -> Z and the final logical check measures X_L instead of Y_L.

Published numbers overlaid: Zenodo 13777072 ``stats.csv``.
"""

import csv
import functools
import json
import pathlib
import sys

from repro import common
from repro.common import Point

STUDY = "gidney_cultivation"
HERE = common.PAPERS / "2409.17595_magic_state_cultivation"
STATS_URL = "https://zenodo.org/records/13777072/files/stats.csv?download=1"
META = dict(arxiv="2409.17595", paper="Gidney, Shutty, Jones (2024), Magic state cultivation: growing T states as cheap as CNOT gates")

P13 = [1e-3, 2e-3, 3e-3, 5e-3, 7e-3, 1e-2]
P21 = [5e-4, 1e-3, 2e-3]
STYLES = {"bell": "bell", "teleport": "degenerate", "unitary": "unitary"}


@functools.lru_cache(None)
def _gen():
    sys.path.insert(0, str(HERE / "stim_src" / "github_magic-state-cultivation" / "src"))
    sys.path.insert(0, str(HERE / "stim_src"))
    import clifft_paper_convert_s_to_t as conv
    import gen
    from cultiv import make_inject_and_cultivate_circuit

    return conv, gen, make_inject_and_cultivate_circuit


def make(d, style, p, variant):
    conv, gen, mk = _gen()
    c = mk(dcolor=d, inject_style=STYLES[style], basis="Y")
    if p > 0:
        c = gen.NoiseModel.uniform_depolarizing(p).noisy_circuit_skipping_mpp_boundaries(c)
    if variant == "t":
        text = conv.convert_circuit(c, is_d5=(d == 5), is_e2e=False)
    else:
        text = str(c.flattened())
        if variant == "z":
            lines = text.splitlines()
            last = max(i for i, l in enumerate(lines) if l.startswith("MPP "))
            prods = lines[last].split()
            prods[1] = prods[1].replace("Y", "X")
            lines[last] = " ".join(prods)
            text = common.s_to_z("\n".join(lines))
    common.noiseless_check(text)
    return text


def cname(d, style, p, variant):
    return f"{style}_d{d}_p{p:g}_{variant}"


def combos():
    out = set()
    for p in P13:
        for v in ("t", "s", "z"):
            out.add((3, "unitary", p, v))
    for p in P21:
        for style in STYLES:
            for v in ("t", "s"):
                out.add((3, style, p, v))
        for v in ("t", "s"):
            out.add((5, "unitary", p, v))
    return sorted(out)


def circuits():
    return {cname(*c): functools.partial(make, *c) for c in combos()}


def points():
    pts = []
    for d, style, p, v in combos():
        variant = "t" if v == "t" else "clifford"
        if d == 3:
            pts.append(Point(cname(d, style, p, v), cname(d, style, p, v), variant, dict(d=d, style=style, p=p, gate=v),
                             target_errors=20000, max_shots=2e12, max_seconds=300, tier=1))
        else:
            # The paper took 1e12 S-proxy shots per point (0 / 50 / 263 errors). We take up to 4e12.
            pts.append(Point(cname(d, style, p, v), cname(d, style, p, v), variant, dict(d=d, style=style, p=p, gate=v),
                             target_errors=1000, max_shots=4e12, max_seconds=2400, tier=3 if p < 2e-3 else 2))
    return pts


# ---------------------------------------------------------------------------------------------
# Published data


def published():
    path = common.REPRO / "data" / "zenodo_13777072_stats.csv"
    if not path.exists():
        import urllib.request

        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(STATS_URL, path)
    rows = []
    for x in csv.DictReader(path.open(), skipinitialspace=True):
        j = json.loads(x["json_metadata"])
        if "cultivate" not in j["c"]:
            continue
        s, e, dsc = int(x["shots"]), int(x["errors"]), int(x["discards"])
        style = j["c"].split("[")[1].split("]")[0]
        rows.append(dict(style=style, d=j["d1"], p=j["p"], decoder=x["decoder"], shots=s, kept=s - dsc, errors=e))
    return rows


# ---------------------------------------------------------------------------------------------
# Figures


def _series(results, d, style, gate):
    xs = []
    for k, r in results.items():
        pr = r["params"]
        if pr["d"] == d and pr["style"] == style and pr["gate"] == gate:
            t = r["totals"]
            xs.append((pr["p"], t))
    return sorted(xs, key=lambda x: x[0])


def figures(results):
    import matplotlib.pyplot as plt

    from repro import plotting

    figs = []
    pub = published()
    out = common.REPORT / "figures" / STUDY
    out.mkdir(parents=True, exist_ok=True)

    # ---- Fig. 13
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    colors = {"t": "C3", "s": "C0", "z": "C2"}
    for g in ("t", "s", "z"):
        ser = _series(results, 3, "unitary", g)
        plotting.ler_points(axes[0], ser, color=colors[g], label=f"Tsim GPU, {g.upper()}")
        plotting.accept_points(axes[1], ser, color=colors[g], label=f"Tsim GPU, {g.upper()}")
        prow = [r for r in pub if r["d"] == 3 and r["style"] == "unitary" and r["decoder"] == f"vec_intercept_{g}"]
        plotting.published_ler(axes[0], prow, color=colors[g], label=f"paper (state vector), {g.upper()}")
        plotting.published_accept(axes[1], prow, color=colors[g])
    plotting.style_ler(axes[0], "noise strength $p$")
    plotting.style_accept(axes[1], "noise strength $p$")
    axes[0].legend(fontsize=6)
    pts = [k for k, r in results.items() if r["params"]["d"] == 3 and r["params"]["style"] == "unitary" and r["params"]["p"] in P13]
    path = out / "fig13_t_vs_s.pdf"
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    figs.append(common.Figure(
        "gidney13", path, "Gidney et al. Fig. 13: cultivating $T$, $S$, $Z$ states ($d=3$, no escape)",
        "Unitary injection followed by $d=3$ cultivation; every detector postselected; noiseless final logical check "
        "(for $T$: $T^{\\dagger}$-rotated $Y_L$). Open markers: the paper's state-vector simulation (Zenodo stats.csv). "
        "Filled markers: Tsim GPU. $S$ and $Z$ are Clifford proxies of the same circuit.",
        common.budget_line(results, pts)))

    # ---- Fig. 21
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    cols = {("bell", 3): "C0", ("teleport", 3): "C1", ("unitary", 3): "C2", ("unitary", 5): "C3"}
    for (style, d), col in cols.items():
        for g, ls in (("s", "--"), ("t", "-")):
            ser = [(p, t) for p, t in _series(results, d, style, g) if p in P21]
            plotting.ler_points(axes[0], ser, color=col, ls=ls, marker="o" if g == "t" else "s",
                                label=f"{style} d={d}, {'T' if g == 't' else 'S proxy'}")
            if g == "s":
                plotting.accept_points(axes[1], ser, color=col, label=f"{style} d={d}")
        prow = [r for r in pub if r["d"] == d and r["style"] == style and r["decoder"] == "perfectionist"]
        plotting.published_ler(axes[0], prow, color=col, label=None)
        plotting.published_accept(axes[1], prow, color=col)
    plotting.style_ler(axes[0], "noise strength $p$")
    plotting.style_accept(axes[1], "noise strength $p$")
    axes[0].legend(fontsize=5.5, ncol=1)
    pts = [k for k, r in results.items() if r["params"]["p"] in P21 and (r["params"]["style"] != "unitary" or r["params"]["gate"] != "z")]
    path = out / "fig21_inject_only_sampled.pdf"
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    figs.append(common.Figure(
        "gidney21", path, "Gidney et al. Fig. 21: injection + cultivation, sampled",
        "Three injection styles with $d=3$ cultivation and unitary injection with $d=5$ cultivation, all detectors postselected. "
        "Dashed/squares: the $S$ proxy (the paper's Clifford simulation); solid/circles: real $T$ gates. "
        "Open diamonds: the paper's Stim data (Zenodo stats.csv, up to $10^{12}$ shots per point). "
        "The right panel shows discard rates of the $S$ proxy.",
        common.budget_line(results, pts)))
    figs.append(table(results, pub))
    return figs


def table(results, pub):
    out = common.REPORT / "figures" / STUDY / "table_d5.tex"
    rows = []
    for p in P21:
        cells = [f"{p:g}"]
        pubrow = [r for r in pub if r["d"] == 5 and r["style"] == "unitary" and r["decoder"] == "perfectionist" and r["p"] == p]
        if pubrow:
            r = pubrow[0]
            cells.append(plotting_fmt(r["errors"], r["kept"], r["shots"]))
        else:
            cells.append("--")
        for g in ("s", "t"):
            r = results.get(cname(5, "unitary", p, g))
            cells.append(plotting_fmt(r["totals"]["errors"], r["totals"]["kept"], r["totals"]["shots"], r["totals"]["seconds"]) if r else "--")
        rows.append(" & ".join(cells) + r" \\")
    body = "\n".join(rows)
    out.write_text(
        "\\begin{tabular}{l l l l}\n\\toprule\n$p$ & paper ($S$ proxy, Stim) & Tsim GPU, $S$ proxy & Tsim GPU, $T$ \\\\\n\\midrule\n"
        + body + "\n\\bottomrule\n\\end{tabular}\n")
    pts = [cname(5, "unitary", p, g) for p in P21 for g in ("s", "t")]
    return common.Figure("gidney_d5_table", out, "Gidney et al.: $d=5$ injection + cultivation (no escape)",
                         "Each cell: logical error rate of kept shots, errors / kept shots, discard rate, and (Tsim) GPU sampling time.",
                         common.budget_line(results, pts), kind="table")


def plotting_fmt(errors, kept, shots, seconds=None):
    ler = errors / kept if kept else float("nan")
    s = f"{ler:.3g} ({errors}/{common.fmt_count(kept)}, disc.\\ {1 - kept / shots:.4f})"
    if seconds is not None:
        s += f", {common.fmt_seconds(seconds)}"
    return s


def checks(results):
    rows = []
    gate_of = {"perfectionist": "s", "vec_intercept_t": "t", "vec_intercept_s": "s", "vec_intercept_z": "z"}
    for r in published():
        g = gate_of.get(r["decoder"])
        if g is None:
            continue
        mine = results.get(cname(r["d"], r["style"], r["p"], g))
        if not mine:
            continue
        lab = f"{r['style']} d={r['d']} p={r['p']:g} {g.upper()} ({'Stim' if r['decoder'] == 'perfectionist' else 'state vector'})"
        variant = "t" if g == "t" else "clifford"
        if r["errors"]:
            rows.append(common.check_row(lab, variant, dict(errors=r["errors"], kept=r["kept"]), mine["totals"]))
        rows.append(common.check_row(lab, variant, dict(kept=r["kept"], shots=r["shots"]), mine["totals"], quantity="acceptance"))
    return [x for x in rows if x]

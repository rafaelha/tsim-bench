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
    from repro import data_sources

    path = data_sources.data_file("zenodo_13777072_stats.csv")
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


def _stats_path():
    from repro import data_sources

    return data_sources.data_file("zenodo_13777072_stats.csv")


# The authors' `sinter plot` arguments (step3_plot at 871e68f). The only changes: the filters also
# admit our decoders, the point labels stay on the paper's series, and in Fig. 21 our series get
# their own group label (otherwise they would merge with the paper's).
GROUP_13 = (
    "{'sort': 'tsz'.index(decoder.split('_')[-1]), 'color': decoder.split('_')[-1], "
    "'linestyle': decoder.split('_')[0][::-1], "
    "'label': f'''gate={decoder.split('_')[-1].upper()}, sim={'stabilizer[twirl-T]' if decoder == 'twirl_intercept_t' "
    "else decoder.split('_')[0].replace('twirl', 'stabilizer').replace('vec', 'Vector').replace('tsimGPU', 'Tsim GPU')}'''}"
)
LABEL_21 = ("f'''p={round(m.p / 10**math.floor(math.log10(m.p * 1.01)))}e{math.floor(math.log10(m.p * 1.01))}''' "
            "if 'unitary' in m.c and decoder == 'perfectionist' else ''")
GROUP_21 = ("{'color': str(m.d1) + m.c, 'marker': str(m.d1) + m.c, "
            "'linestyle': 0 if decoder == 'perfectionist' else (1 if decoder.endswith('S') else 2), "
            "'sort': (m.d1, m.c, decoder), "
            "'label': f'''d1={m.d1} c={m.c}''' + (' [' + decoder.replace('tsimGPU-', 'Tsim GPU, ') + ']' "
            "if decoder.startswith('tsimGPU') else ' [paper, S]')}")


def figures(results):
    """Figs. 13 and 21 with the authors' own ``sinter plot`` commands on their released stats plus ours."""
    from repro import plotting

    figs = []
    out = common.REPORT / "figures" / STUDY
    out.mkdir(parents=True, exist_ok=True)
    src = HERE / "stim_src" / "github_magic-state-cultivation" / "src"
    ours13, ours21 = [], []
    for r in results.values():
        pr, t = r["params"], r["totals"]
        md = dict(b="Y", c=f"inject[{pr['style']}]+cultivate", d1=pr["d"], g="css", noise="uniform", p=pr["p"])
        if pr["d"] == 3 and pr["style"] == "unitary" and pr["p"] in P13:
            ours13.append(plotting.sinter_stats(t, f"tsimGPU_intercept_{pr['gate']}", dict(md, q=15, r=4)))
        if pr["p"] in P21 and pr["gate"] in ("s", "t"):
            ours21.append(plotting.sinter_stats(t, "tsimGPU-S" if pr["gate"] == "s" else "tsimGPU-T", md))
    csv13 = plotting.write_sinter_csv(out / "ours_fig13.csv", ours13)
    csv21 = plotting.write_sinter_csv(out / "ours_fig21.csv", ours21)

    f13 = out / "t-vs-s.png"
    plotting.sinter_plot([
        "--in", _stats_path(), csv13,
        "--title", "Comparing Cultivation of T|+>, S|+>, and Z|+> States",
        "--subtitle", "c=inject[unitary]+cultivate, d1=3, g=css, noise=uniform, q=15, r=4",
        "--type", "error_rate",
        "--x_func", "(stat.shots + 1) / (stat.shots - stat.discards + 2)",
        "--xmin", "1", "--xmax", "100",
        "--xaxis", "[log]Expected Attempts per Kept Shot",
        "--yaxis", "[log]Logical Error Rate (per kept shot)",
        "--group_func", GROUP_13,
        "--point_label_func", "f'''p={m.p}''' * (decoder.split('_')[-1] == 't' and decoder.startswith('vec'))",
        "--ymax", "1e-2", "--ymin", "1e-7",
        "--fig_size", "2048", "1024", "--dpi", "200",
        "--filter_func", "'intercept' in decoder and ('vec' in decoder or 'tsimGPU' in decoder)",
        "--out", f13])
    pts = [k for k, r in results.items() if r["params"]["d"] == 3 and r["params"]["style"] == "unitary" and r["params"]["p"] in P13]
    figs.append(common.Figure(
        "gidney13", f13, "Gidney et al. Fig. 13: cultivating $T|+\\rangle$, $S|+\\rangle$, $Z|+\\rangle$ states ($d=3$, no escape)",
        "Drawn with the authors' own \\texttt{sinter plot} command (\\texttt{step3\\_plot}) on the paper's released stats "
        "(sim=Vector: their state-vector simulation) plus ours (sim=Tsim GPU). Every detector postselected; noiseless final "
        "logical check. $S$ and $Z$ are Clifford proxies of the same circuit.",
        common.budget_line(results, pts)))

    f21 = out / "inject-only-sampled.png"
    plotting.sinter_plot([
        "--in", _stats_path(), csv21,
        "--preprocess_stats_func", "__import__('cultiv').split_by_gap_threshold(stats, gap_rounding=5)",
        "--type", "error_rate",
        "--group_func", GROUP_21,
        "--x_func", "(stat.shots + 1) / (stat.shots - stat.discards + 2)",
        "--title", "Cost of Injection+Cultivation without the Escape Stage by Monte Carlo Sampling",
        "--subtitle", "({common})",
        "--point_label_func", LABEL_21,
        "--filter_func", "']+cultivate' in m.c and (decoder == 'perfectionist' or decoder.startswith('tsimGPU')) and m.noise == 'uniform' and m.b == 'Y'",
        "--fig_size", "2048", "1024", "--dpi", "200",
        "--xaxis", "[log]Expected Attempts per Kept Shot",
        "--yaxis", "[log]Error Rate (per Kept Shot)",
        "--xmin", "1e0", "--xmax", "1e2", "--ymax", "1e-0", "--ymin", "1e-15",
        "--out", f21], pythonpath=[src])
    pts = [k for k, r in results.items() if r["params"]["p"] in P21 and r["params"]["gate"] in ("s", "t")]
    figs.append(common.Figure(
        "gidney21", f21, "Gidney et al. Fig. 21: injection + cultivation without escape, Monte Carlo sampling",
        "Drawn with the authors' own \\texttt{sinter plot} command on the paper's released stats ([paper, S]: Stim, $S$ proxy, "
        "up to $10^{12}$ shots per point) plus ours: [Tsim GPU, S] the same $S$ proxy on the GPU, [Tsim GPU, T] the real $T$ circuit. "
        "Shaded: hypotheses within a factor 1000 of the maximum likelihood.",
        common.budget_line(results, pts)))
    figs.append(table(results, published()))
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

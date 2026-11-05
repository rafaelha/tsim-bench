r"""Hetényi, Brown, Williamson (2026), arXiv:2603.05429 -- gauging Clifford-measurement cultivation, Fig. 4 and Table 1.

- Fig. 4(a): $d=3$, $p$ = 0.1--0.5\%: logical error rate vs. success probability of the authors' Stim
  simulation of the $|{+i}\rangle$ proxy, and of qiskit state-vector simulations of $|{+i}\rangle$ and $|T\rangle$.
- Fig. 4(b): success probability vs. $p$ (1e-4 to 1e-3) for gauging and for Gidney et al.'s cultivation,
  $d = 3, \dots, 11$.
- Fig. 4(c) and Table 1: $P_L$ and expected volume for $d=3,5$ at $p$ = 1e-3 and 5e-4 (the $d=7$ entries are
  skipped here, as agreed).

Every detector is postselected, including a final noiseless stabilizer round.

Circuits: the authors' generator ``get_stim_circ_w_growing(d, basis="Y", pipeline=True)`` with their
``utils.add_noise`` (uniform $p$), as in their notebook (``gauging_clifford_measurement.ipynb``, IBM at
ce90c09). Clifford proxy: as generated, final noiseless $Y_L$ readout. $T$ version: every $S$/$S^\dagger$
becomes $T$/$T^\dagger$ (as in the authors' qiskit check), and a noiseless logical rotation
$\exp(\mp i\pi Z_L/8)$ (``repro/magic_check.py``) is inserted before the readout so that $Y_L$ checks the
$T$ state deterministically, the same observable as the paper's per-shot $XS^\dagger$ expectation. For
Fig. 4(b), exactly the circuits of the notebook's yield comparison: ``pipeline=False`` for gauging, and
the repository's ``cultivation_stim_circuits/noiseless_cultivation_circuit_d*.stim`` with ``add_noise``
for cultivation (success probability only, Clifford proxies).

Figures (a) and (b) are drawn with the notebook's own plotting code (cells 18 and 7) and its data
(cell 17; ``yield_comparison/*.pkl``) overlaid.
"""

import functools
import json
import re
import sys

from repro import common, data_sources, magic_check
from repro.common import Point

STUDY = "gauging_cultivation"
HERE = common.PAPERS / "2603.05429_gauging_clifford_cultivation"
SRC = HERE / "stim_src" / "gauging_clifford_measurement"
META = dict(arxiv="2603.05429", paper="Hetényi, Brown, Williamson (2026), Constant-depth magic state cultivation with Clifford measurements by gauging")
P3 = [5e-4, 1e-3, 2e-3, 3e-3, 4e-3, 5e-3]
P5 = [5e-4, 1e-3, 2e-3]
PY = [1e-4 * k for k in range(1, 11)]
DY = [3, 5, 7, 9, 11]
# Table 1: (p, d) -> (P_L, err, p_succ)
TABLE = {(1e-3, 3): (8.8e-7, 0.8e-7, 0.46), (1e-3, 5): (3.2e-10, 0.4e-10, 0.04),
         (5e-4, 3): (1.2e-7, 0.2e-7, 0.65), (5e-4, 5): (1.1e-11, 0.3e-11, 0.20)}
# Notebook cell 17 (the data of Fig. 4(a)).
NB_A = {
    "stim_Y": dict(err_list=[0.001, 0.002, 0.003, 0.004, 0.005], yield_list=[0.46065795, 0.21261851, 0.09832248, 0.04558834, 0.02117186],
                   LF_list=[8.90031313e-07, 7.61928018e-06, 3.03084300e-05, 6.97546785e-05, 1.45948443e-04],
                   LF_errlist=[1.39844528e-07, 5.99550283e-07, 1.75719251e-06, 3.91472212e-06, 8.30943152e-06]),
    "qiskit_Y": dict(err_list=[0.001, 0.002, 0.003, 0.004, 0.005], yield_list=[0.46073113, 0.21268602, 0.09834676, 0.04551968, 0.02113491],
                     LF_list=[1.27983407e-06, 8.71338546e-06, 2.39828694e-05, 6.47697159e-05, 1.19570503e-04],
                     LF_errlist=[4.83731812e-07, 1.85770002e-06, 4.53233629e-06, 1.09480802e-05, 2.18304872e-05]),
    "qiskit_T": dict(err_list=[0.001, 0.002, 0.003, 0.004, 0.005], yield_list=[0.46065515, 0.21263031, 0.098486, 0.04556521, 0.02117048],
                     LF_list=[2.19152240e-07, 8.07133924e-06, 2.35762749e-05, 6.20363888e-05, 1.19215088e-04],
                     LF_errlist=[2.19152240e-07, 1.95758731e-06, 4.91599314e-06, 1.17237755e-05, 2.38430176e-05]),
}


@functools.lru_cache(None)
def _gen():
    sys.path.insert(0, str(SRC))
    from color_code import get_stim_circ_w_growing
    from utils import add_noise

    return get_stim_circ_w_growing, add_noise


def drop_targetless(text):
    keep = ("TICK", "DETECTOR", "OBSERVABLE_INCLUDE", "SHIFT_COORDS")
    return re.sub(rf"^\s*(?!{'|'.join(keep)})[A-Z_0-9]+(\([^)]*\))?\s*$\n", "", text, flags=re.M)


def _noisy(circ, p):
    _, add_noise = _gen()
    return drop_targetless(str(add_noise(circ, CX_error=p, meas_error=p, single_qubit_error=p, gate_idle_error=p)))


def make(d, p, variant):
    get, _ = _gen()
    proxy = _noisy(get(d, basis="Y", pipeline=True), p)
    if variant == "s":
        common.noiseless_check(proxy)
        return proxy
    t = common.s_to_t(proxy)
    last_mpp = [l for l in t.splitlines() if l.startswith("MPP ")][-1].split()
    assert len(last_mpp) == 2, last_mpp
    _, zl = magic_check.split_y(magic_check.parse_product(last_mpp[1]))
    text, _ = magic_check.make_deterministic(t, zl)
    return text


def make_yield(proto, d, p):
    import stim

    get, _ = _gen()
    if proto == "gauging-nopipeline":
        circ = get(d, basis="Y", pipeline=False)
    elif proto == "gauging":
        # The pickle is named "nopipeline", but at ce90c09 pipeline=False gives success probabilities 15-50%
        # below it (0.379 vs 0.448 at d=3, p=1e-3), while pipeline=True (the circuit of Fig. 4(a)) is within
        # 3-10% (0.461 vs 0.448; d=5: 0.040 vs 0.036). We use pipeline=True; see the figure caption.
        circ = get(d, basis="Y", pipeline=True)
    else:
        circ = stim.Circuit((SRC / "cultivation_stim_circuits" / f"noiseless_cultivation_circuit_d{d}.stim").read_text())
    text = _noisy(circ, p)
    common.noiseless_check(text, require_deterministic_observables=False)
    return text


def combos():
    return [(3, p, v) for p in P3 for v in ("s", "t")] + [(5, p, v) for p in P5 for v in ("s", "t")]


def name(d, p, v):
    return f"d{d}_p{p:g}_{v}"


def yname(proto, d, p):
    return f"yield_{proto}_d{d}_p{p:.0e}"


def circuits():
    out = {name(*c): functools.partial(make, *c) for c in combos()}
    for proto in ("gauging", "cultivation"):
        for d in DY:
            for p in PY:
                out[yname(proto, d, p)] = functools.partial(make_yield, proto, d, p)
    for d in (3, 5):  # pipeline=False, for the comparison with the pickle's yields quoted in the Fig. 4(b) caption
        out[yname("gauging-nopipeline", d, 1e-3)] = functools.partial(make_yield, "gauging-nopipeline", d, 1e-3)
    return out


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
    for proto in ("gauging", "cultivation"):
        for d in DY:
            for p in PY:
                # Success probability only (Fig. 4(b)): 1e8 shots resolve p_succ down to ~1e-6.
                pts.append(Point(yname(proto, d, p), yname(proto, d, p), "clifford", dict(kind="yield", proto=proto, d=d, p=p, gate="s"),
                                 target_errors=10**18, max_shots=1e8, max_seconds=60, tier=1, observable_reference=False))
    for d in (3, 5):
        pts.append(Point(yname("gauging-nopipeline", d, 1e-3), yname("gauging-nopipeline", d, 1e-3), "clifford",
                         dict(kind="yield", proto="gauging-nopipeline", d=d, p=1e-3, gate="s"),
                         target_errors=10**18, max_shots=1e8, max_seconds=60, tier=1, observable_reference=False))
    return pts


def _volume(circuit_text):
    """Qubits x circuit steps (TICK layers), our reading of the paper's 'expected volume (qubits x steps)'."""
    import stim

    c = stim.Circuit(circuit_text)
    steps = sum(1 for inst in c.flattened() if inst.name == "TICK") + 1
    return c.num_qubits * steps


def _pipeline_note(results, paper_g):
    """The generator at ce90c09 vs the pickle's gauging yields, from our own points (p = 1e-3)."""
    rows = []
    for d in (3, 5):
        a = results.get(yname("gauging-nopipeline", d, 1e-3))
        b = results.get(yname("gauging", d, 1e-3))
        y = paper_g[str(d)]["yield"][-1]
        if a and b and a["totals"]["shots"] and b["totals"]["shots"]:
            rows.append(f"$d={d}$: pickle {y:.3f}, \\texttt{{pipeline=False}} {a['totals']['kept'] / a['totals']['shots']:.3f}, "
                        f"\\texttt{{pipeline=True}} {b['totals']['kept'] / b['totals']['shots']:.3f}")
    if not rows:
        return ""
    return ("The generator at the released commit does not reproduce the pickled gauging yields exactly (at $p=10^{-3}$: " + "; ".join(rows)
            + "), although the pickle is named ``nopipeline''; we show \\texttt{pipeline=True}, the circuit of panel (a) and Table 1, "
            "which is closest, so the pickle was presumably made with an earlier version of the generator.")


def figures(results):
    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    out.mkdir(parents=True, exist_ok=True)
    figs = []
    main = {k: r for k, r in results.items() if r["params"].get("kind") != "yield"}

    # ---- Fig. 4(a): the notebook's cell 18, with our two series appended.
    fig = plt.figure(figsize=(4, 3))
    ours = {}
    for g in ("s", "t"):
        rows = sorted((r["params"]["p"], r["totals"]) for r in main.values() if r["params"]["d"] == 3 and r["params"]["gate"] == g
                      and r["params"]["p"] >= 1e-3)
        ours[g] = dict(err_list=np.array([p for p, _ in rows]), yield_list=np.array([t["kept"] / t["shots"] for _, t in rows]),
                       LF_list=np.array([t["errors"] / t["kept"] for _, t in rows]),
                       LF_errlist=np.array([np.sqrt(t["errors"] + 0.5) / t["kept"] for _, t in rows]))
    series = [(NB_A["stim_Y"], r"$|+i\,\rangle$ stim", "-"), (NB_A["qiskit_Y"], r"$|+i\,\rangle$ qiskit", "-"),
              (NB_A["qiskit_T"], r"$|\,T\,\rangle$ qiskit", ":"), (ours["s"], r"$|+i\,\rangle$ Tsim GPU", "--"),
              (ours["t"], r"$|\,T\,\rangle$ Tsim GPU", "--")]
    i = 1
    for res_dict, label, style in series:
        if not len(res_dict["yield_list"]):
            continue
        res = {k: np.asarray(v) for k, v in res_dict.items()}
        plt.errorbar(res["yield_list"], res["LF_list"], yerr=res["LF_errlist"], label=label, marker="o", linestyle=style)
        plt.fill_between(res["yield_list"], res["LF_list"] - res["LF_errlist"], res["LF_list"] + res["LF_errlist"], alpha=0.2)
        if i:
            for physerr, yd, logerr in zip(res["err_list"], res["yield_list"], res["LF_list"]):
                plt.text(yd * .85, logerr * (2.5 - 200 * physerr), r"$p=" + str(physerr) + r"$", fontsize=9, fontfamily="serif")
            i = 0
    plt.loglog()
    plt.legend(prop={"family": "serif", "size": 7})
    plt.xlabel(r"success probability $p_\mathrm{succ}$", fontsize=10, fontfamily="serif")
    plt.ylabel(r"logical error rate $P_L$", fontsize=10, fontfamily="serif")
    plt.xlim(1e-2, 1)
    plt.ylim(1e-7, 4e-4)
    path_a = plotting.save(fig, out / "fig4a.pdf")

    # ---- Fig. 4(b): the notebook's cell 7 (yield comparison), paper (pickles) and ours.
    yres = {k: r for k, r in results.items() if r["params"].get("kind") == "yield"}
    paper_g = json.loads(data_sources.data_file("GaugingClifford_high_dist_yield_nopipeline.json").read_text())
    paper_c = json.loads(data_sources.data_file("Gidney_cultivation_high_dist_yield.json").read_text())
    fig = plt.figure(figsize=(4, 3))
    colors = ["blue", "orange", "green", "red", "purple"]
    for d, c in zip(paper_g["d_list"], colors):
        plt.plot(paper_g["err_list"], paper_g[str(d)]["yield"], ".-", color=c, alpha=0.35, lw=3, label="gauging d=" + str(d) + " (paper)")
    for d, c in zip(paper_c["d_list"], colors):
        plt.plot(paper_c["err_list"], paper_c[str(d)]["yield"], ".--", color=c, alpha=0.35, lw=3, label="cultiv. d=" + str(d) + " (paper)")
    for proto, ls in (("gauging", ".-"), ("cultivation", ".--")):
        for d, c in zip(DY, colors):
            rows = sorted((r["params"]["p"], r["totals"]["kept"] / r["totals"]["shots"]) for r in yres.values()
                          if r["params"]["proto"] == proto and r["params"]["d"] == d and r["totals"]["shots"])
            if rows:
                plt.plot([x for x, _ in rows], [y for _, y in rows], ls, color=c, lw=0.9, ms=3,
                         label=("gauging" if proto == "gauging" else "cultiv.") + f" d={d} (Tsim GPU)")
    plt.yscale("log")
    fig.legend(ncol=2, bbox_to_anchor=(1.62, 0.5), loc="center right", prop={"family": "serif", "size": 5.5})
    plt.xlim(5e-5, 1.05e-3)
    plt.ylim(1e-5, 2)
    plt.xlabel(r"physical error rate $p_\mathrm{phys}$", fontfamily="serif")
    plt.ylabel(r"success probability $p_\mathrm{succ}$", fontfamily="serif")
    path_b = plotting.save(fig, out / "fig4b.pdf")

    # ---- Fig. 4(c): P_L vs expected volume, d = 3, 5 at p = 1e-3 (stars) and 5e-4 (circles).
    fig, ax = plt.subplots(figsize=(4, 3))
    g = common.load_results("gidney_cultivation")
    from repro.studies import gidney_cultivation as gc

    for proto, col in (("cultivation", "blue"), ("gauging", "red")):
        for d in (3, 5):
            for p, mk in ((1e-3, "*"), (5e-4, "o")):
                for gate, fill in (("s", True), ("t", False)):
                    if proto == "gauging":
                        r = main.get(name(d, p, gate))
                        circ = common.circuit_path(STUDY, name(d, p, "s"))
                    else:
                        r = g.get(gc.cname(d, "unitary", p, gate))
                        circ = common.circuit_path("gidney_cultivation", gc.cname(d, "unitary", p, "s"))
                    if not r or not r["totals"]["kept"] or not circ.exists():
                        continue
                    t = r["totals"]
                    vol = _volume(circ.read_text()) * t["shots"] / t["kept"]
                    ler = t["errors"] / t["kept"] if t["errors"] else common.binomial_interval(0, t["kept"])[2]
                    ax.plot([vol], [ler], mk, color=col, ms=9 if mk == "*" else 6, mfc=col if fill else "none",
                            label=f"{proto} @ p={p:g}, {'S proxy' if gate == 's' else 'T'}" + (" (upper bound)" if not t["errors"] else ""))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(2e2, 5e6)
    ax.set_ylim(1e-13, 1e-5)
    ax.set_xlabel(r"expected volume (qubits $\times$ steps)", fontfamily="serif")
    ax.set_ylabel(r"logical error rate $P_L$", fontfamily="serif")
    ax.legend(fontsize=5)
    path_c = plotting.save(fig, out / "fig4c.pdf")

    # Combined, as in the paper (three panels side by side).
    import matplotlib.image as mpimg  # noqa: F401

    figs.append(common.Figure(
        "gauging_a", path_a, "Hetényi et al. Fig. 4(a): $d=3$, logical error rate vs.\\ success probability",
        "Drawn with the authors' notebook code (cell 18) and data (cell 17): $|{+i}\\rangle$ stim, and their qiskit state-vector "
        "$|{+i}\\rangle$ and $|T\\rangle$; dashed: ours on the GPU ($|{+i}\\rangle$ proxy and real $T$, $p$ = 1e-3 to 5e-3).",
        common.budget_line(main, [k for k, r in main.items() if r["params"]["d"] == 3])))
    figs.append(common.Figure(
        "gauging_b", path_b, "Hetényi et al. Fig. 4(b): success probability, gauging vs.\\ cultivation, $d=3,\\dots,11$",
        "The notebook's cell 7 on its pickled data (thick, faint) and ours on the GPU (thin): gauging from the authors' generator, "
        "cultivation from the repository's \\texttt{cultivation\\_stim\\_circuits} with \\texttt{add\\_noise}; $10^8$ shots per point. "
        + _pipeline_note(results, paper_g),
        common.budget_line(yres)))
    figs.append(common.Figure(
        "gauging_c", path_c, "Hetényi et al. Fig. 4(c): logical error rate vs.\\ expected volume, $d=3,5$",
        "Stars: $p=10^{-3}$; circles: $p=5\\times10^{-4}$; filled: Clifford proxy; open: real $T$. Volume = qubits $\\times$ TICK "
        "layers of the circuit, divided by the success probability (the paper's exact volume convention is not released, so the "
        "horizontal positions may be shifted by a constant factor). Cultivation points are the Gidney study's.",
        common.budget_line(main, [k for k, r in main.items() if r["params"]["d"] in (3, 5)])))
    # Table 1, in the paper's format with our columns.
    rows = []
    for p in (1e-3, 5e-4):
        for d in (3, 5):
            pl, e, ps = TABLE[(p, d)]
            cells = [f"{100 * p:g}\\%" if d == 3 else "", f"{d}", f"$({pl / 10**np.floor(np.log10(pl)):.1f}\\pm {e / 10**np.floor(np.log10(pl)):.1f})\\times 10^{{{int(np.floor(np.log10(pl)))}}}$", f"{100 * ps:g}\\%"]
            for g in ("s", "t"):
                r = main.get(name(d, p, g))
                if r and r["totals"]["kept"]:
                    t = r["totals"]
                    ler = t["errors"] / t["kept"]
                    sig = ler / np.sqrt(t["errors"]) if t["errors"] else 0
                    cells.append(f"{ler:.2g} $\\pm$ {sig:.1g} ({t['errors']})" if t["errors"] else f"$<${common.binomial_interval(0, t['kept'])[2]:.1g}")
                    cells.append(f"{100 * t['kept'] / t['shots']:.1f}\\%")
                else:
                    cells += ["--", "--"]
            rows.append(" & ".join(cells) + r" \\")
    tpath = out / "table1.tex"
    tpath.write_text("\\begin{tabular}{cc cc | cc | cc}\n\\toprule\n & & \\multicolumn{2}{c|}{paper ($|{+i}\\rangle$, stim)} & "
                     "\\multicolumn{2}{c|}{Tsim GPU, $|{+i}\\rangle$} & \\multicolumn{2}{c}{Tsim GPU, $T$}\\\\\n"
                     "$p_\\text{phys}$ & $d_f$ & $P_L$ & $p_\\text{succ}$ & $P_L$ & $p_\\text{succ}$ & $P_L$ & $p_\\text{succ}$\\\\\n\\midrule\n"
                     + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    figs.append(common.Figure("gauging_table", tpath, "Hetényi et al. Table 1 (the $d_f=7$ rows are not attempted)",
                              "Logical error probability $P_L$ and success rate $p_\\text{succ}$; Tsim errors in parentheses.",
                              common.budget_line(main, [k for k, r in main.items() if r["params"]["d"] in (3, 5)]), kind="table"))
    return figs


def checks(results):
    rows = []
    for (p, d), (pl, e, ps) in TABLE.items():
        r = results.get(name(d, p, "s"))
        if r:
            rows.append(common.check_row(f"d={d} p={p:g} |+i> proxy", "clifford", dict(value=pl, sigma=e), r["totals"]))
            rows.append(common.check_row(f"d={d} p={p:g} |+i> proxy", "clifford", dict(value=ps), r["totals"], quantity="acceptance"))
    for key, nb in (("stim_Y", "s"),):
        for p, y, lf, le in zip(NB_A[key]["err_list"], NB_A[key]["yield_list"], NB_A[key]["LF_list"], NB_A[key]["LF_errlist"]):
            r = results.get(name(3, p, nb))
            if r:
                rows.append(common.check_row(f"d=3 p={p:g} |+i> (notebook)", "clifford", dict(value=lf, sigma=le), r["totals"]))
                rows.append(common.check_row(f"d=3 p={p:g} |+i> (notebook)", "clifford", dict(value=y, sigma=(y * (1 - y) / 1e7) ** .5), r["totals"], quantity="acceptance"))
    for p, y, lf, le in zip(NB_A["qiskit_T"]["err_list"], NB_A["qiskit_T"]["yield_list"], NB_A["qiskit_T"]["LF_list"], NB_A["qiskit_T"]["LF_errlist"]):
        r = results.get(name(3, p, "t"))
        if r:
            rows.append(common.check_row(f"d=3 p={p:g} T (notebook, qiskit)", "t", dict(value=lf, sigma=le), r["totals"]))
    for proto, f in (("gauging", "GaugingClifford_high_dist_yield_nopipeline.json"), ("cultivation", "Gidney_cultivation_high_dist_yield.json")):
        pj = json.loads(data_sources.data_file(f).read_text())
        for d in DY:
            for p, y in zip(pj["err_list"], pj[str(d)]["yield"]):
                r = results.get(yname(proto, d, p))
                if r:
                    rows.append(common.check_row(f"{proto} d={d} p={p:.0e} success (pickle)", "clifford", dict(value=y), r["totals"], quantity="acceptance"))
    return [x for x in rows if x]

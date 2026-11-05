r"""Wang, Gu (2026), Magna, arXiv:2610.22315 -- Figs. 8(a) and 9(a,b).

- Fig. 8(a): Bravyi--Haah $(3k+8)$-to-$k$ distillation on bare qubits, $k=2,6,10$. Every input
  magic state has a $Z$ error with probability $p$; everything else is noiseless. Plotted: the joint
  infidelity of the $k$ outputs with $|T\rangle^{\otimes k}$, for $p$ from $10^{-4}$ to $10^{-3}$.
- Fig. 9(a,b): colour-code and RP$^2$ cultivation at $d=3,5$ (no escape), acceptance rate and
  infidelity of accepted runs under uniform depolarizing noise.

Circuits: Magna's own example protocols (itpyi/magna at 01ae9c2, ``examples/*/physical.magna``),
translated to the Tsim dialect by our ``make_circuits.py`` (deferred-measurement controlled
corrections etc.). The examples are written at $p=10^{-3}$ and Magna ships no generator, so other
noise strengths are made by changing that literal. Only the detectors named in the examples'
``POSTSELECT`` lines are postselected. The error check is the examples' task definition: undo the
ideal target circuit on the output qubits and require every output to read 0 (a joint check).
Clifford versions: Magna's ``-S`` examples (product-$S$ targets); for the colour code the $S$ proxy is
in the Gidney study.
"""

import functools
import importlib.util
import json
import re
import sys

from repro import common
from repro.common import Point

STUDY = "magna"
HERE = common.PAPERS / "2610.22315_magna"
EX = HERE / "stim_src" / "magna" / "examples"
META = dict(arxiv="2610.22315", paper="Wang, Gu (2026), Magna: simulating magic state factories as cheaply as Clifford circuits")
P8 = [1e-4, 2e-4, 5e-4, 1e-3]
P9 = [5e-4, 1e-3, 2e-3]
BH = [2, 6, 10]
CULT = ["color3", "color5", "rp2-d3", "rp2-d5"]
CULT_S = ["rp2-d3-S", "rp2-d5-S"]


@functools.lru_cache(None)
def _mc():
    sys.path.insert(0, str(common.ROOT / "tools"))
    spec = importlib.util.spec_from_file_location("magna_make_circuits", HERE / "make_circuits.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def with_noise(source, p):
    return re.sub(r"\(0\.001\)", f"({p:g})", source)


def make(example, p):
    m = _mc()
    source = with_noise((EX / example / "physical.magna").read_text(), p)
    text = m.convert(source)
    text = "\n".join(l for l in text.splitlines() if not l.startswith("OBSERVABLE_INCLUDE")) + "\n"
    task = json.loads((EX / example / "task.json").read_text())
    outputs = task["outputs"]
    ideal = [x for x in (m.parse(raw) for raw in (EX / example / task["ideal_state"]).read_text().splitlines()) if x]
    undo = []
    for name, _, _, ts in reversed(ideal):
        arity = 2 if name in ("CX", "CZ") else 1
        groups = [ts[k:k + arity] for k in range(0, len(ts), arity)]
        for group in reversed(groups):
            undo.append(f"{m.INVERSE[name]} {' '.join(str(outputs[int(t)]) for t in group)}")
    text += "\n".join(undo) + "\n" + f"M {' '.join(map(str, outputs))}\n" + "".join(
        f"OBSERVABLE_INCLUDE({k}) rec[{k - len(outputs)}]\n" for k in range(len(outputs)))
    post = m.postselected_detectors(source)
    _check(text, post)
    return text


def _check(text, post):
    import numpy as np
    import tsim

    s = tsim.Circuit(common.strip_noise(text)).compile_detector_sampler(seed=1)
    a = np.asarray(s.sample(512, append_observables=True)).astype(bool)
    nd = tsim.Circuit(text).num_detectors
    det = a[:, :nd]
    if post:
        if (det[:, post] != det[0, post]).any():
            raise ValueError("postselected detector random without noise")
        keep = ~(det[:, post] != det[0, post]).any(1)
    else:
        keep = np.ones(len(a), bool)
    if not keep.any():
        raise ValueError("no shot passes postselection without noise")
    if (a[keep, nd:]).any():
        raise ValueError("target check fails without noise")


@functools.lru_cache(None)
def postselected(example):
    return _mc().postselected_detectors((EX / example / "physical.magna").read_text())


def combos():
    out = [(f"bh{k}-{g}", p) for k in BH for g in ("T", "S") for p in P8]
    out += [(e, p) for e in CULT + CULT_S for p in P9]
    return out


def name(e, p):
    return f"{e}_p{p:g}"


def circuits():
    return {name(e, p): functools.partial(make, e, p) for e, p in combos()}


def points():
    pts = []
    for e, p in combos():
        variant = "clifford" if e.endswith("-S") else "t"
        kw = dict(postselect=postselected(e), detector_reference=True, observable_reference=False)
        if e.startswith("bh"):
            pts.append(Point(name(e, p), name(e, p), variant, dict(example=e, p=p), target_errors=20000, max_shots=2e12,
                             max_seconds=240, tier=1, **kw))
        elif e in ("color3", "rp2-d3", "rp2-d3-S", "rp2-d5-S"):
            pts.append(Point(name(e, p), name(e, p), variant, dict(example=e, p=p), target_errors=20000, max_shots=2e12,
                             max_seconds=420, tier=1, **kw))
        elif e == "color5":
            pts.append(Point(name(e, p), name(e, p), variant, dict(example=e, p=p), target_errors=1000, max_shots=1e13,
                             max_seconds={5e-4: 1500, 1e-3: 900, 2e-3: 600}[p], tier=3 if p < 2e-3 else 2, **kw))
        else:  # rp2-d5, k = 9
            pts.append(Point(name(e, p), name(e, p), variant, dict(example=e, p=p), target_errors=1000, max_shots=1e13,
                             max_seconds={5e-4: 1800, 1e-3: 1800, 2e-3: 1200}[p], tier=3, **kw))
    return pts


def bh_leading(k, p):
    """Bravyi--Haah leading order: output error (1 + 3k) p^2 (joint over the k outputs)."""
    return (1 + 3 * k) * p**2


def figures(results):
    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting
    from repro.studies import gidney_cultivation, soft_d5

    out = common.REPORT / "figures" / STUDY
    figs = []

    def ser(e):
        return sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["example"] == e)

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for k, col in zip(BH, ("C0", "C1", "C2")):
        plotting.ler_points(axes[0], ser(f"bh{k}-T"), color=col, label=f"k={k}, T")
        plotting.ler_points(axes[0], ser(f"bh{k}-S"), color=col, ls="--", marker="s", label=f"k={k}, S")
        plotting.accept_points(axes[1], ser(f"bh{k}-T"), color=col, label=f"k={k}")
    plotting.style_ler(axes[0], "input error probability $p$")
    axes[0].set_ylabel("joint output infidelity")
    plotting.style_accept(axes[1], "input error probability $p$")
    axes[0].legend(fontsize=5.5)
    path = plotting.save(fig, out / "fig8a_bh.pdf")
    pts = [k for k, r in results.items() if r["params"]["example"].startswith("bh")]
    figs.append(common.Figure("magna8", path, "Magna Fig. 8(a): Bravyi--Haah $(3k+8)$-to-$k$ distillation",
                              "Bare qubits, $Z$ errors of probability $p$ on the input magic states only. The $T$ and $S$ curves coincide, as they "
                              "should when the only errors are $Z$ errors on the inputs. "
                              "Dashed/squares: the matched Clifford circuit ($|S\\rangle$ inputs, product-$S$ target).",
                              common.budget_line(results, pts)))

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    cols = {"color3": "C0", "color5": "C3", "rp2-d3": "C2", "rp2-d5": "C1"}
    for e, col in cols.items():
        plotting.ler_points(axes[0], ser(e), color=col, label=f"{e}, T")
        plotting.accept_points(axes[1], ser(e), color=col, label=e)
        if e + "-S" in CULT_S:
            plotting.ler_points(axes[0], ser(e + "-S"), color=col, ls="--", marker="s", label=f"{e}, S")
    pub = [r for r in gidney_cultivation.published() if r["d"] == 3 and r["style"] == "unitary" and r["decoder"] == "vec_intercept_t" and r["p"] <= 2e-3]
    plotting.published_ler(axes[0], pub, color="C0", label="Gidney et al. (state vector)")
    grid = soft_d5.exact_grid()
    axes[0].plot([g[0] for g in grid], [g[2] for g in grid], "x", color="C3", ms=6, mew=1.5, label="exact (2609.18922)")
    axes[1].plot([g[0] for g in grid], [g[1] for g in grid], "x", color="C3", ms=6, mew=1.5)
    plotting.style_ler(axes[0], "noise strength $p$")
    axes[0].set_ylabel("infidelity of accepted runs")
    plotting.style_accept(axes[1], "noise strength $p$", log=True)
    axes[0].legend(fontsize=5.5)
    path = plotting.save(fig, out / "fig9_cultivation.pdf")
    pts = [k for k, r in results.items() if not r["params"]["example"].startswith("bh")]
    figs.append(common.Figure("magna9", path, "Magna Fig. 9(a,b): colour-code and RP$^2$ cultivation at $d=3,5$",
                              "Magna's cultivation examples (no escape). Markers as in the paper: Gidney et al.'s state-vector values for Color $d=3$ "
                              "and the exact values of arXiv:2609.18922 for Color $d=5$. Dashed: Magna's $S$-target RP$^2$ examples.",
                              common.budget_line(results, pts)))
    return figs

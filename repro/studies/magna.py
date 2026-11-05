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
P9_D3 = [5e-4, 1e-3, 2e-3, 3e-3, 5e-3]  # the paper's Fig. 9 grid
P9_D5 = [5e-4, 7e-4, 1e-3, 1.5e-3, 2e-3]
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
    """Scale every noise argument of the p = 1e-3 example by p / 1e-3 (noise channels and measurement flips)."""
    f = p / 1e-3
    noise = r"(DEPOLARIZE1|DEPOLARIZE2|X_ERROR|Y_ERROR|Z_ERROR|PAULI_CHANNEL_1|PAULI_CHANNEL_2|M|MX|MY|MZ|MR|MRX|MRY|MRZ|MPP)"

    def scale(m):
        args = ", ".join(f"{float(a) * f:.12g}" for a in m[2].split(","))
        return f"{m[1]}({args})"

    return re.sub(rf"\b{noise}\(([0-9.eE+\-, ]+)\)", scale, source)


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


def bh_leading(k, p):
    """Bravyi--Haah leading order: output error (1 + 3k) p^2 (joint over the k outputs)."""
    return (1 + 3 * k) * p**2


def combos():
    out = [(f"bh{k}-{g}", p) for k in BH for g in ("T", "S") for p in P8]
    out += [(e, p) for e in ("color3", "rp2-d3", "rp2-d3-S") for p in P9_D3]
    out += [(e, p) for e in ("color5", "rp2-d5", "rp2-d5-S") for p in P9_D5]
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
                             max_seconds={5e-4: 1500, 7e-4: 900, 1e-3: 900, 1.5e-3: 600, 2e-3: 600}[p], tier=3 if p < 2e-3 else 2, **kw))
        else:  # rp2-d5, k = 9
            pts.append(Point(name(e, p), name(e, p), variant, dict(example=e, p=p), target_errors=1000, max_shots=1e13,
                             max_seconds={5e-4: 1800, 7e-4: 1200, 1e-3: 1800, 1.5e-3: 900, 2e-3: 1200}[p], tier=3, **kw))
    return pts


# The paper's figure style (multi-output-current.pdf, cultivation-comparison.pdf): serif text, no top/right spines.
NAVY, ORANGE, GREEN, PURPLE = "#2b5c8a", "#d1693b", "#3e8a6e", "#9b59a6"


def _style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)


def _ler(t):
    import numpy as np

    if not t["kept"]:
        return None
    y = t["errors"] / t["kept"]
    return y, (1.96 * y / np.sqrt(t["errors"]) if t["errors"] else 0)


def figures(results):
    import matplotlib.pyplot as plt

    from repro import plotting
    from repro.studies import gidney_cultivation, soft_d5

    out = common.REPORT / "figures" / STUDY
    figs = []

    def ser(e):
        return sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["example"] == e)

    rc = {"font.family": "serif", "mathtext.fontset": "cm", "font.size": 9}
    with plt.rc_context(rc):
        # ---- Fig. 8(a): joint-output infidelity vs resource error rate.
        fig, ax = plt.subplots(figsize=(3.6, 3.0))
        for k, col in zip(BH, (NAVY, ORANGE, GREEN)):
            for g, ls, mk in (("T", "-", "o"), ("S", ":", "s")):
                xs, ys, es = [], [], []
                for p, t in ser(f"bh{k}-{g}"):
                    v = _ler(t)
                    if v:
                        xs.append(p)
                        ys.append(v[0])
                        es.append(v[1])
                ax.errorbar(xs, ys, yerr=es, color=col, ls=ls, marker=mk, ms=4, capsize=2,
                            label=f"{3 * k + 8}-to-{k}" + ("" if g == "T" else " ($S$)"))
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Resource error rate $p$")
        ax.set_ylabel("Joint-output infidelity")
        ax.set_title("(a) Error suppression", loc="left")
        ax.legend(frameon=False, fontsize=7)
        _style(ax)
        path = plotting.save(fig, out / "multi-output-current.pdf")
        pts = [k for k, r in results.items() if r["params"]["example"].startswith("bh")]
        figs.append(common.Figure("magna8", path, "Magna Fig. 8(a): Bravyi--Haah $(3k+8)$-to-$k$ distillation, error suppression",
                                  "Same axes and style as the paper. Bare qubits, $Z$ errors of probability $p$ on the input magic states only; "
                                  "bars: $1.96\\sigma$. Solid: real $T$ inputs; dotted: the matched Clifford circuit ($|S\\rangle$ inputs, product-$S$ target, "
                                  "which the paper uses for timing only). The two coincide, as they should with $Z$ errors only. Magna's own numbers are not released.",
                                  common.budget_line(results, pts)))

        # ---- Fig. 9(a,b): acceptance and accepted output infidelity vs p.
        fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(3.8, 6.0))
        style = {"color3": (NAVY, "o", "Color $d=3$"), "color5": (ORANGE, "s", "Color $d=5$"),
                 "rp2-d3": (GREEN, "^", "RP$^2$ $d=3$"), "rp2-d5": (PURPLE, "D", "RP$^2$ $d=5$")}
        for e, (col, mk, lab) in style.items():
            s = [(p, t) for p, t in ser(e) if t["shots"]]
            ax_a.plot([p for p, _ in s], [t["kept"] / t["shots"] for _, t in s], ls="--", marker=mk, color=col, ms=5, label=lab)
            xs, ys, es = [], [], []
            for p, t in s:
                v = _ler(t)
                if v and t["errors"]:
                    xs.append(p)
                    ys.append(v[0])
                    es.append(v[1])
            ax_b.errorbar(xs, ys, yerr=es, ls="--", marker=mk, color=col, ms=5, capsize=2, label=lab)
            if e + "-S" in CULT_S:
                s2 = [(p, t) for p, t in ser(e + "-S") if t["kept"] and t["errors"]]
                ax_b.plot([p for p, _ in s2], [t["errors"] / t["kept"] for _, t in s2], ls=":", marker=mk, mfc="none", color=col, ms=4,
                          label=lab + " ($S$ target)")
        pub3 = [r for r in gidney_cultivation.published() if r["d"] == 3 and r["style"] == "unitary" and r["decoder"] == "vec_intercept_t" and r["p"] <= 5e-3]
        ax_a.plot([r["p"] for r in pub3], [r["kept"] / r["shots"] for r in pub3], "*", color="0.3", mec="k", ms=9, label="Published reference")
        ax_b.plot([r["p"] for r in pub3], [r["errors"] / r["kept"] for r in pub3], "*", color="0.3", mec="k", ms=9, label="Published reference")
        grid = soft_d5.exact_grid()
        ax_a.plot([g[0] for g in grid], [g[1] for g in grid], "*", color="0.3", mec="k", ms=9)
        ax_b.plot([g[0] for g in grid], [g[2] for g in grid], "*", color="0.3", mec="k", ms=9)
        for ax in (ax_a, ax_b):
            ax.set_xscale("log")
            ax.set_xlabel("Physical error rate $p$")
            _style(ax)
        ax_a.set_ylim(0, 1)
        ax_a.set_ylabel("Acceptance probability")
        ax_a.set_title("(a) Acceptance", loc="left")
        ax_b.set_yscale("log")
        ax_b.set_ylabel("Accepted output infidelity")
        ax_b.set_title("(b) Output infidelity", loc="left")
        ax_a.legend(frameon=False, fontsize=6.5)
        path = plotting.save(fig, out / "cultivation-comparison.pdf")
        pts = [k for k, r in results.items() if not r["params"]["example"].startswith("bh")]
        figs.append(common.Figure("magna9", path, "Magna Fig. 9(a,b): colour-code and RP$^2$ cultivation at $d=3,5$",
                                  "Same panels, axes and markers as the paper (stars: Gidney et al.'s state-vector values for Color $d=3$ and the exact "
                                  "values of arXiv:2609.18922 for Color $d=5$; bars: $1.96\\sigma$). Our points are Tsim GPU samples of Magna's own example "
                                  "circuits; the paper's dashed lines are Magna's series expansions, which are not released, so ours are guides to the eye. "
                                  "Open markers, dotted: Magna's $S$-target RP$^2$ examples.",
                                  common.budget_line(results, pts)))
    return figs

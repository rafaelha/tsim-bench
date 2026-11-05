r"""Chan, Strikis, Sun, Cai (2026), arXiv:2609.17706 -- degraded fault distance of T-state cultivation and Z flags.

Pre-escape colour-code cultivation (injection + double checks, every detector postselected,
noiseless final check), with and without the paper's Z flags in the final double check:

- Fig. ``d3_pre_escape_ler``: $d=3$ ($a=6$ ancillas, $f=2$ flags), $S$ vs. $T$;
- Figs. ``d5_pre_escape_ler`` and ``improvement_and_cost_ratios``: $d=5$ ($a=19$, $f=13$), $T$ state, original
  vs. flagged. The abstract quotes a 4.9x LER improvement at 1.36x attempts for $p=10^{-3}$, and 10.9x at
  1.17x for $p=5\cdot10^{-4}$.

Circuits: the package's bundled $S$-state references (timchan0/cliffordea at 27385c6,
``sim/stim_files``, the $d=5$ ones with the Bell-growth feedforward and detector healing) and its own
``make_variant_text``: ``replace_noise_level`` from $10^{-3}$ to $p$, and ``swap_t_and_s_gates`` for the
$T$ state. The paper sampled with SymFT.
"""

import functools
import sys

from repro import common
from repro.common import Point

STUDY = "chan_flags"
HERE = common.PAPERS / "2609.17706_chan_color_code_cultivation"
SIM = HERE / "stim_src" / "cliffordea"
META = dict(arxiv="2609.17706", paper="Chan, Strikis, Sun, Cai (2026), Diagnosing and restoring the degraded fault distance of magic state cultivation")
P3 = [5e-4, 1e-3, 2e-3, 3e-3, 5e-3, 7e-3, 1e-2]
P5 = [5e-4, 1e-3, 2e-3, 3e-3]
D3 = ["d3a6", "d3a6f2"]
D5 = ["d5a19", "d5a19f13"]
QUOTED = {1e-3: (4.9, 1.36), 5e-4: (10.9, 1.17)}


@functools.lru_cache(None)
def _ct():
    sys.path.insert(0, str(SIM / "sim"))
    import circuit_text

    return circuit_text


def make(circ, p, variant):
    ct = _ct()
    ref = (SIM / "sim" / "stim_files" / f"{circ}_inject+cultivate_p1e-3.stim").read_text()
    text = ct.replace_noise_level(ref, 0.001, p)
    if variant == "t":
        text = ct.swap_t_and_s_gates(text)
    common.noiseless_check(text)
    return text


def combos():
    out = [(c, p, v) for c in D3 for p in P3 for v in ("s", "t")]
    out += [(c, p, "t") for c in D5 for p in P5]
    return out


def name(c, p, v):
    return f"{c}_p{p:g}_{v}"


def circuits():
    return {name(*c): functools.partial(make, *c) for c in combos()}


def points():
    pts = []
    for c, p, v in combos():
        variant = "t" if v == "t" else "clifford"
        if c.startswith("d3"):
            pts.append(Point(name(c, p, v), name(c, p, v), variant, dict(circuit=c, d=3, p=p, gate=v),
                             target_errors=20000, max_shots=1e12, max_seconds=300, tier=1))
        else:
            sec = {5e-4: 1800, 1e-3: 1200, 2e-3: 600, 3e-3: 600}[p]
            pts.append(Point(name(c, p, v), name(c, p, v), variant, dict(circuit=c, d=5, p=p, gate=v),
                             target_errors=1000, max_shots=2e13, max_seconds=sec, tier=3 if p <= 1e-3 else 2))
    return pts


def figures(results):
    import matplotlib.pyplot as plt

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    figs = []

    def ser(c, g):
        return sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["circuit"] == c and r["params"]["gate"] == g)

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for c, ls in (("d3a6", "-"), ("d3a6f2", "--")):
        for g, col in (("s", "C0"), ("t", "C1")):
            lab = f"{'flagged' if 'f' in c else 'original'}, {g.upper()}"
            plotting.ler_points(axes[0], ser(c, g), color=col, ls=ls, label=lab)
            plotting.accept_points(axes[1], ser(c, g), color=col, ls=ls, label=lab)
    plotting.style_ler(axes[0], "noise strength $p$")
    plotting.style_accept(axes[1], "noise strength $p$")
    axes[0].legend()
    path = plotting.save(fig, out / "fig_d3_pre_escape.pdf")
    pts = [k for k, r in results.items() if r["params"]["d"] == 3]
    figs.append(common.Figure("chan_d3", path, "Chan et al. Fig.~d3\\_pre\\_escape\\_ler: $d=3$ cultivation, $S$ vs.\\ $T$, with and without Z flags",
                              "Blue: $S$ proxy; orange: real $T$ gates. Solid: the original double check ($a=6$); dashed: with two Z flags ($f=2$). "
                              "The flags restore fault distance 3 for the $T$ state.", common.budget_line(results, pts)))

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6))
    for c, col in (("d5a19", "C1"), ("d5a19f13", "C2")):
        lab = "original" if c == "d5a19" else "Z-flagged ($f=13$)"
        plotting.ler_points(axes[0], ser(c, "t"), color=col, label=lab)
        plotting.accept_points(axes[1], ser(c, "t"), color=col, label=lab)
    plotting.style_ler(axes[0], "noise strength $p$")
    plotting.style_accept(axes[1], "noise strength $p$", log=True)
    axes[0].legend()
    a = dict(ser("d5a19", "t"))
    b = dict(ser("d5a19f13", "t"))
    xs, imp, cost = [], [], []
    for p in sorted(set(a) & set(b)):
        ta, tb = a[p], b[p]
        if ta["kept"] and tb["kept"] and ta["errors"] and tb["errors"]:
            xs.append(p)
            imp.append((ta["errors"] / ta["kept"]) / (tb["errors"] / tb["kept"]))
            cost.append((ta["kept"] / ta["shots"]) / (tb["kept"] / tb["shots"]))
    axes[2].plot(xs, imp, "o-", color="C5", ms=3.5, label="LER ratio (orig./flagged)")
    axes[2].plot(xs, cost, "s-", color="C8", ms=3.5, label="attempts ratio (flagged/orig.)")
    for p, (i, cst) in QUOTED.items():
        plotting.published_value(axes[2], p, i, color="C5", label="paper (abstract)" if p == 1e-3 else None)
        plotting.published_value(axes[2], p, cst, color="C8")
    axes[2].set_xscale("log")
    axes[2].set_yscale("log")
    axes[2].set_xlabel("noise strength $p$")
    axes[2].legend(fontsize=5.5)
    path = plotting.save(fig, out / "fig_d5_flags.pdf")
    pts = [k for k, r in results.items() if r["params"]["d"] == 5]
    figs.append(common.Figure("chan_d5", path, "Chan et al. Figs.~d5\\_pre\\_escape\\_ler and improvement\\_and\\_cost\\_ratios: $d=5$ $T$ cultivation with Z flags",
                              "Pre-escape $d=5$ $T$-state cultivation. Right: LER improvement and attempts ratio of the flagged circuit; "
                              "open diamonds are the ratios quoted in the paper's abstract and Sec.~VI.", common.budget_line(results, pts)))
    return figs

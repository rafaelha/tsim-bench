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
P3 = [1e-4, 2e-4, 3e-4, 5e-4, 7e-4, 1e-3, 2e-3, 3e-3, 5e-3, 7e-3, 1e-2]  # the paper's grid
P5 = [5e-4, 7e-4, 1e-3, 2e-3, 3e-3]
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
                             target_errors=20000, max_shots=1e12, max_seconds=300 if p >= 5e-4 else 240, tier=1))
        else:
            sec = {5e-4: 1800, 7e-4: 1200, 1e-3: 1200, 2e-3: 600, 3e-3: 600}[p]
            pts.append(Point(name(c, p, v), name(c, p, v), variant, dict(circuit=c, d=5, p=p, gate=v),
                             target_errors=1000, max_shots=2e13, max_seconds=sec, tier=3 if p <= 1e-3 else 2))
    return pts


def figures(results):
    """The paper's figures (d3_pre_escape_ler.pdf, summary.pdf right panel, improvement_and_cost_ratios.pdf), in the paper's
    sinter.plot_error_rate style (the package README: 'plotted with sinter.plot_error_rate')."""
    import matplotlib.pyplot as plt
    import numpy as np
    import sinter

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    figs = []
    color = {"t": "tab:orange", "s": "tab:blue"}

    def stats(c, g, decoder="tsimGPU"):
        return [plotting.sinter_stats(r["totals"], decoder, {"p": r["params"]["p"], "gate": g.upper(), "circuit": c})
                for r in results.values() if r["params"]["circuit"] == c and r["params"]["gate"] == g]

    # ---- d3_pre_escape_ler.pdf: (a) original, (b) flagged; LER vs noise level; T orange, S blue; o / > markers.
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.6), sharey=True)
    for ax, c, mk, title in ((axes[0], "d3a6", "o", "(a) original"), (axes[1], "d3a6f2", ">", "(b) flagged")):
        for g in ("t", "s"):
            st = stats(c, g)
            if st:
                sinter.plot_error_rate(ax=ax, stats=st, x_func=lambda s: s.json_metadata["p"],
                                       group_func=lambda s: s.json_metadata["gate"],
                                       plot_args_func=lambda i, k, ss, g=g: {"color": color[g], "marker": mk, "label": g.upper()},
                                       highlight_max_likelihood_factor=1000)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(1e-4, 1e-2)
        ax.set_ylim(1e-10, 1e-3)
        ax.set_xlabel(title)
        ax.grid(which="major", color="black", lw=0.6)
        ax.grid(which="minor", color="0.85", lw=0.5)
    axes[0].set_ylabel("logical error rate", fontsize=12)
    axes[0].legend(loc="upper left")
    fig.supxlabel("noise level")
    path = plotting.save(fig, out / "d3_pre_escape_ler.pdf")
    pts = [k for k, r in results.items() if r["params"]["d"] == 3]
    figs.append(common.Figure("chan_d3", path, "Chan et al. Fig.~d3\\_pre\\_escape\\_ler: $d=3$ cultivation, $S$ vs.\\ $T$, (a) original and (b) Z-flagged double check",
                              "Same layout as the paper (sinter's \\texttt{plot\\_error\\_rate}; shaded: 1000x likelihood). Orange: real $T$ gates; "
                              "blue: the $S$ proxy. With the flags the $T$-state error recovers fault distance 3. The paper sampled with SymFT and released no numbers.",
                              common.budget_line(results, pts)))

    # ---- summary.pdf right panel (= d5_pre_escape_ler): LER vs expected attempts per kept shot, original (o) vs flagged (>).
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    labels = {"d5a19": ("original", "o"), "d5a19f13": ("flagged (this work)", ">")}
    for c, (lab, mk) in labels.items():
        st = stats(c, "t")
        if st:
            sinter.plot_error_rate(ax=ax, stats=st, x_func=lambda s: (s.shots + 1) / (s.shots - s.discards + 2),
                                   group_func=lambda s: c, plot_args_func=lambda i, k, ss, lab=lab, mk=mk: {"color": "tab:orange", "marker": mk, "label": lab},
                                   point_label_func=(lambda s: f"$p={s.json_metadata['p']:g}$") if c == "d5a19" else (lambda s: None),
                                   highlight_max_likelihood_factor=1000)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(2, 100)
    ax.set_ylim(1e-11, 1e-7)
    ax.set_xlabel("expected attempts per kept shot")
    ax.set_ylabel("logical error rate per kept shot")
    ax.grid(which="major", color="black", lw=0.6)
    ax.grid(which="minor", color="0.85", lw=0.5)
    ax.legend(loc="lower right")
    path = plotting.save(fig, out / "d5_pre_escape_ler.pdf")
    pts = [k for k, r in results.items() if r["params"]["d"] == 5]
    figs.append(common.Figure("chan_d5", path, "Chan et al. Fig.~d5\\_pre\\_escape\\_ler (\\texttt{summary.pdf}, right): $d=5$ $T$ cultivation, original vs.\\ Z-flagged",
                              "Same axes as the paper; points at $p$ = 5e-4, 7e-4, 1e-3, 2e-3 (and 3e-3).", common.budget_line(results, pts)))

    # ---- improvement_and_cost_ratios.pdf
    a = {r["params"]["p"]: r["totals"] for r in results.values() if r["params"]["circuit"] == "d5a19"}
    b = {r["params"]["p"]: r["totals"] for r in results.values() if r["params"]["circuit"] == "d5a19f13"}
    xs, imp, lo, hi, cost = [], [], [], [], []
    rng = np.random.default_rng(0)
    for p in sorted(set(a) & set(b)):
        ta, tb = a[p], b[p]
        if not (ta["kept"] and tb["kept"] and ta["errors"] and tb["errors"]):
            continue
        ra = rng.beta(ta["errors"] + 0.5, ta["kept"] - ta["errors"] + 0.5, 100000)
        rb = rng.beta(tb["errors"] + 0.5, tb["kept"] - tb["errors"] + 0.5, 100000)
        q = ra / rb
        xs.append(p)
        imp.append(float(np.median(q)))
        l, h = np.percentile(q, [2.5, 97.5])
        lo.append(l)
        hi.append(h)
        cost.append((ta["kept"] / ta["shots"]) / (tb["kept"] / tb["shots"]))
    fig, ax = plt.subplots(figsize=(4.6, 2.9))
    ax.plot(xs, imp, "o-", color="#40b0a6", label="error rate improvement ratio")
    ax.fill_between(xs, lo, hi, color="#40b0a6", alpha=0.2, lw=0)
    ax.plot(xs, cost, "o-", color="#e1be6a", label="expected attempts cost ratio")
    for p, (i, cst) in QUOTED.items():
        ax.plot([p], [i], "D", mfc="none", mec="#40b0a6", ms=7, label="paper (quoted)" if p == 1e-3 else None)
        ax.plot([p], [cst], "D", mfc="none", mec="#e1be6a", ms=7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(5e-4, 2e-3)
    ax.set_ylim(1, 20)
    ax.set_yticks([1, 2, 5, 10, 20], ["1", "2", "5", "10", "20"])
    ax.set_xticks([5e-4, 7e-4, 1e-3, 2e-3], [r"$5\times10^{-4}$", r"$7\times10^{-4}$", r"$10^{-3}$", "0.002"])
    ax.set_xlabel("noise level $p$")
    ax.grid(which="major", color="black", lw=0.6)
    ax.grid(which="minor", color="0.85", lw=0.5)
    ax.legend(fontsize=8)
    path = plotting.save(fig, out / "improvement_and_cost_ratios.pdf")
    figs.append(common.Figure("chan_ratio", path, "Chan et al. Fig.~improvement\\_and\\_cost\\_ratios: $d=5$ Z flags, LER improvement and attempts cost",
                              "Improvement = original/flagged logical error rate (median and 95\\% interval of a Beta-posterior bootstrap); "
                              "cost = flagged/original expected attempts. Open diamonds: the ratios quoted in the paper's abstract and Sec.~VI "
                              "(4.9x at 1.36x for $p=10^{-3}$; 10.9x at 1.17x for $p=5\\times10^{-4}$).", common.budget_line(results, pts)))
    return figs

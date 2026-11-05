r"""Ismail et al. (2025), arXiv:2509.18294 -- transversal STAR small-angle injection with full postselection (Figs. 6, 13, 15).

The paper's Fig. 6 shows the logical error rate and success rate of its transversal multi-rotation
(TMR) STAR injection with full postselection, vs. the physical error rate (at a logical angle of
$10^{-2}$) and vs. the angle; Fig. 13 validates against an analytic success rate at $d=3$.

The authors released no generator; the circuits here are QuEra's public STAR challenge circuits
(``QuEra-Challenge/star_circuits``), with the challenge's own ``physical_angle`` helper to set the
logical angle. They differ from the paper's Fig. 6 protocol: $k=d$ physical rotations (the paper uses
$k=3$; equal at $d=3$), $d$ postselected rounds after the rotations, uniform depolarizing noise
($p=10^{-3}$ in the released files; other $p$ by changing that literal), and a noiseless logical
un-rotation and $X$ readout. Every detector is postselected (raw parity; the $d-1$ detectors right after
the rotations are random by design). The paper's Clifford approximation is not specified, so no
Clifford version is sampled; the noiseless success probability $\cos^{2k}(\phi/2)+\sin^{2k}(\phi/2)$ of
$k$ physical rotations by $\phi$ is overlaid.
"""

import functools
import math
import re

import numpy as np

from repro import common
from repro.common import Point

STUDY = "star_injection"
HERE = common.PAPERS / "2509.18294_transversal_star"
SRC = HERE / "stim"
META = dict(arxiv="2509.18294", paper="Ismail et al. (2025), Transversal architecture for megaquop-scale quantum simulation with neutral atoms (transversal STAR)")
DS = [3, 5, 7]
ANGLES = [0.001, 0.003, 0.01, 0.03, 0.1, 0.25]  # logical angle in units of pi
PS = [3e-4, 5e-4, 1e-3, 2e-3, 3e-3]
PAPER_ANGLE = 1e-2  # radians (Fig. 6a,c)
PAPER_PS = [7.3e-4, 1.3e-3, 2.3e-3, 4.1e-3, 7.3e-3]
PAPER_P = 7.3e-4  # Fig. 6b,d
PAPER_ANGLES = [7.3e-4, 6e-3, 1.2e-2, 5e-2, 1e-1]  # radians


def physical_angle(logical_angle_in_pi, num_physical_rotations):
    """Verbatim from the challenge (challenge.md)."""
    assert num_physical_rotations % 2 == 1 and num_physical_rotations > 0, "k must be a positive odd integer"
    sign = -1 if (num_physical_rotations + 1) % 4 == 0 else 1
    logical_angle_in_rad = logical_angle_in_pi * np.pi
    x = np.tan(logical_angle_in_rad / 2) ** (1 / num_physical_rotations)
    theta_phys = 2 * np.arctan(x)
    return float(sign * theta_phys / np.pi)


def make(d, angle, p):
    text = (SRC / f"star_d={d}.stim").read_text()
    lines = text.splitlines()
    rz = [i for i, l in enumerate(lines) if l.startswith("R_Z(")]
    assert len(rz) == 2, rz
    phys_targets = lines[rz[0]].split()[1:]
    assert len(phys_targets) == d
    lines[rz[0]] = f"R_Z({physical_angle(angle, d)!r}) " + " ".join(phys_targets)
    lines[rz[1]] = f"R_Z({-angle!r}) " + " ".join(lines[rz[1]].split()[1:])
    text = "\n".join(lines) + "\n"
    if p != 1e-3:
        text = re.sub(r"\(0\.001\)", f"({p:g})", text)
    return text


def combos():
    out = {(d, a, 1e-3) for d in DS for a in ANGLES} | {(d, 0.01, p) for d in DS for p in PS}
    # The paper's Fig. 6 grid: p sweep at a logical angle of 1e-2 rad, angle sweep at p = 7.3e-4.
    out |= {(d, PAPER_ANGLE / math.pi, p) for d in DS for p in PAPER_PS}
    out |= {(d, a / math.pi, PAPER_P) for d in DS for a in PAPER_ANGLES}
    return sorted(out)


def name(d, a, p):
    return f"d{d}_a{a:.6g}_p{p:g}"


def circuits():
    return {name(*c): functools.partial(make, *c) for c in combos()}


def points():
    pts = []
    for d, a, p in combos():
        pts.append(Point(name(d, a, p), name(d, a, p), "t", dict(d=d, angle=a, p=p), target_errors=20000, max_shots=2e12,
                         max_seconds={3: 120, 5: 240, 7: 420}[d], tier=1, detector_reference=False, observable_reference=False))
    return pts


def success_noiseless(angle, k):
    phi = abs(physical_angle(angle, k)) * math.pi
    return math.cos(phi / 2) ** (2 * k) + math.sin(phi / 2) ** (2 * k)


COLORS = {3: "#fdd36f", 5: "#f7931e", 7: "#d4590c"}


def figures(results):
    """The paper's Fig. 6 layout (Fig6_injection_fidelity.png): (a,c) vs error rate, (b,d) vs angle in radians."""
    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    rc = {"font.family": "serif", "mathtext.fontset": "cm", "font.size": 11}
    with plt.rc_context(rc):
        fig, axes = plt.subplots(2, 2, figsize=(6.6, 5.6), sharex="col")
        for d in (7, 5, 3):
            col = COLORS[d]
            sp = sorted((r["params"]["p"], r["totals"]) for r in results.values()
                        if r["params"]["d"] == d and abs(r["params"]["angle"] * math.pi - PAPER_ANGLE) < 1e-12 and r["params"]["p"] in PAPER_PS)
            sa = sorted((r["params"]["angle"] * math.pi, r["totals"]) for r in results.values()
                        if r["params"]["d"] == d and r["params"]["p"] == PAPER_P and any(abs(r["params"]["angle"] * math.pi - a) < 1e-12 for a in PAPER_ANGLES))
            for (ax_l, ax_s), ser, mk in (((axes[0, 0], axes[1, 0]), sp, "o"), ((axes[0, 1], axes[1, 1]), sa, "s")):
                xs = [x for x, t in ser if t["kept"] and t["errors"]]
                ys = [t["errors"] / t["kept"] for x, t in ser if t["kept"] and t["errors"]]
                es = [y / np.sqrt(t["errors"]) for (x, t), y in zip([s for s in ser if s[1]["kept"] and s[1]["errors"]], ys)]
                if not xs:
                    continue
                ax_l.errorbar(xs, ys, yerr=es, color=col, marker=mk, ms=7, mec=(0.45, 0.3, 0.1, 0.5), mew=1.5, label=f"$d={d}$ PS")
                ax_s.plot([x for x, t in ser if t["shots"]], [t["kept"] / t["shots"] for x, t in ser if t["shots"]], color=col, marker=mk,
                          ms=7, mec=(0.45, 0.3, 0.1, 0.5), mew=1.5)
        for ax in axes.flat:
            ax.set_xscale("log")
        for ax in axes[0]:
            if ax.has_data():
                ax.set_yscale("log")
        for ax in axes[1]:
            ax.set_ylim(0, 1.05)
        axes[0, 0].set_ylabel("logical error rate")
        axes[1, 0].set_ylabel("success rate")
        axes[1, 0].set_xlabel("physical error rate $p$ (uniform)")
        axes[1, 1].set_xlabel("angle (radians)")
        axes[1, 0].set_xlim(5e-4, 1e-2)
        axes[1, 1].set_xlim(5e-4, 1.5e-1)
        for ax, lab in zip(axes.flat, "abcd"):
            ax.text(0.02, 0.97, f"({lab})", transform=ax.transAxes, va="top")
        axes[0, 0].legend(loc="lower right", frameon=False)
        path = plotting.save(fig, out / "Fig6_injection_fidelity.pdf")
    pts = [k for k, r in results.items() if r["params"]["p"] == PAPER_P or abs(r["params"]["angle"] * math.pi - PAPER_ANGLE) < 1e-12]
    return [common.Figure(
        "star", path, "Ismail et al. Fig. 6: STAR small-angle injection with full postselection (challenge circuits)",
        "The paper's layout and grid: (a, c) logical error and success rate vs.\\ error rate at a logical angle of $10^{-2}$ rad; (b, d) vs.\\ the "
        "logical angle at $p=7.3\\times10^{-4}$. Same colours ($d=3,5,7$) and markers as the paper. The protocol is that of QuEra's public STAR "
        "challenge circuits ($k=d$ rotations, $d$ postselected rounds after them, uniform depolarizing noise $p$ on every gate instead of the "
        "paper's hardware-aware model whose x-axis is the total two-qubit error rate), so the curves are not expected to coincide with the "
        "paper's; the authors released no generator for the paper's circuits.",
        common.budget_line(results, pts))]

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
    return sorted(out)


def name(d, a, p):
    return f"d{d}_a{a:g}_p{p:g}"


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


def figures(results):
    import matplotlib.pyplot as plt

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.2))
    for d, col in zip(DS, ("C0", "C1", "C2")):
        sp = sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["d"] == d and r["params"]["angle"] == 0.01)
        sa = sorted((r["params"]["angle"], r["totals"]) for r in results.values() if r["params"]["d"] == d and r["params"]["p"] == 1e-3)
        plotting.ler_points(axes[0, 0], sp, color=col, label=f"d={d} (k={d})")
        plotting.ler_points(axes[0, 1], sa, color=col, label=f"d={d}")
        plotting.accept_points(axes[1, 0], sp, color=col, label=f"d={d}")
        plotting.accept_points(axes[1, 1], sa, color=col, label=f"d={d}")
        xs = np.geomspace(min(ANGLES), max(ANGLES), 40)
        axes[1, 1].plot(xs, [success_noiseless(a, d) for a in xs], ":", color=col, lw=0.8)
    plotting.style_ler(axes[0, 0], "physical error rate $p$")
    plotting.style_ler(axes[0, 1], "logical angle $\\theta/\\pi$")
    plotting.style_accept(axes[1, 0], "physical error rate $p$", log=True)
    plotting.style_accept(axes[1, 1], "logical angle $\\theta/\\pi$", log=True)
    axes[0, 0].set_title("$\\theta = 0.01\\pi$")
    axes[0, 1].set_title("$p = 10^{-3}$")
    axes[0, 0].legend()
    axes[1, 1].legend(title="dotted: noiseless", fontsize=6)
    path = plotting.save(fig, out / "fig6_star.pdf")
    return [common.Figure(
        "star", path, "Ismail et al. Figs. 6, 13, 15 (protocol of the public STAR challenge circuits)",
        "Logical error of the injected small-angle rotation (noiseless un-rotation, logical $X$ readout) and success rate, "
        "with every detector postselected. Note the protocol differences listed above ($k=d$, $d$ postselected rounds after "
        "the rotations, uniform noise), so the curves are not expected to coincide with the paper's.",
        common.budget_line(results))]

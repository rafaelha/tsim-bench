r"""Rosenfeld et al. (2025), arXiv:2512.13908 -- simulation curves of the cultivation experiment on Willow.

The paper's grey points are state-vector simulations of the experimental circuits under the SI1000
noise model; shots are kept only if no detector fires (post-selected logical tomography). Here:

- Fig. 2(b,c): logical tomography ($\langle X_L\rangle$, $\langle Z_L\rangle$) of injection only and of
  injection + cultivation, vs. the injected angle $\theta$, SI1000 $p=3.0\times10^{-3}$;
- Fig. 3(b): kickback tomography (KT) of the cultivated $|T\rangle$: logical error vs. $\theta$, with and
  without the QEC cycles, SI1000 $p=2.3\times10^{-3}$; SI Fig. ``validating_KT``: KT error at the $T$
  angle vs. $p$ (expected $\propto p^3$);
- Fig. 4(b): tomography after grafting to the surface code, injection only and cultivation with
  $N=2,3$ cycles, SI1000 $p=2.3\times10^{-3}$.

Circuits: the released Zenodo (17872003) circuits, repaired to real gates from their Cirq versions by
our ``make_circuits.py`` (injection $e^{-i\theta Y/2}$ as an $H_{YZ}$-conjugated $Z$ rotation, $T$/$T^\dagger$
checks). The injection rotation is set to $R_Z(\theta/\pi)$; SI1000 noise is added with Gidney's
``gen.NoiseModel.si1000(p)`` (the model the paper cites), with non-Clifford gates mapped to Clifford
placeholders while the noise is inserted. The experiment had no Clifford proxy, so there is none here.
"""

import functools
import math
import re
import sys

from repro import common
from repro.common import Point

STUDY = "google_experiment"
HERE = common.PAPERS / "2512.13908_google_cultivation_experiment"
GEN = common.PAPERS / "2409.17595_magic_state_cultivation" / "stim_src" / "github_magic-state-cultivation" / "src"
META = dict(arxiv="2512.13908", paper="Rosenfeld et al. (2025), Magic state cultivation on a superconducting quantum processor")
THETAS = [2 * math.pi * k / 24 for k in range(24)]
T_ANGLE = math.pi / 4
KT_THETAS = sorted({T_ANGLE + math.pi / 32 * k for k in range(-8, 9)})
TOMO = {  # key: (template stem without basis, p)
    "fig2_injection": ("fig2_injection_stim_{b}_T", 3.0e-3),
    "fig2_cultivation": ("fig2_cultivation_stim_{b}_T", 3.0e-3),
    "fig4_injection_N2": ("fig4_simulation_injection_N2_stim_{b}_T", 2.3e-3),
    "fig4_cultivation_N2": ("fig4_cultivation_N2_stim_{b}_T", 2.3e-3),
    "fig4_cultivation_N3": ("fig4_cultivation_N3_stim_{b}_T", 2.3e-3),
}
KT = {"fig3_kt": "fig3_simulation_stim_T", "fig3_kt_no_qec": "fig3_without_idle_rounds_stim_T"}
KT_P = [1.0e-3, 1.5e-3, 2.3e-3, 3.0e-3, 4.0e-3]


@functools.lru_cache(None)
def _gen():
    sys.path.insert(0, str(GEN))
    import gen

    return gen


def noisy(template, theta, p):
    import stim

    lines = (HERE / "stim" / f"{template}.stim").read_text().splitlines()
    i0 = next(i for i, l in enumerate(lines) if re.match(r"^T ", l))
    assert len(lines[i0].split()) == 2, lines[i0]
    lines[i0] = "SQRT_X " + lines[i0].split()[1]
    x = "\n".join(lines)
    assert not re.search(r"^(S|S_DAG) ", x, flags=re.M)
    x = re.sub(r"^T_DAG ", "S_DAG ", x, flags=re.M)
    x = re.sub(r"^T ", "S ", x, flags=re.M)
    c = _gen().NoiseModel.si1000(p).noisy_circuit_skipping_mpp_boundaries(stim.Circuit(x)) if p > 0 else stim.Circuit(x)
    s = str(c)
    s = re.sub(r"^S_DAG ", "T_DAG ", s, flags=re.M)
    s = re.sub(r"^S ", "T ", s, flags=re.M)
    s = re.sub(r"^SQRT_X ", f"R_Z({theta / math.pi:.12g}) ", s, flags=re.M)
    return s


def raw_zero_check(template):
    """At the T angle and without noise, every detector must read 0 (raw parity), so raw postselection
    on 0 is the experiment's postselection. Away from the T angle the check detectors are random by
    design (postselecting on them is what cultivation does)."""
    import numpy as np
    import tsim

    text = noisy(template, T_ANGLE, 0.0)
    c = tsim.Circuit(text)
    a = np.asarray(c.compile_detector_sampler(seed=1).sample(512)).astype(bool)
    if a.any():
        raise ValueError(f"{template}: detectors not all 0 at the T angle")


def make_tomo(key, basis, theta):
    tmpl, p = TOMO[key]
    raw_zero_check(tmpl.format(b=basis))
    return noisy(tmpl.format(b=basis), theta, p)


def make_kt(key, theta, p):
    raw_zero_check(KT[key])
    return noisy(KT[key], theta, p)


@functools.lru_cache(None)
def kt_reference(key):
    """Raw value of the KT observable for the ideal T state (deterministic at theta = pi/4)."""
    import numpy as np
    import tsim

    c = tsim.Circuit(noisy(KT[key], T_ANGLE, 0.0))
    a = np.asarray(c.compile_detector_sampler(seed=1).sample(512, append_observables=True)).astype(bool)
    obs = a[:, c.num_detectors]
    assert obs.all() or not obs.any(), "KT observable not deterministic at the T angle"
    return int(obs[0])


def tname(key, basis, k):
    return f"{key}_{basis}_th{k:02d}"


def ktname(key, theta, p):
    return f"{key}_th{theta:.4f}_p{p:g}"


def combos():
    out = [("tomo", key, b, k) for key in TOMO for b in ("X", "Z") for k in range(len(THETAS))]
    out += [("kt", key, th, 2.3e-3) for key in KT for th in KT_THETAS]
    out += [("kt", "fig3_kt", T_ANGLE, p) for p in KT_P if p != 2.3e-3]
    return out


def circuits():
    out = {}
    for c in combos():
        if c[0] == "tomo":
            out[tname(*c[1:])] = functools.partial(make_tomo, c[1], c[2], THETAS[c[3]])
        else:
            out[ktname(*c[1:])] = functools.partial(make_kt, *c[1:])
    return out


def points():
    pts = []
    for c in combos():
        if c[0] == "tomo":
            _, key, b, k = c
            pts.append(Point(tname(key, b, k), tname(key, b, k), "t", dict(kind="tomo", key=key, basis=b, theta=THETAS[k], p=TOMO[key][1]),
                             mode="tomo", detector_reference=False, observable_reference=False, target_errors=10**18, max_shots=3e9, max_seconds=60, tier=1))
        else:
            _, key, th, p = c
            pts.append(Point(ktname(key, th, p), ktname(key, th, p), "t", dict(kind="kt", key=key, theta=th, p=p),
                             mode="tomo", detector_reference=False, observable_reference=False, target_errors=10**18, max_shots=2e10, max_seconds=90, tier=1))
    return pts


def _expect(t):
    return 1 - 2 * t["obs_ones"][0] / t["kept"] if t["kept"] else float("nan")


def figures(results):
    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    figs = []
    # ---- tomography (Figs. 2, 4)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4))
    for ax, keys, title in ((axes[0], ("fig2_injection", "fig2_cultivation"), "Fig. 2: SI1000 $p=3\\times10^{-3}$"),
                            (axes[1], ("fig4_injection_N2", "fig4_cultivation_N2", "fig4_cultivation_N3"), "Fig. 4 (grafted): $p=2.3\\times10^{-3}$")):
        ts = np.linspace(0, 2 * np.pi, 200)
        ax.plot(np.sin(ts), np.cos(ts), color="k", lw=0.6)
        ax.plot([-1, 1], [-1, 1], color="0.6", lw=0.6, ls="--")
        for key, col in zip(keys, ("C3", "C0", "C2")):
            xs, zs = [], []
            for k in range(len(THETAS)):
                rx, rz = results.get(tname(key, "X", k)), results.get(tname(key, "Z", k))
                if rx and rz:
                    xs.append(_expect(rx["totals"]))
                    zs.append(_expect(rz["totals"]))
            ax.plot(xs, zs, "o", color=col, ms=3, label=key.split("_", 1)[1])
        ax.set_aspect("equal")
        ax.set_xlim(-1.08, 1.08)
        ax.set_ylim(-1.08, 1.08)
        ax.set_xlabel("$\\langle X_L\\rangle$")
        ax.set_ylabel("$\\langle Z_L\\rangle$")
        ax.set_title(title)
        ax.legend(fontsize=6, loc="lower left")
    path = plotting.save(fig, out / "fig2_fig4_tomography.pdf")
    pts = [k for k, r in results.items() if r["params"]["kind"] == "tomo"]
    figs.append(common.Figure("google_tomo", path, "Rosenfeld et al. Figs. 2(b) and 4(b): post-selected logical tomography vs.\\ injected angle",
                              "Each marker is one injected angle $\\theta$ ($24$ angles in $[0,2\\pi)$), with $\\langle X_L\\rangle$ and $\\langle Z_L\\rangle$ from the "
                              "$X$- and $Z$-basis circuits (up to $3\\times10^9$ shots each). Cultivation projects the state onto the magic axis (dashed). "
                              "These replace the paper's grey state-vector points.", common.budget_line(results, pts)))
    # ---- KT (Fig. 3 + SI)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    for key, col, lab in (("fig3_kt", "C0", "with QEC cycles"), ("fig3_kt_no_qec", "C1", "without QEC cycles")):
        ref = kt_reference(key)
        ser = []
        for r in results.values():
            pr = r["params"]
            if pr["kind"] == "kt" and pr["key"] == key and abs(pr["p"] - 2.3e-3) < 1e-12:
                t = dict(r["totals"])
                t["errors"] = t["obs_ones"][0] if ref == 0 else t["kept"] - t["obs_ones"][0]
                ser.append((pr["theta"], t))
        plotting.ler_points(axes[0], sorted(ser), color=col, label=lab)
    axes[0].axvline(T_ANGLE, color="0.6", lw=0.6, ls="--")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("injected angle $\\theta$ (rad)")
    axes[0].set_ylabel("KT logical error per kept shot")
    axes[0].legend()
    ref = kt_reference("fig3_kt")
    ser = []
    for r in results.values():
        pr = r["params"]
        if pr["kind"] == "kt" and pr["key"] == "fig3_kt" and abs(pr["theta"] - T_ANGLE) < 1e-9:
            t = dict(r["totals"])
            t["errors"] = t["obs_ones"][0] if ref == 0 else t["kept"] - t["obs_ones"][0]
            ser.append((pr["p"], t))
    plotting.ler_points(axes[1], sorted(ser), color="C0", label="KT at the $T$ angle")
    if ser:
        p0, t0 = sorted(ser)[len(ser) // 2]
        if t0["errors"]:
            l0 = t0["errors"] / t0["kept"]
            xs = np.geomspace(min(s[0] for s in ser), max(s[0] for s in ser), 20)
            axes[1].plot(xs, l0 * (xs / p0) ** 3, ":", color="0.4", label="$\\propto p^3$")
    plotting.style_ler(axes[1], "SI1000 noise strength $p$")
    axes[1].legend()
    path = plotting.save(fig, out / "fig3_kt.pdf")
    pts = [k for k, r in results.items() if r["params"]["kind"] == "kt"]
    figs.append(common.Figure("google_kt", path, "Rosenfeld et al. Fig. 3(b) and SI Fig.~validating\\_KT: kickback tomography of the cultivated $|T\\rangle$",
                              "Left: KT logical error vs.\\ injected angle (SI1000 $p=2.3\\times10^{-3}$), with and without the interleaved QEC cycles. "
                              "Without the QEC cycles there is a single stabilizer measurement at the end, so single faults cause logical errors: "
                              "the error is about 100x worse (as in the paper) and, since postselection on the cultivation checks still projects "
                              "onto the $T$ axis, nearly independent of $\\theta$. Right: KT error at $\\theta=\\pi/4$ vs.\\ $p$, which scales "
                              "as $p^3$ (fault distance 3).",
                              common.budget_line(results, pts)))
    return figs

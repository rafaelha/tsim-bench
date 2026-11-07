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
KT_THETAS = sorted({T_ANGLE + math.pi / 32 * k for k in range(-8, 9)} | {2 * math.pi * k / 32 for k in range(32)})  # dense near T, full circle as in the paper
TOMO = {  # key: (template stem without basis, p)
    "fig2_injection": ("fig2_injection_stim_{b}_T", 3.0e-3),
    "fig2_cultivation": ("fig2_cultivation_stim_{b}_T", 3.0e-3),
    "fig4_injection_N2": ("fig4_simulation_injection_N2_stim_{b}_T", 2.3e-3),
    "fig4_cultivation_N2": ("fig4_cultivation_N2_stim_{b}_T", 2.3e-3),
    "fig4_cultivation_N3": ("fig4_cultivation_N3_stim_{b}_T", 2.3e-3),
}
KT = {"fig3_kt": "fig3_simulation_stim_T", "fig3_kt_no_qec": "fig3_without_idle_rounds_stim_T", "fig3_injection": "fig3_injection_stim_T"}
KT_P = [3e-4, 5e-4, 1.0e-3, 1.5e-3, 2.0e-3, 2.3e-3, 2.5e-3, 3.0e-3, 3.5e-3, 4.0e-3]  # SI Fig. validating_KT grid


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


# The paper's palette and markers (figures/fig2-4.pdf).
RED, CYAN, GREY, BLUE, TEAL = "#ef4136", "#29b6d8", "#58595b", "#3a6fc4", "#0f7c80"


def _theta_axis(ax):
    import math

    ax.set_xticks([math.pi / 4, 5 * math.pi / 4, 2 * math.pi], [r"$\pi/4$", r"$5\pi/4$", r"$2\pi$"])
    ax.axvline(math.pi / 4, color="k", ls=":", lw=1.5)
    ax.axvline(5 * math.pi / 4, color="0.5", ls=":", lw=1.5)


def _kt_series(results, key, p=2.3e-3):
    ref = kt_reference(key)
    ser = []
    for r in results.values():
        pr = r["params"]
        if pr["kind"] == "kt" and pr["key"] == key and abs(pr["p"] - p) < 1e-12:
            t = dict(r["totals"])
            t["errors"] = t["obs_ones"][0] if ref == 0 else t["kept"] - t["obs_ones"][0]
            ser.append((pr["theta"], t))
    return sorted(ser)


def figures(results):
    import math

    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    figs = []

    def tomo(key):
        xs, zs, ths, acc = [], [], [], []
        for k in range(len(THETAS)):
            rx, rz = results.get(tname(key, "X", k)), results.get(tname(key, "Z", k))
            if rx and rz and rx["totals"]["kept"] and rz["totals"]["kept"]:
                xs.append(_expect(rx["totals"]))
                zs.append(_expect(rz["totals"]))
                ths.append(THETAS[k])
                acc.append((rx["totals"]["kept"] + rz["totals"]["kept"]) / (rx["totals"]["shots"] + rz["totals"]["shots"]))
        return xs, zs, ths, acc

    # ---- Fig. 2(B, D): tomography in the X-Z plane, data retainment vs theta.
    fig = plt.figure(figsize=(7.2, 4.6))
    ax = fig.add_axes([0.08, 0.1, 0.52, 0.82])
    axd = fig.add_axes([0.70, 0.1, 0.28, 0.36])
    ts = np.linspace(0, 2 * np.pi, 300)
    ax.plot(np.sin(ts), np.cos(ts), "k", lw=1.5)
    ax.plot([-0.71, 0.71], [-0.71, 0.71], ls=":", color="0.75", lw=1.5)
    for key, col, mk, lab in (("fig2_injection", RED, "P", "Injection only (Tsim GPU)"), ("fig2_cultivation", CYAN, "D", "Cultivation (Tsim GPU)")):
        xs, zs, ths, acc = tomo(key)
        ax.plot(xs, zs, mk, color=col, ms=5 if mk == "D" else 7, ls="none", label=lab)
        axd.plot(ths, acc, mk, color=col, ms=3.5, ls="none")
    ax.plot([np.sqrt(0.5)], [np.sqrt(0.5)], "*", color="gold", mec="k", ms=14)
    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$\langle X\rangle_L$")
    ax.set_ylabel(r"$\langle Z\rangle_L$")
    ax.legend(loc="center", fontsize=8)
    ax.set_title("B", loc="left", fontweight="bold")
    _theta_axis(axd)
    axd.set_ylim(0, 0.8)
    axd.set_xlabel(r"Polar angle $\theta$ injected")
    axd.set_ylabel("Data retainment rate")
    axd.set_title("D", loc="left", fontweight="bold")
    path = plotting.save(fig, out / "fig2.pdf")
    pts = [k for k, r in results.items() if r["params"]["kind"] == "tomo" and r["params"]["key"].startswith("fig2")]
    figs.append(common.Figure("google2", path, "Rosenfeld et al. Fig. 2(B, D): post-selected logical tomography and data retainment vs.\\ injected angle",
                              "Layout and markers of the paper's Fig. 2 (panels B and D). Our points replace the paper's grey state-vector "
                              "\\emph{simulation} points (SI1000, $p=3.0\\times10^{-3}$): red, injection only; cyan, injection + cultivation, which is "
                              "projected onto the magic axis (dotted); star: the ideal $|T\\rangle$. 24 angles, up to $3\\times10^9$ shots per basis. "
                              "The paper's experimental points are not released in numeric form here.", common.budget_line(results, pts)))

    # ---- Fig. 3(B, C, D): kickback tomography logical error and retainment vs theta.
    fig = plt.figure(figsize=(7.2, 4.6))
    ax = fig.add_axes([0.09, 0.1, 0.56, 0.84])
    axc = fig.add_axes([0.73, 0.6, 0.25, 0.34])
    axd = fig.add_axes([0.73, 0.1, 0.25, 0.36])
    for key, col, mk, lab in (("fig3_injection", RED, "P", "Injection only (Tsim GPU)"),
                              ("fig3_kt_no_qec", BLUE, "o", "Cultivation without QEC cycles (Tsim GPU)"),
                              ("fig3_kt", CYAN, "D", "Cultivation with QEC cycles (Tsim GPU)")):
        ser = _kt_series(results, key)
        ths = [th for th, t in ser if t["kept"]]
        ys = [t["errors"] / t["kept"] for th, t in ser if t["kept"]]
        es = [np.sqrt(max(t["errors"], 1)) / t["kept"] for th, t in ser if t["kept"]]
        ax.errorbar(ths, ys, yerr=es, ls="none", marker=mk, color=col, ms=4 if mk != "P" else 6, label=lab)
        axd.plot(ths, [t["kept"] / t["shots"] for th, t in ser if t["kept"]], mk, color=col, ms=3, ls="none")
        if key == "fig3_kt":
            near = [(th, y, e) for th, y, e in zip(ths, ys, es) if math.pi / 16 <= th <= 7 * math.pi / 16]
            axc.errorbar([x[0] for x in near], [x[1] for x in near], yerr=[x[2] for x in near], ls="none", marker="D", color=col, ms=4)
    ax.set_yscale("log")
    ax.set_ylim(1e-5, 2)
    _theta_axis(ax)
    ax.set_xlabel(r"Polar angle $\theta$ injected")
    ax.set_ylabel("Logical error probability (total circuit)")
    ax.legend(loc="lower right", fontsize=7)
    ax.set_title("B", loc="left", fontweight="bold")
    axc.set_yscale("log")
    axc.set_xticks([math.pi / 8, math.pi / 4, 3 * math.pi / 8], [r"$\pi/8$", r"$\pi/4$", r"$3\pi/8$"])
    axc.set_xlabel(r"$\theta$")
    axc.set_ylabel("Logical error prob.")
    axc.set_title("C", loc="left", fontweight="bold")
    _theta_axis(axd)
    axd.set_ylabel("Data retainment rate")
    axd.set_xlabel(r"$\theta$")
    axd.set_title("D", loc="left", fontweight="bold")
    path = plotting.save(fig, out / "fig3.pdf")
    pts = [k for k, r in results.items() if r["params"]["kind"] == "kt" and abs(r["params"]["p"] - 2.3e-3) < 1e-12]
    figs.append(common.Figure("google3", path, "Rosenfeld et al. Fig. 3(B, C, D): kickback tomography (KT) vs.\\ injected angle",
                              "Layout and markers of the paper's Fig. 3: logical error of the whole KT circuit vs.\\ $\\theta$ (B), zoom near $\\pi/4$ (C), "
                              "data retainment (D), SI1000 $p=2.3\\times10^{-3}$. All three curves are Tsim GPU simulations of the released circuits "
                              "(the paper's grey points are its state-vector simulation of the cultivation-with-QEC circuit). Without the QEC cycles "
                              "there is a single stabilizer measurement at the end, so single faults cause logical errors: the error is about 100x "
                              "worse (as in the paper) and, since postselection on the cultivation checks still projects onto the $T$ axis, nearly "
                              "independent of $\\theta$.", common.budget_line(results, pts)))

    # ---- Fig. 4(B, C): grafted tomography (positive quadrant) and retainment.
    fig = plt.figure(figsize=(7.2, 4.6))
    ax = fig.add_axes([0.08, 0.1, 0.52, 0.84])
    axc = fig.add_axes([0.70, 0.1, 0.28, 0.36])
    ts = np.linspace(0, np.pi / 2, 200)
    ax.plot(np.sin(ts), np.cos(ts), "k", lw=1.5)
    ax.plot([0, 0.71], [0, 0.71], ls=":", color="0.75", lw=1.5)
    for key, col, mk, lab in (("fig4_injection_N2", GREY, "P", "Simulation, injection, N = 2 (Tsim GPU)"),
                              ("fig4_cultivation_N2", CYAN, "P", "Cultivation, N = 2 (Tsim GPU)"),
                              ("fig4_cultivation_N3", TEAL, "P", "Cultivation, N = 3 (Tsim GPU)")):
        xs, zs, ths, acc = tomo(key)
        ax.plot(xs, zs, mk, color=col, ms=7, ls="none", label=lab)
        axc.plot(ths, acc, "D" if "cult" in key else "o", color=col, ms=3, ls="none")
    ax.plot([np.sqrt(0.5)], [np.sqrt(0.5)], "*", color="gold", mec="k", ms=14)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.set_xlabel(r"$\langle X\rangle_L$")
    ax.set_ylabel(r"$\langle Z\rangle_L$")
    ax.legend(loc="lower left", fontsize=7)
    ax.set_title("B", loc="left", fontweight="bold")
    _theta_axis(axc)
    axc.set_xlabel(r"Polar angle $\theta$ injected")
    axc.set_ylabel("Data retainment rate")
    axc.set_title("C", loc="left", fontweight="bold")
    path = plotting.save(fig, out / "fig4.pdf")
    pts = [k for k, r in results.items() if r["params"]["kind"] == "tomo" and r["params"]["key"].startswith("fig4")]
    figs.append(common.Figure("google4", path, "Rosenfeld et al. Fig. 4(B, C): tomography after grafting to the surface code",
                              "Layout of the paper's Fig. 4 (positive quadrant of the $X$--$Z$ plane, data retainment vs.\\ $\\theta$), SI1000 "
                              "$p=2.3\\times10^{-3}$, the released injection-only simulation circuit and the cultivation circuits with $N=2,3$ cycles.",
                              common.budget_line(results, pts)))

    # ---- SI Fig. validating_KT (SI_kt_sweep_p.pdf): KT error at the T angle vs p, fit to p^3.
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    ref = kt_reference("fig3_kt")
    ser = []
    for r in results.values():
        pr = r["params"]
        if pr["kind"] == "kt" and pr["key"] == "fig3_kt" and abs(pr["theta"] - T_ANGLE) < 1e-9:
            t = dict(r["totals"])
            t["errors"] = t["obs_ones"][0] if ref == 0 else t["kept"] - t["obs_ones"][0]
            ser.append((pr["p"], t))
    ser = sorted(s for s in ser if s[1]["kept"] and s[1]["errors"])
    if ser:
        ps = np.array([p for p, _ in ser])
        ys = np.array([t["errors"] / t["kept"] for _, t in ser])
        es = np.array([np.sqrt(t["errors"]) / t["kept"] for _, t in ser])
        c = np.exp(np.mean(np.log(ys) - 3 * np.log(ps)))
        xs = np.geomspace(1e-4, ps.max(), 50)
        ax.plot(xs, c * xs**3, color="#8a2be2", label=r"Fit to $p^3$")
        ax.errorbar(ps, ys, yerr=es, ls="none", marker="o", color="tab:blue", label="KT simulation results (Tsim GPU)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("SI1000 noise strength p")
    ax.set_ylabel("Logical error probability (total circuit)")
    ax.legend(loc="upper left")
    path = plotting.save(fig, out / "SI_kt_sweep_p.pdf")
    pts = [k for k, r in results.items() if r["params"]["kind"] == "kt" and abs(r["params"]["theta"] - T_ANGLE) < 1e-9]
    figs.append(common.Figure("google_si", path, "Rosenfeld et al. SI Fig.~validating\\_KT: KT error at the $T$ angle vs.\\ SI1000 noise strength",
                              "Same axes as the paper (KT of the cultivated $|T\\rangle$, fit to $p^3$), at the paper's noise grid. Our values are "
                              "somewhat below the paper's (e.g.\\ $2.2\\times10^{-4}$ vs.\\ $\\sim5\\times10^{-4}$ at $p=4\\times10^{-3}$), consistent with a "
                              "slightly different SI1000 variant (we use Gidney's \\texttt{gen.NoiseModel.si1000}).", common.budget_line(results, pts)))
    return figs

r"""Vaknin et al. (2025), arXiv:2502.01743 -- Fig. 26: full state-vector vs. Clifford simulation of H cultivation.

Unrotated $d_1=3$ surface-code $H$-type cultivation (injection + double-checking with GHZ
ancillas), without the expansion step: every stabilizer measurement postselected, then a perfect
logical measurement in the magic-state basis. The authors spent about $10^6$ CPU-hours on a full
state-vector simulation, roughly $10^7$ shots per point, and compared it with their Clifford
approximation.

Circuits: the authors' generator (tomirendo/surface-code-magic-state-cultivation at ec28f6b,
``Simulation(d=3)``: ``generate_syndrome_circuit(detect_x=False)`` + ``generate_injection_circuit`` + ``generate_syndrome_circuit`` +
``generate_double_ghz``, the ``injection-syndrome-ghz`` variant, whose acceptance matches the paper's Fig. 26) in its own pinned environment (``.venvs/vaknin``,
``repro/external/vaknin_generate.py``), with their ``NoiseModel().uniform_depolarizing(p)``:

- Clifford approximation: ``to_stim_circuit(apply_non_cliffords=False, non_clifford_noise_strategy="CZ")``, identical to the
  authors' released ``init-H-injection-syndrome-ghz`` circuit at $p=10^{-3}$ (CH checks replaced by CZ, which measures $Z_L$; their
  noise kept), final $Z_L$ readout;
- non-Clifford: ``apply_non_cliffords=True``, placeholders replaced by $T$/$T^\dagger$/CCZ/CH/CSWAP
  decompositions (our ``make_circuits.py``); the final noiseless readout is set to $Z_L$, preceded by the noiseless logical rotation $\exp(\mp i\pi Y_L/8)$
  (``repro/magic_check.py``) that turns the final $Z_L$ readout into the magic-basis ($H_L$) check.
"""

import functools
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

from repro import common, magic_check
from repro.common import Point

STUDY = "vaknin_full_vector"
HERE = common.PAPERS / "2502.01743_surface_code_cultivation"
VENV_PY = common.ROOT / ".venvs" / "vaknin" / "bin" / "python"
META = dict(arxiv="2502.01743", paper="Vaknin et al. (2025), Efficient magic state cultivation on the surface code")
PS = [2e-4, 5e-4, 1e-3, 2e-3, 4e-3, 8e-3]  # the paper's Fig. 26 grid


@functools.lru_cache(None)
def _mc():
    sys.path.insert(0, str(common.ROOT / "tools"))
    spec = importlib.util.spec_from_file_location("vaknin_make_circuits", HERE / "make_circuits.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@functools.lru_cache(None)
def _generated(p):
    d = pathlib.Path(tempfile.mkdtemp(prefix="vaknin_"))
    subprocess.run([str(VENV_PY), str(common.REPRO / "external" / "vaknin_generate.py"), repr(p), str(d)], check=True,
                   capture_output=True)
    return ((d / "proxy.stim").read_text(), (d / "placeholder.stim").read_text(), json.loads((d / "logicals.json").read_text()))


def make(p, variant):
    proxy, placeholder, logicals = _generated(p)
    if variant == "clifford":
        common.noiseless_check(proxy)
        return proxy
    text = _mc().convert_text(placeholder)
    # The generator's final noiseless readout is ``MPP Y..`` on the Z_L support; the magic-basis check
    # needs Z_L followed by the rotation below (H_L = (X_L + Z_L)/sqrt 2 -> Z_L).
    lines = text.splitlines()
    last = max(i for i, l in enumerate(lines) if l.startswith("MPP "))
    assert len(lines[last].split()) == 2, lines[last]
    lines[last] = "MPP " + "*".join(f"Z{q}" for q in logicals["z"])
    text = "\n".join(lines) + "\n"
    y = {q: "X" for q in logicals["x"]}
    for q in logicals["z"]:
        y[q] = "Y" if q in y else "Z"
    out, _ = magic_check.make_deterministic(text, y)
    return out


def circuits():
    return {f"unrotH_p{p:g}_{v}": functools.partial(make, p, v) for p in PS for v in ("clifford", "t")}


def points():
    return [Point(f"unrotH_p{p:g}_{v}", f"unrotH_p{p:g}_{v}", v, dict(p=p, gate=v), target_errors=20000, max_shots=1e12,
                  max_seconds=600, tier=2 if p < 2e-3 else 1) for p in PS for v in ("clifford", "t")]


def figures(results):
    """The paper's full_vec_sim.png: LER vs attempts per kept shot; Clifford as red line + triangles, full vector as error bars."""
    import matplotlib.pyplot as plt
    import numpy as np

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    fig, ax = plt.subplots(figsize=(8, 6.4))
    if not any(r["totals"]["errors"] for r in results.values()):
        plotting.no_data(ax)
        return [common.Figure("vaknin", plotting.save(fig, out / "full_vec_sim.pdf"), "Vaknin et al. Fig. 26", "", "not yet sampled")]
    for g in ("clifford", "t"):
        ser = sorted((r["params"]["p"], r["totals"]) for r in results.values() if r["params"]["gate"] == g)
        ser = [(p, t) for p, t in ser if t["kept"] and t["errors"]]
        xs = [t["shots"] / t["kept"] for _, t in ser]
        ys = [t["errors"] / t["kept"] for _, t in ser]
        if g == "clifford":
            ax.plot(xs, ys, "-^", color="red", label=r"$H$ Cultivation Unrotated SC - Clifford (Tsim GPU)")
            for (p, _), x, y in zip(ser, xs, ys):
                ax.annotate(f"{p:g}", (x, y), xytext=(3, 3), textcoords="offset points", fontsize=9)
        else:
            es = [y / np.sqrt(t["errors"]) for (_, t), y in zip(ser, ys)]
            ax.errorbar(xs, ys, yerr=es, fmt="o", color="tomato", capsize=4, label=r"$H$ Cultivation Unrotated SC - non-Clifford (Tsim GPU)")
    if ax.has_data():
        ax.set_xscale("log")
        ax.set_yscale("log")
    ax.set_xlabel("Attempts per kept shot", fontsize=14)
    ax.set_ylabel("Logical Error Rate (P)", fontsize=14)
    ax.set_title("Attempts per Kept Shot vs Logical Error Rate")
    ax.grid(True)
    ax.legend(loc="lower right", fontsize=11)
    path = plotting.save(fig, out / "full_vec_sim.pdf")
    return [common.Figure(
        "vaknin", path, "Vaknin et al. Fig. 26 (\\texttt{full\\_vec\\_sim.png}): unrotated $H$ cultivation, non-Clifford vs.\\ Clifford approximation",
        "Same axes, markers and $p$ labels as the paper (red triangles: Clifford approximation; salmon circles with $\\pm1\\sigma$ bars: "
        "the full non-Clifford circuit, which the paper ran as a $10^6$ CPU-hour state-vector simulation with $\\sim10^7$ shots per point). "
        "The paper's figure also shows the $H_{XY}$ rotated-surface-code protocol, which is not reproduced here. All stabilizers postselected, "
        "no expansion, perfect magic-basis logical readout; no numbers for this figure are released.",
        common.budget_line(results))]

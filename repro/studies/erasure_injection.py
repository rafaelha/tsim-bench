r"""Jacoby et al. (2025), arXiv:2504.02935 -- ungrown injection and cultivation with erasure qubits (Figs. 2 and 5(b)).

With erasure qubits, every heralded erasure in the (ungrown, fully postselected) patch discards the
shot, so the logical error rate of kept shots depends only on the residual Pauli rate $p$, and the
acceptance rate is the Pauli acceptance times the probability of no erasure. The paper's scenarios:
$(e, p) = (0, 10^{-3})$, and $e \in \{10^{-3}, 4\cdot10^{-3}, 10^{-2}\}$ with $p = 10^{-4}$; erasure probability $e$ per
two-qubit gate and SPAM operation and $e/10$ per single-qubit gate (``end2end_script.py``: ``e1=e/10, e_SPAM=e``).

Circuits:

- Fig. 5(b), unitary injection + $d=3$ colour-code cultivation: Gidney's generator with uniform depolarizing
  noise (the paper's circuit is Gidney's ``inject[unitary]+cultivate`` file), $S$ proxy and $T$; the $e=0$
  point is the Gidney study's $p=10^{-3}$ point.
- Fig. 2, $d_1=3$ hook injection of $|S\rangle$: the released ``circuits/QEC_hook_d=3.stim`` ($p=10^{-3}$;
  $p=10^{-4}$ by scaling its noise literals, since the notebook that generated the paper's circuits is not
  released). $T$ version: the injection $S\to T$ and a noiseless logical rotation (``repro/magic_check.py``)
  so the final $Y_L$ readout checks the $T$ state. Lao--Criger injection and the hybrid layouts are not
  reproduced.

The no-erasure probability is computed exactly from the Pauli circuit's noise locations, following
``get_erased_circuit``.
"""

import functools
import re

from repro import common, magic_check
from repro.common import Point
from repro.studies import gidney_cultivation

STUDY = "erasure_injection"
SRC = common.PAPERS / "2504.02935_erasure_injection" / "stim_src" / "injection-with-erasure-qubits" / "circuits"
META = dict(arxiv="2504.02935", paper="Jacoby et al. (2025), Magic state injection with erasure qubits")
SCEN = [(0.0, 1e-3), (1e-3, 1e-4), (4e-3, 1e-4), (1e-2, 1e-4)]
HOOK_YL = "Y35*Z31*Z33*X26*X28"


def hook(p, variant):
    text = (SRC / "QEC_hook_d=3.stim").read_text()
    if p != 1e-3:
        f = p / 1e-3
        text = re.sub(r"(DEPOLARIZE[12]|X_ERROR|Z_ERROR|M)\(([0-9.e-]+)\)", lambda m: f"{m[1]}({float(m[2]) * f:.6g})", text)
    if variant == "s":
        common.noiseless_check(text)
        return text
    lines = text.splitlines()
    inj = [i for i, l in enumerate(lines) if l.strip() == "S 24"]
    assert len(inj) == 1
    lines[inj[0]] = "T 24"
    _, zl = magic_check.split_y(magic_check.parse_product(HOOK_YL))
    out, _ = magic_check.make_deterministic("\n".join(lines) + "\n", zl)
    return out


def cult(p, variant):
    return gidney_cultivation.make(3, "unitary", p, variant)


def circuits():
    out = {}
    for p in (1e-3, 1e-4):
        for v in ("s", "t"):
            out[f"hook_p{p:g}_{v}"] = functools.partial(hook, p, v)
    for v in ("s", "t"):
        out[f"cult_p0.0001_{v}"] = functools.partial(cult, 1e-4, v)
    return out


def points():
    pts = []
    for p in (1e-3, 1e-4):
        for v in ("s", "t"):
            pts.append(Point(f"hook_p{p:g}_{v}", f"hook_p{p:g}_{v}", "t" if v == "t" else "clifford", dict(kind="hook", p=p, gate=v),
                             target_errors=50000, max_shots=1e12, max_seconds=180, tier=1))
    for v in ("s", "t"):
        pts.append(Point(f"cult_p0.0001_{v}", f"cult_p0.0001_{v}", "t" if v == "t" else "clifford", dict(kind="cult", p=1e-4, gate=v),
                         target_errors=1000, max_shots=4e12, max_seconds=900, tier=2))
    return pts


def no_erasure_probability(text, e):
    """P(no erasure anywhere), with ``get_erased_circuit``'s rates: e per 2-qubit noise target and per
    SPAM (X/Y/Z_ERROR, noisy measurement) target, e/10 per DEPOLARIZE1 target."""
    logp = 0.0
    import math

    for line in text.splitlines():
        m = re.match(r"^\s*([A-Z_0-9]+)\(([^)]*)\)\s+(.*)$", line)
        if not m:
            continue
        name, arg, targets = m[1], float(m[2].split(",")[0]), [t for t in m[3].split() if t.lstrip("!").isdigit()]
        if arg == 0 and name.startswith("DEPOL"):
            continue
        if name == "DEPOLARIZE2":
            rate = e
        elif name == "DEPOLARIZE1":
            rate = e / 10
        elif name in ("X_ERROR", "Y_ERROR", "Z_ERROR") or name.startswith("M"):
            rate = e
        else:
            continue
        logp += len(targets) * math.log1p(-rate) if rate < 1 else -math.inf
    return math.exp(logp)


def figures(results):
    import matplotlib.pyplot as plt

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    g = common.load_results("gidney_cultivation")
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.9))
    used = []
    for ax, kind, title in ((axes[0], "hook", "Fig. 2: hook injection, $d_1=3$ (ungrown)"),
                            (axes[1], "cult", "Fig. 5(b): unitary injection + cultivation, $d=3$")):
        for gate, col, mk in (("s", "C0", "s"), ("t", "C3", "o")):
            xs, ys, lo, hi, labels = [], [], [], [], []
            for e, p in SCEN:
                if kind == "cult" and p == 1e-3:
                    r = g.get(gidney_cultivation.cname(3, "unitary", 1e-3, gate))
                    circ = common.circuit_path("gidney_cultivation", gidney_cultivation.cname(3, "unitary", 1e-3, gate))
                else:
                    key = f"{kind}_p{p:g}_{gate}"
                    r = results.get(key)
                    circ = common.circuit_path(STUDY, key)
                    used.append(key)
                if not r or not r["totals"]["kept"] or not circ.exists():
                    continue
                t = r["totals"]
                acc = t["kept"] / t["shots"] * no_erasure_probability(circ.read_text(), e)
                b, l, h = common.binomial_interval(t["errors"], t["kept"])
                xs.append(acc)
                ys.append(b)
                lo.append(b - l)
                hi.append(h - b)
                labels.append(f"e={e:g}, p={p:g}")
            if xs:
                ax.errorbar(xs, ys, yerr=[lo, hi], ls="none", marker=mk, color=col, ms=4, capsize=1.5,
                            label="S proxy" if gate == "s" else "T")
                if gate == "t":
                    for x, y, lab in zip(xs, ys, labels):
                        ax.annotate(lab, (x, y), fontsize=5, xytext=(3, 3), textcoords="offset points")
        ax.set_yscale("log")
        ax.set_xlabel("acceptance rate (incl. erasure postselection)")
        ax.set_ylabel("logical error rate per kept shot")
        ax.set_title(title)
        ax.legend()
    path = plotting.save(fig, out / "fig2_fig5b.pdf")
    return [common.Figure("erasure", path, "Jacoby et al. Figs. 2 and 5(b): erasure qubits, ungrown injection and cultivation",
                          "Each point is one erasure scenario $(e, p)$; the logical error rate comes from the Pauli-only circuit at residual rate $p$ "
                          "(one sample serves every $e$), and the acceptance is the sampled Pauli acceptance times the exact no-erasure probability.",
                          common.budget_line(results, used))]

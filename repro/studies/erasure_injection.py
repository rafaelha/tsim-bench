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

from repro import common, data_sources, magic_check
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


def _paper_fig2():
    """The released data of Fig. 2 (out/2024-12-24-compare_injections_5e6runs_2erasures)."""
    import csv

    path = data_sources.data_file("erasure_compare_injections_5e6runs_2erasures.csv")
    return [{k: (float(v) if k in ("p", "e", "pe", "em", "logical_err", "std_err", "success_rate") else v) for k, v in row.items()}
            for row in csv.DictReader(path.open())]


def figures(results):
    """The notebooks' figures (compare_injections.ipynb cell 3, cultivation.ipynb cell 10): two stacked panels, LER vs acceptance."""
    import matplotlib.pyplot as plt

    from repro import plotting

    out = common.REPORT / "figures" / STUDY
    g = common.load_results("gidney_cultivation")
    DBLUE, RED = "#00008B", "r"

    def ours(kind, gate):
        """(acceptance incl. erasure, LER, sigma, e, p) per scenario."""
        pts = []
        for e, p in SCEN:
            if kind == "cult" and p == 1e-3:
                r = g.get(gidney_cultivation.cname(3, "unitary", 1e-3, gate))
                circ = common.circuit_path("gidney_cultivation", gidney_cultivation.cname(3, "unitary", 1e-3, gate))
            else:
                r = results.get(f"{kind}_p{p:g}_{gate}")
                circ = common.circuit_path(STUDY, f"{kind}_p{p:g}_{gate}")
            if not r or not r["totals"]["kept"] or not circ.exists():
                continue
            t = r["totals"]
            acc = t["kept"] / t["shots"] * no_erasure_probability(circ.read_text(), e)
            ler = t["errors"] / t["kept"]
            pts.append((acc, ler, ler / max(t["errors"], 1) ** 0.5, e, p))
        return pts

    fig, axes = plt.subplots(2, 1, figsize=(6, 6.4))
    with plt.rc_context({"font.family": "DejaVu Sans"}):
        # ---- Fig. 2, hook-injection panel.
        ax = axes[0]
        for p, col in ((1e-3, "steelblue"), (1e-4, RED)):
            ax.axhline(7 * p / 30, ls="--", color=col, label=f"$7p/30$ limit for $p=10^{{{int(round(__import__('math').log10(p)))}}}$")
        pub = [r for r in _paper_fig2() if r["injection_type"] == "hook" and r["em"] == 0]
        for r in pub:
            col = DBLUE if r["e"] == 0 else RED
            ax.errorbar([r["success_rate"]], [r["logical_err"]], yerr=[1.96 * r["std_err"]], fmt="o", color=col, alpha=0.6, mfc="none", ms=7)
        ax.plot([], [], "o", color="0.4", mfc="none", label="paper (released data, $S$ state)")
        for gate, mk, lab in (("s", "s", "Tsim GPU, $S$ state"), ("t", "^", "Tsim GPU, $T$ state")):
            for acc, ler, sig, e, p in ours("hook", gate):
                ax.errorbar([acc], [ler], yerr=[1.96 * sig], fmt=mk, color=DBLUE if e == 0 else RED, ms=5)
            ax.plot([], [], mk, color="0.4", label=lab)
        for r in pub:
            ax.annotate(f"p={r['pe']:.0e}\ne={r['e']:.0e}" if r["e"] else f"p={r['pe']:.0e}\ne=0", (r["success_rate"], r["logical_err"]),
                        xytext=(0, 14), textcoords="offset points", ha="center", fontsize=8)
        ax.set_yscale("log")
        ax.set_xlim(0.35, 1.0)
        ax.set_ylim(1e-5, 1e-3)
        ax.set_title("Hook Injection", fontsize=12)
        ax.set_ylabel("Logical Error Rate", fontsize=12)
        ax.legend(fontsize=7.5, loc="upper left")
        ax.grid(True, which="both", alpha=0.3)
        # ---- Fig. 5(b): injection + cultivation.
        ax = axes[1]
        for gate, mk, lab in (("s", "o", "Tsim GPU, $S$ state (the paper's proxy)"), ("t", "^", "Tsim GPU, $T$ state")):
            for acc, ler, sig, e, p in ours("cult", gate):
                ax.errorbar([acc], [ler], yerr=[1.96 * sig], fmt=mk, color=DBLUE if e == 0 else RED, ms=6, alpha=0.75)
                if gate == "s":
                    ax.annotate(f"p={p:.0e}\ne={e:.0e}" if e else f"p$_n$={p:.0e}", (acc, ler), xytext=(8, 4), textcoords="offset points", fontsize=8)
            ax.plot([], [], mk, color="0.4", label=lab)
        ax.set_yscale("log")
        ax.set_xlim(0, 1)
        ax.set_ylim(1e-11, 4e-6)
        ax.set_title("Injection + Cultivation [d=3]", fontsize=12)
        ax.set_xlabel("Acceptance Rate", fontsize=12)
        ax.set_ylabel("Logical Error Rate", fontsize=12)
        ax.legend(fontsize=7.5, loc="upper left")
        ax.grid(True, which="both", alpha=0.3)
    path = plotting.save(fig, out / "injection_comparison.pdf")
    used = [k for k in results]
    return [common.Figure("erasure", path, "Jacoby et al. Figs. 2 (hook-injection panel) and 5(b): erasure qubits, ungrown injection and cultivation",
                          "Layout of the authors' notebooks (\\texttt{compare\\_injections.ipynb}, \\texttt{cultivation.ipynb}): logical error rate vs.\\ "
                          "acceptance, blue $p=10^{-3}$ without erasures, red residual $p=10^{-4}$ with erasure rate $e$; bars $1.96\\sigma$. Top: open circles "
                          "are the paper's released data (\\texttt{out/2024-12-24-compare\\_injections\\_5e6runs\\_2erasures}); our points use the released "
                          "\\texttt{QEC\\_hook\\_d=3.stim} example, whose noise model differs from the circuits behind the data (its LER is about 2x higher). "
                          "Bottom: Gidney's \\texttt{inject[unitary]+cultivate} circuit as in \\texttt{cultivation.ipynb}; the paper's values (read off the figure: "
                          "$3.3\\times10^{-7}$ at 0.69 for $p=10^{-3}$) match our $S$ points. Our acceptances include the exact no-erasure probability. The "
                          "Lao--Criger panel and the hybrid layouts are not reproduced.", common.budget_line(results, used))]

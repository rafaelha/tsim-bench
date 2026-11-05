r"""Chen et al. (2025), arXiv:2503.18657 -- Table 1, "ungrown" columns: MSC-3 and MSC-5 on the RP$^2$ code.

Table 1 lists, at $p=10^{-3}$, the logical error rate and discard rate of each cultivation process
alone (no escape stage), benchmarked by sampling the Clifford variant ($S$ for $T$, cultivating
$S|+\rangle$) with a final round of perfect stabilizer measurement and logical readout:
MSC-3 $8.3\times10^{-7}$ / 48.6\%, MSC-5 $3.6\times10^{-10}$ / 90.5\%.

Circuits: the authors' ``circuit_garage`` files (Zihan-Chen-PhMA/Cultiv_T_RP2 at 77ad9b3, written at
$p=10^{-3}$ by their ``d3_T_cult_sampling.py`` / ``d5_T_cult_sampling.py``). Clifford version: as
released. $T$ version: $S\to T$, $S^\dagger\to T^\dagger$ (reversing the authors' substitution) plus a
noiseless logical rotation (``repro/magic_check.py``) so that the final $Y_L$ readout checks the $T$ state
deterministically. MSC-5 with $T$ gates has Tsim active width 10, which makes it the slowest circuit here.
"""

import functools

from repro import common, magic_check
from repro.common import Point

STUDY = "rp2_ungrown"
SRC = common.PAPERS / "2503.18657_rp2_cultivation" / "stim_src" / "circuit_garage"
META = dict(arxiv="2503.18657", paper="Chen et al. (2025), Efficient magic state cultivation on RP$^2$")
FILES = {"msc3": "rp_3_T_cult", "msc5": "rp_3_rp_5_T_cult"}
TABLE = {"msc3": (8.3e-7, 0.486), "msc5": (3.6e-10, 0.905)}


def make(key, variant):
    proxy = (SRC / f"{FILES[key]}.stim").read_text()
    if variant == "s":
        common.noiseless_check(proxy)
        return proxy
    t = common.s_to_t(proxy)
    last = [l for l in t.splitlines() if l.startswith("MPP ")][-1].split()
    _, zl = magic_check.split_y(magic_check.parse_product(last[-1]))
    text, _ = magic_check.make_deterministic(t, zl)
    return text


def circuits():
    return {f"{k}_{v}": functools.partial(make, k, v) for k in FILES for v in ("s", "t")}


def points():
    return [
        Point("msc3_s", "msc3_s", "clifford", dict(code="msc3", gate="s"), target_errors=20000, max_shots=1e12, max_seconds=300, tier=1),
        Point("msc3_t", "msc3_t", "t", dict(code="msc3", gate="t"), target_errors=20000, max_shots=1e12, max_seconds=300, tier=1),
        Point("msc5_s", "msc5_s", "clifford", dict(code="msc5", gate="s"), target_errors=1000, max_shots=2e13, max_seconds=2400, tier=3),
        Point("msc5_t", "msc5_t", "t", dict(code="msc5", gate="t"), target_errors=1000, max_shots=2e13, max_seconds=3600, tier=3),
    ]


def figures(results):
    out = common.REPORT / "figures" / STUDY
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, label in (("msc3", "MSC-3"), ("msc5", "MSC-5")):
        pl, disc = TABLE[key]
        cells = [label, f"{pl:.2g}", f"{100 * disc:.1f}\\%"]
        for g in ("s", "t"):
            r = results.get(f"{key}_{g}")
            if r:
                t = r["totals"]
                b, lo, hi = common.binomial_interval(t["errors"], t["kept"])
                cells.append(f"{b:.3g} [{lo:.2g}, {hi:.2g}] ({t['errors']})")
                cells.append(f"{100 * (1 - t['kept'] / t['shots']):.2f}\\%")
                cells.append(f"{common.fmt_count(t['shots'])}, {common.fmt_seconds(t['seconds'])}")
            else:
                cells += ["--", "--", "--"]
        rows.append(" & ".join(cells) + r" \\")
    path = out / "table1.tex"
    path.write_text("\\begin{tabular}{l ll | lll | lll}\n\\toprule\n & \\multicolumn{2}{c|}{paper ($S$ proxy)} & \\multicolumn{3}{c|}{Tsim GPU, $S$ proxy} & \\multicolumn{3}{c}{Tsim GPU, $T$}\\\\\n"
                    "protocol & LER & discard & LER [1000x interval] (errors) & discard & shots, time & LER (errors) & discard & shots, time\\\\\n\\midrule\n"
                    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    return [common.Figure("rp2", path, "Chen et al. Table 1 (ungrown columns): RP$^2$ cultivation without escape, $p=10^{-3}$",
                          "Every detector postselected, perfect final stabilizer round and logical readout.",
                          common.budget_line(results), kind="table")]

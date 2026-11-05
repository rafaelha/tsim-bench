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
    """Table 1 in the paper's layout (rows: MSC-3, MSC d_color=3, MSC-5, MSC d_color=5; ungrown columns), with our columns."""
    from repro.studies import gidney_cultivation as gc

    out = common.REPORT / "figures" / STUDY
    out.mkdir(parents=True, exist_ok=True)
    g = common.load_results("gidney_cultivation")
    # Table 1 of the paper, ungrown columns (the end-to-end columns need a decoder).
    paper_rows = [("MSC-3 (this work)", 8.3e-7, 48.6, results, "msc3"),
                  ("MSC ($d_{\\text{color}}=3$)~[Gidney et al.]", 3.4e-7, 31.3, g, gc.cname(3, "unitary", 1e-3, "{g}")),
                  ("MSC-5 (this work)", 3.6e-10, 90.5, results, "msc5"),
                  ("MSC ($d_{\\text{color}}=5$)~[Gidney et al.]", 3.5e-10, 85.6, g, gc.cname(5, "unitary", 1e-3, "{g}"))]
    rows = []
    for label, pl, disc, res, key in paper_rows:
        cells = [label, f"${pl / 10**int(f'{pl:e}'.split('e')[1]):.1f}\\times 10^{{{int(f'{pl:e}'.split('e')[1])}}}$", f"${disc:.1f}\\%$"]
        for gate in ("s", "t"):
            k = key.replace("{g}", gate) if "{g}" in key else f"{key}_{gate}"
            r = res.get(k)
            if r and r["totals"]["kept"]:
                t = r["totals"]
                b, lo, hi = common.binomial_interval(t["errors"], t["kept"])
                cells.append(f"{b:.2g} ({t['errors']})" if t["errors"] else f"$<${hi:.1g}")
                cells.append(f"{100 * (1 - t['kept'] / t['shots']):.1f}\\%")
            else:
                cells += ["--", "--"]
        rows.append(" & ".join(cells) + r" \\")
    path = out / "table1.tex"
    path.write_text("\\begin{tabular}{l cc | cc | cc}\n\\toprule\n & \\multicolumn{2}{c|}{paper ($S$ proxy, Stim)} & \\multicolumn{2}{c|}{Tsim GPU, $S$ proxy} & "
                    "\\multicolumn{2}{c}{Tsim GPU, $T$}\\\\\nMSC protocol & Logical Error rate & Discard Rate & Logical Error rate & Discard Rate & "
                    "Logical Error rate & Discard Rate\\\\\n & (Ungrown) & (Ungrown) & (errors) & & (errors) & \\\\\n\\midrule\n"
                    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    return [common.Figure("rp2", path, "Chen et al. Table 1, ungrown columns: cultivation without escape, $p=10^{-3}$",
                          "The paper's Table 1 rows and ungrown columns (the end-to-end columns need a decoder). MSC-3/5: the authors' RP$^2$ "
                          "circuits; MSC ($d_\\text{color}=3,5$): Gidney et al.'s colour-code cultivation, whose Tsim GPU values are the Gidney "
                          "study's points. Every detector postselected, perfect final stabilizer round and logical readout.",
                          common.budget_line(results), kind="table")]


def checks(results):
    rows = []
    for key, (pl, disc) in TABLE.items():
        r = results.get(f"{key}_s")
        if r:
            rows.append(common.check_row(f"{key.upper()} S proxy", "clifford", dict(value=pl), r["totals"]))
            rows.append(common.check_row(f"{key.upper()} S proxy", "clifford", dict(value=1 - disc), r["totals"], quantity="acceptance"))
    return [x for x in rows if x]

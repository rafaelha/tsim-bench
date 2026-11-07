"""Data of the blog post's reproduction gallery (bloqade-website, ``tsim-gpu-reproductions``), as JSON.

    uv run python -m repro.blog_export [--out path]

Writes ``repro/blog/tsim_reproductions.json``: for each figure, the paper's released points and
the Tsim GPU points on the same axes (log-log, the paper's ranges), and for each table the
paper's values next to Tsim's; each slide carries its own compute budget (Tsim: GPU seconds and
shots summed over its points; paper: core-seconds and shots summed over the released sinter
stats it uses, where the paper released them). Only studies whose published numbers the GPU
reproduces are included. ``make_report`` calls this, so the file follows the results.
"""

import argparse
import json
import math
import pathlib

from repro import common

OUT = common.REPRO / "blog" / "tsim_reproductions.json"


def _point(errors, kept, shots, **extra):
    """One plotted point: max-likelihood rate and the 1000x likelihood interval (sinter's convention)."""
    best, lo, hi = common.binomial_interval(errors, kept)
    return dict(x=(shots + 1) / (kept + 2), y=best if errors else None, lo=lo, hi=hi, errors=errors, kept=kept, shots=shots, **extra)


def _tsim_budget(rows):
    t = [r["totals"] for r in rows]
    return dict(gpu_seconds=round(sum(x["seconds"] for x in t), 1), shots=sum(x["shots"] for x in t), points=len(t),
                gpu=rows[0]["segments"][0].get("gpu", "") if rows else "")


def gidney_figures():
    from repro.studies import gidney_cultivation as gc

    res = common.load_results("gidney_cultivation")
    pub = gc.published()
    meta = dict(arxiv="2409.17595", cite="cultivation", authors="Gidney, Shutty, Jones (2024)")
    slides = []

    # ---- Fig. 13: unitary injection + d=3 cultivation with T, S or Z, vs expected attempts.
    gates = [("t", "T", 1), ("s", "S", 2), ("z", "Z", 3)]
    paper, tsim, prow, trow = [], [], [], []
    for g, label, slot in gates:
        rows = sorted((r for r in pub if r["decoder"] == f"vec_intercept_{g}" and r["d"] == 3 and r["style"] == "unitary"), key=lambda r: r["p"])
        prow += rows
        paper.append(dict(id=g, label=f"{label}|+⟩", slot=slot, points=[_point(r["errors"], r["kept"], r["shots"], p=r["p"]) for r in rows]))
        ours = sorted((r for r in res.values() if r["params"]["d"] == 3 and r["params"]["style"] == "unitary"
                       and r["params"]["gate"] == g and r["params"]["p"] in gc.P13), key=lambda r: r["params"]["p"])
        trow += ours
        tsim.append(dict(id=g, label=f"{label}|+⟩", slot=slot,
                         points=[_point(r["totals"]["errors"], r["totals"]["kept"], r["totals"]["shots"], p=r["params"]["p"]) for r in ours]))
    slides.append(dict(
        id="gidney-fig13", kind="figure", **meta, ref="Fig. 13", tab="Cultivation, Fig. 13",
        title="Cultivating T|+⟩, S|+⟩ and Z|+⟩ states",
        caption="Unitary injection and d=3 cultivation, uniform depolarizing noise p from 0.1% to 1% (labels). "
                "The paper ran a state-vector simulation for every gate; Tsim samples the same circuits.",
        x=dict(label="Expected attempts per kept shot", min=1, max=100),
        y=dict(label="Logical error rate (per kept shot)", min=1e-7, max=1e-2),
        paper=dict(label="Paper (state vector)", series=paper,
                   budget=dict(core_seconds=round(sum(r.get("seconds", 0) for r in prow), 1), shots=sum(r["shots"] for r in prow))),
        tsim=dict(label="Tsim GPU", series=tsim, budget=_tsim_budget(trow))))

    # ---- Fig. 21: injection styles + d=3 cultivation and unitary + d=5, no escape, vs expected attempts.
    styles = [("bell", 3, "Bell injection, d=3", 4), ("teleport", 3, "Teleport injection, d=3", 3),
              ("unitary", 3, "Unitary injection, d=3", 2), ("unitary", 5, "Unitary injection, d=5", 1)]
    paper, tsim, prow, trow = [], [], [], []
    for style, d, label, slot in styles:
        rows = sorted((r for r in pub if r["decoder"] == "perfectionist" and r["d"] == d and r["style"] == style and r["p"] in gc.P21),
                      key=lambda r: r["p"])
        prow += rows
        paper.append(dict(id=f"{style}{d}-s", label=f"{label}, S", slot=slot, gate="S",
                          points=[_point(r["errors"], r["kept"], r["shots"], p=r["p"]) for r in rows]))
        for g in ("s", "t"):
            ours = sorted((r for r in res.values() if r["params"]["d"] == d and r["params"]["style"] == style
                           and r["params"]["gate"] == g and r["params"]["p"] in gc.P21), key=lambda r: r["params"]["p"])
            trow += ours
            tsim.append(dict(id=f"{style}{d}-{g}", label=f"{label}, {g.upper()}", slot=slot, gate=g.upper(),
                             points=[_point(r["totals"]["errors"], r["totals"]["kept"], r["totals"]["shots"], p=r["params"]["p"]) for r in ours]))
    slides.append(dict(
        id="gidney-fig21", kind="figure", **meta, ref="Fig. 21", tab="Cultivation, Fig. 21",
        title="Injection and cultivation without escape",
        caption="Three injection styles with d=3 cultivation, and unitary injection with d=5, at p = 0.05%, 0.1% and 0.2%. "
                "The paper sampled the S-gate stand-in with Stim (up to 10¹² shots per point); Tsim samples both the stand-in "
                "and the real T gates.",
        x=dict(label="Expected attempts per kept shot", min=1, max=100),
        y=dict(label="Logical error rate (per kept shot)", min=1e-13, max=1e-4),
        paper=dict(label="Paper (Stim, S stand-in)", series=paper,
                   budget=dict(core_seconds=round(sum(r.get("seconds", 0) for r in prow), 1), shots=sum(r["shots"] for r in prow))),
        tsim=dict(label="Tsim GPU", series=tsim, budget=_tsim_budget(trow))))
    return slides


def _cell(r):
    if not r or not r["totals"]["kept"]:
        return None
    t = r["totals"]
    best, lo, hi = common.binomial_interval(t["errors"], t["kept"])
    return dict(rate=t["errors"] / t["kept"], sigma=(t["errors"] ** 0.5 / t["kept"]) if t["errors"] else None, upper=None if t["errors"] else hi,
                errors=t["errors"], kept=t["kept"], shots=t["shots"], acceptance=t["kept"] / t["shots"])


def rp2_table():
    from repro.studies import gidney_cultivation as gc
    from repro.studies import rp2_ungrown as rp

    res, g = common.load_results("rp2_ungrown"), common.load_results("gidney_cultivation")
    rows, used = [], []
    for label, (pl, disc), src, key in [
            ("MSC-3 (RP²)", rp.TABLE["msc3"], res, "msc3_{g}"), ("MSC, colour code d=3", (3.4e-7, 0.313), g, gc.cname(3, "unitary", 1e-3, "{g}")),
            ("MSC-5 (RP²)", rp.TABLE["msc5"], res, "msc5_{g}"), ("MSC, colour code d=5", (3.5e-10, 0.856), g, gc.cname(5, "unitary", 1e-3, "{g}"))]:
        cells = {}
        for gate in ("s", "t"):
            r = src.get(key.format(g=gate))
            cells[gate] = _cell(r)
            if r:
                used.append(r)
        rows.append(dict(label=label, paper=dict(rate=pl, acceptance=1 - disc), tsim_s=cells["s"], tsim_t=cells["t"]))
    return dict(
        id="rp2-table1", kind="table", arxiv="2503.18657", cite="rp2", authors="Chen et al. (2025)", ref="Table 1", tab="RP², Table 1", standin="S gates",
        title="Cultivation on RP² vs. the colour code",
        caption="Ungrown cultivation at p = 0.1%: logical error rate per kept shot and acceptance. The paper sampled the "
                "S-gate stand-in with Stim; Tsim samples the stand-in and the real T gates.",
        columns=["Logical error rate", "Acceptance"], paper_label="Paper (Stim, S stand-in)",
        rows=rows, tsim_budget=_tsim_budget(used))


def gauging_table():
    from repro.studies import gauging_cultivation as gg

    res = common.load_results("gauging_cultivation")
    rows, used = [], []
    for (p, d), (pl, e, _) in gg.TABLE.items():
        cells = {}
        for gate in ("s", "t"):
            r = res.get(gg.name(d, p, gate))
            cells[gate] = _cell(r)
            if r:
                used.append(r)
        rows.append(dict(label=f"p = {100 * p:g}%, d = {d}", paper=dict(rate=pl, sigma=e), tsim_s=cells["s"], tsim_t=cells["t"]))
    return dict(
        id="gauging-table1", kind="table", arxiv="2603.05429", cite="gauging", authors="Hetényi, Brown, Williamson (2026)", ref="Table 1", tab="Gauging, Table 1", standin="|+i⟩ state",
        title="Cultivation with Clifford measurements by gauging",
        caption="Logical error rate per kept shot of the gauging protocol at final distance 3 and 5. The paper sampled "
                "the |+i⟩ stand-in with Stim; Tsim samples the stand-in and the real T state.",
        columns=["Logical error rate"], paper_label="Paper (Stim, |+i⟩ stand-in)",
        rows=rows, tsim_budget=_tsim_budget(used))


def _clean(x):
    """JSON without NaN/inf, floats to 4 significant digits."""
    if isinstance(x, float):
        return None if not math.isfinite(x) else float(f"{x:.4g}")
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean(v) for v in x]
    return x


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    slides = gidney_figures() + [rp2_table(), gauging_table()]
    builds = sorted({r["tsim"]["commit"][:8] for st in ("gidney_cultivation", "rp2_ungrown", "gauging_cultivation")
                     for r in common.load_results(st).values() if r.get("tsim")})
    data = dict(source="https://github.com/rafaelha/tsim-bench/tree/master/repro", tsim_builds=builds, slides=slides)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_clean(data), indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({len(slides)} slides)")


if __name__ == "__main__":
    main()

"""Data of the blog post's reproduction gallery (bloqade-website, ``tsim-gpu-reproductions``), as JSON.

    uv run python -m repro.blog_export [--out path]

Writes ``repro/blog/tsim_reproductions.json``, one slide per published figure or table:

- figure slides: axes (log or linear, the paper's ranges), the paper's released points (``paper``,
  absent where the paper released no numbers) and Tsim's (``tsim``) as series of points, plus
  guide lines and footnotes. Every point carries an interval: the rates within a factor 1000 of
  the maximum likelihood (sinter's convention). Published values given only with a standard
  error are turned back into counts (errors ~ (rate/sigma)^2) and get the same interval.
- table slides: the paper's values next to Tsim's, each with one standard deviation.

Each slide carries its own compute budget (Tsim: GPU seconds and shots summed over its points;
paper: core-seconds and shots of the released sinter stats, or the compute the paper quotes).
``make_report`` calls this, so the file follows the results.
"""

import argparse
import csv
import json
import math
import pathlib

from repro import common, data_sources

OUT = common.REPRO / "blog" / "tsim_reproductions.json"
TAU = 2 * math.pi


# ---------------------------------------------------------------------------------------------
# Points, series, budgets


def _rate(errors, kept, x, **extra):
    """A rate point at abscissa ``x``: max likelihood and the 1000x likelihood interval."""
    best, lo, hi = common.binomial_interval(errors, kept)
    return dict(x=x, y=best if errors else None, lo=lo, hi=hi, errors=int(errors), kept=int(kept), **extra)


def _attempts(shots, kept):
    """Expected attempts per kept shot, as in sinter's plots of the papers."""
    return (shots + 1) / (kept + 2)


def _from_totals(t, x, **extra):
    return _rate(t["errors"], t["kept"], x, **extra)


def _from_sigma(rate, sigma, x, **extra):
    """A published rate with only a standard error: back to counts, then the same interval."""
    errors = max(1, round((rate / sigma) ** 2)) if sigma else 1
    return _rate(errors, errors / rate, x, **extra)


def _series(sid, label, slot, points, shape="circle", line=True, dash=False, labels=False):
    return dict(id=sid, label=label, slot=slot, shape=shape, line=line, dash=dash, labels=labels, points=points)


def _budget(rows):
    t = [r["totals"] for r in rows]
    return dict(gpu_seconds=round(sum(x["seconds"] for x in t), 1), shots=sum(x["shots"] for x in t), points=len(t),
                gpu=rows[0]["segments"][0].get("gpu", "") if rows else "")


def _pct(p):
    return f"p={p * 100:.2g}%"


def _layer(label, series, budget=None, quoted=None):
    return dict(label=label, series=series, budget=budget or {}, quoted=quoted)


def _figure(sid, tab, authors, arxiv, cite, ref, title, caption, x, y, tsim, paper=None, notes=(), guides=(), stars=(), square=False):
    return dict(id=sid, kind="figure", tab=tab, authors=authors, arxiv=arxiv, cite=cite, ref=ref, title=title, caption=caption,
                x=x, y=y, paper=paper, tsim=tsim, notes=list(notes), guides=list(guides), stars=list(stars), square=square)


def _axis(label, lo, hi, scale="log", ticks=None):
    return dict(label=label, min=lo, max=hi, scale=scale, ticks=ticks)


GATE_SHAPE = {"t": "triangle", "s": "circle", "z": "square", "y": "circle", "clifford": "circle"}


# ---------------------------------------------------------------------------------------------
# Gidney, Shutty, Jones: Figs. 13 and 21


def gidney():
    from repro.studies import gidney_cultivation as gc

    res = common.load_results("gidney_cultivation")
    pub = gc.published()
    meta = dict(authors="Gidney, Shutty, Jones (2024)", arxiv="2409.17595", cite="cultivation")
    slides = []

    paper, tsim, prow, trow = [], [], [], []
    for g, label, slot in (("t", "T|+⟩", 1), ("s", "S|+⟩", 2), ("z", "Z|+⟩", 3)):
        rows = sorted((r for r in pub if r["decoder"] == f"vec_intercept_{g}" and r["d"] == 3 and r["style"] == "unitary"),
                      key=lambda r: r["p"])
        prow += rows
        paper.append(_series(g, label, slot, [_rate(r["errors"], r["kept"], _attempts(r["shots"], r["kept"]), label=_pct(r["p"]))
                                              for r in rows], shape=GATE_SHAPE[g], dash=g == "t", labels=g == "t"))
        ours = sorted((r for r in res.values() if r["params"]["d"] == 3 and r["params"]["style"] == "unitary"
                       and r["params"]["gate"] == g and r["params"]["p"] in gc.P13), key=lambda r: r["params"]["p"])
        trow += ours
        tsim.append(_series(g, label, slot, [_from_totals(r["totals"], _attempts(r["totals"]["shots"], r["totals"]["kept"]),
                                                          label=_pct(r["params"]["p"])) for r in ours],
                            shape=GATE_SHAPE[g], dash=g == "t", labels=g == "t"))
    slides.append(_figure(
        "gidney-fig13", "Cultivation: T, S and Z", **meta, ref="Fig. 13", title="Cultivating T|+⟩, S|+⟩ and Z|+⟩ states",
        caption="Unitary injection and d=3 cultivation under uniform depolarizing noise p (labels). The paper ran a state-vector "
                "simulation of every gate; Tsim samples the same circuits.",
        x=_axis("Expected attempts per kept shot", 1, 100), y=_axis("Logical error rate (per kept shot)", 1e-7, 1e-2),
        paper=_layer("Paper (state vector)", paper, dict(core_seconds=round(sum(r["seconds"] for r in prow)), shots=sum(r["shots"] for r in prow))),
        tsim=_layer("Tsim GPU", tsim, _budget(trow))))

    paper, tsim, prow, trow = [], [], [], []
    for style, d, label, slot in (("bell", 3, "Bell injection, d=3", 4), ("teleport", 3, "Teleport injection, d=3", 3),
                                  ("unitary", 3, "Unitary injection, d=3", 2), ("unitary", 5, "Unitary injection, d=5", 1)):
        rows = sorted((r for r in pub if r["decoder"] == "perfectionist" and r["d"] == d and r["style"] == style and r["p"] in gc.P21),
                      key=lambda r: r["p"])
        prow += rows
        lab = style == "unitary"
        paper.append(_series(f"{style}{d}-s", f"{label}, S", slot,
                             [_rate(r["errors"], r["kept"], _attempts(r["shots"], r["kept"]), label=_pct(r["p"])) for r in rows], labels=lab))
        for g in ("s", "t"):
            ours = sorted((r for r in res.values() if r["params"]["d"] == d and r["params"]["style"] == style
                           and r["params"]["gate"] == g and r["params"]["p"] in gc.P21), key=lambda r: r["params"]["p"])
            trow += ours
            tsim.append(_series(f"{style}{d}-{g}", f"{label}, {g.upper()}", slot,
                                [_from_totals(r["totals"], _attempts(r["totals"]["shots"], r["totals"]["kept"]), label=_pct(r["params"]["p"]))
                                 for r in ours], shape=GATE_SHAPE[g], dash=g == "t", labels=lab and g == "s"))
    slides.append(_figure(
        "gidney-fig21", "Cultivation: injection styles", **meta, ref="Fig. 21", title="Injection and cultivation without escape",
        caption="Three injection styles with d=3 cultivation, and unitary injection with d=5, at p = 0.05%, 0.1% and 0.2%. The paper "
                "sampled the S-gate stand-in with Stim, up to 10¹² shots per point; Tsim samples the stand-in and the real T gates.",
        x=_axis("Expected attempts per kept shot", 1, 100), y=_axis("Logical error rate (per kept shot)", 1e-13, 1e-4),
        paper=_layer("Paper (Stim, S stand-in)", paper, dict(core_seconds=round(sum(r["seconds"] for r in prow)), shots=sum(r["shots"] for r in prow))),
        tsim=_layer("Tsim GPU", tsim, _budget(trow)),
        notes=["The paper saw no error in 10¹² shots at d=5, p=0.05%: its point is an upper bound (open marker)."]))
    return slides


# ---------------------------------------------------------------------------------------------
# Tables


def _cell(r):
    """Tsim's value: rate with one standard deviation (Poisson on the errors), acceptance with its binomial sigma."""
    if not r or not r["totals"]["kept"]:
        return None
    t = r["totals"]
    a = t["kept"] / t["shots"]
    best, lo, hi = common.binomial_interval(t["errors"], t["kept"])
    return dict(rate=t["errors"] / t["kept"], sigma=(t["errors"] ** 0.5 / t["kept"]) if t["errors"] else None,
                upper=None if t["errors"] else hi, errors=t["errors"], kept=t["kept"], shots=t["shots"],
                acceptance=a, acceptance_sigma=(a * (1 - a) / t["shots"]) ** 0.5)


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
        rows.append(dict(label=label, paper=dict(rate=pl, acceptance=round(1 - disc, 4)), tsim_s=cells["s"], tsim_t=cells["t"]))
    return dict(
        id="rp2-table1", kind="table", tab="RP² cultivation", arxiv="2503.18657", cite="rp2", authors="Chen et al. (2025)", ref="Table 1",
        title="Cultivation on RP² vs. the colour code", standin="S gates", columns=["rate", "acceptance"],
        caption="Ungrown cultivation at p = 0.1%: logical error rate per kept shot (± one standard deviation) and the fraction of "
                "shots kept. The paper sampled the S-gate stand-in with Stim; Tsim samples the stand-in and the real T gates.",
        paper_label="Paper (Stim, S stand-in)", rows=rows, tsim_budget=_budget(used),
        notes=["The paper gives no uncertainties; its values are compared as rounded to the printed digits."])


def gauging_table():
    from repro.studies import gauging_cultivation as gg

    res = common.load_results("gauging_cultivation")
    rows, used = [], []
    for (p, d), (pl, e, ps) in gg.TABLE.items():
        cells = {}
        for gate in ("s", "t"):
            r = res.get(gg.name(d, p, gate))
            cells[gate] = _cell(r)
            if r:
                used.append(r)
        row = dict(label=f"p = {100 * p:g}%, d = {d}", paper=dict(rate=pl, sigma=e, acceptance=ps), tsim_s=cells["s"], tsim_t=cells["t"])
        if (p, d) == (5e-4, 3):
            row["note"] = 1
        rows.append(row)
    return dict(
        id="gauging-table1", kind="table", tab="Gauging: Table 1", arxiv="2603.05429", cite="gauging",
        authors="Hetényi, Brown, Williamson (2026)", ref="Table 1", title="Cultivation with Clifford measurements by gauging",
        standin="|+i⟩ state", columns=["rate", "acceptance"],
        caption="Logical error rate per kept shot (± one standard deviation) and success rate at final distance 3 and 5. The paper "
                "sampled the |+i⟩ stand-in with Stim; Tsim samples the stand-in and the real T state.",
        paper_label="Paper (Stim, |+i⟩ stand-in)", rows=rows, tsim_budget=_budget(used),
        notes=["The authors' generator at its released commit keeps 68% of the shots at d=3, p=0.05%, against the 65% printed in the "
               "paper; the error rates agree. The paper prints success rates to two digits without uncertainties."])


# ---------------------------------------------------------------------------------------------
# Hetényi et al. Fig. 4(a)


def gauging_fig4a():
    from repro.studies import gauging_cultivation as gg

    res = {k: r for k, r in common.load_results("gauging_cultivation").items() if r["params"].get("kind") != "yield"}
    paper = []
    for key, label, slot, shape, dash in (("stim_Y", "|+i⟩, Stim", 2, "circle", False), ("qiskit_Y", "|+i⟩, Qiskit (paper only)", 3, "square", False),
                                          ("qiskit_T", "|T⟩, Qiskit", 1, "triangle", True)):
        nb = gg.NB_A[key]
        paper.append(_series(key, label, slot, [_from_sigma(lf, le, y, label=_pct(p)) for p, y, lf, le in
                                                zip(nb["err_list"], nb["yield_list"], nb["LF_list"], nb["LF_errlist"])],
                             shape=shape, dash=dash, labels=key == "stim_Y"))
    tsim, used = [], []
    for g, label, slot, shape in (("s", "|+i⟩", 2, "circle"), ("t", "|T⟩", 1, "triangle")):
        rows = sorted((r for r in res.values() if r["params"]["d"] == 3 and r["params"]["gate"] == g and r["params"]["p"] >= 1e-3),
                      key=lambda r: r["params"]["p"])
        used += rows
        tsim.append(_series(g, label, slot, [_from_totals(r["totals"], r["totals"]["kept"] / r["totals"]["shots"], label=_pct(r["params"]["p"]))
                                             for r in rows], shape=shape, dash=g == "t", labels=g == "s"))
    return _figure(
        "gauging-fig4a", "Gauging: Fig. 4(a)", "Hetényi, Brown, Williamson (2026)", "2603.05429", "gauging", "Fig. 4(a)",
        "Gauging cultivation, d=3: stand-in and T state",
        "Logical error rate against the success probability for p = 0.1% to 0.5% (labels). The paper sampled the |+i⟩ stand-in with "
        "Stim and Qiskit, and the T state with Qiskit's state-vector simulator; Tsim samples both.",
        x=_axis("Success probability", 1e-2, 1), y=_axis("Logical error rate (per kept shot)", 1e-7, 1e-3),
        paper=_layer("Paper (Stim, Qiskit)", paper), tsim=_layer("Tsim GPU", tsim, _budget(used)),
        notes=["The paper's Qiskit |T⟩ point at p=0.1% rests on a single logical error, hence its wide interval."])


# ---------------------------------------------------------------------------------------------
# Tsim-only figures (the paper released no numbers)


def vaknin():
    res = common.load_results("vaknin_full_vector")
    tsim, used = [], []
    for g, label, slot in (("clifford", "Clifford approximation", 2), ("t", "Real T gates", 1)):
        rows = sorted((r for r in res.values() if r["params"]["gate"] == g), key=lambda r: r["params"]["p"])
        used += rows
        tsim.append(_series(g, label, slot, [_from_totals(r["totals"], _attempts(r["totals"]["shots"], r["totals"]["kept"]), label=_pct(r["params"]["p"]))
                                             for r in rows], shape=GATE_SHAPE[g], dash=g == "t", labels=g == "clifford"))
    return _figure(
        "vaknin-fig26", "Surface-code cultivation", "Vaknin et al. (2025)", "2502.01743", "vaknin", "Fig. 26",
        "Cultivation on the unrotated surface code",
        "H-state cultivation, logical error rate against expected attempts for p = 0.02% to 0.8% (labels): the paper's Clifford "
        "approximation and the circuit with real T gates.",
        x=_axis("Expected attempts per kept shot", 1, 1000), y=_axis("Logical error rate (per kept shot)", 1e-10, 1e-2),
        tsim=_layer("Tsim GPU", tsim, _budget(used)),
        paper=_layer("Paper (state vector)", [], quoted="about 10⁶ CPU hours, about 10⁷ shots per point"),
        notes=["The paper's full state-vector points are shown only as a figure, so only Tsim's data is plotted."])


def chan():
    res = common.load_results("chan_flags")
    slides = []
    tsim, used = [], []
    for c, label, slot in (("d3a6", "Original", 1), ("d3a6f2", "With Z flags", 3)):
        for g in ("s", "t"):
            rows = sorted((r for r in res.values() if r["params"]["circuit"] == c and r["params"]["gate"] == g), key=lambda r: r["params"]["p"])
            used += rows
            tsim.append(_series(f"{c}-{g}", f"{label}, {g.upper()}", slot, [_from_totals(r["totals"], r["params"]["p"]) for r in rows],
                                shape=GATE_SHAPE[g], dash=g == "t"))
    slides.append(_figure(
        "chan-d3", "Flags: d=3", "Chan, Strikis, Sun, Cai (2026)", "2609.17706", "chan", "Fig. 10",
        "Cultivation's degraded fault distance, d=3",
        "Logical error rate before escape against the noise strength, for the original double check and with the paper's Z flags. "
        "With real T gates the original circuit loses a power of p; the flags restore it.",
        x=_axis("Noise strength p", 1e-4, 1e-2), y=_axis("Logical error rate (per kept shot)", 1e-10, 1e-3),
        tsim=_layer("Tsim GPU", tsim, _budget(used)), paper=_layer("Paper (SymFT)", []),
        notes=["The paper released no numbers for this figure, so only Tsim's data is plotted."]))
    tsim, used = [], []
    for c, label, slot in (("d5a19", "Original", 1), ("d5a19f13", "With Z flags", 3)):
        rows = sorted((r for r in res.values() if r["params"]["circuit"] == c and r["params"]["gate"] == "t"), key=lambda r: r["params"]["p"])
        used += rows
        tsim.append(_series(c, f"{label}, T", slot, [_from_totals(r["totals"], _attempts(r["totals"]["shots"], r["totals"]["kept"]),
                                                                  label=_pct(r["params"]["p"])) for r in rows],
                            shape="triangle", dash=True, labels=c == "d5a19"))
    slides.append(_figure(
        "chan-d5", "Flags: d=5", "Chan, Strikis, Sun, Cai (2026)", "2609.17706", "chan", "Fig. 1(c)",
        "Z flags at d=5, with real T gates",
        "Logical error rate before escape against expected attempts, for p = 0.05% to 0.3% (labels). The flags cut the error rate "
        "5 to 11 times at almost no cost in kept shots.",
        x=_axis("Expected attempts per kept shot", 1, 1000), y=_axis("Logical error rate (per kept shot)", 1e-12, 1e-6),
        tsim=_layer("Tsim GPU", tsim, _budget(used)), paper=_layer("Paper (SymFT)", []),
        notes=["The paper released no numbers for this figure, so only Tsim's data is plotted."]))
    return slides


def fold():
    res = common.load_results("fold_transversal")
    tsim, used = [], []
    for g, label, slot in (("y", "|Y⟩ (Clifford)", 2), ("t", "|H_XY⟩ (real T)", 1)):
        rows = sorted((r for r in res.values() if r["params"]["gate"] == g), key=lambda r: r["params"]["p"])
        used += rows
        # Labels on a subset: the low-p points crowd.
        tsim.append(_series(g, label, slot, [_from_totals(r["totals"], _attempts(r["totals"]["shots"], r["totals"]["kept"]),
                                                          label="" if r["params"]["p"] in (7e-4, 1.5e-3) else _pct(r["params"]["p"]))
                                             for r in rows], shape=GATE_SHAPE[g], dash=g == "t", labels=g == "y"))
    return _figure(
        "fold", "Fold-transversal", "Sahay et al. (2025)", "2509.05212", "fold", "Fig. 16(b)",
        "Fold-transversal cultivation: |Y⟩ vs. |H_XY⟩",
        "Fault-distance-3 cultivation without escape, logical error rate against expected attempts for p = 0.05% to 0.7% (labels).",
        x=_axis("Expected attempts per kept shot", 1, 10), y=_axis("Logical error rate (per kept shot)", 1e-9, 1e-3),
        tsim=_layer("Tsim GPU", tsim, _budget(used)), paper=_layer("Paper (Stim, state vector)", []),
        notes=["The paper released no numbers for this panel, so only Tsim's data is plotted.",
               "Read off the paper's figure, its |Y⟩ point at p=0.1% is about 1.8 × 10⁻⁷, against 5 × 10⁻⁸ here: the paper's circuit "
               "for this panel has more fault locations than the one its released generator produces."])


def erasure():
    from repro.studies import erasure_injection as er

    res = common.load_results("erasure_injection")
    rows_csv = [r for r in csv.DictReader(data_sources.data_file("erasure_compare_injections_5e6runs_2erasures.csv").open())
                if r["injection_type"] == "hook" and float(r["em"]) == 0]
    paper = []
    for e_zero, sid, label, slot in ((True, "noerase", "No erasures, p=0.1%, S", 1), (False, "erase", "Erasure qubits, p=0.01%, S", 2)):
        pts = []
        for r in sorted(rows_csv, key=lambda r: -float(r["success_rate"])):
            e = float(r["e"])
            if (e == 0) != e_zero:
                continue
            kept = 5e6 * float(r["success_rate"])
            pts.append(_rate(round(float(r["logical_err"]) * kept), kept, float(r["success_rate"]), label="" if e_zero else f"e={e * 100:g}%"))
        paper.append(_series(sid, label, slot, pts, line=False, labels=not e_zero))
    tsim, used = [], []
    for g in ("s", "t"):
        for e_zero, sid, label, slot in ((True, "noerase", "No erasures, p=0.1%", 1), (False, "erase", "Erasure qubits, p=0.01%", 2)):
            pts = []
            for e, p in er.SCEN:
                if (e == 0) != e_zero:
                    continue
                r = res.get(f"hook_p{p:g}_{g}")
                circ = common.circuit_path(er.STUDY, f"hook_p{p:g}_{g}")
                if not r or not circ.exists():
                    continue
                if r not in used:
                    used.append(r)
                t = r["totals"]
                acc = t["kept"] / t["shots"] * er.no_erasure_probability(circ.read_text(), e)
                pts.append(_from_totals(t, acc, label="" if e_zero or g == "t" else f"e={e * 100:g}%"))
            tsim.append(_series(f"{sid}-{g}", f"{label}, {g.upper()}", slot, pts, shape=GATE_SHAPE[g], line=False, labels=not e_zero and g == "s"))
    guides = [dict(points=[[0.3, 7 * p / 30], [1, 7 * p / 30]], dash=True, label=f"7p/30, p={p * 100:g}%") for p in (1e-3, 1e-4)]
    return _figure(
        "erasure-fig2", "Erasure qubits", "Jacoby et al. (2025)", "2504.02935", "erasure", "Fig. 2",
        "Hook injection with erasure qubits",
        "Logical error rate against acceptance for hook injection at d=3: without erasures at p = 0.1%, and with erasure qubits "
        "(erasure rate e, residual p = 0.01%), where shots with a detected erasure are discarded. The paper sampled the S stand-in.",
        x=_axis("Acceptance", 0.3, 1.0, scale="linear", ticks=[[0.4, "0.4"], [0.6, "0.6"], [0.8, "0.8"], [1.0, "1"]]),
        y=_axis("Logical error rate (per kept shot)", 1e-5, 1e-3),
        paper=_layer("Paper (S stand-in)", paper, dict(shots=5e6 * len(rows_csv))), tsim=_layer("Tsim GPU", tsim, _budget(used)),
        guides=guides,
        notes=["Tsim samples the hook circuit released with the paper. Its noise model differs from the circuits behind the released "
               "data, which explains the higher error rate (about 2×) without erasures."])


def star():
    from repro.studies import star_injection as st

    res = common.load_results("star_injection")
    slides = []
    for panel, xkey, sel, axis, title in (
            ("a", "p", lambda pr: abs(pr["angle"] * math.pi - st.PAPER_ANGLE) < 1e-12 and pr["p"] in st.PAPER_PS,
             _axis("Noise strength p", 5e-4, 1e-2), "against the noise strength, at a logical angle of 0.01 rad"),
            ("b", "angle", lambda pr: pr["p"] == st.PAPER_P and any(abs(pr["angle"] * math.pi - a) < 1e-12 for a in st.PAPER_ANGLES),
             _axis("Logical rotation angle (rad)", 5e-4, 2e-1), "against the rotation angle, at p = 0.073%")):
        tsim, used = [], []
        for d, slot, shape in ((3, 4, "circle"), (5, 2, "square"), (7, 1, "diamond")):
            rows = sorted((r for r in res.values() if r["params"]["d"] == d and sel(r["params"])),
                          key=lambda r: r["params"][xkey])
            used += rows
            xs = (lambda pr: pr["p"]) if xkey == "p" else (lambda pr: pr["angle"] * math.pi)
            tsim.append(_series(f"d{d}", f"d={d}", slot, [_from_totals(r["totals"], xs(r["params"])) for r in rows], shape=shape))
        slides.append(_figure(
            f"star-fig6{panel}", f"STAR: Fig. 6({panel})", "Ismail et al. (2025)", "2509.18294", "star", f"Fig. 6({panel})",
            "Small-angle injection with STAR",
            f"Postselected logical error rate of transversal small-angle rotations, {title}, for d = 3, 5 and 7.",
            x=axis, y=_axis("Logical error rate (per kept shot)", 1e-7 if panel == "a" else 1e-8, 1 if panel == "a" else 1e-3),
            tsim=_layer("Tsim GPU", tsim, _budget(used)), paper=_layer("Paper", []),
            notes=["Tsim samples QuEra's public STAR challenge circuits under uniform depolarizing noise, not the paper's "
                   "hardware-aware noise model, so the curves are not expected to coincide with the paper's, which released no numbers."]))
    return slides


def google():
    from repro.studies import google_experiment as ge

    res = common.load_results("google_experiment")
    meta = dict(authors="Rosenfeld et al. (2025)", arxiv="2512.13908", cite="google")
    slides = []

    def tomo(key):
        pts, used = [], []
        for k in range(len(ge.THETAS)):
            rx, rz = res.get(ge.tname(key, "X", k)), res.get(ge.tname(key, "Z", k))
            if not (rx and rz and rx["totals"]["kept"] and rz["totals"]["kept"]):
                continue
            used += [rx, rz]
            vals = []
            for r in (rx, rz):
                t = r["totals"]
                best, lo, hi = common.binomial_interval(t["obs_ones"][0], t["kept"])
                vals.append((1 - 2 * best, 1 - 2 * hi, 1 - 2 * lo))
            pts.append(dict(x=vals[0][0], xlo=vals[0][1], xhi=vals[0][2], y=vals[1][0], lo=vals[1][1], hi=vals[1][2]))
        return pts, used

    circle = [[math.sin(a), math.cos(a)] for a in (TAU * k / 120 for k in range(121))]
    star_pt = [[math.sqrt(0.5), math.sqrt(0.5)]]
    tsim, used = [], []
    for key, label, slot, shape in (("fig2_injection", "Injection only", 2, "cross"), ("fig2_cultivation", "Injection + cultivation", 1, "diamond")):
        pts, u = tomo(key)
        used += u
        tsim.append(_series(key, label, slot, pts, shape=shape, line=False))
    lin = [[-1, "−1"], [-0.5, "−0.5"], [0, "0"], [0.5, "0.5"], [1, "1"]]
    slides.append(_figure(
        "google-fig2", "Google: Fig. 2", **meta, ref="Fig. 2(B)", title="Logical tomography of the injected state",
        caption="Postselected logical ⟨X⟩ and ⟨Z⟩ for 24 injected angles θ, SI1000 noise at p = 0.3%: injection alone, and with d=3 "
                "cultivation, which projects every input onto the magic axis (dotted). Star: the ideal T state.",
        x=_axis("⟨X⟩", -1.1, 1.1, "linear", lin), y=_axis("⟨Z⟩", -1.1, 1.1, "linear", lin), square=True,
        tsim=_layer("Tsim GPU", tsim, _budget(used)), paper=_layer("Paper (state vector)", []),
        guides=[dict(points=circle), dict(points=[[-0.71, -0.71], [0.71, 0.71]], dash=True)], stars=star_pt,
        notes=["The paper's grey simulation points are not released, so only Tsim's data is plotted."]))

    tsim, used = [], []
    for key, label, slot, shape in (("fig3_injection", "Injection only", 2, "cross"), ("fig3_kt_no_qec", "Cultivation, no QEC cycles", 3, "circle"),
                                    ("fig3_kt", "Cultivation with QEC cycles", 1, "diamond")):
        ser = ge._kt_series(res, key)
        rows = [r for r in res.values() if r["params"]["kind"] == "kt" and r["params"]["key"] == key and abs(r["params"]["p"] - 2.3e-3) < 1e-12]
        used += rows
        tsim.append(_series(key, label, slot, [_from_totals(t, th) for th, t in ser if t["kept"]], shape=shape, line=False))
    pis = [[math.pi / 4, "π/4"], [math.pi, "π"], [5 * math.pi / 4, "5π/4"], [TAU, "2π"]]
    slides.append(_figure(
        "google-fig3", "Google: Fig. 3", **meta, ref="Fig. 3(B)", title="Kickback tomography against the injected angle",
        caption="Logical error of the whole kickback-tomography circuit against the injected angle θ, SI1000 noise at p = 0.23%. "
                "Cultivation with QEC cycles is lowest at θ = π/4, the T state (dotted).",
        x=_axis("Injected angle θ", 0, TAU, "linear", pis), y=_axis("Logical error probability", 1e-5, 2),
        tsim=_layer("Tsim GPU", tsim, _budget(used)), paper=_layer("Paper (state vector)", []),
        guides=[dict(points=[[math.pi / 4, 1e-5], [math.pi / 4, 2]], dash=True), dict(points=[[5 * math.pi / 4, 1e-5], [5 * math.pi / 4, 2]], dash=True)],
        notes=["The paper's grey simulation points are not released, so only Tsim's data is plotted."]))

    quarter = [[math.sin(a), math.cos(a)] for a in (math.pi / 2 * k / 60 for k in range(61))]
    tsim, used = [], []
    for key, label, slot, shape in (("fig4_injection_N2", "Injection, N = 2", 2, "cross"), ("fig4_cultivation_N2", "Cultivation, N = 2", 3, "circle"),
                                    ("fig4_cultivation_N3", "Cultivation, N = 3", 1, "diamond")):
        pts, u = tomo(key)
        used += u
        # The paper's panel shows the positive quadrant, the angles between 0 and pi/2.
        pts = [pt for pt in pts if pt["x"] > -0.02 and pt["y"] > -0.02]
        tsim.append(_series(key, label, slot, pts, shape=shape, line=False))
    q = [[0, "0"], [0.5, "0.5"], [1, "1"]]
    slides.append(_figure(
        "google-fig4", "Google: Fig. 4", **meta, ref="Fig. 4(B)", title="Tomography after grafting to the surface code",
        caption="Logical ⟨X⟩ and ⟨Z⟩ after growing the cultivated state into a d=5 surface code and idling N QEC cycles, SI1000 "
                "noise at p = 0.23%. Star: the ideal T state.",
        x=_axis("⟨X⟩", 0, 1.02, "linear", q), y=_axis("⟨Z⟩", 0, 1.02, "linear", q), square=True,
        tsim=_layer("Tsim GPU", tsim, _budget(used)), paper=_layer("Paper (state vector)", []),
        guides=[dict(points=quarter), dict(points=[[0, 0], [0.71, 0.71]], dash=True)], stars=star_pt,
        notes=["The paper decodes the grafted surface code with a decoder; here every detector is postselected, so these points "
               "are a decoder-free upper bound on the fidelity, not the paper's protocol.",
               "The paper's grey simulation points are not released, so only Tsim's data is plotted."]))
    return slides


# ---------------------------------------------------------------------------------------------


def _clean(x):
    """JSON without NaN/inf, floats to 4 significant digits."""
    if isinstance(x, float):
        return None if not math.isfinite(x) else float(f"{x:.4g}")
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_clean(v) for v in x]
    return x


STUDIES = ("gidney_cultivation", "rp2_ungrown", "gauging_cultivation", "vaknin_full_vector", "chan_flags", "fold_transversal",
           "erasure_injection", "star_injection", "google_experiment")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)
    slides = (gidney() + [rp2_table(), gauging_table(), gauging_fig4a(), vaknin()] + chan() + [fold(), erasure()] + star() + google())
    builds = sorted({r["tsim"]["commit"][:8] for st in STUDIES for r in common.load_results(st).values() if r.get("tsim")})
    data = dict(source="https://github.com/rafaelha/tsim-bench/tree/master/repro", tsim_builds=builds, slides=slides)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_clean(data), indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {out} ({len(slides)} slides)")


if __name__ == "__main__":
    main()

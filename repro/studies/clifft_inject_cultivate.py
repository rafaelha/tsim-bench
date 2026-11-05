r"""Chase, Labib (2026), Clifft, arXiv:2604.27058 -- Fig. 6: inject + cultivate, $T$ vs. $S$ proxy, $d=3$ and $d=5$.

Clifft's Fig. 6 plots the logical error rate per kept shot of Gidney's unitary-injection
cultivation circuits (no escape) with real $T$ gates and with the $S$ proxy against the expected
attempts per kept shot, with the $T/S$ ratio below; its Table 2 lists the $d=5$ $T$-gate values at
three noise strengths (stratified importance sampling, $9.6\times10^{10}$ shots, 12 machine-hours on a
16-core c6i.8xlarge).

Clifft's circuits are the Clifft paper's converter applied to Gidney's generator, the same as the
Gidney study's (byte-identical at $p=10^{-3}$), so this study samples nothing itself: it re-plots the
Gidney study's unitary-injection points. The figures are drawn with the plotting code of the Clifft
paper (unitaryfoundation/clifft-paper at db7dc9f, ``magic_state_cultivation/plot_results.py``:
``_plot_ic_single`` and ``_compute_ic_ratio``, Apache-2.0), fed with our points instead of their
importance-sampling strata; their published values (``results/inject_cultivate/analysis.json``)
are overlaid.
"""

import json

from repro import common, data_sources

STUDY = "clifft_inject_cultivate"
META = dict(arxiv="2604.27058", paper="Chase, Labib (2026), Clifft: fast exact simulation of near-Clifford quantum circuits")
TABLE2 = {5e-4: 1.56e-10, 1e-3: 2.67e-9, 2e-3: 5.78e-8}
# From plot_results.py: SOFT Table III, (noise, total_shots, preserved_shots, error_rate).
_SOFT_IC_D5 = [(0.0005, 134.4e9, 50.9e9, 1.57e-10), (0.001, 74.0e9, 10.6e9, 4.59e-9), (0.002, 28.9e9, 0.60e9, 3.41e-8)]
N_BOOTSTRAP = 100_000


def circuits():
    return {}


def points():
    return []


def _compute_ic_ratio(t_stats, s_stats, rng):
    """Verbatim from clifft-paper plot_results.py: bootstrap the T/S error-rate ratio."""
    import numpy as np

    t_by_p = {s.json_metadata["p"]: s for s in t_stats}
    s_by_p = {s.json_metadata["p"]: s for s in s_stats}
    shared_ps = sorted(set(t_by_p) & set(s_by_p))
    xs_apk, medians, lows, highs, err_mins, ps_out = [], [], [], [], [], []
    for p in shared_ps:
        t = t_by_p[p]
        s = s_by_p[p]
        t_kept = t.shots - t.discards
        s_kept = s.shots - s.discards
        if t_kept < 10 or s_kept < 10:
            continue
        samples_t = rng.beta(t.errors + 0.5, t_kept - t.errors + 0.5, size=N_BOOTSTRAP)
        samples_s = rng.beta(s.errors + 0.5, s_kept - s.errors + 0.5, size=N_BOOTSTRAP)
        ratio = samples_t / samples_s
        xs_apk.append((t.shots + 1) / (t_kept + 2))
        medians.append(float(np.median(ratio)))
        lo, hi = np.percentile(ratio, [2.5, 97.5])
        lows.append(float(lo))
        highs.append(float(hi))
        err_mins.append(min(t.errors, s.errors))
        ps_out.append(p)
    if not xs_apk:
        return None
    order = np.argsort(xs_apk)
    return {"xs_apk": np.array(xs_apk)[order], "ps": [ps_out[i] for i in order], "medians": np.array(medians)[order],
            "lows": np.array(lows)[order], "highs": np.array(highs)[order], "err_mins": np.array(err_mins)[order]}


def _plot_ic_single(t_stats, s_stats, dcolor, output_path, published=None):
    """clifft-paper plot_results._plot_ic_single, with stats passed in and the paper's values overlaid."""
    import matplotlib.pyplot as plt
    import numpy as np
    import sinter

    all_stats = t_stats + s_stats
    ratio_data = _compute_ic_ratio(t_stats, s_stats, rng=np.random.default_rng(42)) if t_stats and s_stats else None
    if ratio_data is not None:
        fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [3, 1.5]}, sharex=True)
    else:
        fig, ax_top = plt.subplots(figsize=(10, 7))
        ax_bot = None
    _GATE_COLOR = {"T": "tab:blue", "S": "tab:orange"}
    _GATE_LABEL = {"T": "T-Gate (Tsim GPU)", "S": "S-Proxy (Tsim GPU)"}

    def _x_func(stat):
        return (stat.shots + 1) / (stat.shots - stat.discards + 2)

    if all_stats:
        sinter.plot_error_rate(
            ax=ax_top, stats=all_stats, x_func=_x_func,
            group_func=lambda stat: f"gate={stat.json_metadata['gate']}",
            plot_args_func=lambda idx, group_key, group_stats: {
                "color": _GATE_COLOR.get(group_stats[0].json_metadata["gate"], "gray"), "linestyle": "-", "marker": "o",
                "label": _GATE_LABEL.get(group_stats[0].json_metadata["gate"], group_stats[0].json_metadata["gate"])},
            highlight_max_likelihood_factor=1000)
    # The Clifft paper's own values (analysis.json), same colors, open markers, dashed.
    for key, gate in (("t_gate", "T"), ("s_proxy", "S")):
        rows = (published or {}).get(f"{key}_d{dcolor}")
        if rows:
            ax_top.errorbar([r["attempts_per_kept"] for r in rows], [r["error_rate"] for r in rows],
                            yerr=[r["std_error"] for r in rows], color=_GATE_COLOR[gate], ls="--", marker="o", mfc="white",
                            ms=5, lw=0.9, capsize=2, label=f"{'T-Gate' if gate == 'T' else 'S-Proxy'} (Clifft paper)")
    if dcolor == 5:
        from repro.studies import soft_d5

        ex = soft_d5.exact_grid()
        ax_top.plot([1 / a for _, a, _ in ex], [pl for _, _, pl in ex], "x", color="C2", ms=8, mew=1.8, zorder=6,
                    label="exact (Wan, Zapirain)")
        soft_x = [total / kept for _, total, kept, _ in _SOFT_IC_D5]
        soft_y = [rate for _, _, _, rate in _SOFT_IC_D5]
        ax_top.scatter(soft_x, soft_y, marker="*", s=140, facecolors="none", edgecolors="black", linewidths=1.2, zorder=5,
                       label="SOFT (Li et al.)")
    ax_top.set_xscale("log")
    ax_top.set_yscale("log")
    ax_top.set_ylabel("Logical Error Rate (per Kept Shot)")
    ax_top.grid(True, which="major", axis="y", linewidth=0.8, alpha=0.5, color="gray")
    ax_top.grid(True, which="minor", axis="y", linewidth=0.5, alpha=0.4, color="gray")
    ax_top.grid(True, which="major", axis="x", linewidth=0.5, alpha=0.3, color="gray")
    t_by_p = {s.json_metadata["p"]: s for s in t_stats}
    s_by_p = {s.json_metadata["p"]: s for s in s_stats}
    for p in sorted(set(t_by_p) | set(s_by_p)):
        anchor_stat = t_by_p.get(p, s_by_p.get(p))
        kept = max(1, anchor_stat.shots - anchor_stat.discards)
        ax_top.annotate(f"p={p}", xy=(_x_func(anchor_stat), (anchor_stat.errors + 0.5) / (kept + 1)), xytext=(8, 0),
                        textcoords="offset points", va="center", fontsize=9)
    handles, labels = ax_top.get_legend_handles_labels()
    seen, dedup = set(), []
    for h, l in zip(handles, labels):
        if l not in seen:
            seen.add(l)
            dedup.append((h, l))
    ax_top.legend([h for h, _ in dedup], [l for _, l in dedup], loc="upper left", fontsize=10)
    if ax_bot is not None and ratio_data is not None:
        xs, m, lo, hi = ratio_data["xs_apk"], ratio_data["medians"], ratio_data["lows"], ratio_data["highs"]
        SHADE = "0.3"
        ax_bot.plot(xs, m, "o-", color=SHADE, markersize=4, label="Tsim GPU")
        ax_bot.fill_between(xs, lo, hi, color=SHADE, alpha=0.2, linewidth=0)
        if published and f"t_gate_d{dcolor}" in published:
            tp = {r["p"]: r for r in published[f"t_gate_d{dcolor}"]}
            sp = {r["p"]: r for r in published[f"s_proxy_d{dcolor}"]}
            ps = sorted(set(tp) & set(sp))
            ax_bot.plot([tp[p]["attempts_per_kept"] for p in ps], [tp[p]["error_rate"] / sp[p]["error_rate"] for p in ps], "o--",
                        color=SHADE, mfc="white", markersize=4, lw=0.9, label="Clifft paper")
            ax_bot.legend(fontsize=8)
        ax_bot.set_xscale("log")
        ax_bot.set_xlabel("Expected Attempts per Kept Shot")
        ax_bot.set_ylabel("Error Ratio (T / S)")
        ax_bot.grid(True, which="major", linewidth=0.8, alpha=0.5, color="black")
        ax_bot.grid(True, which="minor", linewidth=0.4, alpha=0.2, color="black")
    else:
        ax_top.set_xlabel("Expected Attempts per Kept Shot")
    _, xmax = ax_top.get_xlim()
    ax_top.set_xlim(right=xmax * 1.6)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def figures(results):
    from repro import plotting

    g = common.load_results("gidney_cultivation")
    published = json.loads(data_sources.data_file("clifft_paper_inject_cultivate_analysis.json").read_text())
    out = common.REPORT / "figures" / STUDY
    figs = []
    for d in (3, 5):
        t_stats, s_stats, used = [], [], []
        for k, r in g.items():
            pr = r["params"]
            if pr["d"] != d or pr["style"] != "unitary" or pr["gate"] not in ("t", "s"):
                continue
            st = plotting.sinter_stats(r["totals"], "tsimGPU", {"d1": d, "p": pr["p"], "gate": pr["gate"].upper(), "r1": d})
            (t_stats if pr["gate"] == "t" else s_stats).append(st)
            used.append(k)
        path = _plot_ic_single(t_stats, s_stats, d, out / f"ic_comparison_d{d}.png", published)
        figs.append(common.Figure(
            f"clifft6_d{d}", path, f"Clifft Fig. 6({'a' if d == 3 else 'b'}): inject + cultivate, $d={d}$ colour code, $T$ vs.\\ $S$ proxy",
            "Drawn with the Clifft paper's own plotting code (\\texttt{plot\\_results.py}) on the Gidney study's samples (filled, solid; "
            "shaded: 1000x likelihood). Open markers, dashed: the Clifft paper's published importance-sampling values "
            "(\\texttt{analysis.json}" + (", $d=5$ only)" if d == 5 else "; $d=3$ values are not in it)") +
            (". Stars: SOFT." if d == 5 else ".") + " Bottom: $T/S$ ratio, median and 95\\% credible interval (bootstrap, as in the paper)." +
            (" Crosses: exact $T$-gate values of Wan and Zapirain (arXiv:2609.18922); our direct samples agree with them, "
             "while the paper's importance-sampling values at $p\\le10^{-3}$ lie 2--3$\\sigma$ below." if d == 5 else ""),
            common.budget_line(g, used, label="(Gidney study points)")))
    return figs


def checks(results):
    from repro.studies import gidney_cultivation as gc

    g = common.load_results("gidney_cultivation")
    published = json.loads(data_sources.data_file("clifft_paper_inject_cultivate_analysis.json").read_text())
    sigma = {row["p"]: row["std_error"] for row in published.get("t_gate_d5", [])}
    rows = []
    for p, v in TABLE2.items():
        r = g.get(gc.cname(5, "unitary", p, "t"))
        if r:
            rows.append(common.check_row(f"d=5 p={p:g} T (Clifft Table 2, importance sampling)", "t",
                                         dict(value=v, sigma=sigma.get(p, float("nan"))), r["totals"]))
    # The exact values (Wan, Zapirain, arXiv:2609.18922) for the same circuits: the reference the sampled values should hit.
    from repro.studies import soft_d5

    for p, _, pl in soft_d5.exact_grid():
        r = g.get(gc.cname(5, "unitary", p, "t"))
        if r:
            rows.append(common.check_row(f"d=5 p={p:g} T (exact, 2609.18922)", "t", dict(value=pl, sigma=0.0), r["totals"]))
    return [x for x in rows if x]

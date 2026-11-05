r"""Small plotting helpers shared by the study figures (matplotlib, project environment)."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from repro import common  # noqa: E402

plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "legend.fontsize": 6.5, "figure.dpi": 150,
                     "savefig.bbox": "tight", "axes.grid": True, "grid.alpha": 0.25})


def _ler(t):
    return common.binomial_interval(t["errors"], t["kept"])


def ler_points(ax, series, color, label=None, ls="-", marker="o", x=lambda p: p):
    """series: list of (x, totals). Max-likelihood LER with a 1000x likelihood band; zero-error points as upper bounds."""
    xs, ys, lo, hi = [], [], [], []
    ub_x, ub_y = [], []
    for p, t in series:
        if t["kept"] == 0:
            continue
        best, low, high = _ler(t)
        if t["errors"] == 0:
            ub_x.append(x(p))
            ub_y.append(high)
            continue
        xs.append(x(p))
        ys.append(best)
        lo.append(low)
        hi.append(high)
    if xs:
        ax.plot(xs, ys, ls=ls, marker=marker, color=color, ms=3.5, lw=1, label=label)
        ax.fill_between(xs, lo, hi, color=color, alpha=0.18, lw=0)
    if ub_x:
        ax.plot(ub_x, ub_y, ls="none", marker="v", color=color, ms=4, label=None if xs else label)


def accept_points(ax, series, color, label=None, ls="-", marker="o", x=lambda p: p):
    xs = [x(p) for p, t in series if t["shots"]]
    ys = [t["kept"] / t["shots"] for p, t in series if t["shots"]]
    if xs:
        ax.plot(xs, ys, ls=ls, marker=marker, color=color, ms=3.5, lw=1, label=label)


def published_ler(ax, rows, color, label=None, x="p"):
    xs, ys, lo, hi = [], [], [], []
    for r in sorted(rows, key=lambda r: r[x]):
        if r["kept"] <= 0 or r["errors"] <= 0:
            continue
        best, low, high = common.binomial_interval(r["errors"], r["kept"])
        xs.append(r[x])
        ys.append(best)
        lo.append(best - low)
        hi.append(high - best)
    if xs:
        ax.errorbar(xs, ys, yerr=[lo, hi], ls="none", marker="D", mfc="white", mec=color, ecolor=color, ms=4.5, mew=1,
                    capsize=1.5, elinewidth=0.7, label=label, zorder=5)


def published_accept(ax, rows, color, x="p"):
    xs = [r[x] for r in sorted(rows, key=lambda r: r[x]) if r["shots"]]
    ys = [r["kept"] / r["shots"] for r in sorted(rows, key=lambda r: r[x]) if r["shots"]]
    if xs:
        ax.plot(xs, ys, ls="none", marker="D", mfc="white", mec=color, ms=4.5, mew=1, zorder=5)


def published_value(ax, x, y, color, label=None, yerr=None):
    ax.errorbar([x], [y], yerr=None if yerr is None else [[yerr[0]], [yerr[1]]], ls="none", marker="D", mfc="white",
                mec=color, ecolor=color, ms=4.5, mew=1, capsize=1.5, label=label, zorder=5)


def style_ler(ax, xlabel, logx=True):
    ax.set_yscale("log")
    if logx:
        ax.set_xscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("logical error rate per kept shot")


def style_accept(ax, xlabel, logx=True, log=False):
    if logx:
        ax.set_xscale("log")
    if log:
        ax.set_yscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("acceptance rate")


def save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path


def no_data(ax):
    ax.text(0.5, 0.5, "not yet sampled", transform=ax.transAxes, ha="center", va="center", color="0.5")


__all__ = ["ler_points", "accept_points", "published_ler", "published_accept", "published_value", "style_ler",
           "style_accept", "save", "np", "plt"]


# ---------------------------------------------------------------------------------------------
# sinter-based figures: export our results as sinter stats and run the authors' own `sinter plot`
# commands on them (plus the authors' published stats where released).


def sinter_stats(totals, decoder, metadata):
    """Our point totals -> a sinter.TaskStats (discards = shots - kept)."""
    import hashlib
    import json

    import sinter

    sid = hashlib.sha256(json.dumps([decoder, metadata], sort_keys=True).encode()).hexdigest()
    return sinter.TaskStats(strong_id=sid, decoder=decoder, json_metadata=metadata, shots=int(totals["shots"]),
                            errors=int(totals["errors"]), discards=int(totals["shots"] - totals["kept"]),
                            seconds=float(totals["seconds"]))


def write_sinter_csv(path, stats, extra_lines=()):
    import sinter

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        print(sinter.CSV_HEADER, file=f)
        for line in extra_lines:
            print(line.rstrip("\n"), file=f)
        for s in stats:
            print(s.to_csv_line(), file=f)
    return path


def sinter_plot(args, cwd=None, pythonpath=()):
    """Run ``sinter plot`` (the CLI the authors used) with the given argument list."""
    import os
    import subprocess
    import sys

    env = dict(os.environ)
    if pythonpath:
        env["PYTHONPATH"] = os.pathsep.join([*map(str, pythonpath), env.get("PYTHONPATH", "")])
    # Exactly how the authors call it (tools/sinter_plot_echo.py): sinter's CLI main with 'plot'.
    code = "import sys; from sinter._command._main import main; main(command_line_args=['plot', *sys.argv[1:]])"
    p = subprocess.run([sys.executable, "-c", code, *map(str, args)], cwd=cwd, env=env, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"sinter plot failed:\n{p.stderr[-3000:]}")

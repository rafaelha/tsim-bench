# %% [markdown]
# # Compare the spacetime volume of different MSI


# %%
def gidney_spacetime(d1: int, r1: int, d2: int, r2: int, r_discard: float, round_depth: int = 4) -> float:
    """
    Calculate the spacetime volume of a given code.
    """
    nq1 = 2 * d1 * d1
    V1 = nq1 * r1 * round_depth
    nq2 = 2 * d2 * d2
    V2 = nq2 * r2 * round_depth
    return V1 / (1 - r_discard) + V2


def gidney_pregrown_spacetime(d1: int, r1: int, d2: int, r2: int, r_discard: float, round_depth: int = 4) -> float:
    """
    Calculate the spacetime volume of a given code.
    """
    nq1 = 2 * d2 * d2
    V1 = nq1 * r1 * round_depth
    nq2 = 2 * d2 * d2
    V2 = nq2 * r2 * round_depth
    return V1 / (1 - r_discard) + V2


def bb_spacetime(r1: int, n1: int, r2: int, r_discard: float, round_depth: int = 7) -> float:
    """
    Calculate the spacetime volume of a given code.
    """
    r = r1 + r2
    nq = 2 * n1
    V1 = nq * r * round_depth
    return V1 / (1 - r_discard)


n_bb = 144
n_inj = 4
d2 = 11

st_gidney = gidney_spacetime(5, 2, d2, 1, 0.33)
# st_gidney_pregrown = gidney_pregrown_spacetime(5, 2, d2, 1, 0.33)
st_our = bb_spacetime(2, 144, 1, 0.9)
print(n_inj * st_gidney, st_our)


# %%
def block_LER(
    LER_one: float,
    N: int,
) -> float:
    return 1 - (1 - LER_one) ** N


print(block_LER(0.001, 4))

import math

# %%
from dataclasses import dataclass

import pandas as pd


@dataclass
class _VisDat:
    ps: list[float]
    p_injs: list[float]
    r_discs: list[float]
    params: dict[str, int]


def to_float(x: float, bit: int = 2) -> str:
    return f"{x:.{bit}f}"


def to_e(x: float, bit: int = 2) -> str:
    return f"{x:.{bit}e}"


labels = [
    r"$p$",
    r"Surf., $p_{\{1\}}$",
    r"BB, $p_{\mathcal{I}}/|\mathcal{I}|$",
    r"Surf., $r_{\rm disc}$",
    r"BB, $r_{\rm disc}$",
    r"Surf., $|\mathcal{I}|\cdot V^{\rm surf}$",
    r"BB, $V^{\rm BB}$",
]
ps = [0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.001]
surf_dat = _VisDat(
    ps=ps,
    p_injs=[
        5.2870510672758204e-05,
        0.00012024166978488834,
        0.00017610933700473586,
        0.000328367149972821,
        0.0004822204924724242,
        0.0008440044717151315,
    ],
    r_discs=[
        0.039727199159157185,
        0.07792249595695384,
        0.11462724251756777,
        0.18356866616550888,
        0.24669213065507378,
        0.33396685889249367,
    ],
    params={"d1": 5, "d2": 11, "r1": 2, "r2": 1},
)

bb_dat = _VisDat(
    ps=ps,
    p_injs=[
        0.0001510113840356779,
        0.00031029884428639815,
        0.00045575074577394763,
        0.0008026281048027582,
        0.0011306154992353642,
        0.0017126301892328004,
    ],
    r_discs=[0.23515700000000006, 0.41508, 0.553484, 0.738671, 0.846986, 0.93183],
    params={"n1": 144, "r1": 2, "r2": 1, "n_inj": 4},
)

bb_spacetimes = [
    bb_spacetime(bb_dat.params["r1"], bb_dat.params["n1"], bb_dat.params["r2"], r_discard)
    for r_discard in bb_dat.r_discs
]
surf_spacetimes = [
    bb_dat.params["n_inj"]
    * gidney_spacetime(
        surf_dat.params["d1"], surf_dat.params["r1"], surf_dat.params["d2"], surf_dat.params["r2"], r_discard
    )
    for r_discard in surf_dat.r_discs
]

rows = []


def to_aps_sci(x: float, sig: int = 2) -> str:
    """
    Format x as LaTeX scientific notation: m \\times 10^{e}
    with 'sig' significant digits in m. Returns '0' for x=0.
    """
    if x == 0 or (isinstance(x, float) and math.isfinite(x) and abs(x) == 0):
        return "0"
    if not math.isfinite(x):
        return r"\infty" if x > 0 else r"-\infty" if x < 0 else r"\mathrm{NaN}"

    sign = "-" if x < 0 else ""
    ax = abs(x)

    e = int(math.floor(math.log10(ax)))
    m = ax / (10**e)

    # round mantissa to 'sig' significant digits
    m_str = f"{m:.{sig-1}f}".rstrip("0").rstrip(".")

    # handle rare case: rounding makes mantissa 10.0
    if float(m_str) >= 10:
        m_str = f"{float(m_str)/10:.{sig-1}f}".rstrip("0").rstrip(".")
        e += 1

    if e == 0:
        return f"{sign}{m_str}"
    if m_str == "1":
        return f"{sign}10^{{{e}}}"
    return f"{sign}{m_str} \\times 10^{{{e}}}"


lists = [ps, surf_dat.p_injs, bb_dat.p_injs, surf_dat.r_discs, bb_dat.r_discs, surf_spacetimes, bb_spacetimes]
formatters = [
    lambda x: to_aps_sci(x, 1),
    to_aps_sci,
    to_aps_sci,
    to_float,
    to_float,
    lambda x: to_float(x, 0),
    lambda x: to_float(x, 0),
]
for lst, formatter in zip(lists, formatters):
    if formatter is None:
        rows.append(lst)
    else:
        rows.append([f"${formatter(v)}$" for v in lst])

df = pd.DataFrame(rows)
df.insert(0, "label", labels)

ss = "\\toprule\n"
for row_idx, row in df.iterrows():
    if row_idx % 2 == 1:
        ss += "\\midrule" + "\n"
    ss += " & ".join(row) + " \\\\"
    ss += "\n"

ss += r"Surf., #Qubits & \multicolumn{6}{c}{placeholder} \\" + "\n"
ss += r"BB, #Qubits & \multicolumn{6}{c}{placeholder} \\" + "\n"


ss += "\\bottomrule\n"
# table_latex = df.to_latex(index=False, escape=False, header=False)
# print(table_latex)

print(ss)


# %%
from matplotlib import pyplot as plt

params = {
    "legend.fontsize": 15,
    #   'figure.figsize': (8, 5),
    "axes.labelsize": 18,  # 'x-large',
    "axes.titlesize": 20,  # 'x-large',
    "xtick.labelsize": 16,
    "ytick.labelsize": 18,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}
plt.rcParams.update(params)
fig, axs = plt.subplots(1, 3, figsize=(15, 4))


# vis error rate
def _plot_error_rate(ax: plt.Axes):
    ax.plot(ps, surf_dat.p_injs, label="Surf.")
    ax.plot(ps, bb_dat.p_injs, label="BB")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$p$")
    ax.set_ylabel(r"Injection error rate/qubit")
    ax.legend()


# plot discard rate
def _plot_discard_rate(ax: plt.Axes):
    ax.plot(ps, surf_dat.r_discs, label="Surf.")
    ax.plot(ps, bb_dat.r_discs, label="BB")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$p$")
    ax.set_ylabel("Discard rate")
    ax.legend()


# vis spacetime volume
def _plot_spacetime_volume(ax: plt.Axes):
    ax.plot(surf_dat.ps, surf_spacetimes, label="Surf.")
    ax.plot(bb_dat.ps, bb_spacetimes, label="BB")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$p$")
    ax.set_ylabel("Spacetime volume")
    ax.legend()


_plot_error_rate(axs[0])
_plot_discard_rate(axs[1])
_plot_spacetime_volume(axs[2])

plt.tight_layout()
plt.show()


# %%


# %%

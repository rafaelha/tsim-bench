# %%

from typing import Any

import numpy as np
from tqdm import tqdm

from qldpc_msi import tour_bb
from qldpc_msi.data_mgr import InitCfgMgrV2

# %%

SAVE_FIG = False

remove_dummy_cnots = False
c_tol_per_q_lst = []
n_fixed_stabs = []
cfg_mgr = InitCfgMgrV2()
noise_model = "li_uniform"
code = tour_bb.make_code(n=144)

print(f"{code.identifier=}")

# %%
for cfg_id in tqdm(range(627)):
    dat1: dict[str, Any] = cfg_mgr.load(
        code_id=code.identifier,
        noise_model=noise_model,
        init_method="max_fixed_stabs",
        _id=cfg_id,
        remove_dummy_cnots=remove_dummy_cnots,
    )
    dat2: dict[str, Any] = cfg_mgr.load(
        code_id=code.identifier,
        noise_model=noise_model,
        init_method="max_supp_protection",
        _id=cfg_id,
        remove_dummy_cnots=remove_dummy_cnots,
    )

    # make sure they are the same config
    assert dat1["init_cfg"].inj_lids == dat2["init_cfg"].inj_lids
    assert dat1["init_cfg"].inj_uids == dat2["init_cfg"].inj_uids
    assert dat1["init_cfg"].ghz_uids_lst == dat2["init_cfg"].ghz_uids_lst

    # c_tol_per_q_lst.append(dat1["perf"]["c_tol_per_q"] - dat2["perf"]["c_tol_per_q"])
    c_tol_per_q_lst.append(dat1["perf"]["c_tol"] - dat2["perf"]["c_tol"])
    n_fixed_stabs.append(dat1["init_cfg"].n_fixed_stabs - dat2["init_cfg"].n_fixed_stabs)


# %%
c_tol_per_q_lst_arr = np.array(c_tol_per_q_lst)
n_fixed_stabs_arr = np.array(n_fixed_stabs)

print(c_tol_per_q_lst_arr[:5])
print(n_fixed_stabs_arr[:5])
print(len(c_tol_per_q_lst_arr > 0))
print(len(n_fixed_stabs_arr > 0))

print(max(c_tol_per_q_lst_arr))
print(min(c_tol_per_q_lst_arr))
print(max(n_fixed_stabs_arr))
print(min(n_fixed_stabs_arr))

import matplotlib.ticker as ticker
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

fig, axs = plt.subplots(1, 2, figsize=(10, 4))
axs[0].hist(c_tol_per_q_lst_arr, bins=100)
axs[0].set_ylabel("Count")
# axs[0].set_xticklabels()


# Define the formatting function
def currency_formatter(x, pos):
    """Formats the tick values as currency with a '$' sign."""
    if x >= 0:
        return f"${x:1.2f}"
    return f"-${abs(x):1.2f}"


def unit_formatter(x, pos):
    """Formats the tick values with a 'cm' unit."""
    return rf"{x:.0f}$p$"


# Apply the formatter to the y-axis (currency)
# ax.yaxis.set_major_formatter(ticker.FuncFormatter(currency_formatter))

# Apply the formatter to the x-axis (unit)
axs[0].xaxis.set_major_formatter(ticker.FuncFormatter(unit_formatter))
# axs[0].set_xlabel(r"Coeff reduction, $\Delta c$ ($p_L = c\cdot p$)")
# axs[0].set_xlabel(r"Total injection error rate reduction" + "\n" + r"$\Delta c,\text{ where } p^{\rm tot}_{\mathcal{{I}}} = c\cdot p$")
axs[0].set_xlabel(r"Total injection error rate reduction" + "\n" + r"$\Delta p^{\rm tot}_{\mathcal{{I}}}$")
axs[1].hist(n_fixed_stabs_arr, bins=100)
axs[1].set_ylabel("Count")
axs[1].set_xlabel("#Fixed stabs reduction")
plt.tight_layout()
if SAVE_FIG:
    plt.savefig("../../../qldpc-msi-paper/figs/cmp_fixing_methods.pdf", bbox_inches="tight", dpi=300)
plt.show()


# %%


# %%

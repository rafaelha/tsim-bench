# %% [markdown]
# # Learn detector error model
#
# How to directly count error mechanisms that can flip the logical operators without triggering specific detectors?
# - 1Q error
# - 2Q error
#
#

import matplotlib.pyplot as plt

# %%
import numpy as np
from matplotlib import transforms

from qldpc_msi import tour_bb
from qldpc_msi.data_mgr import InitCfgMgrV2
from qldpc_msi.msi.init_cfgs import InitCfg
from qldpc_msi.noise_spec import LiMsiNoiseSpec

# Source - https://stackoverflow.com/a/79822386
# Posted by koarla, modified by community. See post 'Timeline' for change history
# Retrieved 2026-03-07, License - CC BY-SA 4.0


def partial_circle(x_center, y_center, radius_x, radius_y, start_deg, end_deg, n=100):
    t = np.linspace(start_deg / 180 * np.pi, end_deg / 180 * np.pi, n)
    return x_center + radius_x * np.cos(t), y_center + radius_y * np.sin(t)


def underbrace(
    ax,
    x_start,
    x_end,  # horizontal position in data coords
    y=-0.15,  # vertical position in axes coords (0 = bottom, 1 = top)
    label=None,
    radius_y=0.02,  # vertical radius in axes coords
    radius_x=0.1,  # horizontal radius in data coords
    lw=1.0,
    color="black",
    text_offset=-0.04,  # extra offset for the label in axes coords
    **text_kwargs,
):

    # x in data coords, y in axes coords
    trans = transforms.blended_transform_factory(ax.transData, ax.transAxes)

    x_mid = 0.5 * (x_start + x_end)

    y_top = y + radius_y
    y_mid = y
    y_bottom = y - radius_y

    # left brace
    X_circ_left, Y_circ_left = partial_circle(x_start + radius_x, y_top, radius_x, radius_y, 180, 270)
    X_line_left = np.linspace(x_start + radius_x, x_mid - radius_x)
    Y_line_left = np.full_like(X_line_left, y_mid)
    # middle kink
    X_circ_mid_left, Y_circ_mid_left = partial_circle(x_mid - radius_x, y_bottom, radius_x, radius_y, 90, 0)
    X_circ_mid_right, Y_circ_mid_right = partial_circle(x_mid + radius_x, y_bottom, radius_x, radius_y, 180, 90)
    # right brace
    X_line_right = np.linspace(x_mid + radius_x, x_end - radius_x)
    Y_line_right = np.full_like(X_line_right, y_mid)
    X_circ_right, Y_circ_right = partial_circle(x_end - radius_x, y_top, radius_x, radius_y, 270, 360)

    Xs = np.concatenate([X_circ_left, X_line_left, X_circ_mid_left, X_circ_mid_right, X_line_right, X_circ_right])
    Ys = np.concatenate([Y_circ_left, Y_line_left, Y_circ_mid_left, Y_circ_mid_right, Y_line_right, Y_circ_right])

    ax.plot(Xs, Ys, color=color, lw=lw, transform=trans, clip_on=False)

    if label is not None:
        ax.text(x_mid, y + text_offset, label, ha="center", va="top", transform=trans, color=color, **text_kwargs)


code = tour_bb.make_code(n=144)
p = 0.001

init_method = "max_supp_protection"
noise_model_name = "li_uniform"
remove_dummy_cnots = False
init_cfg_id = 491
init_dat = InitCfgMgrV2().load(
    code_id=code.identifier,
    noise_model=noise_model_name,
    init_method=init_method,
    _id=init_cfg_id,
    remove_dummy_cnots=remove_dummy_cnots,
)
init_cfg = init_dat["init_cfg"]
print(init_cfg.inj_lids)
assert isinstance(init_cfg, InitCfg)
logical_basis = "Y"
n_se_cycles = 2
n_psel_cycles = 2

print(init_cfg.inj_uids)
print(init_cfg.dat_uids_init_in_x)
print(init_cfg.dat_uids_init_in_z)

# aut = tour_bb.get_bb_aut(code)
# lxs = aut.get_logical_qubits("X")
# lzs = aut.get_logical_qubits("Z")
# lxs = [np.array(lx.to_vec(), dtype=np.int_) for lx in lxs]
# lzs = [np.array(lz.to_vec(), dtype=np.int_) for lz in lzs]
# for i in init_cfg.inj_lids:
#     print(f"{i=}, lx={lxs[i].nonzero()[0].tolist()}, lz={lzs[i].nonzero()[0].tolist()}")

print(p)


# %%


msi_circ = tour_bb.build_msi_circuit(code, init_cfg=init_cfg, n_cycles=2, remove_dummy_cnots=remove_dummy_cnots)
if noise_model_name == "li_uniform":
    noise_spec = LiMsiNoiseSpec.li_msi_uniform(p)
elif noise_model_name == "li_twoq_dominant":
    noise_spec = LiMsiNoiseSpec.li_msi_twoq_dominant(p, 0.1)
else:
    raise ValueError(f"Invalid noise model: {noise_model_name}")

ana_LER_breakdown = noise_spec.analytical_1st_order_LER_breakdown(
    lambda: msi_circ,
    init_cfg.inj_lids,
)


# %%


for k, v in ana_LER_breakdown.items():
    print(k, v)


import pickle

# %%
import sinter

with open(f"./stats-{logical_basis}-{init_method}-{init_cfg_id}-w_idle.pkl", "rb") as f:
    data_stats = pickle.load(f)

for stat in data_stats:
    print(stat)
    ler_tot = stat.errors / (stat.shots - stat.discards)
    print(f"{ler_tot=:.4f}")


def mask_to_tuple(mask: str) -> tuple[int]:
    tu = []
    for i, ch in enumerate(mask):
        if ch == "E":
            tu.append(i)
    return tuple(tu)


def count_corr_errs_from_custom_counts(stat: sinter.TaskStats) -> dict[tuple[int], float]:
    custom_counts = getattr(stat, "custom_counts", {})
    # print(custom_counts)
    masks = {
        mask_to_tuple(k.split("=", 1)[1]): v for k, v in custom_counts.items() if k.startswith("obs_mistake_mask=")
    }
    LER_breakdown = {k: v / (stat.shots - stat.discards) for k, v in masks.items()}
    return LER_breakdown  # (list, dict)


p = 1e-3
J_to_c_tol: dict[tuple[int], float] = {}
stat = data_stats[0]
LER_breakdown_exp = count_corr_errs_from_custom_counts(stat)
# print(LER_breakdown)
# thresh = 1e-5
# print(f"thresh={thresh}")
p_all_obs = sum(LER_breakdown_exp.values())
print(f"{p_all_obs=:.4f}")
for k, v in sorted(LER_breakdown_exp.items(), key=lambda x: (len(x[0]), x[0])):
    # if v < thresh:
    #     continue
    coeff = v / p
    print(k, f"{coeff=:.3f}")
    J_to_c_tol[k] = coeff


# %%
from matplotlib import pyplot as plt
from matplotlib.axes import Axes


def rel_J_to_abs_J(J: tuple[int, ...]) -> tuple[int, ...]:
    rel_lid_to_abs_lid = {0: 4, 1: 5, 2: 7, 3: 10}
    return tuple(sorted(rel_lid_to_abs_lid[lid] for lid in J))


def _vis_LER_breakdown(
    ax: Axes,
    ana_breakdown: dict[tuple[int, ...], dict[str, float]],
    exp_J_to_LER: dict[tuple[int, ...], float],
    p: float,
    c_types: list[str] | None = None,
    c_type_labels: list[str] | None = None,
):
    """Use double bar chart to visualize the LER breakdown.
    Left bar: experimental LER.
    Right bar: analytical LER breakdown. Multiple layers of bars.
    """
    all_Js = sorted(list(set(ana_breakdown.keys()) | set(exp_J_to_LER.keys())), key=lambda x: (len(x), x))

    n_inj = sum(1 for J in all_Js if len(J) == 1)

    y_exp = [exp_J_to_LER[J] if J in exp_J_to_LER else 0 for J in all_Js]
    c_types = c_types or list(ana_breakdown[all_Js[0]].keys())
    y_ana_lst = [
        np.array([ana_breakdown[J][c_type] if J in ana_breakdown else 0 for J in all_Js]) * p for c_type in c_types
    ]
    xs = np.arange(len(all_Js))
    bar_width = 0.2
    xtick_labels = []
    for J_idx, J in enumerate(all_Js):
        J_abs = rel_J_to_abs_J(J)
        J_str = f"$\\mathcal{{J}}={J_abs}$" if J_idx == 0 else f"${J_abs}$"
        xtick_labels.append(J_str)
    ax.bar(xs - bar_width / 2, y_exp, bar_width, label=f"Circuit-level sim., ${p=:.3f}$")
    ys_bottom = np.zeros(len(xs))
    c_type_labels = c_type_labels or c_types
    for c_type, c_label, ys in zip(c_types, c_type_labels, y_ana_lst):
        ax.bar(xs + bar_width / 2, ys, bottom=ys_bottom, width=bar_width, label=c_label)
        ys_bottom += ys
    underbrace(ax, xs[0], xs[n_inj - 1], label="independent errors", color="green", y=-0.4, fontsize=14)
    underbrace(ax, xs[n_inj], xs[-1], label="correlated errors", color="red", y=-0.4, fontsize=14)

    ax.set_xticks(xs)
    ax.set_xticklabels(xtick_labels, rotation=45, ha="right", rotation_mode="anchor")


params = {
    "legend.fontsize": 14,
    #   'figure.figsize': (8, 5),
    "axes.labelsize": 18,  # 'x-large',
    "axes.titlesize": 20,  # 'x-large',
    "xtick.labelsize": 16,
    "ytick.labelsize": 18,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
}
plt.rcParams.update(params)
fig, ax = plt.subplots(1, 1, figsize=(7, 6))

_vis_LER_breakdown(
    ax,
    ana_LER_breakdown,
    LER_breakdown_exp,
    p,
    ["c_init", "c_2q"],
    ["Analytically contributed by $p_{IN}$", "Analytically contributed by $p_{2Q}$"],
)
n_shots = 100000000
# ax.set_xlabel(
#     f"$\\mathcal{{J}} \\subseteq \\mathcal{{I}}$, $\\mathcal{{I}}={tuple(init_cfg.inj_lids)}$, shots={n_shots:.0e}",
# )
ax.set_title(
    f"$\\mathcal{{J}} \\subseteq \\mathcal{{I}}$, $\\mathcal{{I}}={tuple(init_cfg.inj_lids)}$, shots={n_shots:.0e}",
    y=-0.66,
)
ax.set_ylabel("Injection error rate on $\\mathcal{{J}}$,\n$p_{\\mathcal{J}}$", fontsize=16)
# ax.set_ylim(0, 0.008)
# ax.set_yscale("log")
xlim = ax.get_xlim()
# ax.hlines(0.001, xlim[0], xlim[1], color="black", linestyle="--", label=r"$p_{\mathcal{{J}}}=0.001$", alpha=0.3)
ax.legend(loc="upper right")
ax.grid(True, alpha=0.4)
# ax.set_title(f"LER breakdown, shots={n_shots:.0e}, p={p}")
plt.tight_layout()
fig_path = f"./../../../qldpc-msi-paper-git/figs/LER-breakdown-{init_method}-{len(init_cfg.inj_lids)}-{init_cfg_id}.pdf"
SAVE_FIG = True
if SAVE_FIG:
    plt.savefig(fig_path, bbox_inches="tight", dpi=300)

plt.show()

# %%


# %%

# %%
import argparse
import os
from dataclasses import dataclass

SAVE_FIG = False
import numpy as np
import sinter
from scipy.stats import pearsonr, spearmanr

from qldpc_msi import tour_bb, xu_hgp
from qldpc_msi.data_mgr import MsiDataMgr
from qldpc_msi.msi.init_cfgs.init_cfg import InitCfg

n_inj_lst = [1, 2, 3, 4, 5, 6]

parser = argparse.ArgumentParser()
parser.add_argument("--save-fig", "-s", action="store_true")
args = parser.parse_args()

method = "psel_dec"
noise_model = "li_uniform"
# noise_model = "li_twoq_dominant"
init_method = "max_supp_protection"
logical_basis = "Y"
# cfg_id = 369
n_psel_cycles = 2
n_se_cycles = 3
# code = BBCode.from_n(144)
# code = XuHgpCode(225)
code_id = "xu_hgp_n225"
# code_id = "bb-[[144,12,12]]"
if code_id == "xu_hgp_n225":
    code = xu_hgp.make_code(n=225)
    cfg_ids = [32, 45, 38, 35, 4, 5]
    ps = [0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.001]
else:
    code = tour_bb.make_code(n=144)
    cfg_ids = [369, 422, 342, 491, 328, 88]
    n_inj_lst = [1, 2, 3, 4, 5, 6]
    ps = [0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.001]


n_shots = 10000000
ideal_dat_meas = False
no_det_stab_dat_meas = False


@dataclass
class _VisDat:
    lers: list[float]
    ps: list[float]
    discard_rates: list[float]
    n_inj: int
    n_fixed_stabs: int
    highs: list[float]
    bests: list[float]
    lows: list[float]


# %%

datas = []

# def err_rate(stat: sinter.TaskStats) -> sinter.Fit:
#     return sinter.fit_binomial(
#         num_shots=stat.shots - stat.discards,
#         num_hits=stat.errors,
#         max_likelihood_factor=1e3,
#     )


def err_rate_per_qubit(shots: int, errors: int, discards: int) -> sinter.Fit:
    return sinter.fit_binomial(
        num_shots=shots - discards,
        num_hits=errors,
        max_likelihood_factor=1e3,
    )


ana_rates_lst = []
X_disc = []
# ps = [0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.001]
for cfg_id, n_inj in zip(cfg_ids, n_inj_lst):
    data_mgr = MsiDataMgr()
    data = data_mgr.load(
        code_id=code_id,
        ps=ps,
        inj_method=method,
        noise_model=noise_model,
        cfg_id=cfg_id,
        n_psel_cycles=n_psel_cycles,
        n_se_cycles=n_se_cycles,
        n_shots=n_shots,
        idm=ideal_dat_meas,
        nodet=no_det_stab_dat_meas,
    )

    discards = data["discards"]
    errors = data["errors"]
    shots = data["shots"]

    # analytical discard rates

    # print(f"{n_inj=}, {data['discards']}")
    X_disc.append(np.array(discards) / n_shots)

    fits = [err_rate_per_qubit(s, e, d) for s, e, d in zip(shots, errors, discards)]

    init_cfg = data["init_cfg"]
    assert isinstance(init_cfg, InitCfg)

    vis_dat = _VisDat(
        lers=data["ler_posts_per_obs"],
        ps=data["ps"],
        discard_rates=[1 - r for r in data["postsel_rates"]],
        n_inj=len(init_cfg.inj_lids),
        n_fixed_stabs=len(init_cfg.fixed_stab_uids),
        highs=[f.high for f in fits],
        bests=[f.best for f in fits],
        lows=[f.low for f in fits],
    )
    # print(data["discards"])

    datas.append(vis_dat)


# %%

n_prot_dat_uids_lst = [110, 126, 123, 125, 118, 86]
n_fixed_stabs = [26, 32, 31, 32, 28, 18]
# print(n_prot_dat_uids_lst)

# print(X_disc)
# ps = [0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.001]
X_disc = np.array(X_disc).T
print(X_disc)
for p, x in zip(ps, X_disc):
    print(f"p={p}")
    x = np.asarray(x)
    # y = np.asarray(n_prot_dat_uids_lst)
    y = np.asarray(n_fixed_stabs)

    print("discards=", x.tolist())
    print("n_prot_dat_uids=", y.tolist())

    r_p, p_p = pearsonr(x, y)  # Pearson
    r_s, p_s = spearmanr(x, y)  # Spearman

    print("Pearson r, p:", r_p, p_p)
    print("Spearman r, p:", r_s, p_s)
    print("-" * 10)
    # Pearson correlation
    # r = np.corrcoef(x, y)[0, 1]
    # print(f"r={r}")

# %%
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

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

markers = ["s", "D", "o", "x", "v", "P"]

line_styles = ["--", "-.", ":"]


def _plot_discard_rates(ax: Axes, datas: list[_VisDat], ana_rates_lst: list[list[float]], ana_rates_labels: list[str]):
    for data, marker in zip(datas, markers):
        ax.plot(data.ps, data.discard_rates, label=f"$|\\mathcal{{I}}|$={data.n_inj}", marker=marker)
        print(data.discard_rates)
    for ana_rates, line_style, label in zip(ana_rates_lst, line_styles, ana_rates_labels):
        ax.plot(datas[0].ps, ana_rates, label=label, linestyle=line_style, color="black")
    ax.legend()
    ax.set_xlabel("Physical error rate, $p$")
    ax.set_xscale("log")
    ax.grid(True)
    ax.set_ylabel("Discard rate per shot")


def _plot_ler(ax: Axes, datas: list[_VisDat], linear_coeffs: list[float]):
    for data, marker in zip(datas, markers):
        ys = np.array(data.bests) / data.n_inj
        ax.plot(data.ps, ys, label=f"$|\\mathcal{{I}}|$={data.n_inj}", marker=marker)
        print(ys.tolist())
        ax.fill_between(data.ps, np.array(data.lows) / data.n_inj, np.array(data.highs) / data.n_inj, alpha=0.2)
    for coeff, line_style in zip(linear_coeffs, line_styles):
        ys = np.array(datas[0].ps) * coeff
        ax.plot(datas[0].ps, ys, label=f"{coeff:.2f}$p$", color="black", linestyle=line_style)
        # ax.hlines(ys[0], 1e-5, 1e-3, color="black", linestyle=line_style)

    ax.legend(loc="upper left", ncol=2)
    ax.set_xlabel("Physical error rate, $p$")
    ax.set_yscale("log")
    ax.set_xscale("log")
    ax.grid(True)
    ax.set_ylabel(f"Injection error rate/qubit, $p^{{\\rm tot}}_{{\\mathcal{{I}}}}/|\\mathcal{{I}}|$", loc="top")


fig, axs = plt.subplots(2, 1, figsize=(8, 10))
if code_id == "bb-[[144,12,12]]":
    if noise_model == "li_uniform":
        # coefficients from the table in the paper
        _plot_ler(axs[0], datas, [1.57, 6.04, 13.76])
        # copy-paste from current cell's output
        ana_rates_lst = [[0.23515700000000006, 0.41508, 0.553484, 0.738671, 0.846986, 0.93183]]
    elif noise_model == "li_twoq_dominant":
        # coefficients from the table in the paper
        _plot_ler(axs[0], datas, [0.67, 2.49, 5.50])
        # copy-paste from current cell's output
        ana_rates_lst = [[0.15309099999999998, 0.28235, 0.39260699999999993, 0.564398, 0.688598, 0.810342]]
    else:
        raise ValueError(f"Unknown noise model: {noise_model}")
elif code_id == "xu_hgp_n225":
    ana_rates_lst = []
    # linear_coeffs = [6.33, 6.50]
    linear_coeffs = []
    _plot_ler(axs[0], datas, linear_coeffs)
else:
    raise ValueError(f"Unknown code: {code_id}")


_plot_discard_rates(axs[1], datas, ana_rates_lst, [r"$r_{disc}^{UP}$, $|\mathcal{I}|=4$"])
# y_title = -0.3
y_title = None
axs[0].set_title("(a) Injection error rate per qubit", y=y_title)
axs[1].set_title("(b) Discard rate (per shot)", y=y_title)
plt.tight_layout()

current_dir = os.path.dirname(os.path.abspath(__file__))
if True:
    plt.savefig(
        os.path.join(current_dir, f"../../../qldpc-msi-paper-git/figs/scalability-{code_id}-{noise_model}.pdf"),
        bbox_inches="tight",
        dpi=300,
    )
plt.show()


# %%


# %%

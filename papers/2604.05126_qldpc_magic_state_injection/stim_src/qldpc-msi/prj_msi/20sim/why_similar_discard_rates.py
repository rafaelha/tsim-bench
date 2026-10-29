# %%
import math
from typing import Iterable

import numpy as np
import sinter
from scipy.stats import pearsonr, spearmanr

from qldpc_msi import tour_bb
from qldpc_msi.data_mgr import InitCfgMgrV2, MsiDataMgr
from qldpc_msi.msi.cnt_errs_by_dem import compute_union_proxy_discard_rates
from qldpc_msi.msi.init_cfgs import InitCfg
from qldpc_msi.noise_spec import get_noise_model


def prt_corr(x: Iterable[float], y: Iterable[float]):
    x = np.asarray(x)
    y = np.asarray(y)

    # print("x=", x.tolist())
    # print("y=", y.tolist())

    r_p, p_p = pearsonr(x, y)  # Pearson
    r_s, p_s = spearmanr(x, y)  # Spearman

    print("Pearson r, p:", r_p, p_p)
    print("Spearman r, p:", r_s, p_s)


def err_rate_per_qubit(shots: int, errors: int, discards: int) -> sinter.Fit:
    return sinter.fit_binomial(
        num_shots=shots - discards,
        num_hits=errors,
        max_likelihood_factor=1e3,
    )


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


# %%

SAVE_FIG = False
method = "psel_dec"
# noise_model = "li"
noise_model = "li_uniform"
init_method = "max_supp_protection"
logical_basis = "Y"
# cfg_id = 369
remove_dummy_cnots = False
n_psel_cycles = 2
n_se_cycles = 3
code = tour_bb.make_code(n=144)
n_shots = 1000000
ideal_dat_meas = False
no_det_stab_dat_meas = False
ps = [0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.001]
cfg_ids = [369, 422, 342, 491, 328, 88]


# %%
def _get_r_disc_exp(cfg_id: int, n_shots: int):
    data_mgr = MsiDataMgr()
    data = data_mgr.load(
        code_id=code.identifier,
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

    return np.array(discards) / n_shots


X_disc = []
for cfg_id in cfg_ids:
    r_disc_exp = _get_r_disc_exp(cfg_id, n_shots)
    X_disc.append(r_disc_exp)

X_disc = np.array(X_disc).T
print(X_disc.shape)


# %%

r_disc_up_arr = []

items = []

r_disc_up_dict = {}

for p, r_disc_exp_lst in zip(ps, X_disc):
    r_disc_up_lst = []
    print(f"p={p}")
    print(f"{r_disc_exp_lst=}")
    for i, (r_disc_exp, cfg_id) in enumerate(zip(r_disc_exp_lst, cfg_ids)):
        init_dat = InitCfgMgrV2().load(
            code_id=code.identifier,
            noise_model=noise_model,
            init_method=init_method,
            _id=cfg_id,
            remove_dummy_cnots=remove_dummy_cnots,
        )
        init_cfg = init_dat["init_cfg"]
        assert isinstance(init_cfg, InitCfg)
        n_inj = len(init_cfg.inj_lids)
        noise_m = get_noise_model(noise_model, p)
        ideal_circ = tour_bb.build_msi_circuit(
            code,
            init_cfg=init_cfg,
            n_cycles=n_se_cycles,
            remove_dummy_cnots=remove_dummy_cnots,
        )

        circ = noise_m.noisy_circuit_skipping_mpp_boundaries(ideal_circ)

        postsel_det_ids = list(range(len(init_cfg.fixed_stab_uids) + code.num_checks))
        fixed_stab_det_ids = list(range(len(init_cfg.fixed_stab_uids)))

        n_mech, p_discard_1st_by_dem, det_discard_prob, a_fixed_stabs, a_parity_checks, a_both = (
            compute_union_proxy_discard_rates(circ, postsel_det_ids, fixed_stab_det_ids, verbose=False)
        )
        r_disc_up_lst.append(p_discard_1st_by_dem)

        print(f"{n_inj}, a_fixed_stabs: {a_fixed_stabs:.3f}, a_parity_checks: {a_parity_checks:.3f}")

        item = {
            "p": p,
            "n_inj": n_inj,
            "n_fixed_stabs": len(init_cfg.fixed_stab_uids),
            "a_fixed": a_fixed_stabs,
            "a_par_cond_fixed": a_parity_checks,
            "1_minus_acc": 1 - a_fixed_stabs * a_parity_checks,
            "r_disc_ub": p_discard_1st_by_dem,
            "r_disc_exp": r_disc_exp,
        }
        items.append(item)

    print(f"r_disc_up_lst: {r_disc_up_lst}")
    # if p == 0.001:
    r_disc_up_arr.append(r_disc_up_lst)
    # print(f"#discards: {discards}")
    # prt_corr(susceptibilities, discards)
    print("*" * 10)


# %%
import pandas as pd

df = pd.DataFrame(items)
df.to_csv("acc_and_disc_rates_v3.csv", index=False)

# %%
print(df.columns)

# for row in df.itertuples():


# %%
df["a_fixed_and_a_par_cond_fixed"] = df.apply(lambda row: (row["a_fixed"], row["a_par_cond_fixed"]), axis=1)

# %%
# merge a_fixed and a_par_cond_fixed to a tuple
# for item in items:
#     item["a_fixed_par_cond_fixed"] = (item["a_fixed"], item["a_par_cond_fixed"])
df.columns


# %%
def fmt_float(x: float, bits: int = 4) -> str:
    return f"{x:.{bits}f}"


def fmt_default(x: float | int | str) -> str:
    return str(x)


def fmt_tuple(x: tuple) -> str:
    return f"({', '.join(fmt_float(i) for i in x)})"


formatters = {
    "p": lambda x: f"${to_aps_sci(x)}$",
    "n_inj": fmt_default,
    "n_fixed_stabs": fmt_default,
    # "a_fixed": fmt_float,
    # "a_par_cond_fixed": fmt_float,
    "a_fixed_and_a_par_cond_fixed": fmt_tuple,
    # "1_minus_acc": fmt_float,
    "r_disc_ub": fmt_float,
    "r_disc_exp": fmt_float,
}

# new_items = []
for i, row in enumerate(df.to_dict(orient="records")):
    # print(row)
    # print(row)
    if row["p"] not in [0.0001, 0.0005, 0.001]:
        continue
    # row =
    item = {}
    for col_name, formatter in formatters.items():
        item[col_name] = formatter(row[col_name])

    ss = ""
    for key, val in item.items():
        ss += f"{val} & "
    ss = ss[:-2] + " \\\\"
    print(ss)
    if (i + 1) % 6 == 0 and i != len(df) - 1:
        print("\\midrule")


# %%

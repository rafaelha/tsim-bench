# %%

import itertools
from typing import Any

import numpy as np
import pandas as pd

from qldpc_msi.msi.cnt_init_errs import (
    get_protected_1q_dat_uids,
    get_protected_ghz_dat_uids,
)
from qldpc_msi.msi.init_cfgs import InitCfg

# %%


def format_p(x: float) -> str:
    return f"{x:.2f}" + r"$p$" if not np.isclose(x, 0.0) else "0"


def format_ratio(x: float, bit: int = 2) -> str:
    return f"{x:.{bit}f}" if not np.isclose(x, 0.0) else "0"


# %% [markdown]
# # Find the best init cfg of different injection counts

from qldpc_msi import xu_hgp

# %%
from qldpc_msi.data_mgr import InitCfgMgrV2

# code_id = "bb-[[144,12,12]]"
noise_model = "li_uniform"
# noise_model = "li_twoq_dominant"
remove_dummy_cnots = False

code = xu_hgp.make_code(n=225)

cfg_mgr = InitCfgMgrV2()
n_inj_to_visited_inj_cfgs: dict[int, set[str]] = {}
n_inj_to_best_dat: dict[int, tuple[int, Any]] = {}
cfg_count = cfg_mgr.count(
    code_id=code.identifier,
    noise_model=noise_model,
    init_method="max_supp_protection",
    remove_dummy_cnots=remove_dummy_cnots,
)
print(f"{cfg_count=}")
for cfg_id in range(cfg_count):
    # dat1: dict[str, Any] = cfg_mgr.load(method="max_fixed_stabs", _id=cfg_id)
    dat: dict[str, Any] = cfg_mgr.load(
        code_id=code.identifier,
        noise_model=noise_model,
        init_method="max_supp_protection",
        remove_dummy_cnots=remove_dummy_cnots,
        _id=cfg_id,
    )

    init_cfg = dat["init_cfg"]
    assert isinstance(init_cfg, InitCfg)
    inj_uids = tuple(sorted(init_cfg.inj_uids))
    # ana_LER_breakdown = dat["perf"]["ana_LER_breakdown"]
    # print(ana_LER_breakdown)
    n_inj = len(init_cfg.inj_lids)
    if n_inj not in n_inj_to_visited_inj_cfgs:
        n_inj_to_visited_inj_cfgs[n_inj] = set()
    lid_to_uid = str({lid: uid for lid, uid in zip(init_cfg.inj_lids, init_cfg.inj_uids)})
    if lid_to_uid in n_inj_to_visited_inj_cfgs[n_inj]:
        print(f"visited {lid_to_uid}")
        continue
    n_inj_to_visited_inj_cfgs[n_inj].add(str(lid_to_uid))

    if n_inj not in n_inj_to_best_dat:
        n_inj_to_best_dat[n_inj] = (cfg_id, dat)
    else:
        if dat["perf"]["c_tol"] < n_inj_to_best_dat[n_inj][1]["perf"]["c_tol"]:
            n_inj_to_best_dat[n_inj] = (cfg_id, dat)

# print(f"unique injection configs: {len(visited_inj_cfgs)}")
for n_inj in sorted(n_inj_to_visited_inj_cfgs.keys()):
    print(f"{n_inj=}, {len(n_inj_to_visited_inj_cfgs[n_inj])=}")
    dat = n_inj_to_best_dat[n_inj][1]
    ana_LER_breakdown = dat["perf"]["ana_LER_breakdown"]
    # print(ana_LER_breakdown)
    for J, c_breakdown in ana_LER_breakdown.items():
        c_breakdown_values = np.array(list(c_breakdown.values()))
        if np.all(c_breakdown_values == 0.0):
            continue
        print(J, c_breakdown)

best_cfg_ids = [n_inj_to_best_dat[n_inj][0] for n_inj in sorted(n_inj_to_best_dat.keys())]

print(f"{best_cfg_ids=}")


# %%

from qldpc_msi.msi.cnt_errs_by_dem import compute_union_proxy_discard_rates

items = []
p = 0.0001
for n_inj, (cfg_id, dat) in n_inj_to_best_dat.items():
    print(f"{n_inj=}, {cfg_id=}")
    perf = dat["perf"]
    init_cfg = dat["init_cfg"]
    assert isinstance(init_cfg, InitCfg)
    print(code.Hx.shape)
    protected_1q_dat_uids = get_protected_1q_dat_uids(
        code.Hx.astype(np.bool_),
        code.Hz.astype(np.bool_),
        init_cfg.fixed_x_stab_ids,
        init_cfg.fixed_z_stab_ids,
        init_cfg.dat_uids_init_in_x,
        init_cfg.dat_uids_init_in_z,
    )
    print(f"{init_cfg.ghz_uids_lst=}")

    protected_ghz_dat_uids = get_protected_ghz_dat_uids(
        init_cfg.ghz_uids_lst, code.Hx, code.Hz, init_cfg.fixed_x_stab_ids, init_cfg.fixed_z_stab_ids
    )

    postsel_det_ids = list(range(len(init_cfg.fixed_stab_uids) + code.num_checks))

    error_params = {
        "p_i": p,
        "p_state_p": p,
        "p_m": p,
        "p_CX": p,
        "p_idling_gate": p,
    }
    circ = xu_hgp.build_msi_circuit(code, init_cfg=init_cfg, n_cycles=2, error_params=error_params)

    postsel_det_ids = list(range(len(init_cfg.fixed_stab_uids) + code.num_checks))
    fixed_stab_det_ids = list(range(len(init_cfg.fixed_stab_uids)))

    _, r_disc_o1, _, _, _, _ = compute_union_proxy_discard_rates(circ, postsel_det_ids, fixed_stab_det_ids)

    n_prot_dat_uids = len(set(protected_1q_dat_uids) | set(itertools.chain(*protected_ghz_dat_uids)))
    item = {
        "n_inj": n_inj,
        # "cfg_id": cfg_id,
        "c_tol_per_q": format_p(perf["c_tol_per_q"]),
        "c_tol": format_p(perf["c_tol"]),
        "c_corr_per_q": format_p(perf["c_corr_per_q"]),
        "c_corr": format_p(perf["c_corr"]),
        "c_corr_over_tot": format_ratio(perf["c_corr_over_tot"]),
        "n_fixed_stabs": dat["init_cfg"].n_fixed_stabs,
        # "n_prot_dat_uids": n_prot_dat_uids,
        "r_disc_o1": format_ratio(r_disc_o1, 4),
        "n_bell_pairs": len(init_cfg.ghz_uids_lst),
    }
    print(f"c_tol_per_q={perf['c_tol_per_q']:.3f}, c_tol={perf['c_tol']:.3f}")
    print(f"c_corr_per_q={perf['c_corr_per_q']:.3f}, c_corr={perf['c_corr']:.3f}")
    print(f"c_corr_over_tot={perf['c_corr_over_tot']:.3f}")

    items.append(item)

str_I = r"$|\mathcal{{I}}|$"
# headers  = [str_I,
# r"$c^{{\text{{tot}}}}$/"+str_I,
# r"$c^{{\text{{tot}}}}$",
# r"$c^{{\text{{corr}}}}$/"+str_I,
# r"$c^{{\text{{corr}}}}$",
# r"$c^{{\text{{corr}}}}/c^{{\text{{tot}}}}$",
# "$|F|$",
# ]

# headers = [
#     r"$|\mathcal{{I}}|$",
#     r"$\frac{p_\mathcal{{I}}}{|\mathcal{{I}}|}$",
#     r"$p_\mathcal{{I}}$",
#     r"$\frac{p^{\text{corr}}_\mathcal{{I}}}{|\mathcal{{I}}|}$",
#     r"$p^{\text{corr}}_\mathcal{{I}}$",
#     r"$\frac{p^{\text{corr}}_\mathcal{{I}}}{p_\mathcal{{I}}}$",
#     r"$|F|$",
# ]

df = pd.DataFrame(items)
table = df.to_latex(float_format=lambda x: f"{x:.2f}", index=False, column_format="c" * len(items[0].keys()))


print(table)

# %%
items_count_cfgs = []
for n_inj in sorted(n_inj_to_visited_inj_cfgs.keys()):
    count = len(n_inj_to_visited_inj_cfgs[n_inj])
    items_count_cfgs.append({"n_inj": n_inj, "count": count})

df_count_cfgs = pd.DataFrame(items_count_cfgs).T
table_count_cfgs = df_count_cfgs.to_latex(header=False, index=False, column_format="c" * len(df_count_cfgs.columns))
print(table_count_cfgs)


# %%


# %%

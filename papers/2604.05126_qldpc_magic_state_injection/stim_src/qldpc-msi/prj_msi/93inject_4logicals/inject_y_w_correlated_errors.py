# %% [markdown]
# Bell pairs and do X and Z experiments separately.
#
# Now, we want to inject $|{i}\rangle$ state and do Y experiments.

# %%
import argparse
import pickle

import sinter

from qldpc_msi import tour_bb
from qldpc_msi.data_mgr import InitCfgMgrV2
from qldpc_msi.msi.init_cfgs import InitCfg
from qldpc_msi.tour_bb import psel_and_dec


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


# %%


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--n_workers", type=int, default=None)
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()
    n_workers = args.n_workers

    method = "psel_dec"
    # logical_basis = "X"
    logical_basis = "Y"
    n_psel_cycles = 2
    n_shots = 100000000
    noise_model_name = "li_uniform"
    # no_det_stab_dat_meas = False
    # ideal_dat_meas = True # excluding data qubit measurement errors
    n_se_cycles = 2
    ana_corr_err = True

    code = tour_bb.make_code(n=144)
    init_method = "max_supp_protection"
    init_cfg_id = 491
    remove_dummy_cnots = False
    init_dat = InitCfgMgrV2().load(
        code_id=code.identifier,
        noise_model=noise_model_name,
        init_method=init_method,
        _id=init_cfg_id,
        remove_dummy_cnots=remove_dummy_cnots,
    )
    init_cfg = init_dat["init_cfg"]
    assert isinstance(init_cfg, InitCfg)

    # ps = [1e-4, 3e-4, 5e-4, 7e-4, 1e-3]
    ps = [1e-3]

    if method == "psel_dec":
        data_stats = psel_and_dec(
            ps,
            code,
            init_cfg,
            n_se_cycles,
            method,
            n_psel_cycles,
            n_shots,
            noise_model_name="li_uniform",
            # no_det_stab_dat_meas,
            # ideal_dat_meas,
            ana_corr_err=True,
            num_workers=n_workers,
        )
    else:
        raise ValueError(f"Invalid method: {method}")

    for stat in data_stats:
        print(stat)

    # %%
    if not args.no_save:
        with open(f"./stats-{logical_basis}-{init_method}-{init_cfg_id}-w_idle.pkl", "wb") as f:
            pickle.dump(data_stats, f)

    for stat in data_stats:
        print(stat)

    # %%

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


if __name__ == "__main__":
    main()

"""Find initialization settings for MSI."""

import argparse
import time
from typing import Any

from qldpc_msi import tour_bb, xu_hgp
from qldpc_msi.data_mgr import InitCfgMgrV2
from qldpc_msi.msi.init_cfgs import (
    find_init_cfg_w_max_fixed_stabs,
    find_init_cfg_w_max_supp_protection,
)
from qldpc_msi.msi.inj_cfgs import find_all_valid_inj_cfgs, groups_to_pairs
from qldpc_msi.noise_spec import (
    LiMsiNoiseSpec,
    dummy_analytical_1st_order_LER_breakdown,
)

ABBR_TO_METHOD = {
    "mfs": "max_fixed_stabs",
    "msp": "max_supp_protection",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--code", type=str, required=True)
    parser.add_argument("-v", "--verbose", action="store_true")
    # parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("-m", "--method", choices=ABBR_TO_METHOD.keys(), help=str(ABBR_TO_METHOD), default="msp")
    parser.add_argument("-n", "--noise-model", type=str, help="noise model", default="li_uniform")
    parser.add_argument("-r", "--remove-dummy-cnots", action="store_true", help="remove dummy CNOTs")
    parser.add_argument("-t", "--dem-test", action="store_true", help="test the DEM compilation of the MSI circuit")
    parser.add_argument("--no-save", action="store_true", help="do not save the results")
    args = parser.parse_args()
    print(f"{args=}")
    method = ABBR_TO_METHOD[args.method]
    time_start = time.time()
    noise_model = args.noise_model

    if noise_model == "li_uniform":
        noise_spec = LiMsiNoiseSpec.li_msi_uniform(0.001)
    elif noise_model == "li_twoq_dominant":
        noise_spec = LiMsiNoiseSpec.li_msi_twoq_dominant(0.001, 0.1)
    else:
        raise ValueError(f"Unknown noise model: {noise_model}")

    if args.code == "bb-n144":
        code = tour_bb.make_code(n=144)
    elif args.code == "xu-hgp-n225":
        code = xu_hgp.make_code(n=225)
    else:
        raise ValueError(f"Unknown code: {args.code}")
    lxs_stim, lzs_stim = code.get_logical_ops_stim()
    lxs = [lx.to_numpy()[0] for lx in lxs_stim]
    lzs = [lz.to_numpy()[1] for lz in lzs_stim]
    lxs_supp = [lx.nonzero()[0].tolist() for lx in lxs]
    lzs_supp = [lz.nonzero()[0].tolist() for lz in lzs]

    valid_inj_cfgs = find_all_valid_inj_cfgs(lxs_supp, lzs_supp)
    print(f"{len(valid_inj_cfgs)=}")
    # exit()

    out_mgr = InitCfgMgrV2()
    total_cfgs = len(valid_inj_cfgs)

    for cfg_id, inj_cfg in enumerate(valid_inj_cfgs):
        # inj_lid_to_uid = {lid: uid for lid, uid in zip(inj_cfg.inj_lids, inj_cfg.inj_uids)}
        # inj_uids = list(inj_lid_to_uid.values())
        # ghz_uids_lst = compute_ghzs_w_partial_inject(inj_cfg.inj_lids, inj_lid_to_uid)
        ghz_uids_lst = list(map(list, groups_to_pairs(inj_cfg.groups)))
        if method == "max_fixed_stabs":
            init_cfg = find_init_cfg_w_max_fixed_stabs(
                code.Hx, code.Hz, lxs_supp, lzs_supp, inj_cfg.inj_lids, inj_cfg.inj_uids, ghz_uids_lst
            )
        elif method == "max_supp_protection":
            init_cfg = find_init_cfg_w_max_supp_protection(
                code.Hx, code.Hz, lxs_supp, lzs_supp, inj_cfg.inj_lids, inj_cfg.inj_uids, ghz_uids_lst
            )
        else:
            raise ValueError(f"Invalid method: {method}")

        print(f"{len(init_cfg.inj_lids)=}, {cfg_id=}/{total_cfgs}")
        if args.code == "xu-hgp-n225":
            assert isinstance(code, xu_hgp.XuHgpCode)
            p_ref = 0.001
            error_params = {"p_i": p_ref, "p_state_p": p_ref, "p_m": p_ref, "p_CX": p_ref, "p_idling_gate": p_ref}
            msi_circ = xu_hgp.build_msi_circuit(code, init_cfg=init_cfg, n_cycles=2, error_params=error_params)
            msi_circ = msi_circ.without_noise()
            ana_LER_breakdown = dummy_analytical_1st_order_LER_breakdown(
                lambda error_params: xu_hgp.build_msi_circuit(
                    code, init_cfg=init_cfg, n_cycles=2, error_params=error_params
                ),
                p_ref,
                init_cfg.inj_lids,
                error_params.keys(),
            )
        elif args.code == "bb-n144":
            assert isinstance(code, tour_bb.BBCode)
            msi_circ = tour_bb.build_msi_circuit(
                code, init_cfg=init_cfg, n_cycles=2, remove_dummy_cnots=args.remove_dummy_cnots
            )
            ana_LER_breakdown = noise_spec.analytical_1st_order_LER_breakdown(
                lambda: msi_circ,
                init_cfg.inj_lids,
            )
        else:
            raise ValueError(f"Unknown code: {args.code}")

        if args.dem_test:
            _ = msi_circ.detector_error_model()

        out_data: dict[str, Any] = {
            "inj_cfg": inj_cfg,
            "init_cfg": init_cfg,
        }
        c_tol = 0.0
        c_corr = 0.0
        for J, c_breakdown in ana_LER_breakdown.items():
            c_tol += sum(c_breakdown.values())
            if len(J) > 1:
                c_corr += sum(c_breakdown.values())
        c_tol_per_q = c_tol / len(init_cfg.inj_lids)
        c_corr_per_q = c_corr / len(init_cfg.inj_lids)
        perf: dict[str, Any] = {}
        perf["ana_LER_breakdown"] = ana_LER_breakdown
        perf["c_tol"] = c_tol
        perf["c_tol_per_q"] = c_tol_per_q
        perf["c_corr"] = c_corr
        perf["c_corr_per_q"] = c_corr_per_q
        perf["c_corr_over_tot"] = c_corr / c_tol
        print(f"{c_tol_per_q=:.3f}, {c_corr_per_q=:.3f}, {c_corr / c_tol=:.3f}")
        out_data["perf"] = perf

        print("")

        if not args.no_save:
            out_mgr.save(
                out_data,
                code_id=code.identifier,
                noise_model=noise_model,
                init_method=method,
                remove_dummy_cnots=args.remove_dummy_cnots,
                _id=cfg_id,
            )

    print(f"time taken: {time.time() - time_start}")


if __name__ == "__main__":
    main()

import argparse

from qldpc_msi.data_mgr import InitCfgMgrV2, MsiDataMgr
from qldpc_msi.msi.init_cfgs import InitCfg
from qldpc_msi.msi.psel_dec import process_stats
from qldpc_msi.tour_bb import make_code, psel_and_dec


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-injm", "--inj_method", type=str, default="psel_dec", choices=["psel_dec", "psel", "dec"])
    parser.add_argument(
        "-initm",
        "--init_method",
        type=str,
        default="max_supp_protection",
        choices=["max_supp_protection", "max_fixed_stabs"],
    )
    parser.add_argument("-initid", "--init_cfg_ids", nargs="+", type=int, default=[369, 422, 342, 491, 328, 88])
    parser.add_argument(
        "-n", "--noise_model", type=str, default="li_uniform", choices=["li_uniform", "li_twoq_dominant"]
    )
    parser.add_argument("-b", "--logical_basis", type=str, default="Y", choices=["Y"])
    parser.add_argument("-s", "--n_shots", type=int, default=1000000)
    parser.add_argument("-sc", "--n_se_cycles", type=int, default=None)
    parser.add_argument("-pc", "--n_psel_cycles", type=int, default=2)
    parser.add_argument("-nodet", "--no_det_stab_dat_meas", action="store_true")
    parser.add_argument("-idm", "--ideal_dat_meas", action="store_true")
    parser.add_argument("-r", "--remove-dummy-cnots", action="store_true")
    parser.add_argument("-f", "--force", action="store_true")
    parser.add_argument("-j", "--num-workers", type=int, default=None)
    parser.add_argument("--no-save", action="store_true")

    default_ps = [0.0001, 0.0002, 0.0003, 0.0005, 0.0007, 0.001]
    parser.add_argument("-ps", type=float, nargs="+", default=default_ps)
    args = parser.parse_args()

    for arg, val in args.__dict__.items():
        print(f"{arg}={val}")

    inj_method = args.inj_method
    noise_model = args.noise_model
    logical_basis = args.logical_basis
    n_psel_cycles = args.n_psel_cycles
    n_shots = args.n_shots
    remove_dummy_cnots = args.remove_dummy_cnots

    if inj_method == "psel":
        # for psel only, it must be no_det_stab_dat_meas = True and ideal_dat_meas = True
        # assert args.no_det_stab_dat_meas == True
        # assert args.ideal_dat_meas == True
        pass
    no_det_stab_dat_meas = args.no_det_stab_dat_meas
    ideal_dat_meas = args.ideal_dat_meas
    print(f"{no_det_stab_dat_meas=}, {ideal_dat_meas=}")

    if inj_method == "psel":
        # if it is postsel only, the default n_se_cycles should be 2
        if args.n_se_cycles is None:
            n_se_cycles = 2
        else:
            n_se_cycles = args.n_se_cycles
    elif inj_method == "psel_dec":
        # if it is postsel and decode, the default n_se_cycles should be 3
        if args.n_se_cycles is None:
            n_se_cycles = 3
        else:
            n_se_cycles = args.n_se_cycles
    else:
        raise ValueError(f"Invalid method: {inj_method}")
    print(f"{n_se_cycles=}")

    msi_data_mgr = MsiDataMgr()

    code = make_code(n=144)
    init_cfg_mgr = InitCfgMgrV2()
    init_cfg_datas = [
        init_cfg_mgr.load(
            code_id=code.identifier,
            noise_model=noise_model,
            init_method=args.init_method,
            remove_dummy_cnots=args.remove_dummy_cnots,
            _id=init_cfg_id,
        )
        for init_cfg_id in args.init_cfg_ids
    ]
    init_cfgs = [init_cfg_data["init_cfg"] for init_cfg_data in init_cfg_datas]
    assert all(isinstance(init_cfg, InitCfg) for init_cfg in init_cfgs)
    ps = args.ps

    for cfg_id, init_cfg in zip(args.init_cfg_ids, init_cfgs):
        if not args.no_save and msi_data_mgr.is_data_exist(
            code_id=code.identifier,
            ps=ps,
            inj_method=inj_method,
            noise_model=noise_model,
            cfg_id=cfg_id,
            n_psel_cycles=n_psel_cycles,
            n_se_cycles=n_se_cycles,
            n_shots=n_shots,
            idm=ideal_dat_meas,
            nodet=no_det_stab_dat_meas,
        ):
            print(f"Data already exists")
            if args.force:
                print(f"Force flag is set, will overwrite the existing data but still run the experiment")
            else:
                print(f"Force flag is not set, do not overwrite the existing data; exit")
                continue

        # if n_psel_cycles == 1:
        #     postsel_det_ids = list(range(len(init_cfg.fixed_stab_uids)))
        # elif n_psel_cycles == 2:
        #     postsel_det_ids = list(range(len(init_cfg.fixed_stab_uids) + code.num_checks))
        # elif n_psel_cycles == -1:  # all the detectors
        #     postsel_det_ids = None
        # else:
        #     raise ValueError(f"Invalid postsel_n_cycles: {n_psel_cycles}")

        # if postsel_det_ids is not None:
        #     print(f"{len(postsel_det_ids)=}")
        if inj_method == "psel_dec":
            stats = psel_and_dec(
                ps,
                code,
                init_cfg,
                n_se_cycles,
                inj_method,
                n_psel_cycles,
                n_shots,
                noise_model,
                num_workers=args.num_workers,
            )
        else:
            raise ValueError(f"Invalid method: {inj_method}")

        data_stats = process_stats(stats, len(init_cfg.inj_lids))

        data = {
            **data_stats,
            "stats": stats,
            "init_cfg": init_cfg,
            "args": args,
        }

        # datas.append(data)

        print("p | LER post per obs | LER post all obs | Post-sel Rate:")
        for p, ler_post_per_obs, ler_post_all_obs, postsel_rate in zip(
            data["ps"], data["ler_posts_per_obs"], data["ler_posts_all_obs"], data["postsel_rates"]
        ):
            print(f"{p:.1e}, {ler_post_per_obs:.6f}, {ler_post_all_obs:.6f}, {postsel_rate:.6f}")

        if inj_method == "psel_dec":
            print("p | Errors | Discards | Shots:")
            for p, errors, discards, shots in zip(data["ps"], data["errors"], data["discards"], data["shots"]):
                print(f"{p:.1e}, {errors}, {discards}, {shots}")

        if not args.no_save:
            msi_data_mgr.save(
                data,
                code_id=code.identifier,
                ps=ps,
                inj_method=inj_method,
                noise_model=noise_model,
                cfg_id=cfg_id,
                n_psel_cycles=n_psel_cycles,
                n_se_cycles=n_se_cycles,
                n_shots=n_shots,
                idm=ideal_dat_meas,
                nodet=no_det_stab_dat_meas,
            )


if __name__ == "__main__":
    main()

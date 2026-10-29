import itertools

import numpy as np


def is_fixed_stab(
    stab: np.ndarray,
    stab_type: str,
    ghz_states: list[list[int]],
    inj_uids: set[int],
    dat_uids_init_in_x: set[int],
    dat_uids_init_in_z: set[int],
) -> bool:
    """Check if a stabilizer is fixed."""
    assert stab_type in ["X", "Z"]
    supp = set(stab.nonzero()[0].tolist())
    if supp & inj_uids:
        return False
    for ghz in ghz_states:
        if len(supp & set(ghz)) % 2 == 1:
            return False
    if stab_type == "X":
        if supp & dat_uids_init_in_z:
            return False
    else:
        if supp & dat_uids_init_in_x:
            return False
    return True


def _check_overlap(
    inj_uids: list[int],
    dat_uids_init_in_x: list[int],
    dat_uids_init_in_z: list[int],
    dat_uids_uninit: list[int],
) -> bool:
    assert set(dat_uids_init_in_x) & set(dat_uids_init_in_z) == set()
    assert set(dat_uids_init_in_x) & set(inj_uids) == set()
    assert set(dat_uids_init_in_z) & set(inj_uids) == set()
    assert set(dat_uids_init_in_x) & set(dat_uids_uninit) == set()
    assert set(dat_uids_init_in_z) & set(dat_uids_uninit) == set()
    assert set(dat_uids_uninit) & set(inj_uids) == set()
    return True


def get_1q_inits_of_data_qubits_on_logical_supps(
    n: int,
    lxs_supp: list[list[int]],
    lzs_supp: list[list[int]],
    ghz_uids_lst: list[list[int]],
    inj_lids: list[int],
    inj_uids: list[int],
) -> tuple[list[int], list[int], list[int]]:
    """Get the single data qubit initializations on logical supports.
    Once we want to inject a logical qubit i,
    supp(X_i) \\ Overlap(X_i, Z_j) \\forall j must be initialized in X. Same for Z_i.
    Overlaps = ghz_uids_lst + inj_uids.

    Returns:
    (
        list[int]: The data qubit uids of 1-qubit initializations in X basis,
        list[int]: The data qubit uids of 1-qubit initializations in Z basis,
        list[int]: The data qubit uids that are not initialized,
    )
    """
    lxs_supp = [lxs_supp[lid] for lid in inj_lids]
    lzs_supp = [lzs_supp[lid] for lid in inj_lids]
    dat_uids_init_in_x = []
    dat_uids_init_in_z = []
    dat_uids_uninit = []

    disallow_uids = set(itertools.chain(*ghz_uids_lst, inj_uids))
    # print(f"{len(disallow_uids)=}")
    x_supp_union = set(itertools.chain(*lxs_supp))
    z_supp_union = set(itertools.chain(*lzs_supp))
    x_supp_union -= disallow_uids
    z_supp_union -= disallow_uids
    assert x_supp_union & z_supp_union == set(), "X and Z supports should not overlap"
    for uid in range(n):
        if uid in disallow_uids:
            continue

        if uid in x_supp_union:
            dat_uids_init_in_x.append(uid)
        elif uid in z_supp_union:
            dat_uids_init_in_z.append(uid)
        else:
            dat_uids_uninit.append(uid)

    assert set(dat_uids_init_in_x) & set(dat_uids_init_in_z) == set()
    assert set(dat_uids_init_in_x) & set(inj_uids) == set()
    assert set(dat_uids_init_in_z) & set(inj_uids) == set()
    _check_overlap(inj_uids, dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit)

    return dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit

"""Init errors: flipping Rx/Rz errors.

Target: for a given flipped logical operator set J,
what are the init errors that do so?

Method-1: derive by counting (this script)

Steps:
1. Find the unprotected qubits and find the logical errors that they can cause
2. Do a reverse mapping for 1. to get a mapping from flipped logical operator set to init errors


Method-2: derive by stim simulation (have not implemented yet)

"""

import numpy as np


def get_protected_1q_dat_uids(
    Hx: np.ndarray,
    Hz: np.ndarray,
    fixed_x_stab_ids: list[int],
    fixed_z_stab_ids: list[int],
    dat_uids_init_in_x: list[int],
    dat_uids_init_in_z: list[int],
) -> list[int]:
    assert set(dat_uids_init_in_x) & set(dat_uids_init_in_z) == set()
    protected = []
    x_protected = _get_protected_1q_dat_uids_by_fixed_p_stabs(Hx, fixed_x_stab_ids, dat_uids_init_in_x)
    z_protected = _get_protected_1q_dat_uids_by_fixed_p_stabs(Hz, fixed_z_stab_ids, dat_uids_init_in_z)
    assert set(x_protected) & set(z_protected) == set(), f"{set(x_protected) & set(z_protected)=}"
    protected = list(sorted(x_protected + z_protected))
    return protected


def _get_protected_1q_dat_uids_by_fixed_p_stabs(
    Hp: np.ndarray,
    fixed_p_stab_ids: list[int],
    dat_uids_init_in_p: list[int],
) -> list[int]:
    """Get the protected 1-qubit data qubits of Pauli basis p.

    Returns:
        list[int]: The data qubit uids of 1-qubit initializations in Pauli basis p.
    """
    reduced_Hp = Hp[fixed_p_stab_ids]
    protected_1q_dat_uids = set()
    mask = np.zeros(Hp.shape[1], dtype=np.bool_)
    mask[dat_uids_init_in_p] = True
    protected_1q_dat_uids = np.any(reduced_Hp & mask, axis=0).nonzero()[0].tolist()
    return list(sorted(protected_1q_dat_uids))


def get_protected_ghz_dat_uids(
    ghz_uids_lst: list[list[int]],
    Hx: np.ndarray,
    Hz: np.ndarray,
    fixed_x_stab_ids: list[int],
    fixed_z_stab_ids: list[int],
) -> list[list[int]]:
    """Get the protected GHZs."""
    # reduced_Hx = Hx[fixed_x_stab_ids]
    # reduced_Hz = Hz[fixed_z_stab_ids]
    fixed_x_stab_ids_set = set(fixed_x_stab_ids)
    fixed_z_stab_ids_set = set(fixed_z_stab_ids)
    protected_ghz_dat_uids = []
    for ghz_uids in ghz_uids_lst:
        cur_protected: list[int] = []
        dat_uids_init_in_x = ghz_uids[:1]
        dat_uids_init_in_z = ghz_uids[1:]
        for dat_uid in dat_uids_init_in_x:
            involved_stabs = Hx[:, dat_uid].nonzero()[0].tolist()
            involved_fixed_stabs = set(involved_stabs) & fixed_x_stab_ids_set
            if involved_fixed_stabs:
                cur_protected.append(dat_uid)
                # print(f"{dat_uid=} is protected by {involved_fixed_stabs=}")

        for dat_uid in dat_uids_init_in_z:
            involved_stabs = Hz[:, dat_uid].nonzero()[0].tolist()
            involved_fixed_stabs = set(involved_stabs) & fixed_z_stab_ids_set
            if involved_fixed_stabs:
                # print(f"{dat_uid=} is protected by {involved_fixed_stabs=}")
                cur_protected.append(dat_uid)
        protected_ghz_dat_uids.append(cur_protected)

    return protected_ghz_dat_uids

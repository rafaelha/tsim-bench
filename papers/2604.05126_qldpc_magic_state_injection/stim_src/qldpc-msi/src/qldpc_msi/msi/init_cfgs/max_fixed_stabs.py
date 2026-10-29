from typing import Dict, List, Set, Tuple

import numpy as np
from ortools.sat.python import cp_model

from qldpc_msi.msi.init_cfgs.init_cfg import InitCfg

from .utils import (
    _check_overlap,
    get_1q_inits_of_data_qubits_on_logical_supps,
    is_fixed_stab,
)


def find_init_cfg_w_max_fixed_stabs(
    Hx: np.ndarray,
    Hz: np.ndarray,
    lxs_supp: list[list[int]],
    lzs_supp: list[list[int]],
    inj_lids: list[int],
    inj_uids: list[int],
    ghz_uids_lst: list[list[int]],
    verbose: bool = False,
) -> InitCfg:
    """Find the fixed stabilizers and 1-qubit initializations in X or Z basis.
    Diff. from v0:
    - No standalone stabilizers

    Returns:
    InitCfg: The initialization configuration with maximum fixed stabilizers.
    """
    dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit = get_1q_inits_of_data_qubits_on_logical_supps(
        Hx.shape[1], lxs_supp, lzs_supp, ghz_uids_lst, inj_lids, inj_uids
    )
    if verbose:
        print(f"{len(dat_uids_init_in_x)=}")
        print(f"{len(dat_uids_init_in_z)=}")
        print(f"{len(dat_uids_uninit)=}")

    fixed_X_stab_cand_ids: list[int] = []
    for stab_id, stab in enumerate(Hx):
        if not is_fixed_stab(stab, "X", ghz_uids_lst, set(inj_uids), set(dat_uids_init_in_x), set(dat_uids_init_in_z)):
            continue
        fixed_X_stab_cand_ids.append(stab_id)

    fixed_Z_stab_cand_ids = []
    for stab_id, stab in enumerate(Hz):
        if not is_fixed_stab(stab, "Z", ghz_uids_lst, set(inj_uids), set(dat_uids_init_in_x), set(dat_uids_init_in_z)):
            continue
        fixed_Z_stab_cand_ids.append(stab_id)

    never_fixed_x_stab_ids = [i for i in range(Hx.shape[0]) if i not in set(fixed_X_stab_cand_ids)]
    never_fixed_z_stab_ids = [i for i in range(Hz.shape[0]) if i not in set(fixed_Z_stab_cand_ids)]
    # if verbose:
    #     print(f"------------  candidate, never-fixed and standalone stabilizers ------------")
    # (
    #     standalone_x_stab_ids,
    #     standalone_z_stab_ids,
    #     standalone_dat_uids_init_in_x,
    #     standalone_dat_uids_init_in_z,
    #     dat_uids_uninit,  # update directly
    # ) = _find_standalone_stabs(Hx, Hz, fixed_X_stab_cand_ids, fixed_Z_stab_cand_ids, dat_uids_uninit)

    if verbose:
        print(f"{len(fixed_X_stab_cand_ids)=}")
        print(f"{len(fixed_Z_stab_cand_ids)=}")
        print(f"{len(never_fixed_x_stab_ids)=}")
        print(f"{len(never_fixed_z_stab_ids)=}")
        # print(f"{len(standalone_x_stab_ids)=}")
        # print(f"{len(standalone_z_stab_ids)=}")

    # dat_uids_init_in_x += standalone_dat_uids_init_in_x
    # dat_uids_init_in_z += standalone_dat_uids_init_in_z

    # unfixed_x_stab_ids = [i for i in fixed_X_stab_cand_ids if i not in set(standalone_x_stab_ids)]
    # unfixed_z_stab_ids = [i for i in fixed_Z_stab_cand_ids if i not in set(standalone_z_stab_ids)]

    if verbose:
        # print(f"{len(unfixed_x_stab_ids)=}")
        # print(f"{len(unfixed_z_stab_ids)=}")

        print(f"{len(dat_uids_init_in_x)=}, {dat_uids_init_in_x=}")
        print(f"{len(dat_uids_init_in_z)=}, {dat_uids_init_in_z=}")

    assert _check_overlap(inj_uids, dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit)

    if verbose:
        print(f"------------  more fixed stabilizers by solving SAT ------------")

    more_fixed_x_stab_ids, more_fixed_z_stab_ids, more_init_in_X, more_init_in_Z, dat_uids_uninit = (
        maximize_num_fixed_stabs(
            Hx,
            Hz,
            fixed_X_stab_cand_ids,
            fixed_Z_stab_cand_ids,
            dat_uids_uninit,
        )
    )

    if verbose:
        print(f"{len(dat_uids_uninit)=}")
        print(f"{len(more_fixed_x_stab_ids)=}")
        print(f"{len(more_fixed_z_stab_ids)=}")
        print(f"{len(more_init_in_X)=}, {more_init_in_X=}")
        print(f"{len(more_init_in_Z)=}, {more_init_in_Z=}")

    final_fixed_x_stab_ids = more_fixed_x_stab_ids
    final_fixed_z_stab_ids = more_fixed_z_stab_ids
    fixed_stab_uids = final_fixed_x_stab_ids + [stab_id + Hx.shape[0] for stab_id in final_fixed_z_stab_ids]

    dat_uids_init_in_x += more_init_in_X
    dat_uids_init_in_z += more_init_in_Z
    if verbose:
        print(f"------------  final fixed stabilizers ------------")
        print(f"{len(fixed_stab_uids)=}")
        print(f"{len(dat_uids_init_in_x)=}")
        print(f"{len(dat_uids_init_in_z)=}")

    assert _check_overlap(inj_uids, dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit)

    # return final_fixed_x_stab_ids, final_fixed_z_stab_ids, dat_uids_init_in_x, dat_uids_init_in_z

    return InitCfg(
        inj_lids,
        inj_uids,
        ghz_uids_lst,
        fixed_stab_uids,
        final_fixed_x_stab_ids,
        final_fixed_z_stab_ids,
        dat_uids_init_in_x,
        dat_uids_init_in_z,
    )


def _validate_inputs(
    Hx: np.ndarray,
    Hz: np.ndarray,
    unfixed_x_stab_ids: List[int],
    unfixed_z_stab_ids: List[int],
    uninit_dat_uids: List[int],
) -> None:
    if Hx.ndim != 2 or Hz.ndim != 2:
        raise ValueError("Hx and Hz must be 2D arrays.")
    if Hx.shape[1] != Hz.shape[1]:
        raise ValueError("Hx and Hz must have the same number of columns.")
    num_x, num_z, num_cols = Hx.shape[0], Hz.shape[0], Hx.shape[1]
    if any(i < 0 or i >= num_x for i in unfixed_x_stab_ids):
        raise ValueError("unfixed_x_stab_ids out of range for Hx.")
    if any(i < 0 or i >= num_z for i in unfixed_z_stab_ids):
        raise ValueError("unfixed_z_stab_ids out of range for Hz.")
    if any(c < 0 or c >= num_cols for c in uninit_dat_uids):
        raise ValueError("uninit_dat_uids out of range for columns.")


def _supports_on_uninit(H: np.ndarray, row_ids: List[int], uninit: Set[int]) -> Dict[int, List[int]]:
    """Map each row id to the list of columns in uninit where H[row, col] == 1."""
    return {r: [c for c in uninit if H[r, c] == 1] for r in row_ids}


def _solve_cp_sat(
    x_supports: Dict[int, List[int]],
    z_supports: Dict[int, List[int]],
    uninit_dat_uids: List[int],
    time_limit_seconds: float | None,
) -> Tuple[List[int], List[int], List[int], List[int]]:
    """
    Variables:
      is_X[col] ∈ {0,1} for col in uninit_dat_uids.
      row_fixed_X[r] ∈ {0,1} for X rows touching ≥1 uninit column.
      row_fixed_Z[r] ∈ {0,1} for Z rows touching ≥1 uninit column.

    Constraints (only on uninit columns):
      For X row r and c in x_supports[r]: row_fixed_X[r] ≤  is_X[c]  (via implication)
      For Z row r and c in z_supports[r]: row_fixed_Z[r] ≤ 1 - is_X[c]

    Objective:
      Maximize Σ row_fixed_X + Σ row_fixed_Z
      (Rows with empty support on uninit are ignored—they cannot be influenced.)
    """
    model = cp_model.CpModel()

    # Decision vars for uninitialized columns
    is_X: Dict[int, cp_model.IntVar] = {c: model.NewBoolVar(f"is_X_col{c}") for c in sorted(uninit_dat_uids)}

    # Row indicators and linking constraints
    row_fixed_X: Dict[int, cp_model.IntVar] = {}
    for r, cols in x_supports.items():
        if not cols:  # no overlap with uninit ⇒ outside our control ⇒ ignore in objective
            continue
        rf = model.NewBoolVar(f"rowX_{r}_fixed")
        row_fixed_X[r] = rf
        for c in cols:
            model.Add(is_X[c] == 1).OnlyEnforceIf(rf)

    row_fixed_Z: Dict[int, cp_model.IntVar] = {}
    for r, cols in z_supports.items():
        if not cols:
            continue
        rf = model.NewBoolVar(f"rowZ_{r}_fixed")
        row_fixed_Z[r] = rf
        for c in cols:
            model.Add(is_X[c] == 0).OnlyEnforceIf(rf)

    # Objective: maximize the number of fixed rows we can actually influence
    model.Maximize(sum(row_fixed_X.values()) + sum(row_fixed_Z.values()))

    solver = cp_model.CpSolver()
    if time_limit_seconds is not None:
        solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("Solver did not find a solution.")

    fixed_x = sorted([r for r, v in row_fixed_X.items() if solver.Value(v) == 1])
    fixed_z = sorted([r for r, v in row_fixed_Z.items() if solver.Value(v) == 1])
    init_in_X = sorted([c for c, v in is_X.items() if solver.Value(v) == 1])
    init_in_Z = sorted([c for c, v in is_X.items() if solver.Value(v) == 0])
    return fixed_x, fixed_z, init_in_X, init_in_Z


def maximize_num_fixed_stabs(
    Hx: np.ndarray,
    Hz: np.ndarray,
    unfixed_x_stab_ids: List[int],
    unfixed_z_stab_ids: List[int],
    uninit_dat_uids: List[int],
    *,
    time_limit_seconds: float | None = None,
) -> Tuple[List[int], List[int], List[int], List[int], List[int]]:
    """
    Maximize the number of X/Z stabilizers that become “fixed” *with respect to*
    the set `uninit_dat_uids`. A stabilizer is counted as fixed iff **all**
    uninitialized columns it touches are set to its required basis (X for X-rows, Z for Z-rows).
    Columns outside `uninit_dat_uids` are ignored.

    Returns:
      (fixed_x_stab_ids, fixed_z_stab_ids, init_in_X, init_in_Z)
    """
    _validate_inputs(Hx, Hz, unfixed_x_stab_ids, unfixed_z_stab_ids, uninit_dat_uids)
    uninit: Set[int] = set(uninit_dat_uids)
    x_supports = _supports_on_uninit(Hx, unfixed_x_stab_ids, uninit)
    z_supports = _supports_on_uninit(Hz, unfixed_z_stab_ids, uninit)
    rst = _solve_cp_sat(x_supports, z_supports, uninit_dat_uids, time_limit_seconds)
    still_uninit = set(uninit_dat_uids) - set(rst[2]) - set(rst[3])
    return rst[0], rst[1], rst[2], rst[3], list(still_uninit)


def _find_standalone_stabs(
    Hx: np.ndarray,
    Hz: np.ndarray,
    x_stab_cand_ids: list[int],
    z_stab_cand_ids: list[int],
    uids_uninit: list[int],
) -> tuple[list[int], list[int], list[int], list[int], list[int]]:
    """Find the fixed stabilizers and 1-qubit initializations in X or Z basis.

    Returns:
    (
        list[int]: The row indices of fixed X-type stabilizers in Hx,
        list[int]: The row indices of fixed Z-type stabilizers in Hz,
        list[int]: The data qubit uids of 1-qubit initializations in X basis,
        list[int]: The data qubit uids of 1-qubit initializations in Z basis,
        list[int]: The data qubit uids that are not initialized,
    )
    """
    reduced_Hx = Hx[x_stab_cand_ids]
    reduced_Hz = Hz[z_stab_cand_ids]

    # x stabs that do not overlap with any z stabilizers (full support); vice versa
    mx_mz = reduced_Hx @ reduced_Hz.T
    _fixed_x_stab_relative_ids = np.all(mx_mz == 0, axis=1).nonzero()[0].tolist()
    _fixed_z_stab_relative_ids = np.all(mx_mz == 0, axis=0).nonzero()[0].tolist()
    fixed_x_stab_ids = [x_stab_cand_ids[i] for i in _fixed_x_stab_relative_ids]
    fixed_z_stab_ids = [z_stab_cand_ids[i] for i in _fixed_z_stab_relative_ids]

    # initialize the data qubits that are not initialized according to the standalone stabs
    uids_init_in_x = set()
    uids_init_in_z = set()
    uids_uninit_set = set(uids_uninit)
    for x_stab_id in fixed_x_stab_ids:
        uids_init_in_x.update(set(Hx[x_stab_id].nonzero()[0].tolist()) & uids_uninit_set)
    for z_stab_id in fixed_z_stab_ids:
        uids_init_in_z.update(set(Hz[z_stab_id].nonzero()[0].tolist()) & uids_uninit_set)
    assert uids_init_in_x & uids_init_in_z == set(), f"{uids_init_in_x & uids_init_in_z=}"
    uids_uninit_set -= uids_init_in_x
    uids_uninit_set -= uids_init_in_z
    assert uids_uninit_set & uids_init_in_x == set(), f"{uids_uninit_set & uids_init_in_x=}"
    assert uids_uninit_set & uids_init_in_z == set(), f"{uids_uninit_set & uids_init_in_z=}"
    return fixed_x_stab_ids, fixed_z_stab_ids, list(uids_init_in_x), list(uids_init_in_z), list(uids_uninit_set)


def find_fixed_stabs_and_1q_inits(
    Hx: np.ndarray,
    Hz: np.ndarray,
    lxs_supp: list[list[int]],
    lzs_supp: list[list[int]],
    inj_lids: list[int],
    inj_uids: list[int],
    ghz_uids_lst: list[list[int]],
    verbose: bool = False,
) -> tuple[list[int], list[int], list[int], list[int]]:
    """Find the fixed stabilizers and 1-qubit initializations in X or Z basis.

    Returns:
    (
        list[int]: The row indices of fixed X-type stabilizers in Hx,
        list[int]: The row indices of fixed Z-type stabilizers in Hz,
        list[int]: The data qubit uids of 1-qubit initializations in X basis,
        list[int]: The data qubit uids of 1-qubit initializations in Z basis,
    )
    """
    dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit = get_1q_inits_of_data_qubits_on_logical_supps(
        Hx.shape[1], lxs_supp, lzs_supp, ghz_uids_lst, inj_lids, inj_uids
    )
    if verbose:
        print(f"{len(dat_uids_init_in_x)=}")
        print(f"{len(dat_uids_init_in_z)=}")
        print(f"{len(dat_uids_uninit)=}")

    fixed_X_stab_cand_ids: list[int] = []
    for stab_id, stab in enumerate(Hx):
        if not is_fixed_stab(stab, "X", ghz_uids_lst, set(inj_uids), set(dat_uids_init_in_x), set(dat_uids_init_in_z)):
            continue
        fixed_X_stab_cand_ids.append(stab_id)

    fixed_Z_stab_cand_ids = []
    for stab_id, stab in enumerate(Hz):
        if not is_fixed_stab(stab, "Z", ghz_uids_lst, set(inj_uids), set(dat_uids_init_in_x), set(dat_uids_init_in_z)):
            continue
        fixed_Z_stab_cand_ids.append(stab_id)

    never_fixed_x_stab_ids = [i for i in range(Hx.shape[0]) if i not in set(fixed_X_stab_cand_ids)]
    never_fixed_z_stab_ids = [i for i in range(Hz.shape[0]) if i not in set(fixed_Z_stab_cand_ids)]
    if verbose:
        print(f"------------  candidate, never-fixed and standalone stabilizers ------------")
    (
        standalone_x_stab_ids,
        standalone_z_stab_ids,
        standalone_dat_uids_init_in_x,
        standalone_dat_uids_init_in_z,
        dat_uids_uninit,  # update directly
    ) = _find_standalone_stabs(Hx, Hz, fixed_X_stab_cand_ids, fixed_Z_stab_cand_ids, dat_uids_uninit)

    if verbose:
        print(f"{len(fixed_X_stab_cand_ids)=}")
        print(f"{len(fixed_Z_stab_cand_ids)=}")
        print(f"{len(never_fixed_x_stab_ids)=}")
        print(f"{len(never_fixed_z_stab_ids)=}")
        print(f"{len(standalone_x_stab_ids)=}")
        print(f"{len(standalone_z_stab_ids)=}")

    dat_uids_init_in_x += standalone_dat_uids_init_in_x
    dat_uids_init_in_z += standalone_dat_uids_init_in_z

    unfixed_x_stab_ids = [i for i in fixed_X_stab_cand_ids if i not in set(standalone_x_stab_ids)]
    unfixed_z_stab_ids = [i for i in fixed_Z_stab_cand_ids if i not in set(standalone_z_stab_ids)]

    if verbose:
        print(f"{len(unfixed_x_stab_ids)=}")
        print(f"{len(unfixed_z_stab_ids)=}")

        print(f"{len(dat_uids_init_in_x)=}, {dat_uids_init_in_x=}")
        print(f"{len(dat_uids_init_in_z)=}, {dat_uids_init_in_z=}")

    assert _check_overlap(inj_uids, dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit)

    if verbose:
        print(f"------------  more fixed stabilizers by solving SAT ------------")

    more_fixed_x_stab_ids, more_fixed_z_stab_ids, more_init_in_X, more_init_in_Z, dat_uids_uninit = (
        maximize_num_fixed_stabs(
            Hx,
            Hz,
            unfixed_x_stab_ids,
            unfixed_z_stab_ids,
            dat_uids_uninit,
        )
    )

    if verbose:
        print(f"{len(dat_uids_uninit)=}")
        print(f"{len(more_fixed_x_stab_ids)=}")
        print(f"{len(more_fixed_z_stab_ids)=}")
        print(f"{len(more_init_in_X)=}, {more_init_in_X=}")
        print(f"{len(more_init_in_Z)=}, {more_init_in_Z=}")

    final_fixed_x_stab_ids = standalone_x_stab_ids + more_fixed_x_stab_ids
    final_fixed_z_stab_ids = standalone_z_stab_ids + more_fixed_z_stab_ids
    fixed_stab_uids = final_fixed_x_stab_ids + [stab_id + Hx.shape[0] for stab_id in final_fixed_z_stab_ids]

    dat_uids_init_in_x += more_init_in_X
    dat_uids_init_in_z += more_init_in_Z
    if verbose:
        print(f"------------  final fixed stabilizers ------------")
        print(f"{len(fixed_stab_uids)=}")
        print(f"{len(dat_uids_init_in_x)=}")
        print(f"{len(dat_uids_init_in_z)=}")

    assert _check_overlap(inj_uids, dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit)

    return final_fixed_x_stab_ids, final_fixed_z_stab_ids, dat_uids_init_in_x, dat_uids_init_in_z

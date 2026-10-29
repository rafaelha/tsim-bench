from typing import Dict, List, Optional, Tuple

import numpy as np
import pulp

from qldpc_msi.msi.init_cfgs.init_cfg import InitCfg

from .utils import (
    _check_overlap,
    get_1q_inits_of_data_qubits_on_logical_supps,
    is_fixed_stab,
)


def find_init_cfg_w_max_supp_protection(
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

    Returns:
    InitCfg: The initialization configuration with maximum support protection.
    """
    dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit = get_1q_inits_of_data_qubits_on_logical_supps(
        Hx.shape[1], lxs_supp, lzs_supp, ghz_uids_lst, inj_lids, inj_uids
    )
    # dat_uids_init_in_x += [ghz_uids[0] for ghz_uids in ghz_uids_lst]
    # dat_uids_init_in_z += [ghz_uids[1] for ghz_uids in ghz_uids_lst]
    inj_supp_uids = set(
        dat_uids_init_in_x
        + dat_uids_init_in_z
        + [ghz_uids[0] for ghz_uids in ghz_uids_lst]
        + [ghz_uids[1] for ghz_uids in ghz_uids_lst]
    )

    basis_on_uid_to_protect: dict[int, str] = {}
    for uid in inj_supp_uids:
        if uid in dat_uids_init_in_x + [ghz_uids[0] for ghz_uids in ghz_uids_lst]:
            basis_on_uid_to_protect[uid] = "X"
        elif uid in dat_uids_init_in_z + [ghz_uids[1] for ghz_uids in ghz_uids_lst]:
            basis_on_uid_to_protect[uid] = "Z"
        else:
            raise ValueError(f"Invalid uid: {uid}")

    # for lid in inj_lids:
    #     x_remainder = set(lxs_supp[lid]) - set(inj_uids)
    #     z_remainder = set(lzs_supp[lid]) - set(inj_uids)
    #     print(f"{lid=}, {x_remainder=}, {z_remainder=}")
    #     inj_supp_uids.update(x_remainder)
    #     inj_supp_uids.update(z_remainder)

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
    #     print(f"{len(standalone_x_stab_ids)=}")
    #     print(f"{len(standalone_z_stab_ids)=}")

    # dat_uids_init_in_x += standalone_dat_uids_init_in_x
    # dat_uids_init_in_z += standalone_dat_uids_init_in_z

    # unfixed_x_stab_ids = [i for i in fixed_X_stab_cand_ids if i not in set(standalone_x_stab_ids)]
    # unfixed_z_stab_ids = [i for i in fixed_Z_stab_cand_ids if i not in set(standalone_z_stab_ids)]

    # if verbose:
    # print(f"{len(unfixed_x_stab_ids)=}")
    # print(f"{len(unfixed_z_stab_ids)=}")

    # print(f"{len(dat_uids_init_in_x)=}, {dat_uids_init_in_x=}")
    # print(f"{len(dat_uids_init_in_z)=}, {dat_uids_init_in_z=}")

    # assert _check_overlap(inj_uids, dat_uids_init_in_x, dat_uids_init_in_z, dat_uids_uninit)

    if verbose:
        print(f"------------  more fixed stabilizers by solving SAT ------------")

    protected_uids, more_fixed_x_stab_ids, more_fixed_z_stab_ids, more_init_in_X, more_init_in_Z, dat_uids_uninit = (
        maximize_protection_for_injected_supports_pulp(
            Hx,
            Hz,
            dat_uids_uninit,
            list(inj_supp_uids),
            basis_on_uid_to_protect=basis_on_uid_to_protect,
            candidate_x_stab_ids=fixed_X_stab_cand_ids,
            candidate_z_stab_ids=fixed_Z_stab_cand_ids,
        )
    )

    if verbose:
        print(f"{len(protected_uids)=}")
        unprotected_uids = list(inj_supp_uids - set(protected_uids))
        print(f"{len(unprotected_uids)=}, {unprotected_uids=}")
        print(f"{len(dat_uids_uninit)=}")
        print(f"{len(more_fixed_x_stab_ids)=}")
        print(f"{len(more_fixed_z_stab_ids)=}")
        print(f"{len(more_init_in_X)=}, {more_init_in_X=}")
        print(f"{len(more_init_in_Z)=}, {more_init_in_Z=}")

    # final_fixed_x_stab_ids = standalone_x_stab_ids + more_fixed_x_stab_ids
    # final_fixed_z_stab_ids = standalone_z_stab_ids + more_fixed_z_stab_ids
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


def maximize_protection_for_injected_supports_pulp(
    Hx: np.ndarray,
    Hz: np.ndarray,
    uninit_dat_uids: List[int],
    uid_to_protect: List[int],
    *,
    basis_on_uid_to_protect: Dict[int, str],
    candidate_x_stab_ids: Optional[List[int]] = None,
    candidate_z_stab_ids: Optional[List[int]] = None,
    solver: Optional[pulp.LpSolver] = None,
) -> Tuple[
    List[int],  # protected_uids: subset of uid_to_protect that end up protected
    List[int],  # fixed_x_stab_ids
    List[int],  # fixed_z_stab_ids
    List[int],  # init_in_X
    List[int],  # init_in_Z
    List[int],  # still_uninit
]:
    """
    Maximize protection of injected logical supports from single-qubit init (reset) errors,
    when:
        - The qubits you want to protect (uid_to_protect) already have fixed bases.
        - You can only choose bases on qubits outside those supports (uninit_dat_uids).

    This matches your situation where:
        - I (here: uid_to_protect) = \\cup_i (O_{i,i} \\ {Q_i}), with O_{i,j} = supp(X_i) \\cap supp(Z_j),
          and Q_i is the injection uid (inj_uid).
        - U (uninit_dat_uids) are qubits outside the injected logical supports.

    Model:
        - For j ∈ uninit_dat_uids (U), we choose x_j ∈ {0,1}:
              x_j = 1 → initialize qubit j in X basis  (reset error modeled as Z_j)
              x_j = 0 → initialize qubit j in Z basis  (reset error modeled as X_j)

        - For each X-stabilizer row r (candidate_x_stab_ids), we may mark it "fixed":
              f_r^X = 1 ⇒ all uninitialized qubits in its support are in X basis.

        - For each Z-stabilizer row r (candidate_z_stab_ids), we may mark it "fixed":
              f_r^Z = 1 ⇒ all uninitialized qubits in its support are in Z basis.

        - For each j in uid_to_protect (I), the basis is given externally via basis_on_uid_to_protect[j]:
              "X" → we care about detecting Z_j errors via X-type stabilizers.
              "Z" → we care about detecting X_j errors via Z-type stabilizers.

        - A target qubit j ∈ uid_to_protect is "protected" if:
              basis_on_uid_to_protect[j] == "X" and ∃ fixed X-row touching j, or
              basis_on_uid_to_protect[j] == "Z" and ∃ fixed Z-row touching j.

        - Objective: maximize the number of protected target qubits.

    Inputs
    ------
    Hx, Hz :
        Binary numpy arrays (0/1) representing X- and Z-type stabilizer checks.
        Hx.shape == (m_X, n), Hz.shape == (m_Z, n).
    uninit_dat_uids :
        Qubit indices (0-based) whose initialization basis we are free to choose (U).
    uid_to_protect :
        Qubit indices (0-based) on injected logical supports that we want to protect (I).
        In your notation, this would be \\cup_i (O_{i,i} \\ {Q_i}).
    basis_on_uid_to_protect :
        Dict mapping each j in uid_to_protect to "X" or "Z", indicating the basis
        that qubit j is initialized in by the injection scheme. This determines
        whether we try to detect Z_j (if "X") or X_j (if "Z") errors.
    candidate_x_stab_ids, candidate_z_stab_ids :
        Optional subsets of stabilizer row indices that we allow as "fixable" candidates.
        If None, we use all rows in Hx/Hz.

    Returns
    -------
    protected_uids :
        Sorted list of qubits in uid_to_protect that end up protected in the optimal solution.
    fixed_x_stab_ids, fixed_z_stab_ids :
        Sorted lists of stabilizer row indices that the optimizer marks as "fixed".
    init_in_X, init_in_Z :
        Sorted lists of uninitialized qubits that should be initialized in X or Z basis.
    still_uninit :
        Any uninitialized qubits that, due to numerical issues, were not clearly assigned
        to X or Z (should be empty in normal operation).
    """

    # -----------------------
    # Basic validation
    # -----------------------
    if Hx.ndim != 2 or Hz.ndim != 2:
        raise ValueError("Hx and Hz must be 2D numpy arrays.")

    if Hx.shape[1] != Hz.shape[1]:
        raise ValueError("Hx and Hz must have the same number of columns (same number of data qubits).")

    num_x_rows, num_qubits = Hx.shape
    num_z_rows, num_qubits_z = Hz.shape
    assert num_qubits == num_qubits_z

    U = set(uninit_dat_uids)
    I = set(uid_to_protect)

    # Check index ranges
    if any(q < 0 or q >= num_qubits for q in U):
        raise ValueError("uninit_dat_uids contain an index out of range.")
    if any(q < 0 or q >= num_qubits for q in I):
        raise ValueError("uid_to_protect contain an index out of range.")

    # Ensure basis_on_uid_to_protect is specified for all targets
    for j in I:
        if j not in basis_on_uid_to_protect:
            raise ValueError(f"basis_on_uid_to_protect missing entry for qubit {j}.")
        if basis_on_uid_to_protect[j] not in ("X", "Z"):
            raise ValueError(
                f"basis_on_uid_to_protect[{j}] must be 'X' or 'Z', " f"got {basis_on_uid_to_protect[j]!r}."
            )

    # If caller does not restrict candidate stabilizers, use all rows
    if candidate_x_stab_ids is None:
        candidate_x_stab_ids = list(range(num_x_rows))
    if candidate_z_stab_ids is None:
        candidate_z_stab_ids = list(range(num_z_rows))

    if any(r < 0 or r >= num_x_rows for r in candidate_x_stab_ids):
        raise ValueError("candidate_x_stab_ids out of range for Hx.")
    if any(r < 0 or r >= num_z_rows for r in candidate_z_stab_ids):
        raise ValueError("candidate_z_stab_ids out of range for Hz.")

    # -----------------------
    # Precompute supports on U and detection sets on I
    # -----------------------
    # Support on U:
    #   supp_U^X(r) = { j in U | Hx[r,j] == 1 }
    #   supp_U^Z(r) = { j in U | Hz[r,j] == 1 }
    x_support_U: Dict[int, List[int]] = {}
    for r in candidate_x_stab_ids:
        cols = [j for j in U if Hx[r, j] == 1]
        x_support_U[r] = cols

    z_support_U: Dict[int, List[int]] = {}
    for r in candidate_z_stab_ids:
        cols = [j for j in U if Hz[r, j] == 1]
        z_support_U[r] = cols

    # Detection sets for target qubits (uid_to_protect):
    #   D_X(j) = { X-rows r | Hx[r,j] == 1 }
    #   D_Z(j) = { Z-rows r | Hz[r,j] == 1 }
    D_X: Dict[int, List[int]] = {}
    D_Z: Dict[int, List[int]] = {}
    for j in I:
        D_X[j] = [r for r in candidate_x_stab_ids if Hx[r, j] == 1]
        D_Z[j] = [r for r in candidate_z_stab_ids if Hz[r, j] == 1]

    # -----------------------
    # Build PuLP model
    # -----------------------
    model = pulp.LpProblem("MaximizeProtectionInjectedSupports", pulp.LpMaximize)

    # 1) Basis choice on U: x_j ∈ {0,1}
    #    x_j = 1 → X-basis; x_j = 0 → Z-basis
    x_var: Dict[int, pulp.LpVariable] = {
        j: pulp.LpVariable(f"x_{j}", lowBound=0, upBound=1, cat=pulp.LpBinary) for j in sorted(U)
    }

    # 2) Row-fixed indicators: fX_r, fZ_r ∈ {0,1}
    #    Only for rows that have support on U, because rows disjoint from U
    #    cannot be influenced by our basis choices on U.
    fX: Dict[int, pulp.LpVariable] = {}
    for r in candidate_x_stab_ids:
        if x_support_U[r]:
            fX[r] = pulp.LpVariable(f"fX_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)

    fZ: Dict[int, pulp.LpVariable] = {}
    for r in candidate_z_stab_ids:
        if z_support_U[r]:
            fZ[r] = pulp.LpVariable(f"fZ_{r}", lowBound=0, upBound=1, cat=pulp.LpBinary)

    # 3) Protection indicators for each target qubit j ∈ I:
    #    p_j = 1 if j is protected under its *given* basis.
    p: Dict[int, pulp.LpVariable] = {
        j: pulp.LpVariable(f"p_{j}", lowBound=0, upBound=1, cat=pulp.LpBinary) for j in sorted(I)
    }

    # -----------------------
    # Constraints
    # -----------------------

    # (A) Fixed stabilizer constraints on U:
    #     For X-rows: if fX[r] = 1, then all uninitialized qubits in its support
    #     must be in X basis → fX[r] <= x_j for all j ∈ supp_U^X(r).
    for r, cols in x_support_U.items():
        if r not in fX:
            continue
        for j in cols:
            model += fX[r] <= x_var[j], f"FixedX_row{r}_col{j}"

    #     For Z-rows: if fZ[r] = 1, then all uninitialized qubits in its support
    #     must be in Z basis → fZ[r] <= 1 - x_j for all j ∈ supp_U^Z(r).
    for r, cols in z_support_U.items():
        if r not in fZ:
            continue
        for j in cols:
            model += fZ[r] <= 1 - x_var[j], f"FixedZ_row{r}_col{j}"

    # (Optional) If any target qubit j is ALSO listed in U, enforce its basis to
    # match basis_on_uid_to_protect[j] so that we don't contradict the injection scheme.
    for j in I & U:
        basis = basis_on_uid_to_protect[j]
        if basis == "X":
            model += x_var[j] == 1, f"FixBasisX_j{j}"
        elif basis == "Z":
            model += x_var[j] == 0, f"FixBasisZ_j{j}"

    # (B) Protection constraints:
    #
    #   For each target j ∈ I:
    #     - If basis_on_uid_to_protect[j] == "X":
    #         we want Z_j errors detected by fixed X-rows.
    #         So: p_j ≤ Σ_{r ∈ D_X(j)} fX[r].
    #
    #     - If basis_on_uid_to_protect[j] == "Z":
    #         we want X_j errors detected by fixed Z-rows.
    #         So: p_j ≤ Σ_{r ∈ D_Z(j)} fZ[r].
    #
    #   If D_X(j) or D_Z(j) is empty, that qubit simply cannot be protected
    #   under the given scheme, and p_j is forced to 0.
    never_protected_uids = []
    for j in I:
        basis = basis_on_uid_to_protect[j]

        if basis == "X":
            if D_X[j]:
                model += (p[j] <= pulp.lpSum(fX[r] for r in D_X[j] if r in fX), f"Protect_j{j}_basisX")
            else:
                # No X stabilizer touches j, cannot detect Z_j → no protection in X-basis
                model += p[j] == 0, f"NoProtect_j{j}_basisX"
                never_protected_uids.append(j)
            # print(f"uid={j}, {basis=}, {len(D_X[j])=}")
        elif basis == "Z":
            if D_Z[j]:
                model += (p[j] <= pulp.lpSum(fZ[r] for r in D_Z[j] if r in fZ), f"Protect_j{j}_basisZ")
            else:
                # No Z stabilizer touches j, cannot detect X_j → no protection in Z-basis
                model += p[j] == 0, f"NoProtect_j{j}_basisZ"
                never_protected_uids.append(j)
            # print(f"uid={j}, {basis=}, {len(D_Z[j])=}")
        else:
            raise ValueError(f"Invalid basis: {basis}")
    # print(f"{len(never_protected_uids)=}, {never_protected_uids=}")
    # -----------------------
    # Objective: maximize Σ p_j over all target qubits j ∈ I
    # -----------------------
    model += pulp.lpSum(p[j] for j in I), "TotalProtectedTargets"

    # -----------------------
    # Solve the MILP
    # -----------------------
    if solver is None:
        solver = pulp.PULP_CBC_CMD(msg=False)

    result_status = model.solve(solver)
    status_str = pulp.LpStatus[result_status]
    if status_str not in ("Optimal", "Feasible"):
        raise RuntimeError(f"PuLP solver did not find a feasible solution (status: {status_str}).")

    # -----------------------
    # Extract solution
    # -----------------------

    # Basis choices for U
    init_in_X = sorted(j for j in U if j in x_var and (x_var[j].varValue is not None) and x_var[j].varValue > 0.5)
    init_in_Z = sorted(j for j in U if j in x_var and (x_var[j].varValue is not None) and x_var[j].varValue <= 0.5)

    # Fixed stabilizer rows
    fixed_x_stab_ids = sorted(r for r, var in fX.items() if var.varValue is not None and var.varValue > 0.5)
    fixed_z_stab_ids = sorted(r for r, var in fZ.items() if var.varValue is not None and var.varValue > 0.5)

    # Targets that are actually protected
    protected_uids = sorted(j for j in I if p[j].varValue is not None and p[j].varValue > 0.5)

    # Any uninitialized qubits that didn't get a clear assignment
    still_uninit = sorted(U - set(init_in_X) - set(init_in_Z))

    return protected_uids, fixed_x_stab_ids, fixed_z_stab_ids, init_in_X, init_in_Z, still_uninit

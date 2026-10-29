"""Build the MSI circuit for generic CSS codes."""

import itertools
from dataclasses import dataclass
from typing import Iterable

import stim

from ..circuits.moment_schedule import insert_jit_resets, moments_to_circuit
from ..circuits.util import H_to_pauli_maps, measure_pauli_product
from ..codes.base_code import CSSSpec
from ..msi.init_cfgs.init_cfg import InitCfg


@dataclass(frozen=True)
class SyndromeLayout:
    """Information needed to reference syndrome measurement results in `se_circ` using rec offsets.

    `meas_per_cycle` counts *all* measurement results produced by `se_circ` (including any non-check measurements).
    For a check uid `u`, `rec_offset_in_cycle[u]` is the rec offset (negative integer) that refers to the
    measurement result of `u` at the end of one `se_circ` execution.
    """

    meas_per_cycle: int
    chk_to_meas_index_in_cycle: dict[int, int]
    chk_to_rec_offset_in_cycle: dict[int, int]


def infer_syndrome_layout(se_circ: stim.Circuit, check_uids: Iterable[int]) -> SyndromeLayout:
    """Infer where each check uid's syndrome appears in the measurement record of one SE cycle.

    This makes `build_msi_circ` robust to schedules that measure Z then X, X then Z, or any other ordering.
    The only requirement is that each `check_uid` is measured exactly once per execution of `se_circ`
    using single-qubit measurement instructions (e.g., MZ/MX/MRZ/MRX).
    """
    check_uids = list(check_uids)
    check_set = set(check_uids)

    meas_index: dict[int, int] = {}
    m = 0

    for inst in se_circ:
        data = stim.gate_data(inst.name)
        name = inst.name
        if name == "MPP":
            raise ValueError(
                "infer_syndrome_layout does not currently support MPP inside se_circ. "
                "If you need MPP-based SE, use a MeasurementTracker-style builder API."
            )
        if not data.produces_measurements:
            continue

        if isinstance(inst, stim.CircuitRepeatBlock):
            raise ValueError(f"Repeat block should not be in se_circ.")

        for t in inst.targets_copy():
            # Single-qubit measurement instructions should only have qubit targets (possibly inverted).
            if not t.is_qubit_target:
                raise ValueError(f"Unexpected non-qubit target {t} in measurement instruction {name}.")
            q = t.value
            if q in check_set:
                if q in meas_index:
                    raise ValueError(f"Check uid {q} is measured more than once in se_circ.")
                meas_index[q] = m
            m += 1

    missing = sorted(check_set - meas_index.keys())
    if missing:
        raise ValueError(f"se_circ did not measure all check_uids exactly once. Missing: {missing[:10]}")

    rec_offset = {u: meas_index[u] - m for u in check_uids}
    return SyndromeLayout(
        meas_per_cycle=m, chk_to_meas_index_in_cycle=meas_index, chk_to_rec_offset_in_cycle=rec_offset
    )


def _get_check_uids_in_mpp_order(code: CSSSpec) -> list[int]:
    """Map Hx/Hz row order to canonical circuit check UIDs."""
    layout = code.get_circ_layout()
    layout.validate_for(code)
    return list(layout.check_uids)


def init_ghz_states(c: stim.Circuit, ghz_uids_lst: list[list[int]]) -> None:
    """Initialize the ghz states on the support overlaps of the logical Xi and Zj operators."""
    cnots: list[tuple[int, int]] = []
    init_x_uids: list[int] = []
    init_z_uids: list[int] = []
    for ghz_uids in ghz_uids_lst:
        init_x_uids.append(ghz_uids[0])
        init_z_uids.extend(ghz_uids[1:])
        for uid in ghz_uids[1:]:
            cnots.append((ghz_uids[0], uid))
    assert set(init_x_uids) & set(init_z_uids) == set()
    c.append_operation("RX", init_x_uids)
    c.append_operation("RZ", init_z_uids)
    c.append_operation("TICK")
    c.append_operation("CNOT", list(itertools.chain(*cnots)))
    # c.append_operation("TICK") # should delegate the right of adding TICK to the caller


def build_msi_circ_v2(
    code: CSSSpec,
    se_circ: stim.Circuit,
    init_cfg: InitCfg,
    n_cycles: int,
    uid_to_coord: dict[int, tuple[int, int]] | None = None,
) -> stim.Circuit:
    """Generic and ideal MSI circuit builder, not using backend. This function is used to build the subcircuits of the MSI circuit.
    The noise is configured by Gidney's noise_model. See src/qldpc_msi/noise.py for more details.

    Args:
        se_circ: The ideal, **one round** syndrome extraction circuit that implements the reset, two-qubit gates, and measurement of each stabilizer check.
        Do not include detector setup in `se_circ`. This is done in this function.
        The convention of the uid of data qubits and check qubits is defined in `code`.
    """
    assert n_cycles >= 2, f"{n_cycles=}"
    init_cfg.verify()
    ghz_uids_lst = init_cfg.ghz_uids_lst
    dat_uids_init_in_x = init_cfg.dat_uids_init_in_x
    dat_uids_init_in_z = init_cfg.dat_uids_init_in_z
    inj_uids = init_cfg.inj_uids
    inj_lids = init_cfg.inj_lids
    fixed_stab_uids = init_cfg.fixed_stab_uids
    # print(f"fixed_stab_uids: {fixed_stab_uids}")

    # Determine how stabilizer checks map to measurement record positions.
    # This makes the circuit robust to SE schedules (e.g., Z-then-X vs X-then-Z).
    layout = code.get_circ_layout()
    check_uids_in_mpp_order = _get_check_uids_in_mpp_order(code)
    syndrome_layout = infer_syndrome_layout(se_circ, check_uids_in_mpp_order)

    lxs_stim, lzs_stim = code.get_logical_ops_stim()
    lxs_supp = [lx.to_numpy()[0].nonzero()[0].tolist() for lx in lxs_stim]
    lzs_supp = [lz.to_numpy()[1].nonzero()[0].tolist() for lz in lzs_stim]

    full_circ = stim.Circuit()
    if uid_to_coord is not None:
        for uid, coord in uid_to_coord.items():
            full_circ.append_operation("QUBIT_COORDS", uid, coord)

    # ------------------- 01. initialize GHZ states ------------------
    init_ghz_states(full_circ, ghz_uids_lst)

    # ------------------- 02. initialize data qubits in X/Z -------------------
    full_circ.append_operation("RX", dat_uids_init_in_x)
    full_circ.append_operation("RZ", dat_uids_init_in_z)

    # ------------------- 03. inject magic states -------------------
    inj_state = "Y"
    full_circ.append_operation(f"R{inj_state}", inj_uids)

    # ------------------- 04. first round of syndrome extraction, the fixed stabilizers must be +1 -------------------
    full_circ += se_circ
    for fixed_stab_uid in fixed_stab_uids:
        # `fixed_stab_uids` is currently interpreted as a stabilizer row id in canonical check order.
        chk_uid = layout.check_uids[fixed_stab_uid]
        full_circ.append_operation("DETECTOR", [stim.target_rec(syndrome_layout.chk_to_rec_offset_in_cycle[chk_uid])])

    # ------------------- 05. second round of syndrome extraction, two rounds of syndrome extraction should be the same -------------------

    repeat_circ = se_circ.copy()
    for chk_uid in check_uids_in_mpp_order:
        curr = syndrome_layout.chk_to_rec_offset_in_cycle[chk_uid]
        prev = curr - syndrome_layout.meas_per_cycle
        repeat_circ.append_operation("DETECTOR", [stim.target_rec(curr), stim.target_rec(prev)])
    repeat_circ.append_operation("TICK")
    full_circ += repeat_circ * (n_cycles - 1)

    # ------------------- 07. measure out all stabilizers using MPP -------------------
    pauli_maps = H_to_pauli_maps(code.Hx, "X") + H_to_pauli_maps(code.Hz, "Z")
    measure_pauli_product(full_circ, pauli_maps)
    # ------------------- 08. apply DETECTOR(MPP result and its previous SE result) -------------------
    # MPP appends one measurement result per stabilizer, in the same order as `pauli_maps`.
    # Compare each MPP outcome to the most recent SE outcome for the corresponding check.
    if len(pauli_maps) != len(check_uids_in_mpp_order):
        raise ValueError(
            "Mismatch between stabilizer count from (Hx,Hz) and check uid list. "
            f"{len(pauli_maps)=} vs {len(check_uids_in_mpp_order)=}"
        )
    num_mpp = len(pauli_maps)
    for i, chk_uid in enumerate(check_uids_in_mpp_order):
        mpp_rec = i - num_mpp
        se_rec = syndrome_layout.chk_to_rec_offset_in_cycle[chk_uid] - num_mpp
        full_circ.append_operation("DETECTOR", [stim.target_rec(mpp_rec), stim.target_rec(se_rec)])
    # ------------------- 09. measure Y observables using MPP -------------------
    ly_pauli_maps = []
    for i, (lx_supp, lz_supp) in enumerate(zip(lxs_supp, lzs_supp)):
        if i not in inj_lids:
            continue
        y_indices = list(set(lx_supp) & set(lz_supp))
        ly_pauli_map = (
            {j: "Y" for j in y_indices}
            | {j: "X" for j in lx_supp if j not in y_indices}
            | {j: "Z" for j in lz_supp if j not in y_indices}
        )
        ly_pauli_maps.append(ly_pauli_map)
    measure_pauli_product(full_circ, ly_pauli_maps)

    # ------------------- 10. include logical observables -------------------
    # TODO: use logical_obs_ids instead of range(len(logical_obs_ids))
    for i in range(len(ly_pauli_maps)):
        full_circ.append_operation("OBSERVABLE_INCLUDE", [stim.target_rec(i - len(ly_pauli_maps))], i)

    return full_circ


def build_msi_circ_v3(
    code: CSSSpec,
    se_moments: list[stim.Circuit],
    init_cfg: InitCfg,
    n_cycles: int,
    uid_to_coord: dict[int, tuple[int, int]] | None = None,
) -> stim.Circuit:
    """Generic and ideal MSI circuit builder, not using backend. This function is used to build the subcircuits of the MSI circuit.
    The noise is configured by Gidney's noise_model. See src/qldpc_msi/noise.py for more details.

    Args:
        se_circ: The ideal, **one round** syndrome extraction circuit that implements the reset, two-qubit gates, and measurement of each stabilizer check.
        Do not include detector setup in `se_circ`. This is done in this function.
        The convention of the uid of data qubits and check qubits is defined in `code`.
    """
    assert n_cycles >= 2, f"{n_cycles=}"
    init_cfg.verify()
    ghz_uids_lst = init_cfg.ghz_uids_lst
    dat_uids_init_in_x = init_cfg.dat_uids_init_in_x
    dat_uids_init_in_z = init_cfg.dat_uids_init_in_z
    inj_uids = init_cfg.inj_uids
    inj_lids = init_cfg.inj_lids
    fixed_stab_uids = init_cfg.fixed_stab_uids
    # print(f"fixed_stab_uids: {fixed_stab_uids}")

    # Determine how stabilizer checks map to measurement record positions.
    # This makes the circuit robust to SE schedules (e.g., Z-then-X vs X-then-Z).
    layout = code.get_circ_layout()
    check_uids_in_mpp_order = _get_check_uids_in_mpp_order(code)
    se_circ = moments_to_circuit(se_moments)

    syndrome_layout = infer_syndrome_layout(se_circ, check_uids_in_mpp_order)

    lxs_stim, lzs_stim = code.get_logical_ops_stim()
    lxs_supp = [lx.to_numpy()[0].nonzero()[0].tolist() for lx in lxs_stim]
    lzs_supp = [lz.to_numpy()[1].nonzero()[0].tolist() for lz in lzs_stim]

    full_circ = stim.Circuit()
    if uid_to_coord is not None:
        for uid, coord in uid_to_coord.items():
            full_circ.append_operation("QUBIT_COORDS", uid, coord)

    # ------------------- 01. initialize GHZ states ------------------
    init_ghz_states(full_circ, ghz_uids_lst)

    # ------------------- 02. initialize data qubits in X/Z -------------------
    # full_circ.append_operation("RX", dat_uids_init_in_x)
    # full_circ.append_operation("RZ", dat_uids_init_in_z)

    # ------------------- 03. inject magic states -------------------
    inj_state = "Y"
    # full_circ.append_operation(f"R{inj_state}", inj_uids)

    reset_gate_by_qubit: dict[int, str] = {}
    for q in dat_uids_init_in_x:
        _merge_reset_gate(reset_gate_by_qubit, q, "RX", src="init_cfg.dat_uids_init_in_x")
    for q in dat_uids_init_in_z:
        _merge_reset_gate(reset_gate_by_qubit, q, "RZ", src="init_cfg.dat_uids_init_in_z")
    for q in inj_uids:
        _merge_reset_gate(reset_gate_by_qubit, q, f"R{inj_state}", src="init_cfg.inj_uids")

    plan = insert_jit_resets(
        se_moments,
        reset_gate_by_qubit=reset_gate_by_qubit,
    )
    reset_and_1st_se_circ = moments_to_circuit(plan.moments)

    # ------------------- 04. first round of syndrome extraction, the fixed stabilizers must be +1 -------------------
    full_circ += reset_and_1st_se_circ
    for fixed_stab_uid in fixed_stab_uids:
        # `fixed_stab_uids` is currently interpreted as a stabilizer row id in canonical check order.
        chk_uid = layout.check_uids[fixed_stab_uid]
        full_circ.append_operation("DETECTOR", [stim.target_rec(syndrome_layout.chk_to_rec_offset_in_cycle[chk_uid])])

    # ------------------- 05. second round of syndrome extraction, two rounds of syndrome extraction should be the same -------------------

    repeat_circ = se_circ.copy()
    for chk_uid in check_uids_in_mpp_order:
        curr = syndrome_layout.chk_to_rec_offset_in_cycle[chk_uid]
        prev = curr - syndrome_layout.meas_per_cycle
        repeat_circ.append_operation("DETECTOR", [stim.target_rec(curr), stim.target_rec(prev)])
    repeat_circ.append_operation("TICK")
    full_circ += repeat_circ * (n_cycles - 1)

    # ------------------- 07. measure out all stabilizers using MPP -------------------
    pauli_maps = H_to_pauli_maps(code.Hx, "X") + H_to_pauli_maps(code.Hz, "Z")
    measure_pauli_product(full_circ, pauli_maps)
    # ------------------- 08. apply DETECTOR(MPP result and its previous SE result) -------------------
    # MPP appends one measurement result per stabilizer, in the same order as `pauli_maps`.
    # Compare each MPP outcome to the most recent SE outcome for the corresponding check.
    if len(pauli_maps) != len(check_uids_in_mpp_order):
        raise ValueError(
            "Mismatch between stabilizer count from (Hx,Hz) and check uid list. "
            f"{len(pauli_maps)=} vs {len(check_uids_in_mpp_order)=}"
        )
    num_mpp = len(pauli_maps)
    for i, chk_uid in enumerate(check_uids_in_mpp_order):
        mpp_rec = i - num_mpp
        se_rec = syndrome_layout.chk_to_rec_offset_in_cycle[chk_uid] - num_mpp
        full_circ.append_operation("DETECTOR", [stim.target_rec(mpp_rec), stim.target_rec(se_rec)])
    # ------------------- 09. measure Y observables using MPP -------------------
    ly_pauli_maps = []
    for i, (lx_supp, lz_supp) in enumerate(zip(lxs_supp, lzs_supp)):
        if i not in inj_lids:
            continue
        y_indices = list(set(lx_supp) & set(lz_supp))
        ly_pauli_map = (
            {j: "Y" for j in y_indices}
            | {j: "X" for j in lx_supp if j not in y_indices}
            | {j: "Z" for j in lz_supp if j not in y_indices}
        )
        ly_pauli_maps.append(ly_pauli_map)
    measure_pauli_product(full_circ, ly_pauli_maps)

    # ------------------- 10. include logical observables -------------------
    # TODO: use logical_obs_ids instead of range(len(logical_obs_ids))
    for i in range(len(ly_pauli_maps)):
        full_circ.append_operation("OBSERVABLE_INCLUDE", [stim.target_rec(i - len(ly_pauli_maps))], i)

    return full_circ


def build_msi_circ_v4(
    code: CSSSpec,
    se_1st_cycle: list[stim.Circuit],
    se_for_repeat: list[stim.Circuit],
    init_cfg: InitCfg,
    n_cycles: int,
    uid_to_coord: dict[int, tuple[int, int]] | None = None,
) -> stim.Circuit:
    """Generic and ideal MSI circuit builder, not using backend. This function is used to build the subcircuits of the MSI circuit.
    The noise is configured by Gidney's noise_model. See src/qldpc_msi/noise.py for more details.

    Args:
        se_circ: The ideal, **one round** syndrome extraction circuit that implements the reset, two-qubit gates, and measurement of each stabilizer check.
        Do not include detector setup in `se_circ`. This is done in this function.
        The convention of the uid of data qubits and check qubits is defined in `code`.
    """
    assert n_cycles >= 2, f"{n_cycles=}"
    init_cfg.verify()
    ghz_uids_lst = init_cfg.ghz_uids_lst
    dat_uids_init_in_x = init_cfg.dat_uids_init_in_x
    dat_uids_init_in_z = init_cfg.dat_uids_init_in_z
    inj_uids = init_cfg.inj_uids
    inj_lids = init_cfg.inj_lids
    fixed_stab_uids = init_cfg.fixed_stab_uids
    # print(f"fixed_stab_uids: {fixed_stab_uids}")

    # Determine how stabilizer checks map to measurement record positions.
    # This makes the circuit robust to SE schedules (e.g., Z-then-X vs X-then-Z).
    layout = code.get_circ_layout()
    check_uids_in_mpp_order = _get_check_uids_in_mpp_order(code)
    # se_circ = moments_to_circuit(se_moments)

    syndrome_layout = infer_syndrome_layout(moments_to_circuit(se_for_repeat), check_uids_in_mpp_order)

    lxs_stim, lzs_stim = code.get_logical_ops_stim()
    lxs_supp = [lx.to_numpy()[0].nonzero()[0].tolist() for lx in lxs_stim]
    lzs_supp = [lz.to_numpy()[1].nonzero()[0].tolist() for lz in lzs_stim]

    full_circ = stim.Circuit()
    if uid_to_coord is not None:
        for uid, coord in uid_to_coord.items():
            full_circ.append_operation("QUBIT_COORDS", uid, coord)

    # ------------------- 01. initialize GHZ states ------------------
    init_ghz_states(full_circ, ghz_uids_lst)

    # ------------------- 02. initialize data qubits in X/Z -------------------
    # full_circ.append_operation("RX", dat_uids_init_in_x)
    # full_circ.append_operation("RZ", dat_uids_init_in_z)

    # ------------------- 03. inject magic states -------------------
    inj_state = "Y"
    # full_circ.append_operation(f"R{inj_state}", inj_uids)

    reset_gate_by_qubit: dict[int, str] = {}
    for q in dat_uids_init_in_x:
        _merge_reset_gate(reset_gate_by_qubit, q, "RX", src="init_cfg.dat_uids_init_in_x")
    for q in dat_uids_init_in_z:
        _merge_reset_gate(reset_gate_by_qubit, q, "RZ", src="init_cfg.dat_uids_init_in_z")
    for q in inj_uids:
        _merge_reset_gate(reset_gate_by_qubit, q, f"R{inj_state}", src="init_cfg.inj_uids")

    plan = insert_jit_resets(
        se_1st_cycle,
        reset_gate_by_qubit=reset_gate_by_qubit,
    )
    reset_and_1st_se_circ = moments_to_circuit(plan.moments)

    # ------------------- 04. first round of syndrome extraction, the fixed stabilizers must be +1 -------------------
    full_circ += reset_and_1st_se_circ
    for fixed_stab_uid in fixed_stab_uids:
        # ! `fixed_stab_uids` is currently interpreted as a stabilizer row id in canonical check order.
        chk_uid = layout.check_uids[fixed_stab_uid]
        full_circ.append_operation("DETECTOR", [stim.target_rec(syndrome_layout.chk_to_rec_offset_in_cycle[chk_uid])])

    # ------------------- 05. second round of syndrome extraction, two rounds of syndrome extraction should be the same -------------------

    repeat_circ = moments_to_circuit(se_for_repeat).copy()
    for chk_uid in check_uids_in_mpp_order:
        curr = syndrome_layout.chk_to_rec_offset_in_cycle[chk_uid]
        prev = curr - syndrome_layout.meas_per_cycle
        repeat_circ.append_operation("DETECTOR", [stim.target_rec(curr), stim.target_rec(prev)])
    repeat_circ.append_operation("TICK")
    full_circ += repeat_circ * (n_cycles - 1)

    # ------------------- 07. measure out all stabilizers using MPP -------------------
    pauli_maps = H_to_pauli_maps(code.Hx, "X") + H_to_pauli_maps(code.Hz, "Z")
    measure_pauli_product(full_circ, pauli_maps)
    # ------------------- 08. apply DETECTOR(MPP result and its previous SE result) -------------------
    # MPP appends one measurement result per stabilizer, in the same order as `pauli_maps`.
    # Compare each MPP outcome to the most recent SE outcome for the corresponding check.
    if len(pauli_maps) != len(check_uids_in_mpp_order):
        raise ValueError(
            "Mismatch between stabilizer count from (Hx,Hz) and check uid list. "
            f"{len(pauli_maps)=} vs {len(check_uids_in_mpp_order)=}"
        )
    num_mpp = len(pauli_maps)
    for i, chk_uid in enumerate(check_uids_in_mpp_order):
        mpp_rec = i - num_mpp
        se_rec = syndrome_layout.chk_to_rec_offset_in_cycle[chk_uid] - num_mpp
        full_circ.append_operation("DETECTOR", [stim.target_rec(mpp_rec), stim.target_rec(se_rec)])
    # ------------------- 09. measure Y observables using MPP -------------------
    ly_pauli_maps = []
    for i, (lx_supp, lz_supp) in enumerate(zip(lxs_supp, lzs_supp)):
        if i not in inj_lids:
            continue
        y_indices = list(set(lx_supp) & set(lz_supp))
        ly_pauli_map = (
            {j: "Y" for j in y_indices}
            | {j: "X" for j in lx_supp if j not in y_indices}
            | {j: "Z" for j in lz_supp if j not in y_indices}
        )
        ly_pauli_maps.append(ly_pauli_map)
    measure_pauli_product(full_circ, ly_pauli_maps)

    # ------------------- 10. include logical observables -------------------
    # TODO: use logical_obs_ids instead of range(len(logical_obs_ids))
    for i in range(len(ly_pauli_maps)):
        full_circ.append_operation("OBSERVABLE_INCLUDE", [stim.target_rec(i - len(ly_pauli_maps))], i)

    return full_circ


def _merge_reset_gate(reset_gate_by_qubit: dict[int, str], q: int, gate: str, *, src: str) -> None:
    prev = reset_gate_by_qubit.get(q)
    if prev is None:
        reset_gate_by_qubit[q] = gate
        return
    if prev != gate:
        raise ValueError(f"Conflicting reset gates for qubit {q}: {prev} vs {gate} (from {src}).")

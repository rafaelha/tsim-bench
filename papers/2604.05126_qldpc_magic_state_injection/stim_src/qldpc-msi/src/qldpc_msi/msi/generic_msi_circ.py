"""Build the MSI circuit for generic CSS codes."""

import itertools

import stim

# TODO: remove the dependency on backend
from ..circuits.backends import BaseBackend
from ..circuits.util import H_to_pauli_maps, measure_pauli_product
from ..codes.base_code import CSSSpec
from ..msi.init_cfgs.init_cfg import InitCfg


def init_ghz_states(c: stim.Circuit, ghz_uids_lst: list[list[int]], backend: BaseBackend | None = None) -> None:
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
    if backend is not None:
        backend.apply_init_err(c, init_x_uids, "X")
    c.append_operation("RZ", init_z_uids)
    if backend is not None:
        backend.apply_init_err(c, init_z_uids, "Z")
    c.append_operation("TICK")
    c.append_operation("CNOT", list(itertools.chain(*cnots)))
    if backend is not None:
        backend.apply_depol2_err(c, cnots)
    c.append_operation("TICK")


def build_msi_circ(
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

    lxs_stim, lzs_stim = code.get_logical_ops_stim()
    lxs_supp = [lx.to_numpy()[0].nonzero()[0].tolist() for lx in lxs_stim]
    lzs_supp = [lz.to_numpy()[1].nonzero()[0].tolist() for lz in lzs_stim]

    full_circ = stim.Circuit()
    if uid_to_coord is not None:
        for uid, coord in uid_to_coord.items():
            full_circ.append_operation("QUBIT_COORDS", uid, coord)

    # ------------------- 01. initialize data qubits in X/Z -------------------

    full_circ.append_operation("RX", dat_uids_init_in_x)
    # backend.apply_init_err(full_circ, dat_uids_init_in_x, "X")
    full_circ.append_operation("RZ", dat_uids_init_in_z)
    # backend.apply_init_err(full_circ, dat_uids_init_in_z, "Z")

    full_circ.append_operation("TICK")

    # ------------------- 02. initialize GHZ states -------------------
    init_ghz_states(full_circ, ghz_uids_lst)

    # ------------------- 03. inject magic states -------------------
    inj_state = "Y"
    full_circ.append_operation(f"R{inj_state}", inj_uids)
    # backend.apply_init_err(full_circ, inj_uids, inj_state)

    full_circ.append_operation("TICK")

    # ------------------- 04. first round of syndrome extraction, the fixed stabilizers must be +1 -------------------
    # synd_ext_one_cycle = se_circ_fn(backend)
    full_circ += se_circ
    for fixed_stab_uid in fixed_stab_uids:
        full_circ.append_operation("DETECTOR", [stim.target_rec(fixed_stab_uid - code.num_checks)])
    full_circ.append_operation("TICK")

    # ------------------- 05. second round of syndrome extraction, two rounds of syndrome extraction should be the same -------------------

    repeat_circ = se_circ.copy()
    for stab_uid in range(code.num_checks):
        prev = stab_uid - 2 * code.num_checks
        curr = stab_uid - code.num_checks
        repeat_circ.append_operation("DETECTOR", [stim.target_rec(curr), stim.target_rec(prev)])
    repeat_circ.append_operation("TICK")
    full_circ += repeat_circ * (n_cycles - 1)

    # ------------------- 07. measure out all stabilizers using MPP -------------------
    pauli_maps = H_to_pauli_maps(code.Hx, "X") + H_to_pauli_maps(code.Hz, "Z")
    measure_pauli_product(full_circ, pauli_maps)
    # ------------------- 08. apply DETECTOR(MPP result and its previous SE result) -------------------
    for stab_uid in range(code.num_checks):
        prev = stab_uid - 2 * code.num_checks
        curr = stab_uid - code.num_checks
        full_circ.append_operation("DETECTOR", [stim.target_rec(curr), stim.target_rec(prev)])
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

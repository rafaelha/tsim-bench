import itertools
from typing import override

import stim

from ..circuits.backends import BaseBackend
from ..log_util import get_logger
from .code import BBCode

logger = get_logger("INFO")
# logger = get_logger("DEBUG")
assert logger is not None


class _CXType:
    def __init__(self, src_qtype: str, dst_qtype: str, matrix_i: int):
        self.src_qtype = src_qtype
        self.dst_qtype = dst_qtype
        self.matrix_i = matrix_i


def get_cx_orders_for_two_interleaved() -> list[list[_CXType]]:
    """IBM paper, Fig. 5. depth 7."""
    x_chk_to_dst_and_mat_id = [("IDLE", -1), ("L", 2), ("R", 2), ("R", 1), ("R", 3), ("L", 1), ("L", 3)]
    z_chk_to_dst_and_mat_id = [("R", 1), ("R", 3), ("L", 1), ("L", 2), ("L", 3), ("R", 2), ("IDLE", -1)]
    cx_orders: list[list[_CXType]] = []
    for pass_i, ((x_dst, x_mat_i), (z_dst, z_mat_i)) in enumerate(
        zip(x_chk_to_dst_and_mat_id, z_chk_to_dst_and_mat_id)
    ):
        if pass_i == 0:
            cx_types = [_CXType("Z", z_dst, z_mat_i - 1)]
        elif pass_i == 6:
            cx_types = [_CXType("X", x_dst, x_mat_i - 1)]
        else:
            cx_types = [_CXType("X", x_dst, x_mat_i - 1), _CXType("Z", z_dst, z_mat_i - 1)]
        cx_orders.append(cx_types)
    return cx_orders


class BaseMemSimulator:
    """Standard circuit-level, depolarizing noise model threshold simulator.

    Three types of ids are used to describe all kinds of qubits in the simulator:
    1. (qubit type, qubit id): in BaseLayout.qubit_to_coord[qtype][qid].
    2. x_check_ids / z_check_ids & data_ids: correspond to rows & cols of the parity-check matrix, respectively.
    3. unique ids: in stim circuit, unique identifier for each qubit.
    """

    def __init__(
        self,
        code: BBCode,
        n_cycles: int,
        backend: BaseBackend,
    ):
        """Depolarizing noise model threshold simulator.

        Args:
            code (BBCode): Bicycle bi-variate code
            layout (BaseLayout): Layout of the code
            n_cycles (int): Number of times to repeat the syndrome extraction circuit. Usually set to d of the code.
        """
        self.code = code
        self.n_cycles = n_cycles
        self.backend = backend

        # track the previous absolute measurement index for each qubit (including check and data qubits). Dynamic.
        # aim for setting detectors
        self._uid_to_prev_meas_abs_idx = [-1] * (self.code.num_checks + self.code.n)
        self._uid_to_curr_meas_abs_idx = [-1] * (self.code.num_checks + self.code.n)

    def build_circ(
        self,
        logical_op_type: str,
        logical_supps: list[list[int]],
        no_det_stab_dat_meas: bool = False,
        ideal_dat_meas: bool = False,
    ) -> stim.Circuit:
        """Build the circuit for threshold simulation."""
        assert logical_op_type in ["Z", "X"], "only Z logical operator is supported for now"
        c = stim.Circuit()
        c.append_operation(f"R{logical_op_type}", self.code.all_dat_uids)
        # c.append_operation(f"R", self.code.all_chk_uids)
        self.apply_all_checks(c)
        c = c.without_noise()
        # logger.info(f"Circuit after state prep:\n{self.c}")
        c.append_operation("TICK")
        for cycle_i in range(self.n_cycles):
            # self.c.append("SHIFT_COORDS", [], (0, 0, 1))  # cycle += 1
            self.apply_all_checks(c)
            self.apply_all_detectors(c)
            c.append_operation("TICK")

        logger.debug(f"Circuit after parity checks:\n{c}")
        logger.debug(f"Number of measurements: {c.num_measurements}")

        self.apply_meas_and_record_abs_ids(c, logical_op_type, self.code.all_dat_uids, ideal_dat_meas)
        if not no_det_stab_dat_meas:
            self.apply_detectors_of_final_cycle(c, logical_op_type)
        self.apply_observables(c, logical_supps)
        return c

    def apply_all_checks(self, c: stim.Circuit) -> None:
        """Default implementation of applying all checks of one cycle. Assume we can apply checks by multiple passes."""
        raise NotImplementedError()

    def apply_all_detectors(self, c: stim.Circuit):
        for chk_type in ["X", "Z"]:
            self.apply_detectors_of_one_type(c, chk_type)

    def apply_detectors_of_one_type(self, c: stim.Circuit, chk_type: str):
        logger.debug(f"Applying detectors of type {chk_type}, num_measurements: {c.num_measurements}")
        chk_uids = self.code.select_uids(chk_type)
        for _, chk_uid in enumerate(chk_uids):
            prev_meas_idx = self._uid_to_prev_meas_abs_idx[chk_uid]
            curr_meas_idx = self._uid_to_curr_meas_abs_idx[chk_uid]
            assert prev_meas_idx >= 0 and prev_meas_idx < c.num_measurements
            assert curr_meas_idx >= 0 and curr_meas_idx < c.num_measurements
            logger.debug(f"Detector {chk_uid}: {prev_meas_idx=}, {curr_meas_idx=}")
            prev_meas_rel_idx = self.meas_abs_id_to_rel_id(c, prev_meas_idx)
            curr_meas_rel_idx = self.meas_abs_id_to_rel_id(c, curr_meas_idx)
            logger.debug(f"Detector {chk_uid}: {prev_meas_rel_idx=}, {curr_meas_rel_idx=}")
            # annotation is used to record the (row, col, round_id) of the detector
            # TODO: for unknown reason, we fix round_id to be 0
            # annotation = (*self._UID_TO_COORD[chk_uid], 0)
            annotation = None
            c.append_operation(
                "DETECTOR", [stim.target_rec(prev_meas_rel_idx), stim.target_rec(curr_meas_rel_idx)], annotation
            )

    def apply_observables(self, c: stim.Circuit, logical_supps: list[list[int]]):
        """Apply OBSERVABLE_INCLUDE to measure the logical operators.

        Each logical operator is a (n,) binary vector, then the support of the logical operator
        is the set {i | logical[i] == 1}.
        We will apply OBSERVABLE_INCLUDE to the support of the logical operator.
        """
        assert len(logical_supps) == self.code.k, f"length of logicals is not {self.code.k}"
        for logical_id, supp_uids in enumerate(logical_supps):
            meas_rel_ids_of_supp = [
                self.meas_abs_id_to_rel_id(c, self._uid_to_curr_meas_abs_idx[uid]) for uid in supp_uids
            ]
            c.append_operation(
                "OBSERVABLE_INCLUDE", [stim.target_rec(rel_id) for rel_id in meas_rel_ids_of_supp], logical_id
            )

    def apply_meas_and_record_abs_ids(
        self, c: stim.Circuit, meas_base: str, uids: list[int], ideal_dat_meas: bool = False
    ):
        assert meas_base in ["X", "Z"]
        prev_n_meas = c.num_measurements
        if not ideal_dat_meas:
            self.backend.apply_meas_err(c, uids, meas_base)
        c.append_operation(f"M{meas_base}", uids)
        for i, uid in enumerate(uids):
            self._uid_to_prev_meas_abs_idx[uid] = self._uid_to_curr_meas_abs_idx[uid]
            self._uid_to_curr_meas_abs_idx[uid] = prev_n_meas + i

    def apply_detectors_of_final_cycle(self, c: stim.Circuit, logical_op_type: str):
        chk_uids = self.code.select_uids(logical_op_type)
        mat = self.code.Hx if logical_op_type == "X" else self.code.Hz
        for chk_uid, row in zip(chk_uids, mat):
            dat_uids = row.nonzero()[0].tolist()
            rel_ids = [
                self.meas_abs_id_to_rel_id(c, self._uid_to_curr_meas_abs_idx[uid]) for uid in dat_uids + [chk_uid]
            ]
            c.append_operation("DETECTOR", [stim.target_rec(rel_id) for rel_id in rel_ids])

    def meas_abs_id_to_rel_id(self, c: stim.Circuit, meas_abs_id: int) -> int:
        return meas_abs_id - c.num_measurements


class BBMemSimulator(BaseMemSimulator):
    """Standard circuit-level, depolarizing noise model threshold simulator.

    Three types of ids are used to describe all kinds of qubits in the simulator:
    1. (qubit type, qubit id): in BaseLayout.qubit_to_coord[qtype][qid].
    2. x_check_ids / z_check_ids & data_ids: correspond to rows & cols of the parity-check matrix, respectively.
    3. unique ids: in stim circuit, unique identifier for each qubit.
    """

    def __init__(
        self,
        code: BBCode,
        n_cycles: int,
        backend: BaseBackend,
    ):
        """Depolarizing noise model threshold simulator.

        Args:
            code (BBCode): Bicycle bi-variate code
            layout (BaseLayout): Layout of the code
            n_cycles (int): Number of times to repeat the syndrome extraction circuit. Usually set to d of the code.
        """
        super().__init__(code, n_cycles, backend)
        self.code = code

    def _apply_all_cx_of_same_type(self, c: stim.Circuit, cx_type: _CXType):
        assert cx_type.src_qtype in ["X", "Z"]
        cnots = []
        for src_qid in range(self.code.lm):
            dst_qid = self.code._get_interacting_qids(cx_type.src_qtype, src_qid, cx_type.dst_qtype, cx_type.matrix_i)[
                0
            ]
            chk_type = cx_type.src_qtype
            chk_uid = self.code._qtype_and_qid_to_uid(cx_type.src_qtype, src_qid)
            dat_uid = self.code._qtype_and_qid_to_uid(cx_type.dst_qtype, dst_qid)
            if chk_type == "X":
                cnots.append((chk_uid, dat_uid))
            else:
                cnots.append((dat_uid, chk_uid))

        seen_uids = set()
        for chk_uid, dat_uid in cnots:
            assert chk_uid not in seen_uids and dat_uid not in seen_uids, f"CNOT {chk_uid} {dat_uid} is repeated"
            seen_uids.add(chk_uid)
            seen_uids.add(dat_uid)

        c.append_operation("CNOT", list(itertools.chain(*cnots)))
        self.backend.apply_depol2_err(c, cnots)

    def _get_cx_of_same_type(self, cx_type: _CXType) -> list[tuple[int, int]]:
        assert cx_type.src_qtype in ["X", "Z"]
        cnots = []
        for src_qid in range(self.code.lm):
            dst_qid = self.code._get_interacting_qids(cx_type.src_qtype, src_qid, cx_type.dst_qtype, cx_type.matrix_i)[
                0
            ]
            chk_type = cx_type.src_qtype
            chk_uid = self.code._qtype_and_qid_to_uid(cx_type.src_qtype, src_qid)
            dat_uid = self.code._qtype_and_qid_to_uid(cx_type.dst_qtype, dst_qid)
            if chk_type == "X":
                cnots.append((chk_uid, dat_uid))
            else:
                cnots.append((dat_uid, chk_uid))

        seen_uids = set()
        for chk_uid, dat_uid in cnots:
            assert chk_uid not in seen_uids and dat_uid not in seen_uids, f"CNOT {chk_uid} {dat_uid} is repeated"
            seen_uids.add(chk_uid)
            seen_uids.add(dat_uid)

        return cnots

    @override
    def apply_all_checks(self, c: stim.Circuit, remove_meas: bool = False) -> None:
        """Apply CNOTs in the order shown in IBM paper, Fig. 5.
        Assume all the check qubits are reset to |0> state.
        """

        # IBM paper, Fig. 5 order of CNOTs
        cx_orders = get_cx_orders_for_two_interleaved()

        _X_CHK_UIDS = self.code.select_uids("X")
        _Z_CHK_UIDS = self.code.select_uids("Z")
        c.append_operation("RX", _X_CHK_UIDS)
        self.backend.apply_init_err(c, _X_CHK_UIDS, "X")

        c.append_operation("TICK")

        c.append_operation("RZ", _Z_CHK_UIDS)
        self.backend.apply_init_err(c, _Z_CHK_UIDS, "Z")

        c.append_operation("TICK")
        for round_i, cx_types in enumerate(cx_orders):
            for cx_type in cx_types:
                self._apply_all_cx_of_same_type(c, cx_type)
            c.append_operation("TICK")

        # self.backend.apply_idle_err(c, self.code.all_chk_uids)
        # c.append_operation("H", self.code.select_uids("X"))
        if not remove_meas:
            self.apply_meas_and_record_abs_ids(c, "X", _X_CHK_UIDS)
            self.apply_meas_and_record_abs_ids(c, "Z", _Z_CHK_UIDS)

    def apply_all_checks_compactly(
        self,
        c: stim.Circuit,
        remove_meas: bool = False,
        *,
        dat_uid_to_reset_basis: dict[int, str] | None = None,
    ) -> None:
        """Apply CNOTs in the order shown in IBM paper, Fig. 5 and Eq. (9).

        Apply SE compactly, i.e., between two `TICK`s, we fill in the time slots as much as possible to minimize the idling errors.
        In this way, we can use Gidney's noise_model to insert single-qubit idling errors between two `TICK`s if there are no operations on those qubits.
        Note that if a physical qubit is involved in more than one gate between two `TICK`s, Gidney's noise_model will raise an error.
        This is a good sanity check.

        For surface codes, Rx/Rz are applied simultaneously, and so does Mx/Mz.
        For BB codes, Rx/Rz are not applied simultaneously, and neither do Mx/Mz.
        See IBM paper, Fig. 5 for the order of CNOTs and Eq. (9) for specific CNOT pairs.

        Also see Tour de Gross, Figure 4, caption:
        - "It should be understood that the Z check qubit is initialized in timestep 0 and measured in timestep 7."
        - "Similarly, the X check qubit is initialized in timestep 1 and measured in timestep 8."
        - "While the X check is measured, the Z check is reinitialized for the next syndrome cycle."

        Notes:
        - The first TICK and last TICK are not included in what returns. I.e., we will not start/end with a TICK.
        We leave the flexibility to the caller since we might want to append/insert other operations before/after the returned circuit.
        """

        # IBM paper, Fig. 5 order of CNOTs
        cx_orders = get_cx_orders_for_two_interleaved()

        _X_CHK_UIDS = self.code.select_uids("X")
        _Z_CHK_UIDS = self.code.select_uids("Z")

        # timestep 0
        c.append_operation("RZ", _Z_CHK_UIDS)
        self.backend.apply_init_err(c, _Z_CHK_UIDS, "Z")
        c.append_operation("TICK")

        # timestep 1
        c.append_operation("RX", _X_CHK_UIDS)
        self.backend.apply_init_err(c, _X_CHK_UIDS, "X")

        cx_type = cx_orders[0][0]
        cnots = self._get_cx_of_same_type(cx_type)
        # print(f"cnots: {cnots}")
        # print(f"dat_uid_to_reset_basis: {dat_uid_to_reset_basis}")
        remaining_cnots = []
        if dat_uid_to_reset_basis is not None:
            for ctrl, trgt in cnots:
                if ctrl in dat_uid_to_reset_basis and dat_uid_to_reset_basis[ctrl] == "Z":
                    continue
                if trgt in dat_uid_to_reset_basis and dat_uid_to_reset_basis[trgt] == "X":
                    continue
                remaining_cnots.append((ctrl, trgt))
        else:
            remaining_cnots = cnots

        print(f"remaining_cnots/first_layer: {len(remaining_cnots)}/{len(cnots)}")
        # print(f"remaining_cnots: {remaining_cnots}")
        c.append_operation("CNOT", list(itertools.chain(*remaining_cnots)))
        self.backend.apply_depol2_err(c, remaining_cnots)
        c.append_operation("TICK")

        # timestep 2 to 6, totally 5 rounds where each round has 2 types of CNOTs
        for cx_types in cx_orders[1:-1]:
            for cx_type in cx_types:
                self._apply_all_cx_of_same_type(c, cx_type)
            c.append_operation("TICK")

        # timestep 7
        if not remove_meas:
            self.apply_meas_and_record_abs_ids(c, "Z", _Z_CHK_UIDS)

        cx_type = cx_orders[-1][0]
        self._apply_all_cx_of_same_type(c, cx_type)
        c.append_operation("TICK")

        # timestep 8
        if not remove_meas:
            self.apply_meas_and_record_abs_ids(c, "X", _X_CHK_UIDS)

        # do not apply TICK here and delegate the right to the caller

from abc import abstractmethod

import galois
import numpy as np
import stim
from numpy.typing import NDArray

from ..code import BBCode
from ..ring import Monomial


class LogicalOp:
    """General logical operator.
    It can be a Pauli operator, or a product of Pauli operators.
    """

    ps: stim.PauliString

    def __init__(self, ps: stim.PauliString):
        self.ps = ps

    def to_symp_vec(self) -> galois.GF2:
        xs, zs = self.ps.to_numpy()
        vec = np.vstack([xs, zs])
        return galois.GF2(vec)

    def commutes_with(self, other: "LogicalOp") -> bool:
        return self.ps.commutes(other.ps)


class BBLogicalQubit(LogicalOp):
    def __init__(
        self,
        alpha: Monomial,
        l: int,
        m: int,
        lop_t: str,
        primed: bool,
        l_qubits: list[Monomial],
        r_qubits: list[Monomial],
    ):
        """Logical qubit of BB code. Only support X and Z for now.
        If for general logical operator, use LogicalOp instead.

        Args:
            alpha (Monomial): alpha in the logical operator
            l (int): l of the code
            m (int): m of the code
            lop_t (str): "X" or "Z"
            primed (bool): whether the logical operator is in the primed block
            l_qubits (list[Monomial]): list of L qubits
            r_qubits (list[Monomial]): list of R qubits
        """
        assert lop_t in ["X", "Z"], "only support X and Z for now"
        self.alpha = alpha
        self.l = l
        self.m = m
        self.lop_t = lop_t
        self.primed = primed
        # sort the qubits by their (x, y) exponents
        self.l_qubits = sorted([l_qubit for l_qubit in l_qubits], key=lambda mono: mono.as_tuple())
        self.r_qubits = sorted([r_qubit for r_qubit in r_qubits], key=lambda mono: mono.as_tuple())
        vec = self.to_vec()
        if lop_t == "X":
            xs, zs = np.zeros(2 * self.l * self.m, dtype=np.bool_), np.array(vec, dtype=np.bool_)
        else:
            xs, zs = np.array(vec, dtype=np.bool_), np.zeros(2 * self.l * self.m, dtype=np.bool_)
        assert xs.shape == zs.shape == (2 * self.l * self.m,)
        ps = stim.PauliString.from_numpy(xs=xs, zs=zs)
        super().__init__(ps)

    def commutes_with(self, other: "BBLogicalQubit") -> bool:
        assert self.l == other.l and self.m == other.m
        if self.lop_t == other.lop_t:
            return True
        # assert sorted([self.lop_t, other.lop_t]) == ["X", "Z"], "only support X and Z for now"
        l_overlap, r_overlap = self.get_support_overlap(other)
        return (len(l_overlap) + len(r_overlap)) % 2 == 0

    def get_support_overlap(self, other: "BBLogicalQubit") -> tuple[list[Monomial], list[Monomial]]:
        """Get the overlap of the support of two logical operators.
        Return two lists, the first list contains the overlap of the L qubits,
        the second list contains the overlap of the R qubits.
        """
        l_overlap = []
        r_overlap = []
        for l_qubit in self.l_qubits:
            if l_qubit in other.l_qubits:
                l_overlap.append(l_qubit)
        for r_qubit in self.r_qubits:
            if r_qubit in other.r_qubits:
                r_overlap.append(r_qubit)
        return l_overlap, r_overlap

    def has_same_support_with(self, other: "BBLogicalQubit") -> bool:
        # print(f"{self.l_qubits=}\n{other.l_qubits=}")
        assert len(self.l_qubits) == len(other.l_qubits)
        assert len(self.r_qubits) == len(other.r_qubits)

        for q1, q2 in zip(self.l_qubits, other.l_qubits):
            if q1.as_tuple() != q2.as_tuple():
                return False
        for q1, q2 in zip(self.r_qubits, other.r_qubits):
            if q1.as_tuple() != q2.as_tuple():
                return False
        return True

    def get_logical_Y_op(self, other: "BBLogicalQubit") -> "LogicalOp":
        """Assume self and other are X (Z) and Z (X) logical operators
        of the same logical qubit.

        Returns:
            LogicalOp: the logical Y operator
        """
        assert self.l == other.l and self.m == other.m
        assert sorted([self.lop_t, other.lop_t]) == ["X", "Z"], "only support X and Z"
        assert self.primed == other.primed, "only support same primedness"
        return LogicalOp(self.ps * other.ps)

    def joint_tensor(self, other: "BBLogicalQubit") -> "BBLogicalQubit":
        assert self.l == other.l and self.m == other.m
        assert self.lop_t == other.lop_t, "only support joint XX or ZZ"
        assert self.primed == (not other.primed), "only support one in primed and the other in unprimed"
        # ! here lop_t, alpha and primed are just a placeholder, we don't care about it
        return BBLogicalQubit(
            self.alpha * other.alpha,
            self.l,
            self.m,
            self.lop_t,
            self.primed,
            self.l_qubits + other.l_qubits,
            self.r_qubits + other.r_qubits,
        )

    def to_vec(self) -> galois.GF2:
        """Return a length-n vector on F2.
        First n/2 elements are for l_qubits, last n/2 elements are for r_qubits.
        """
        vec = np.zeros(self.l * self.m * 2, dtype=np.int_)
        lm = self.l * self.m
        for q in self.l_qubits:
            idx = q.xexp * self.m + q.yexp
            vec[idx] = 1
        for q in self.r_qubits:
            idx = q.xexp * self.m + q.yexp + lm
            vec[idx] = 1
        return galois.GF2(vec)

    def to_symplectic_vec(self) -> galois.GF2:
        """Return a length-2n vector on F2. First n elements are X part,
        and last n elements are Z part.
        """
        vec = self.to_vec()
        if self.lop_t == "X":
            return galois.GF2(np.hstack([vec, galois.GF2.Zeros(2 * self.l * self.m)]))
        else:
            return galois.GF2(np.hstack([galois.GF2.Zeros(2 * self.l * self.m), vec]))

    def apply_grid_translation_aut_gate(self, mono: Monomial) -> "BBLogicalQubit":
        """Apply a grid translation automorphism to the logical operator,
        which is equivalent to multiplying all the L and R qubits by `mono`.
        """
        new_l_qubits = [l_qubit * mono for l_qubit in self.l_qubits]
        new_r_qubits = [r_qubit * mono for r_qubit in self.r_qubits]
        return BBLogicalQubit(self.alpha * mono, self.l, self.m, self.lop_t, self.primed, new_l_qubits, new_r_qubits)

    @property
    def n_qubits(self) -> int:
        return len(self.l_qubits) + len(self.r_qubits)

    def __repr__(self):
        primed_str = "'" if self.primed else " "
        ss = f"[Logical {self.lop_t}{primed_str}_{self.alpha} Op]\n"
        ss += f"l_qubits={self.l_qubits}\n"
        ss += f"r_qubits={self.r_qubits}\n"
        return ss


class BaseBBAut:
    def __init__(self, code: BBCode):
        self.code = code
        self.ring = code.ring

        self.n_matrices = 3
        self.AiAjT = {
            (i, j): self.ring.monomial(*self.code.a_pows[i]) * self.ring.monomial(*self.code.a_pows[j]).T()
            for i in range(self.n_matrices)
            for j in range(self.n_matrices)
            if i != j
        }

        self.BiBjT = {
            (i, j): self.ring.monomial(*self.code.b_pows[i]) * self.ring.monomial(*self.code.b_pows[j]).T()
            for i in range(self.n_matrices)
            for j in range(self.n_matrices)
            if i != j
        }

        self.trans = list(self.AiAjT.values()) + list(self.BiBjT.values())
        assert len(self.trans) == self.n_matrices * 2 * 2

    @abstractmethod
    def find_valid_alphas(self, lop_t: str, primed: bool) -> list[Monomial]:
        raise NotImplementedError()

    @abstractmethod
    def get_logical_qubit(self, alpha: Monomial, lop_t: str, primed: bool) -> BBLogicalQubit:
        raise NotImplementedError()

    @staticmethod
    def get_equiv_mat(all_lops: list[BBLogicalQubit]) -> NDArray[np.int_]:
        equiv_mat = np.zeros((len(all_lops), len(all_lops)), dtype=np.int_)
        for i, op1 in enumerate(all_lops):
            for j, op2 in enumerate(all_lops):
                if op1.has_same_support_with(op2):
                    equiv_mat[i, j] = 1
        # print(f"{equiv_mat=}")
        assert BaseBBAut.check_symmetry(equiv_mat), "equiv_mat is not symmetric"
        return equiv_mat

    @staticmethod
    def check_symmetry(mat: NDArray[np.int_]) -> bool:
        return bool(np.all(mat == mat.T))

    @staticmethod
    def get_comm_mat(all_lops: list[BBLogicalQubit]) -> NDArray[np.int_]:
        comm_mat = np.zeros((len(all_lops), len(all_lops)), dtype=np.int_)
        for i, op1 in enumerate(all_lops):
            for j, op2 in enumerate(all_lops):
                if op1.commutes_with(op2):
                    comm_mat[i, j] = 1
        assert BaseBBAut.check_symmetry(comm_mat), "comm_mat is not symmetric"
        return comm_mat

    def get_logical_qubits(self, lop_t: str, primed: bool | None = None) -> list[BBLogicalQubit]:
        assert lop_t in ["X", "Z"], "only support X and Z for now"
        if primed is None:
            return self.get_logical_qubits(lop_t, False) + self.get_logical_qubits(lop_t, True)
        alphas = self.find_valid_alphas(lop_t, primed)
        return [self.get_logical_qubit(alpha, lop_t, primed) for alpha in alphas]

    def get_all_logical_qubits(
        self,
    ) -> tuple[list[BBLogicalQubit], list[BBLogicalQubit], list[BBLogicalQubit], list[BBLogicalQubit]]:
        """
        Returns all logical qubits for the BB code, in order of lx_unprimes, lx_primes, lz_unprimes, lz_primes.
        """
        lx_unprimes: list[BBLogicalQubit] = self.get_logical_qubits("X", False)
        lx_primes: list[BBLogicalQubit] = self.get_logical_qubits("X", True)
        lz_unprimes: list[BBLogicalQubit] = self.get_logical_qubits("Z", False)
        lz_primes: list[BBLogicalQubit] = self.get_logical_qubits("Z", True)
        return lx_unprimes, lx_primes, lz_unprimes, lz_primes

    def get_available_pauli_strings_w_one_probe(
        self, probe_x: BBLogicalQubit | None = None, probe_z: BBLogicalQubit | None = None
    ) -> dict[str, list[Monomial]]:
        """Get all Pauli strings that we can implement by
        (1) automorphisms and (2) measurement on the probe.
        If probe_x and probe_z are both given, it is the Y operator connected by the ancilla system.
        But notice that they should be belong to the same logical qubit.
        In this function, we have no way to check this but users should ensure
        this by themselves.

        Args:
            probe (BBLogicalQubit): the probe, where we have an ancilla system to measure in logical basis probe.lop_t

        Returns:
            dict[str, list[Monomial]]: a dictionary, where the key is the Pauli string, and the value is a list of automorphisms.
        """
        assert probe_x is not None or probe_z is not None, "probe_x and probe_z cannot be both None"
        ring = self.code.ring
        # omegas characterize all the automorphism gates that are available with the same hardware coupling as those in
        # syndrome extraction circuit
        omegas = ring.get_all_monomials()
        lxs = self.get_logical_qubits("X")
        lzs = self.get_logical_qubits("Z")
        visited_pauli_str_to_auts = {}
        for omega in omegas:
            new_lxs = [lop.apply_grid_translation_aut_gate(omega) for lop in lxs]
            new_lzs = [lop.apply_grid_translation_aut_gate(omega) for lop in lzs]

            if probe_z is not None:
                z_bits = [not probe_z.commutes_with(new_lop) for new_lop in new_lxs]
            else:
                z_bits = [False] * len(new_lxs)
            if probe_x is not None:
                x_bits = [not probe_x.commutes_with(new_lop) for new_lop in new_lzs]
            else:
                x_bits = [False] * len(new_lzs)
            ps = stim.PauliString.from_numpy(xs=np.array(x_bits, dtype=np.bool_), zs=np.array(z_bits, dtype=np.bool_))
            if str(ps) not in visited_pauli_str_to_auts:
                visited_pauli_str_to_auts[str(ps)] = []
            visited_pauli_str_to_auts[str(ps)].append(omega)
        return visited_pauli_str_to_auts

    def get_available_pauli_strs_w_two_probes(
        self, probe_unprimed: LogicalOp, probe_primed: LogicalOp
    ) -> dict[str, list[Monomial]]:
        """Get all Pauli strings that we can implement by
        (1) automorphisms and (2) measurement on the probe.

        Args:
            probe_unprimed (BBLogicalQubit): the probe in unprimed block
            probe_primed (BBLogicalQubit): the probe in primed block

        Returns:
            set[tuple[int, ...]]: a set of Pauli strings, where each Pauli string is represented by a tuple of integers.
            E.g., (0, 1, 0, 1) represents Pauli IXIX if probe.lop_t == "X", or Pauli IZIZ if probe.lop_t == "Z"
        """
        # assert probe_unprimed.lop_t == probe_primed.lop_t, "only support joint XX or ZZ"
        # assert probe_unprimed.primed == (
        #     not probe_primed.primed
        # ), "only support one in primed and the other in unprimed"
        ring = self.code.ring
        # omegas characterize all the automorphism gates that are available with the same hardware coupling as those in
        # syndrome extraction circuit
        omegas = ring.get_all_monomials()
        # visited_pauli_strs = set()
        visited_pauli_strs_to_auts = {}
        lxs = self.get_logical_qubits("X")
        lzs = self.get_logical_qubits("Z")
        for omega in omegas:
            new_lxs = [lop.apply_grid_translation_aut_gate(omega) for lop in lxs]
            new_lzs = [lop.apply_grid_translation_aut_gate(omega) for lop in lzs]

            z_bits_unprimed = [int(not probe_unprimed.commutes_with(new_lop)) for new_lop in new_lxs]
            x_bits_unprimed = [int(not probe_unprimed.commutes_with(new_lop)) for new_lop in new_lzs]
            z_bits_primed = [int(not probe_primed.commutes_with(new_lop)) for new_lop in new_lxs]
            x_bits_primed = [int(not probe_primed.commutes_with(new_lop)) for new_lop in new_lzs]

            x_bits = np.array(x_bits_unprimed, dtype=np.int_) + np.array(x_bits_primed, dtype=np.int_)
            z_bits = np.array(z_bits_unprimed, dtype=np.int_) + np.array(z_bits_primed, dtype=np.int_)
            stim_ps = stim.PauliString.from_numpy(xs=x_bits.astype(np.bool_), zs=z_bits.astype(np.bool_))
            # visited_pauli_strs.add(str(stim_ps))
            if str(stim_ps) not in visited_pauli_strs_to_auts:
                visited_pauli_strs_to_auts[str(stim_ps)] = []
            visited_pauli_strs_to_auts[str(stim_ps)].append(omega)
        return visited_pauli_strs_to_auts

    def get_all_available_pauli_strs(
        self,
        probe_x_unprimed: BBLogicalQubit,
        probe_x_primed: BBLogicalQubit,
        probe_z_unprimed: BBLogicalQubit,
        probe_z_primed: BBLogicalQubit,
    ) -> set[str]:
        """Get all Pauli strings that we can implement by
        (1) automorphisms and (2) measurement on the probe.
        """
        assert probe_x_unprimed.lop_t == probe_x_primed.lop_t == "X"
        assert probe_z_unprimed.lop_t == probe_z_primed.lop_t == "Z"

        visited_by_x_unp = self.get_available_pauli_strings_w_one_probe(probe_x_unprimed)
        visited_by_x_pri = self.get_available_pauli_strings_w_one_probe(probe_x_primed)
        visited_by_z_unp = self.get_available_pauli_strings_w_one_probe(probe_z=probe_z_unprimed)
        visited_by_z_pri = self.get_available_pauli_strings_w_one_probe(probe_z=probe_z_primed)
        visited_by_y_unp = self.get_available_pauli_strings_w_one_probe(probe_x_unprimed, probe_z_unprimed)
        visited_by_y_pri = self.get_available_pauli_strings_w_one_probe(probe_x_primed, probe_z_primed)
        visited_by_xx = self.get_available_pauli_strs_w_two_probes(probe_x_unprimed, probe_x_primed)
        visited_by_zz = self.get_available_pauli_strs_w_two_probes(probe_z_unprimed, probe_z_primed)

        all_visited = [
            visited_by_x_unp,
            visited_by_x_pri,
            visited_by_z_unp,
            visited_by_z_pri,
            visited_by_y_unp,
            visited_by_y_pri,
            visited_by_xx,
            visited_by_zz,
        ]
        visited_pauli_strs = set()
        for visited in all_visited:
            visited_pauli_strs |= visited.keys()
        return visited_pauli_strs

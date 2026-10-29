import itertools
from functools import lru_cache
from typing import override

import numpy as np
import stim

from ...common.packed_ps import PackedPS
from ...utils import get_pauli_string_from_sparse, to_stim_ps
from ..code import BBCode

# from ..data_mgr import ConjPathDataMgr
from ..ring import Monomial
from .base_bb_aut import BaseBBAut, BBLogicalQubit
from .lop_basis_searcher import BBLopBasisSearchResult


class TourBBAut(BaseBBAut):
    def __init__(
        self,
        code: BBCode,
        p_pows: list[tuple[int, int]],
        q_pows: list[tuple[int, int]],
        r_pows: list[tuple[int, int]],
        s_pows: list[tuple[int, int]],
        alphas: list[tuple[int, int]],
        betas: list[tuple[int, int]],
        # alphas_x_unp: list[tuple[int, int]],
        # alphas_z_unp: list[tuple[int, int]],
        # alphas_x_pri: list[tuple[int, int]],
        # alphas_z_pri: list[tuple[int, int]],
    ):
        super().__init__(code)
        self.p_pows = p_pows
        self.q_pows = q_pows
        self.r_pows = r_pows
        self.s_pows = s_pows

        self.p = [self.ring.monomial(*alpha) for alpha in self.p_pows]
        self.q = [self.ring.monomial(*alpha) for alpha in self.q_pows]
        self.r = [self.ring.monomial(*alpha) for alpha in self.r_pows]
        self.s = [self.ring.monomial(*alpha) for alpha in self.s_pows]

        self.alphas = alphas
        self.betas = betas

        # self.alphas_x_unp = alphas_x_unp
        # self.alphas_z_unp = alphas_z_unp
        # self.alphas_x_pri = alphas_x_pri
        # self.alphas_z_pri = alphas_z_pri

    def find_valid_alphas(self, lop_t: str, primed: bool) -> list[Monomial]:
        raise NotImplementedError()
        _dict = {
            ("X", True): self.alphas_x_pri,
            ("X", False): self.alphas_x_unp,
            ("Z", True): self.alphas_z_pri,
            ("Z", False): self.alphas_z_unp,
        }
        tuples = _dict[(lop_t, primed)]
        return [self.ring.monomial(*alpha) for alpha in tuples]

    @override
    def get_logical_qubits(self, lop_t: str, primed: bool | None = None) -> list[BBLogicalQubit]:
        if primed is None:
            return self.get_logical_qubits(lop_t, False) + self.get_logical_qubits(lop_t, True)
        return [self.get_logical_qubit(i, lop_t, primed) for i in range(len(self.alphas))]

    @override
    def get_logical_qubit(self, _id: int, lop_t: str, primed: bool) -> BBLogicalQubit:
        """Different from CrossBBAut."""
        v = self.ring.monomial(1, 1)
        mu = self.ring.monomial(1, 1)
        alpha = self.ring.monomial(*self.alphas[_id])
        beta = self.ring.monomial(*self.betas[_id])
        match (lop_t, primed):
            case ("X", False):
                subscript_mono = alpha
                lqs = [alpha * mono for mono in self.p]
                rqs = [alpha * mono for mono in self.q]
            case ("X", True):
                subscript_mono = beta.T()
                lqs = [beta.T() * mono for mono in self.r]
                rqs = [beta.T() * mono for mono in self.s]
            case ("Z", False):
                subscript_mono = beta * v
                lqs = [beta * v * mono.T() for mono in self.s]
                rqs = [beta * v * mono.T() for mono in self.r]
            case ("Z", True):
                subscript_mono = alpha.T() * mu
                lqs = [alpha.T() * mu * mono.T() for mono in self.q]
                rqs = [alpha.T() * mu * mono.T() for mono in self.p]
            case _:
                raise ValueError(f"Invalid operator type: {lop_t}")

        assert self._check_unique(lqs), "lqs must be unique"
        assert self._check_unique(rqs), "rqs must be unique"
        lop = BBLogicalQubit(subscript_mono, self.code.l, self.code.m, lop_t, primed, lqs, rqs)
        return lop

    @staticmethod
    def _check_unique(lops: list[Monomial]) -> bool:
        for i, lop in enumerate(lops):
            for j in range(i + 1, len(lops)):
                if lop.as_tuple() == lops[j].as_tuple():
                    return False
        return True

    @staticmethod
    def from_lop_basis(code: BBCode, lop_basis: BBLopBasisSearchResult) -> "TourBBAut":
        raise NotImplementedError("Require fixing.")
        p_pows = lop_basis.p
        q_pows = lop_basis.q
        r_pows = lop_basis.r
        s_pows = lop_basis.s
        aut = TourBBAut(
            code,
            p_pows,
            q_pows,
            r_pows,
            s_pows,
            lop_basis.alphas_x_unp,
            lop_basis.alphas_z_unp,
            lop_basis.alphas_x_pri,
            lop_basis.alphas_z_pri,
        )
        return aut

    @staticmethod
    def from_existing_paper(code: BBCode) -> "TourBBAut":
        assert code.n in [144, 288], "only support gross code for now"
        if code.n == 144:
            p = [(4, 0), (5, 0), (6, 1), (4, 2), (5, 4), (6, 5)]
            q = [(3, 0), (4, 0), (3, 1), (3, 2), (4, 2), (3, 5)]
            r = [(0, 0), (8, 0), (1, 1), (9, 1), (3, 4), (11, 4)]
            s = [(1, 0), (9, 0), (4, 4), (8, 4), (0, 5), (8, 5)]
            alphas = [
                (0, 0),  # 1
                (3, 5),  # x^3 y^5
                (11, 5),  # x^11 y^5
                (10, 1),  # x^10 y
                (5, 4),  # x^5 y^4
                (4, 2),
            ]  # x^4 y^2

            betas = [(0, 0), (2, 4), (1, 2), (2, 5), (1, 1), (3, 1)]  # 1  # x^2 y^4  # x y^2  # x^2 y^5  # x y  # x^3 y
            return TourBBAut(code, p, q, r, s, alphas, betas)
        elif code.n == 288:
            p = [
                (2, 0),
                #
                (2, 2),
                (8, 2),
                (9, 2),
                #
                (3, 3),
                (4, 3),
                #
                (7, 4),
                (8, 6),
                (6, 7),
                (7, 11),
            ]

            q = [
                (3, 2),
                #
                (5, 3),
                (7, 3),
                (11, 3),
                #
                (8, 4),
                (8, 5),
                (6, 7),
                (4, 8),
                (1, 9),
                (1, 10),
            ]

            r = [
                (4, 2),
                (11, 2),
                #
                (0, 5),
                (1, 5),
                (5, 5),
                (6, 5),
                #
                (1, 8),
                (8, 8),
                #
                (2, 11),
                (10, 11),
            ]

            s = [
                (2, 6),
                (2, 9),
                (2, 10),
                #
                (11, 6),
                (11, 9),
                (11, 10),
                #
                (8, 7),
                (11, 7),
                #
                (5, 8),
                (11, 8),
            ]

            alphas = [
                (0, 0),  # 1
                (0, 3),  # y^3
                (3, 7),  # x^3 y^7
                (11, 11),  # x^11 y^11
                (2, 9),  # x^2 y^9
                (7, 4),  # x^7 y^4
            ]

            betas = [
                (0, 0),  # 1
                (1, 1),  # x y
                (4, 0),  # x^4
                (5, 4),  # x^5 y^4
                (4, 3),  # x^4 y^3
                (3, 5),  # x^3 y^5
            ]
            return TourBBAut(code, p, q, r, s, alphas, betas)
        else:
            raise ValueError(f"Invalid code: {code.n}")

    @override
    def get_all_available_pauli_strs(self) -> set[str]:
        X1 = self.get_logical_qubits("X", False)[0]
        X7 = self.get_logical_qubits("X", True)[0]
        Z1 = self.get_logical_qubits("Z", False)[0]
        Z7 = self.get_logical_qubits("Z", True)[0]
        Y1 = X1.get_logical_Y_op(Z1)
        Y7 = X7.get_logical_Y_op(Z7)

        visited_by_x_unp = self.get_available_pauli_strings_w_one_probe(X1)
        visited_by_x_pri = self.get_available_pauli_strings_w_one_probe(X7)
        visited_by_z_unp = self.get_available_pauli_strings_w_one_probe(probe_z=Z1)
        visited_by_z_pri = self.get_available_pauli_strings_w_one_probe(probe_z=Z7)
        visited_by_y_unp = self.get_available_pauli_strings_w_one_probe(X1, Z1)
        visited_by_y_pri = self.get_available_pauli_strings_w_one_probe(X7, Z7)

        visited_by_joint_meas: dict[tuple[str, str], set[str]] = {}
        probe1_dict = {"X": X1, "Y": Y1, "Z": Z1}
        probe7_dict = {"X": X7, "Y": Y7, "Z": Z7}
        for probe1_type, probe7_type in itertools.product(["X", "Y", "Z"], ["X", "Y", "Z"]):
            probe1 = probe1_dict[probe1_type]
            probe7 = probe7_dict[probe7_type]
            visited_by_joint_meas[probe1_type, probe7_type] = self.get_available_pauli_strs_w_two_probes(probe1, probe7)

        all_visited: list[set[str]] = [
            set(visited_by_x_unp.keys()),
            set(visited_by_x_pri.keys()),
            set(visited_by_z_unp.keys()),
            set(visited_by_z_pri.keys()),
            set(visited_by_y_unp.keys()),
            set(visited_by_y_pri.keys()),
            set(itertools.chain.from_iterable(visited_by_joint_meas.values())),
        ]
        visited_pauli_strs = set()
        for visited in all_visited:
            visited_pauli_strs |= visited
        return visited_pauli_strs

    def get_nat_pss_w_auts(self) -> dict[str, list[Monomial]]:
        X1 = self.get_logical_qubits("X", False)[0]
        X7 = self.get_logical_qubits("X", True)[0]
        Z1 = self.get_logical_qubits("Z", False)[0]
        Z7 = self.get_logical_qubits("Z", True)[0]
        Y1 = X1.get_logical_Y_op(Z1)
        Y7 = X7.get_logical_Y_op(Z7)

        visited_by_x_unp = self.get_available_pauli_strings_w_one_probe(X1)
        visited_by_x_pri = self.get_available_pauli_strings_w_one_probe(X7)
        visited_by_z_unp = self.get_available_pauli_strings_w_one_probe(probe_z=Z1)
        visited_by_z_pri = self.get_available_pauli_strings_w_one_probe(probe_z=Z7)
        visited_by_y_unp = self.get_available_pauli_strings_w_one_probe(X1, Z1)
        visited_by_y_pri = self.get_available_pauli_strings_w_one_probe(X7, Z7)

        visited_by_joint_meas: dict[tuple[str, str], dict[str, list[Monomial]]] = {}
        probe1_dict = {"X": X1, "Y": Y1, "Z": Z1}
        probe7_dict = {"X": X7, "Y": Y7, "Z": Z7}
        for probe1_type, probe7_type in itertools.product(["X", "Y", "Z"], ["X", "Y", "Z"]):
            probe1 = probe1_dict[probe1_type]
            probe7 = probe7_dict[probe7_type]
            visited_by_joint_meas[probe1_type, probe7_type] = self.get_available_pauli_strs_w_two_probes(probe1, probe7)

        all_visited: list[dict[str, list[Monomial]]] = [
            visited_by_x_unp,
            visited_by_x_pri,
            visited_by_z_unp,
            visited_by_z_pri,
            visited_by_y_unp,
            visited_by_y_pri,
            *visited_by_joint_meas.values(),
        ]
        visited_pauli_str_to_auts: dict[str, list[Monomial]] = {}
        for visited in all_visited:
            for ps, auts in visited.items():
                if ps not in visited_pauli_str_to_auts:
                    visited_pauli_str_to_auts[ps] = []
                visited_pauli_str_to_auts[ps].extend(auts)
        return visited_pauli_str_to_auts

    def get_native_paulis_mat(self) -> np.ndarray:
        pauli_strs = self.get_all_available_pauli_strs()
        pauli_strs = list(pauli_strs)
        pauli_strs = [stim.PauliString(pauli_str) for pauli_str in pauli_strs]
        pauli_bits_lst = []
        for i, pauli in enumerate(pauli_strs):
            xs, zs = pauli.to_numpy()
            symp_vec = np.hstack((xs, zs))
            pauli_bits_lst.append(symp_vec)
        return np.array(pauli_bits_lst, dtype=np.bool_)

    def get_pss_of_native_rotation(self) -> list[stim.PauliString]:
        pivot_id = 0  # the pivot is the first logical qubit
        native_pss = self.get_all_available_pauli_strs()
        # remove "+"
        native_pss = [ps[1:] for ps in native_pss]
        # native rotations are those who has support on pivot_id
        pss_of_native_rotation = set([ps[:pivot_id] + ps[pivot_id + 1 :] for ps in native_pss if ps[pivot_id] != "_"])
        pss_of_native_rotation = [stim.PauliString(ps) for ps in pss_of_native_rotation]
        return pss_of_native_rotation

    def get_n_native_meas_by_native_rot(
        self, ps: stim.PauliString | tuple[np.ndarray, np.ndarray] | np.ndarray | dict[int, str]
    ) -> int:
        """Figure 9. Page 25.

        Read #Layer first, and return 6 * layer - 5.
        - layer range: [1, 5];
        - if layer == 1: just one native measurement;
        - if layer == i: i-1 native rotations + 1 native measurement + i-1 native rotations (Clifford dagger)
        - Each native rotation costs 3 native measurements
        """
        # print(ps)
        if isinstance(ps, stim.PauliString):
            assert len(ps) == self.code.k - 1, f"only support {self.code.k - 1} qubits for now"
            ps_tuple = PackedPS.from_pauli_string(ps).to_tuple()
        elif isinstance(ps, tuple) and len(ps) == 2 and isinstance(ps[0], np.ndarray) and isinstance(ps[1], np.ndarray):
            assert ps[0].shape == ps[1].shape, "xs and zs must have the same shape"
            assert ps[0].shape[0] == self.code.k - 1, f"only support {self.code.k - 1} qubits for now"
            ps_tuple = PackedPS.from_numpy(ps[0], ps[1]).to_tuple()
        elif isinstance(ps, np.ndarray):  # symplectic vector
            ps_stim = to_stim_ps(ps)
            assert len(ps_stim) == self.code.k - 1, f"only support {self.code.k - 1} qubits for now"
            ps_tuple = PackedPS.from_pauli_string(ps_stim).to_tuple()
        elif isinstance(ps, dict) and all(isinstance(v, str) for v in ps.values()):  # sparse pauli string
            ps_stim = get_pauli_string_from_sparse(ps, self.code.k - 1)
            assert (
                len(ps_stim) == self.code.k - 1
            ), f"only support {self.code.k - 1} qubits for now, but got {len(ps_stim)}"
            ps_tuple = PackedPS.from_pauli_string(ps_stim).to_tuple()
        else:
            raise ValueError(f"Invalid type: {type(ps)}")

        layer = _load_ps_tuple_to_length_map(self.code.n)[ps_tuple]
        return 6 * layer - 5

    @staticmethod
    def from_n(n: int) -> "TourBBAut":
        assert n == 144, "only support 144 for now"
        code = BBCode.from_n(n)
        return TourBBAut.from_existing_paper(code)


@lru_cache(maxsize=1)
def _load_ps_tuple_to_length_map(n: int) -> dict[tuple[int, int], int]:
    return None
    if n == 144:
        data = ConjPathDataMgr().load(source="tour", n=144, round_id=4, r=-1)
    elif n == 288:
        data = ConjPathDataMgr().load(source="tour", n=288, round_id=5, r=-1)
    else:
        raise ValueError(f"Invalid n: {n}")
    return data

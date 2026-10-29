from typing import TypeVar, override

import galois
import numpy as np
import stim
from numpy.linalg import matrix_power, matrix_rank
from numpy.typing import NDArray

from ..codes.base_code import CSSSpec
from .ring import GF2CyclicPolyRing2D, Monomial

KEY_TYPE = TypeVar("KEY_TYPE")
VALUE_TYPE = TypeVar("VALUE_TYPE")


def invert_map(dictionary: dict[KEY_TYPE, VALUE_TYPE]) -> dict[VALUE_TYPE, KEY_TYPE]:
    """Invert a dictionary mapping."""
    return {v: k for k, v in dictionary.items()}


def cyclic_shift_matrix(l: int) -> NDArray[np.int_]:
    arr = np.eye(l, dtype=np.int_)
    return np.roll(arr, axis=1, shift=1)


class BBQubit:
    def __init__(self, qubit_type: str, mono: Monomial) -> None:
        self.qubit_type = qubit_type
        self.qid = mono.xexp * mono.ring.l + mono.yexp
        self.mono = mono

    def __repr__(self) -> str:
        return f"{self.qubit_type}{self.qid}({self.mono.xexp},{self.mono.yexp})"

    def label(self) -> str:
        return f"{self.mono.xexp},{self.mono.yexp}"

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, BBQubit), f"{type(other)}"
        return self.qubit_type == other.qubit_type and self.qid == other.qid and self.mono == self.mono


class BBCode(CSSSpec):
    def __init__(
        self,
        n: int,
        k: int,
        d: int,
        is_max_d: bool,
        l: int,
        m: int,
        a_pows: list[tuple[int, int]],
        b_pows: list[tuple[int, int]],
    ):
        """
        Initialize a Bivariate Bicycle (BB) code.

        Parameters:
        l, m : int
            Dimensions of the code. Total number of qubits is l*m.
        a_pows : list of tuples
            Powers for the A terms. Each tuple is (x_power, y_power).
            E.g. [[144, 12, 12]]: A_i = { x^3, y, y^2 }, B_i = { y^3, x, x^2 }. Then
            a_pows = [(3, 0), (0, 1), (0, 2)], b_pows = [(0, 3), (1, 0), (2, 0)].
        b_pows : list of tuples
            Powers for the B terms. Each tuple is (x_power, y_power).
        """
        assert len(a_pows) == 3 and len(b_pows) == 3, "Must have 3 terms each for A and B"

        self._k = k
        self.l = l
        self.m = m
        self.d = d
        self.lm = l * m
        self.ring = GF2CyclicPolyRing2D(l, m)

        self.dlm = 2 * self.lm
        self.lmsq = self.lm * self.lm

        self.a_pows = [pow for pow in a_pows]
        self.b_pows = [pow for pow in b_pows]

        self.a = [self.xypow(pow[0], pow[1]) for pow in a_pows]
        self.b = [self.xypow(pow[0], pow[1]) for pow in b_pows]

        self.a_inv = [invert_map(a) for a in self.a]
        self.b_inv = [invert_map(b) for b in self.b]

        self.maxlength = int(np.ceil(np.log10((self.m - 1) * self.m + self.l - 0.9)))

        data_to_check_mappings = {
            ("L", "X"): "a_inv",
            ("L", "Z"): "b",
            ("R", "X"): "b_inv",
            ("R", "Z"): "a",
        }
        check_to_data_mappings = {
            ("X", "L"): "a",
            ("Z", "L"): "b_inv",
            ("X", "R"): "b",
            ("Z", "R"): "a_inv",
        }

        self.mapping_matrices_dict = data_to_check_mappings | check_to_data_mappings
        self.setup_connections()

        self.field = galois.GF(2)
        self.x = np.kron(cyclic_shift_matrix(self.l), np.eye(self.m))
        self.y = np.kron(np.eye(self.l), cyclic_shift_matrix(self.m))

        self.As = [matrix_power(self.x, pow[0]) @ matrix_power(self.y, pow[1]) for pow in a_pows]
        self.Bs = [matrix_power(self.x, pow[0]) @ matrix_power(self.y, pow[1]) for pow in b_pows]

        self.A = np.array(sum(self.As)).astype(np.int_) % 2
        self.B = np.array(sum(self.Bs)).astype(np.int_) % 2

        self._Hx = np.hstack([self.A, self.B])
        self._Hz = np.hstack([self.B.T, self.A.T])

        Hx_rank = galois.GF2(self._Hx).row_space().shape[0]
        Hz_rank = galois.GF2(self._Hz).row_space().shape[0]

        self.H = galois.GF2(
            np.block(
                [
                    [self._Hx, np.zeros((self._Hx.shape[0], self._Hz.shape[1]), dtype=np.int_)],
                    [np.zeros((self._Hz.shape[0], self._Hx.shape[1]), dtype=np.int_), self._Hz],
                ]
            )
        )

        H_rank = galois.GF2(self.H).row_space().shape[0]
        derived_k = 2 * (self._Hz.T.shape[1] - matrix_rank(self.field(self._Hz.T)))
        assert Hx_rank >= 0 and Hz_rank >= 0
        assert n - H_rank == derived_k
        assert self.dlm == n
        if is_max_d:
            pass

    @property
    def Hx(self) -> NDArray[np.int_]:
        return self._Hx

    @property
    def Hz(self) -> NDArray[np.int_]:
        return self._Hz

    @property
    def n(self) -> int:
        return self.num_dat_qubits

    @property
    def num_logicals(self) -> int:
        return self._k

    @property
    def k(self) -> int:
        return self._k

    @property
    def all_dat_uids(self) -> list[int]:
        return list(self.get_circ_layout().col_id_to_dat_uid)

    @property
    def all_chk_uids(self) -> list[int]:
        return list(self.get_circ_layout().check_uids)

    @staticmethod
    def from_n(n: int) -> "BBCode":
        match n:
            case 144:
                return BBCode(144, 12, 12, False, 12, 6, [(0, 0), (0, 1), (3, -1)], [(0, 0), (1, 0), (-1, -3)])
            case 288:
                return BBCode(288, 12, 18, False, 12, 12, [(0, 0), (0, 1), (3, -1)], [(0, 0), (1, 0), (-1, -3)])
            case _:
                raise ValueError(f"n = {n} is not supported")

    @staticmethod
    def get_fake_code(l: int, m: int) -> "BBCode":
        n = 2 * l * m
        return BBCode(n, -1, -1, False, l, m, [(-1, -1), (-1, -1), (-1, -1)], [(-1, -1), (-1, -1), (-1, -1)])

    def xypow(self, xexp: int, yexp: int) -> dict[int, int]:
        """The matrix :math:`x^xexp \\otimes y^yexp` in the form of dictionary."""
        x = self.xpow(xexp)
        y = self.ypow(yexp)
        return {i: y[x[i]] for i in range(self.lm)}

    def xpow(self, exponent: int) -> dict[int, int]:
        """The matrix :math:`(S_l \\otimes I_m)^exponent` in the form of dictionary."""
        return {i: (i + exponent * self.m) % self.lm for i in range(self.lm)}

    def ypow(self, exponent: int) -> dict[int, int]:
        """The matrix :math:`(I_l \\otimes S_m)^exponent` in the form of dictionary."""
        return {i: self.m * (i // self.m) + ((i + exponent) % self.m) for i in range(self.lm)}

    def format_label(self, ind):
        return f"{ind:0{self.maxlength}d}"

    def qtype_and_qid_to_label(self, qtype: str, qid: int) -> str:
        return f"{qtype}{self.format_label(qid)}"

    def label_to_qtype_and_qid(self, label: str) -> tuple[str, int]:
        return label[0], int(label[1:])

    def setup_connections(self):
        self.x_connections = {
            f"X{self.format_label(ind)}": [
                f"L{self.format_label(self.a[0][ind])}",
                f"L{self.format_label(self.a[1][ind])}",
                f"L{self.format_label(self.a[2][ind])}",
                f"R{self.format_label(self.b[0][ind])}",
                f"R{self.format_label(self.b[1][ind])}",
                f"R{self.format_label(self.b[2][ind])}",
            ]
            for ind in range(self.lm)
        }

        self.z_connections = {
            f"Z{self.format_label(ind)}": [
                f"L{self.format_label(self.b_inv[0][ind])}",
                f"L{self.format_label(self.b_inv[1][ind])}",
                f"L{self.format_label(self.b_inv[2][ind])}",
                f"R{self.format_label(self.a_inv[0][ind])}",
                f"R{self.format_label(self.a_inv[1][ind])}",
                f"R{self.format_label(self.a_inv[2][ind])}",
            ]
            for ind in range(self.lm)
        }

        self.connections = {}
        self.connections.update(self.x_connections)
        self.connections.update(self.z_connections)

    def __str__(self):
        return f"BBCode(l={self.l}, m={self.m}, A={self.a_pows}, B={self.b_pows})"

    def monomial_to_qid(self, monomial: Monomial) -> int:
        return monomial.xexp * self.m + monomial.yexp

    def qid_to_monomial(self, qid: int) -> Monomial:
        return self.ring.monomial(qid // self.m, qid % self.m)

    def get_interacting_qubits(
        self, src_qubit: int, src_qtype: str, dst_qtype: str, matrix_i: int | None = None
    ) -> list[BBQubit]:
        mapping_matrices = self.mapping_matrices_dict[(src_qtype, dst_qtype)]
        if isinstance(matrix_i, int):
            interacting_qid = self.__dict__[mapping_matrices][matrix_i][src_qubit]
            interacting_qids = [interacting_qid]
        else:
            interacting_qids = [self.__dict__[mapping_matrices][i][src_qubit] for i in range(3)]
        return [BBQubit(dst_qtype, self.qid_to_monomial(qid)) for qid in interacting_qids]

    def _qtype_and_qid_to_uid(self, qtype: str, qid: int) -> int:
        assert 0 <= qid < self.lm, f"qid {qid} is out of range for {qtype}"
        match qtype:
            case "L":
                uid = qid
            case "R":
                uid = self.lm + qid
            case "X":
                uid = self.dlm + qid
            case "Z":
                uid = self.dlm + self.lm + qid
            case _:
                raise ValueError(f"Invalid qtype: {qtype}")
        return uid

    def _get_interacting_qids(
        self,
        src_qtype: str,
        src_qid: int,
        dst_qtype: str,
        matrix_i: int | None = None,
    ) -> list[int]:
        assert 0 <= src_qid < self.lm, f"src_qid {src_qid} is out of range for {src_qtype}"
        assert dst_qtype in ["L", "R", "X", "Z"], f"Invalid dst_qtype: {dst_qtype}"
        assert matrix_i is None or matrix_i in [0, 1, 2], f"Invalid matrix_i: {matrix_i}"

        mapping_matrices = self.mapping_matrices_dict[(src_qtype, dst_qtype)]
        if isinstance(matrix_i, int):
            interacting_qid = self.__dict__[mapping_matrices][matrix_i][src_qid]
            interacting_qids = [interacting_qid]
        else:
            interacting_qids = [self.__dict__[mapping_matrices][i][src_qid] for i in range(3)]
        return interacting_qids

    def select_uids(self, qtype: str) -> list[int]:
        match qtype:
            case "L":
                return list(range(self.lm))
            case "R":
                return list(range(self.lm, self.dlm))
            case "X":
                return list(range(self.dlm, self.dlm + self.lm))
            case "Z":
                return list(range(self.dlm + self.lm, 2 * self.dlm))
            case _:
                raise ValueError(f"Invalid qtype: {qtype}")

    def decompose_mono_to_native_auts(self) -> dict[Monomial, int]:
        """Decompose a monomial to native automorphisms, assuming the start is Monomial(0, 0)."""
        ring = self.ring
        n_all_monos = len(self.ring.get_all_monomials())

        ai_aj_t: list[Monomial] = []
        for ai_pow in self.a_pows:
            for aj_pow in self.a_pows:
                ai = ring.monomial(*ai_pow)
                aj = ring.monomial(*aj_pow)
                if ai != aj:
                    ai_aj_t.append(ai * aj.T())

        bi_bj_t: list[Monomial] = []
        for bi_pow in self.b_pows:
            for bj_pow in self.b_pows:
                bi = ring.monomial(*bi_pow)
                bj = ring.monomial(*bj_pow)
                if bi != bj:
                    bi_bj_t.append(bi * bj.T())

        gens = ai_aj_t + bi_bj_t + [ring.monomial(0, 0)]
        mono_to_n_native_auts = {mono: -1 for mono in self.ring.get_all_monomials()}
        mono_to_n_native_auts[ring.monomial(0, 0)] = 0

        cur_monos = gens
        round_i = 1
        visited_mono_cnt = 1
        while visited_mono_cnt < n_all_monos:
            for cur_mono in cur_monos:
                if mono_to_n_native_auts[cur_mono] == -1:
                    mono_to_n_native_auts[cur_mono] = round_i
                    visited_mono_cnt += 1
            cur_monos = self._get_next_round_monos(cur_monos, gens)
            round_i += 1

        assert visited_mono_cnt == sum(cnt != -1 for cnt in mono_to_n_native_auts.values())
        return mono_to_n_native_auts

    def _get_next_round_monos(self, cur_monos: list[Monomial], gens: list[Monomial]) -> list[Monomial]:
        next_round_monos: set[Monomial] = set()
        for cur_mono in cur_monos:
            for gen in gens:
                next_round_monos.add(cur_mono * gen)
        return list(next_round_monos)

    @override
    def get_logical_ops_stim(self) -> tuple[list[stim.PauliString], list[stim.PauliString]]:
        from .bb_aut import TourBBAut

        aut = TourBBAut.from_n(self.n)
        lxs = aut.get_logical_qubits("X")
        lzs = aut.get_logical_qubits("Z")
        all_zeros = np.zeros(self.n, dtype=np.bool_)
        lxs_ops = [stim.PauliString.from_numpy(xs=np.array(lx.to_vec(), dtype=np.bool_), zs=all_zeros) for lx in lxs]
        lzs_ops = [stim.PauliString.from_numpy(xs=all_zeros, zs=np.array(lz.to_vec(), dtype=np.bool_)) for lz in lzs]
        return lxs_ops, lzs_ops

    @property
    def identifier(self) -> str:
        return f"bb-[[{self.n},{self.k},{self.d}]]"


__all__ = ["BBCode"]

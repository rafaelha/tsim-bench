from typing import override

import numpy as np

from ..bb_aut.base_bb_aut import BaseBBAut, BBLogicalQubit
from ..code import BBCode
from ..ring import Monomial
from .lop_basis_searcher import BBLopBasisSearchResult


class CrossGrossAut(BaseBBAut):
    """
    Cross BB Automorphism for the gross code.
    Docs: https://arxiv.org/abs/2407.18393.
    """

    def __init__(self, code: BBCode):
        # assert (code.n, code.k, code.d) == (144, 12, 12), "only support gross code for now"
        super().__init__(code)
        """Section 4.1, Eq. (62-65)"""
        self.p_pows = [
            (0, 1),
            (1, 5),
            (2, 2),
            (2, 4),
            (3, 1),
            (3, 2),
            (4, 1),
            (4, 2),
            (9, 3),
            (10, 0),
            (11, 0),
            (11, 3),
        ]
        self.q_pows = [(0, 2), (1, 1), (1, 5), (6, 0)]
        self.r_pows = [(2, 3), (2, 5), (3, 0), (3, 3), (3, 4), (3, 5)]
        self.s_pows = [(1, 3), (1, 5), (2, 0), (2, 4), (3, 2), (3, 4)]

        self.p = [self.ring.monomial(*alpha) for alpha in self.p_pows]
        self.q = [self.ring.monomial(*alpha) for alpha in self.q_pows]
        self.r = [self.ring.monomial(*alpha) for alpha in self.r_pows]
        self.s = [self.ring.monomial(*alpha) for alpha in self.s_pows]

    def find_valid_alphas(self, lop_t: str, is_unprimed_blk: bool) -> list[Monomial]:
        r"""Logical X_\\alpha is supported on L(\\alpha p) \\cup R(\alpha q).
        Logical X'_\\alpha is supported on L(\\alpha s^\\top) \\cup R(\\alpha r^\\top).
        Logical Z_\\alpha is supported on L(\\alpha r) \\cup R(\\alpha q^\\top).
        Logical Z'_\\alpha is supported on L(\\alpha p^\\top) \\cup R(\\alpha s^\\top).
        """
        assert is_unprimed_blk, "only support unprimed block for now"
        assert lop_t in ["X", "Z"], "only support X and Z for now"
        lops = self._get_all_rep_lops_for_one_lop_t(lop_t, is_unprimed_blk)

        # get the opposite logical operator, e.g., if lop_t is X, then oppo_lop_t is Z
        oppo_lop_t = "X" if lop_t == "Z" else "Z"
        oppo_lops = self._get_all_rep_lops_for_one_lop_t(oppo_lop_t, is_unprimed_blk)

        comm_mat = np.zeros((len(lops), len(oppo_lops)), dtype=np.int_)
        n_overlap_mat = np.zeros((len(lops), len(oppo_lops)), dtype=np.int_)
        for i, lop in enumerate(lops):
            for j, oppo_lop in enumerate(oppo_lops):
                l_overlap, r_overlap = lop.get_support_overlap(oppo_lop)
                n_overlap_mat[i, j] = len(l_overlap) + len(r_overlap)
                comm_mat[i, j] = 1 if lop.commutes_with(oppo_lop) else 0

        # print(f"{comm_mat[0]=}")
        assert np.all([comm_mat[i, i] == 0 for i in range(comm_mat.shape[0])]), "diagonal elements must be 0"
        assert np.all([n_overlap_mat[i, i] % 2 == 1 for i in range(comm_mat.shape[0])]), "non-zero overlap must be odd"

        target_n_alphas = 6  # TODO: make it code.k // 2
        valid_q0_ids = []
        max_n_nonzero = 0
        min_n_nonzero = np.inf
        for lop_id, comm_vec in enumerate(comm_mat):
            n_nonzero = np.sum(comm_vec == 1)
            max_n_nonzero = max(max_n_nonzero, n_nonzero)
            min_n_nonzero = min(min_n_nonzero, n_nonzero)
            if n_nonzero >= target_n_alphas:  # must include q0 itself
                valid_q0_ids.append(lop_id)

        print(f"{len(valid_q0_ids)=}, {max_n_nonzero=}, {min_n_nonzero=}")

        max_n_nonzero = 0
        min_n_nonzero = np.inf
        tmp_valid_q0_ids = []
        for lop_id, overlap_vec in enumerate(n_overlap_mat):
            n_equal_1 = np.sum(overlap_vec == 0)
            max_n_nonzero = max(max_n_nonzero, n_equal_1)
            min_n_nonzero = min(min_n_nonzero, n_equal_1)
            if n_equal_1 >= target_n_alphas:
                tmp_valid_q0_ids.append(lop_id)
        # exit()
        print(f"{len(tmp_valid_q0_ids)=}, {max_n_nonzero=}, {min_n_nonzero=}")
        exit()
        valid_alphas = [rep_lops[lop_id].alpha for lop_id in valid_q0_ids]

        # print(f"{valid_alphas=}")
        # print(f"{len(all_lops)=}, {len(rep_lops)=}")
        return valid_alphas

    def _get_all_rep_lops_for_one_lop_t(self, lop_t: str, primed: bool) -> list[BBLogicalQubit]:
        all_alphas = [self.ring.monomial(i, j) for i in range(self.code.l) for j in range(self.code.m)]
        all_lops = [self.get_logical_qubit(alpha, lop_t, primed) for alpha in all_alphas]
        n_qubits_lst = [lop.n_qubits for lop in all_lops]
        print(f"{np.min(n_qubits_lst)=}, {np.max(n_qubits_lst)=}, {np.mean(n_qubits_lst)=}")
        all_lops = [lop for lop in all_lops if lop.n_qubits == 12]
        print(f"{len(all_lops)=}")
        groups = self.group_lops_by_equiv(all_lops)
        rep_lops = [all_lops[group[0]] for group in groups]
        return rep_lops

    # def _get_valid_logical_qubits(self, xlops: list[LogicalOp], zlops: list[LogicalOp], k: int
    #                               ) -> tuple[list[int], list[int]]:
    #     xlop_n_qbts_lst = [lop.n_qubits for lop in xlops]
    #     zlop_n_qbts_lst = [lop.n_qubits for lop in zlops]
    #     xk = k
    #     zk = k
    #     xlop_n_qbts_max = max(xlop_n_qbts_lst)
    #     zlop_n_qbts_max = max(zlop_n_qbts_lst)
    #     xlop_n_qbts_min = min(xlop_n_qbts_lst)
    #     zlop_n_qbts_min = min(zlop_n_qbts_lst)

    #     assert xlop_n_qbts_max >= k, "X lops must have at most k qubits"
    #     assert zlop_n_qbts_max >= k, "Z lops must have at most k qubits"

    def group_lops_by_equiv(self, all_lops: list[BBLogicalQubit]) -> list[list[int]]:
        matrix = self.get_equiv_mat(all_lops)
        # assert np.all(matrix == np.eye(matrix.shape[0])), "equiv_mat is not identity matrix"
        if np.all(matrix == np.eye(matrix.shape[0])):
            print("all lops are unique, the equiv mat is identity matrix")
            return [[i] for i in range(matrix.shape[0])]
        # print(f"{matrix=}")
        n = matrix.shape[0]
        groups = []
        visited = set()

        def dfs(node, current_group):
            visited.add(node)
            current_group.append(node)
            for neighbor in range(n):
                if matrix[node, neighbor] == 1 and neighbor not in visited:
                    dfs(neighbor, current_group)

        for i in range(n):
            if i not in visited:
                current_group = []
                dfs(i, current_group)
                groups.append(current_group)

        return groups

    @override
    def get_logical_qubit(self, alpha: Monomial, lop_t: str, primed: bool) -> BBLogicalQubit:
        if not primed:  # unprimed block
            if lop_t == "X":
                lqs = [alpha * mono for mono in self.p]
                rqs = [alpha * mono for mono in self.q]
            else:
                lqs = [alpha * mono for mono in self.r]
                rqs = [alpha * mono for mono in self.s]
        else:  # primed block
            if lop_t == "X":
                lqs = [alpha * mono.T() for mono in self.s]
                rqs = [alpha * mono.T() for mono in self.r]
            else:
                lqs = [alpha * mono.T() for mono in self.q]
                rqs = [alpha * mono.T() for mono in self.p]

        assert self._check_unique(lqs), "lqs must be unique"
        assert self._check_unique(rqs), "rqs must be unique"
        lop = BBLogicalQubit(alpha, self.code.l, self.code.m, lop_t, primed, lqs, rqs)
        return lop

    @staticmethod
    def _check_unique(lops: list[Monomial]) -> bool:
        for i, lop in enumerate(lops):
            for j in range(i + 1, len(lops)):
                if lop.as_tuple() == lops[j].as_tuple():
                    return False
        return True


class CrossBBAut(BaseBBAut):
    """
    Cross BB Automorphism for the gross code.
    Docs: https://arxiv.org/abs/2407.18393.
    """

    def __init__(
        self,
        code: BBCode,
        p_pows: list[tuple[int, int]],
        q_pows: list[tuple[int, int]],
        r_pows: list[tuple[int, int]],
        s_pows: list[tuple[int, int]],
        alphas_x_unp: list[tuple[int, int]],
        alphas_z_unp: list[tuple[int, int]],
        alphas_x_pri: list[tuple[int, int]],
        alphas_z_pri: list[tuple[int, int]],
    ):
        super().__init__(code)
        """Section 4.1, Eq. (62-65)"""
        self.p_pows = p_pows
        self.q_pows = q_pows
        self.r_pows = r_pows
        self.s_pows = s_pows

        self.p = [self.ring.monomial(*alpha) for alpha in self.p_pows]
        self.q = [self.ring.monomial(*alpha) for alpha in self.q_pows]
        self.r = [self.ring.monomial(*alpha) for alpha in self.r_pows]
        self.s = [self.ring.monomial(*alpha) for alpha in self.s_pows]

        self.alphas_x_unp = alphas_x_unp
        self.alphas_z_unp = alphas_z_unp
        self.alphas_x_pri = alphas_x_pri
        self.alphas_z_pri = alphas_z_pri

    def find_valid_alphas(self, lop_t: str, primed: bool) -> list[Monomial]:
        _dict = {
            ("X", True): self.alphas_x_pri,
            ("X", False): self.alphas_x_unp,
            ("Z", True): self.alphas_z_pri,
            ("Z", False): self.alphas_z_unp,
        }
        tuples = _dict[(lop_t, primed)]
        return [self.ring.monomial(*alpha) for alpha in tuples]

    @override
    def get_logical_qubit(self, alpha: Monomial, lop_t: str, primed: bool) -> BBLogicalQubit:
        if not primed:  # unprimed block
            if lop_t == "X":
                lqs = [alpha * mono for mono in self.p]
                rqs = [alpha * mono for mono in self.q]
            else:
                lqs = [alpha * mono for mono in self.r]
                rqs = [alpha * mono for mono in self.s]
        else:  # primed block
            if lop_t == "X":
                lqs = [alpha * mono.T() for mono in self.s]
                rqs = [alpha * mono.T() for mono in self.r]
            else:
                lqs = [alpha * mono.T() for mono in self.q]
                rqs = [alpha * mono.T() for mono in self.p]

        assert self._check_unique(lqs), "lqs must be unique"
        assert self._check_unique(rqs), "rqs must be unique"
        lop = BBLogicalQubit(alpha, self.code.l, self.code.m, lop_t, primed, lqs, rqs)
        return lop

    @staticmethod
    def _check_unique(lops: list[Monomial]) -> bool:
        for i, lop in enumerate(lops):
            for j in range(i + 1, len(lops)):
                if lop.as_tuple() == lops[j].as_tuple():
                    return False
        return True

    @staticmethod
    def from_lop_basis(code: BBCode, lop_basis: BBLopBasisSearchResult) -> "CrossBBAut":
        p_pows = lop_basis.p
        q_pows = lop_basis.q
        r_pows = lop_basis.r
        s_pows = lop_basis.s
        # aut.alphas_x_unp = lop_basis.alphas_x_unp
        # aut.alphas_z_unp = lop_basis.alphas_z_unp
        # aut.alphas_x_pri = lop_basis.alphas_x_pri
        # aut.alphas_z_pri = lop_basis.alphas_z_pri
        # aut.lxs_unp = lop_basis.lxs_unp
        # aut.lzs_unp = lop_basis.lzs_unp
        # aut.lxs_pri = lop_basis.lxs_pri
        # aut.lzs_pri = lop_basis.lzs_pri
        aut = CrossBBAut(
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

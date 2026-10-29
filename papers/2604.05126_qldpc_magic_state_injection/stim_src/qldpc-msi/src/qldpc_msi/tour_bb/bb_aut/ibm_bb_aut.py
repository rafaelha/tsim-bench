# IBM's gross code's automorphism group
# @docs: https://arxiv.org/abs/2308.07915, Section 9
from typing import override

from ..code import BBCode
from ..ring import Monomial
from .base_bb_aut import BaseBBAut, BBLogicalQubit


class IBMBBAut(BaseBBAut):
    """IBM's gross code's automorphism group.
    Docs: https://arxiv.org/abs/2308.07915, Section 9.
    """

    def __init__(self, code: BBCode):
        assert (code.n, code.k, code.d) == (144, 12, 12), "only support gross code for now"
        super().__init__(code)
        self.f_pows = [
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (6, 0),
            (7, 0),
            (8, 0),
            (9, 0),  # y = 0 row
            (1, 3),
            (5, 3),
            (7, 3),
            (11, 3),
        ]  # y = 3 row
        self.g_pows = [(0, 2), (0, 4), (1, 0), (1, 2), (2, 1), (2, 3)]  # x = 0 col
        self.h_pows = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 3)]  # x = 0 col
        self.f = [self.ring.monomial(*f) for f in self.f_pows]
        self.g = [self.ring.monomial(*g) for g in self.g_pows]
        self.h = [self.ring.monomial(*h) for h in self.h_pows]
        self.moduli = (self.code.l, self.code.m)

    @override
    def find_valid_alphas(self, lop_t: str, primed: bool) -> list[Monomial]:
        """Find valid alphas (subscripts) for the logical operator. For IBM's gross code,
        primed and unprimed blocks are using the same set of valid alphas.
        See Section 9.1 of the paper.
        """
        if lop_t == "X":
            # {1, y, x2y, x2y5, x3y2, x4}
            unprimed_alphas = [(0, 0), (0, 1), (2, 1), (2, 5), (3, 2), (4, 0)]
        else:
            # {y, y5, xy, 1, x4, x5y2},
            unprimed_alphas = [(0, 1), (0, 5), (1, 1), (0, 0), (4, 0), (5, 2)]
        return [self.ring.monomial(*alpha) for alpha in unprimed_alphas]

    @override
    def get_logical_qubit(self, alpha: Monomial, lop_t: str, primed: bool) -> BBLogicalQubit:
        """Get the logical qubits for the given alpha. See Section 9.1, Eq. (16)."""
        assert lop_t in ["X", "Z"]
        if not primed:  # non-prime block
            if lop_t == "X":
                lqs = [alpha * mono for mono in self.f]  # alpha * f
                rqs = []
            else:
                lqs = [alpha * mono.T() for mono in self.h]  # alpha * h^T
                rqs = [alpha * mono.T() for mono in self.g]  # alpha * g^T
        else:  # prime block
            if lop_t == "X":
                lqs = [alpha * mono for mono in self.g]  # alpha * g
                rqs = [alpha * mono for mono in self.h]  # alpha * h
            else:
                lqs = []
                rqs = [alpha * mono.T() for mono in self.f]  # alpha * f^T

        return BBLogicalQubit(alpha, self.code.l, self.code.m, lop_t, primed, lqs, rqs)

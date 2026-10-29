import itertools
from dataclasses import dataclass, field
from typing import Counter

import galois
import numpy as np

from ..code import BBCode
from ..ring import Monomial, Polynomial
from .base_bb_aut import BBLogicalQubit
from .search_lops import get_anticommuting_lxs_and_lzs, get_anticommuting_mat


@dataclass
class BBLopBasisSearchResult:
    p: list[tuple[int, int]] = field(default_factory=list)
    q: list[tuple[int, int]] = field(default_factory=list)
    r: list[tuple[int, int]] = field(default_factory=list)
    s: list[tuple[int, int]] = field(default_factory=list)
    alphas_x_unp: list[tuple[int, int]] = field(default_factory=list)
    alphas_z_unp: list[tuple[int, int]] = field(default_factory=list)
    alphas_x_pri: list[tuple[int, int]] = field(default_factory=list)
    alphas_z_pri: list[tuple[int, int]] = field(default_factory=list)
    # lxs_unp: list[BBLogicalQubit] = field(default_factory=list)
    # lxs_pri: list[BBLogicalQubit] = field(default_factory=list)
    # lzs_unp: list[BBLogicalQubit] = field(default_factory=list)
    # lzs_pri: list[BBLogicalQubit] = field(default_factory=list)


def _solve_gB_plus_hA_eq_0(A: galois.GF2, B: galois.GF2, M_size: int) -> galois.GF2:
    composed_matrix = galois.GF2(np.hstack([B, A]))
    print(f"{composed_matrix.shape=}")
    composed_matrix = composed_matrix.row_reduce()
    print(f"{composed_matrix.shape=}")
    null_space = composed_matrix.null_space()
    print(f"{null_space.shape=}")
    # gs = null_space[:, :M_size]
    # hs = null_space[:, M_size:]
    # assert isinstance(gs, galois.GF2)
    # assert isinstance(hs, galois.GF2)
    return null_space


def _solve_fB_eq_0(B: galois.GF2) -> galois.GF2:
    return B.null_space()


def _build_weight_to_vecs(vecs: galois.GF2) -> dict[int, list[galois.GF2]]:
    weight_to_vecs = {}
    for vec in vecs:
        weight = vec.nonzero()[0].size
        if weight not in weight_to_vecs:
            weight_to_vecs[weight] = []
        weight_to_vecs[weight].append(vec)

    weight_to_vecs = {int(k): v for k, v in sorted(weight_to_vecs.items(), key=lambda item: item[0])}
    return weight_to_vecs


def search_lop_basis_by_fgh(code: BBCode, n_sols: int = 1) -> list[BBLopBasisSearchResult]:
    ring = code.ring
    # Get the monomial basis
    basis = ring.get_all_monomials()
    M_size = len(basis)
    # print("Monomial basis:", basis)
    print("M_size:", M_size)
    print(f"{code.l=}, {code.m=}")
    # Construct the matrix representation of A using galois.GF2
    A_matrix = construct_matrix(code.a_pows, code.l, code.m)
    B_matrix = construct_matrix(code.b_pows, code.l, code.m)
    print(f"{code.a_pows=}")
    print(f"{code.b_pows=}")

    assert np.all((code.Hx @ code.Hz.T) % 2 == 0)

    assert np.array_equal(np.array(A_matrix), code.A.T)
    assert np.array_equal(np.array(B_matrix), code.B.T)
    fs = _solve_fB_eq_0(B_matrix)
    print(f"{len(fs)=}")
    ghs = _solve_gB_plus_hA_eq_0(A_matrix, B_matrix, M_size)
    print(f"{len(ghs)=}")
    all_zeros_vec = np.zeros(M_size)
    composed_matrix = galois.GF2(np.hstack([B_matrix, A_matrix]))
    for vec in ghs:
        transformed_vec = composed_matrix @ vec
        # print("Transformed vector shape:", transformed_vec.shape)
        assert np.array_equal(transformed_vec, all_zeros_vec)

    min_weight = np.inf
    for vec in ghs:
        weight = vec.nonzero()[0].size
        if weight < min_weight:
            min_weight = weight
    print(f"{min_weight=}")

    weight_to_fs = _build_weight_to_vecs(fs)
    weight_to_ghs = _build_weight_to_vecs(ghs)

    # ignore those with weight less than d
    weight_to_fs = {k: v for k, v in weight_to_fs.items() if k >= code.d}
    weight_to_ghs = {k: v for k, v in weight_to_ghs.items() if k >= code.d}
    print(f"{weight_to_fs.keys()=}")
    print(f"{weight_to_ghs.keys()=}")

    sols = []
    fs = weight_to_fs[min(weight_to_fs.keys())]
    ghs = weight_to_ghs[8]
    for comb_i, (vec_f, vec_gh) in enumerate(itertools.product(fs, ghs)):
        g = vec_gh[:M_size]
        h = vec_gh[M_size:]
        f_monos = ring.get_monomials_from_vec(vec_f)
        g_monos = ring.get_monomials_from_vec(g)
        h_monos = ring.get_monomials_from_vec(h)
        # print(f"{len(f_monos)=}, {len(g_monos)=}, {len(h_monos)=}")
        if len(f_monos) == 0 or len(g_monos) == 0 or len(h_monos) == 0:
            print(f"some of {len(f_monos)=}, {len(g_monos)=}, {len(h_monos)=} are empty")
            continue
        lxs_unp, lzs_unp, lxs_pri, lzs_pri = get_all_lops_by_fgh(f_monos, g_monos, h_monos)

        rank = get_logical_basis_dim(lxs_unp, lzs_unp, lxs_pri, lzs_pri)
        if rank < code.k // 2:
            print(f"rank of {comb_i=} is {rank}, less than {code.k // 2}; this is not a valid basis")
            continue
        # print(f"{len(lxs_unprime)=}, {len(lzs_unprime)=}")

        # try to find valid unprimed and prime subscripts
        valid_unp_pairs = get_anticommuting_lxs_and_lzs(lxs_unp, lzs_unp, code.k // 2, max_n_sols=1)[0]
        # print(f"{type(valid_unp_pairs[0])=}, {type(valid_unp_pairs[1])=}")
        if len(valid_unp_pairs) == 0:
            print(f"no unprime solutions found for {comb_i=}")
            continue
        valid_pri_pairs = get_anticommuting_lxs_and_lzs(lxs_pri, lzs_pri, code.k // 2, max_n_sols=1)[0]
        if len(valid_pri_pairs) == 0:
            print(f"no prime solutions found for {comb_i=}")
            continue

        # due to the duality, actually we only need to search one set of valid pairs
        # but we might have other requirements, e.g., minimize the overlap of X and Z support of a logical qubit
        assert np.array_equal(valid_unp_pairs[0], valid_pri_pairs[0])
        assert np.array_equal(valid_unp_pairs[1], valid_pri_pairs[1])
        all_monos = ring.get_all_monomials()
        alphas_x_unp = [all_monos[i] for i in valid_unp_pairs[0]]
        alphas_z_unp = [all_monos[i] for i in valid_unp_pairs[1]]
        alphas_x_pri = [all_monos[i] for i in valid_pri_pairs[0]]
        alphas_z_pri = [all_monos[i] for i in valid_pri_pairs[1]]
        sols.append(BBLopBasisSearchResult(p, q, r, s, alphas_x_unp, alphas_z_unp, alphas_x_pri, alphas_z_pri))
        if len(sols) >= n_sols:
            break

    return sols


class BBLopBasisSearcher:
    """Find the basis of logical operators for a given BB code."""

    def __init__(self, code: BBCode, n_sols: int = 1):
        self.code = code
        self.ring = code.ring
        self.n_sols = n_sols

    def search(self) -> list[BBLopBasisSearchResult]:
        """Search for the basis of logical operators for the given BB code.
        Solve gB + hA = 0, corresponding to null space of [B, A].

        Returns:
            tuple[list[Monomial], list[Monomial], list[Monomial], list[Monomial]]: p, q, r, s
        """

        # Get the monomial basis
        basis = self.ring.get_all_monomials()
        M_size = len(basis)
        # print("Monomial basis:", basis)
        # print("M_size:", M_size)
        # Construct the matrix representation of A using galois.GF2
        A_matrix = construct_matrix(self.code.a_pows, self.code.l, self.code.m)
        B_matrix = construct_matrix(self.code.b_pows, self.code.l, self.code.m)

        assert np.array_equal(np.array(A_matrix), self.code.A.T)
        assert np.array_equal(np.array(B_matrix), self.code.B.T)
        # print("Matrix representation of A:")
        # print(A_matrix)
        # print("Matrix representation of B:")
        # print(B_matrix)
        composed_matrix = galois.GF2(np.hstack([B_matrix, A_matrix]))
        # print("Composed matrix shape:", composed_matrix.shape)
        composed_matrix = composed_matrix.row_reduce()
        column_space = composed_matrix.column_space()
        # print("Column space shape:", column_space.shape)
        null_space = composed_matrix.null_space()
        # print("Null space of composed matrix, shape:", null_space.shape)
        all_zeros_vec = np.zeros(M_size)
        for vec in null_space:
            transformed_vec = composed_matrix @ vec
            # print("Transformed vector shape:", transformed_vec.shape)
            assert np.array_equal(transformed_vec, all_zeros_vec)

        # rsts = get_min_weight_combination_by_brute_force(null_space)
        rsts = []
        min_weight = np.inf
        for vec in null_space:
            weight = vec.nonzero()[0].size
            if weight < min_weight:
                min_weight = weight
                rsts = [(vec, min_weight)]
            elif weight == min_weight:
                rsts.append((vec, min_weight))
        # print(f"{len(rsts)=}, {min_weight=}")

        weight_to_vecs = _build_weight_to_vecs(null_space)
        # print(f"{Counter({k: len(v) for k, v in weight_to_vecs.items()})=}")
        weight_to_vecs = {k: v for k, v in sorted(weight_to_vecs.items(), key=lambda item: item[0])}
        weight_to_vecs = {k: v for k, v in weight_to_vecs.items() if k >= self.code.d}
        cnt = Counter({k: len(v) for k, v in weight_to_vecs.items()})
        print(f"{cnt=}")

        rsts = list(itertools.chain.from_iterable(weight_to_vecs.values()))

        # count rsts[i] having 1 in how many positions with rsts[j]
        # overlap_cnt_matrix = np.zeros((len(rsts), len(rsts)))
        # for i in range(len(rsts)):
        #     for j in range(len(rsts)):
        #         if i != j:
        #             overlap_cnt_matrix[i, j] = np.sum(np.array(rsts[i][0]) & np.array(rsts[j][0]))
        # print(overlap_cnt_matrix)
        sols = []

        for comb_i, (basis1, basis2) in enumerate(itertools.combinations(rsts, 2)):
            # assert weight1 == weight2
            # print(f"{weight1=}, {weight2=}")
            p = self.ring.get_monomials_from_vec(basis1[:M_size])
            q = self.ring.get_monomials_from_vec(basis1[M_size:])
            # r = self.ring.get_monomials_from_vec(basis2[:M_size])
            # s = self.ring.get_monomials_from_vec(basis2[M_size:])
            s = [e.T() for e in self.ring.get_monomials_from_vec(basis2[:M_size])]
            r = [e.T() for e in self.ring.get_monomials_from_vec(basis2[M_size:])]
            lxs_unp, lzs_pri = get_all_lops_by_basis_poly(p, q, "X")
            lxs_pri, lzs_unp = get_all_lops_by_basis_poly(r, s, "Z")

            rank = get_logical_basis_dim(lxs_unp, lzs_unp, lxs_pri, lzs_pri)
            if rank < self.code.k // 2:
                # print(f"rank of {comb_i=} is {rank}, less than {self.code.k // 2}; this is not a valid basis")
                continue
            else:
                assert rank == self.code.k // 2
            # print(f"{len(lxs_unprime)=}, {len(lzs_unprime)=}")

            # try to find valid unprimed and prime subscripts
            valid_unp_pairs = get_anticommuting_lxs_and_lzs(lxs_unp, lzs_unp, self.code.k // 2, max_n_sols=1)[0]
            # print(f"{type(valid_unp_pairs[0])=}, {type(valid_unp_pairs[1])=}")
            if len(valid_unp_pairs) == 0:
                print(f"no unprime solutions found for {comb_i=}")
                continue
            valid_pri_pairs = get_anticommuting_lxs_and_lzs(lxs_pri, lzs_pri, self.code.k // 2, max_n_sols=1)[0]
            if len(valid_pri_pairs) == 0:
                print(f"no prime solutions found for {comb_i=}")
                continue

            # due to the duality, actually we only need to search one set of valid pairs
            # but we might have other requirements, e.g., minimize the overlap of X and Z support of a logical qubit
            assert np.array_equal(valid_unp_pairs[0], valid_pri_pairs[0])
            assert np.array_equal(valid_unp_pairs[1], valid_pri_pairs[1])
            all_monos = self.ring.get_all_monomials()
            alphas_x_unp = [all_monos[i] for i in valid_unp_pairs[0]]
            alphas_z_unp = [all_monos[i] for i in valid_unp_pairs[1]]
            alphas_x_pri = [all_monos[i] for i in valid_pri_pairs[0]]
            alphas_z_pri = [all_monos[i] for i in valid_pri_pairs[1]]
            sols.append(
                BBLopBasisSearchResult(
                    [e.as_tuple() for e in p],
                    [e.as_tuple() for e in q],
                    [e.as_tuple() for e in r],
                    [e.as_tuple() for e in s],
                    [e.as_tuple() for e in alphas_x_unp],
                    [e.as_tuple() for e in alphas_z_unp],
                    [e.as_tuple() for e in alphas_x_pri],
                    [e.as_tuple() for e in alphas_z_pri],
                )
            )
            if len(sols) >= self.n_sols:
                break

        return sols


def _get_random_logical_basis(basis: galois.GF2, n_trgt_basis: int, max_tries: int, min_weight: int) -> galois.GF2:
    n_basis = basis.shape[0]
    for _ in range(max_tries):
        basis_indices = np.random.choice(n_basis, size=n_trgt_basis, replace=False)
        basis_selected = basis[basis_indices]
        assert isinstance(basis_selected, galois.GF2)
        rank = basis_selected.row_space().shape[0]
        if rank < n_trgt_basis:
            continue
        for vec in basis_selected:
            weight = len(vec.nonzero()[0])
            if weight < min_weight:
                min_weight = weight
                rsts = [(vec, min_weight)]
            elif weight == min_weight:
                rsts.append((vec, min_weight))


def get_logical_basis_dim(
    lxs_unp: list[BBLogicalQubit],
    lzs_unp: list[BBLogicalQubit],
    lxs_pri: list[BBLogicalQubit],
    lzs_pri: list[BBLogicalQubit],
) -> int:
    # lxs_unp, lzs_pri = get_all_lops_by_basis_poly(p, q, "X")
    # lxs_pri, lzs_unp = get_all_lops_by_basis_poly(r, s, "Z")
    anticomm_mat = get_anticommuting_mat(lxs_unp, lzs_unp)
    # print(f"{anticomm_mat=}")
    rank_unp = galois.GF2(anticomm_mat).row_space().shape[0]
    anticomm_mat = get_anticommuting_mat(lxs_pri, lzs_pri)
    # print(f"{anticomm_mat=}")
    rank_pri = galois.GF2(anticomm_mat).row_space().shape[0]
    assert rank_unp == rank_pri, f"violate duality of X and Z"
    return rank_unp


def _get_minimum_weight_basis(basis: galois.GF2) -> list[tuple[galois.GF2, int]]:
    rsts = []
    min_weight = np.inf
    for vec in basis:
        weight = len(vec.nonzero()[0])
        if weight < min_weight:
            min_weight = weight
            rsts = [(vec, min_weight)]
        elif weight == min_weight:
            rsts.append((vec, min_weight))
    return rsts


def construct_matrix(A: list[tuple[int, int]], l: int, m: int) -> galois.GF2:
    basis = get_monomial_basis(l, m)
    size = len(basis)
    A_matrix = galois.GF2.Zeros((size, size))  # Initialize a zero matrix over F2

    for col, (a, b) in enumerate(basis):
        result = apply_A(A, a, b, l, m)
        for i, j in result:
            row = basis.index((i, j))
            A_matrix[row, col] = 1  # Set the entry to 1 in F2

    return A_matrix


def get_monomial_basis(l: int, m: int) -> list[tuple[int, int]]:
    return [(i, j) for i in range(l) for j in range(m)]


def apply_A(A: list[tuple[int, int]], a: int, b: int, l: int, m: int) -> list[tuple[int, int]]:
    result = []
    for i, j in A:
        # Multiply x^i y^j by x^a y^b and simplify using x^l = 1 and y^m = 1
        new_i = (i + a) % l
        new_j = (j + b) % m
        result.append((new_i, new_j))
    return result


def get_all_lops_by_fgh(
    f: list[Monomial], g: list[Monomial], h: list[Monomial]
) -> tuple[list[BBLogicalQubit], list[BBLogicalQubit], list[BBLogicalQubit], list[BBLogicalQubit]]:
    """IBM Nature paper, Eq. (16)."""
    ring = f[0].ring
    lxs_unp = []
    lzs_unp = []
    lxs_pri = []
    lzs_pri = []

    # unprimed X
    for alpha in ring.get_all_monomials():
        L_supp = [alpha * mono for mono in f]
        lxs_unp.append(BBLogicalQubit(alpha, ring.l, ring.m, "X", False, L_supp, []))

    # primed X
    for alpha in ring.get_all_monomials():
        L_supp = [alpha * mono for mono in g]
        R_supp = [alpha * mono for mono in h]
        lxs_pri.append(BBLogicalQubit(alpha, ring.l, ring.m, "X", True, L_supp, R_supp))

    # unprimed Z
    for alpha in ring.get_all_monomials():
        L_supp = [alpha * mono.T() for mono in h]
        R_supp = [alpha * mono.T() for mono in g]
        lzs_unp.append(BBLogicalQubit(alpha, ring.l, ring.m, "Z", False, L_supp, R_supp))

    # primed Z
    for alpha in ring.get_all_monomials():
        R_supp = [alpha * mono.T() for mono in f]
        lzs_pri.append(BBLogicalQubit(alpha, ring.l, ring.m, "Z", True, [], R_supp))

    return lxs_unp, lzs_unp, lxs_pri, lzs_pri


def get_all_lops_by_pqrs(
    p: list[Monomial], q: list[Monomial], r: list[Monomial], s: list[Monomial]
) -> tuple[list[BBLogicalQubit], list[BBLogicalQubit]]:
    """Cross et al."""
    ...


def get_all_lops_by_basis_poly(
    p: list[Monomial],
    q: list[Monomial],
    unprimed_op_t: str,
) -> tuple[list[BBLogicalQubit], list[BBLogicalQubit]]:
    ring = p[0].ring if len(p) > 0 else q[0].ring
    mono_basis = ring.get_all_monomials()
    lxs: list[BBLogicalQubit] = []
    lzs: list[BBLogicalQubit] = []

    match unprimed_op_t:
        case "X":
            X_basis1 = Polynomial(p)
            X_basis2 = Polynomial(q)
            Z_basis1 = X_basis2.T()
            Z_basis2 = X_basis1.T()
            is_X_primed = False
        case "Z":  # p == r, q == s
            Z_basis1 = Polynomial(p)
            Z_basis2 = Polynomial(q)
            X_basis1 = Z_basis2.T()
            X_basis2 = Z_basis1.T()
            is_X_primed = True
        case _:
            raise ValueError(f"Invalid operator type: {unprimed_op_t}")

    for alpha in mono_basis:
        L_supp = [alpha * mono for mono in X_basis1.monomials]
        R_supp = [alpha * mono for mono in X_basis2.monomials]
        lx = BBLogicalQubit(alpha, ring.l, ring.m, "X", is_X_primed, L_supp, R_supp)
        lxs.append(lx)

    for alpha in mono_basis:
        L_supp = [alpha * mono for mono in Z_basis1.monomials]
        R_supp = [alpha * mono for mono in Z_basis2.monomials]
        lz = BBLogicalQubit(alpha, ring.l, ring.m, "Z", not is_X_primed, L_supp, R_supp)
        lzs.append(lz)

    return lxs, lzs

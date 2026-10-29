import numpy as np
import qldpc

from ..code import BBCode
from .cross_bb_aut import CrossBBAut
from .ibm_bb_aut import IBMBBAut
from .lop_basis_searcher import (
    BBLopBasisSearcher,
    _solve_gB_plus_hA_eq_0,
    construct_matrix,
    get_logical_basis_dim,
    search_lop_basis_by_fgh,
)


def test_basis_search():
    code = BBCode.from_n(144)
    basis_searcher = BBLopBasisSearcher(code)
    rsts = basis_searcher.search()
    print(f"{rsts=}")


def test_196_code_basis_search_fgh():
    code = BBCode.from_n(196)
    rst = search_lop_basis_by_fgh(code, n_sols=1)
    print(f"{rst=}")


def test_196_code_basis_search_pqrs():
    code = BBCode.from_n(196)
    searcher = BBLopBasisSearcher(code, 10)
    rst = searcher.search()
    print(f"{rst=}")


def test_get_lop_by_package():
    code = BBCode.from_n(196)
    qldpc_code = qldpc.codes.CSSCode(code.Hx, code.Hz)
    print(f"{qldpc_code.dimension=}")
    d_upper_bound = qldpc_code.get_distance_bound(100000)
    print(f"{d_upper_bound=}")
    lxs = qldpc_code.get_logical_ops(pauli=qldpc.objects.Pauli.X)
    lzs = qldpc_code.get_logical_ops(pauli=qldpc.objects.Pauli.Z)
    for lx, lz in zip(lxs, lzs):
        weight_lx = np.nonzero(lx)[0].size
        weight_lz = np.nonzero(lz)[0].size  # type: ignore
        print(f"{weight_lx=}, {weight_lz=}")


def test_get_logical_basis_dim():
    code = BBCode.from_n(144)
    aut = CrossBBAut(code)
    p, q, r, s = aut.p, aut.q, aut.r, aut.s
    rank = get_logical_basis_dim(p, q, r, s)
    assert rank == code.k // 2

    aut = IBMBBAut(code)
    h_trans = [e.T() for e in aut.h]
    g_trans = [e.T() for e in aut.g]
    rank = get_logical_basis_dim(aut.f, [], h_trans, g_trans)
    assert rank == code.k // 2
    A = construct_matrix(code.a_pows, code.l, code.m)
    B = construct_matrix(code.b_pows, code.l, code.m)
    ghs = _solve_gB_plus_hA_eq_0(A, B, code.k // 2)

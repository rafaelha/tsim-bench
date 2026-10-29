import numpy as np
import stim
from qlop.ring import Monomial

from ..code import BBCode
from .tour_bb_aut import TourBBAut


def test_cost():
    """Native rotations cost 1 native measurement"""
    code = BBCode.from_n(144)
    aut = TourBBAut.from_existing_paper(code)
    ps_of_nat_rot = aut.get_pss_of_native_rotation()
    print(len(ps_of_nat_rot))
    for i, ps in enumerate(ps_of_nat_rot):
        if ps == stim.PauliString("_" * (code.k - 1)):
            print(f"i={i}, {ps=}")
            continue
        if ps == stim.PauliString.from_numpy(
            xs=np.zeros(code.k - 1, dtype=np.bool_), zs=np.array([0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], dtype=np.bool_)
        ):
            print(f"i={i}, {ps=}")
        assert aut.get_n_native_meas_by_native_rot(ps) == 1, f"i={i}"


def test_native_paulis_same():
    aut = TourBBAut.from_n(144)
    native_paulis = aut.get_all_available_pauli_strs()
    native_paulis = sorted(native_paulis)
    with open("data/tour_native_paulis/sorted_native_paulis.txt", "r") as f:
        target_paulis = f.readlines()
    target_paulis = [pauli.strip() for pauli in target_paulis]
    for actual_pauli, target_pauli in zip(native_paulis, target_paulis):
        print(f"{actual_pauli=}, {target_pauli=}")
        assert actual_pauli == target_pauli, f"{actual_pauli=}, {target_pauli=}"
    # assert native_paulis == target_paulis, f"{native_paulis=}, {target_paulis=}"


def test_logical_qubits():
    aut = TourBBAut.from_n(144)
    lxs = aut.get_logical_qubits("X")
    lzs = aut.get_logical_qubits("Z")
    n_overlaps = [1] * 12
    n_overlaps[1] = 3
    n_overlaps[5] = 3
    n_overlaps[7] = 3
    n_overlaps[11] = 3

    expected_overlaps = {
        0: [(4, 0)],
        1: [(7, 1), (6, 4), (7, 5)],
        2: [(3, 5)],
        3: [(3, 1)],
        4: [(10, 4)],
        5: [(8, 4), (7, 1), (8, 2)],
        6: [(9, 1)],
        7: [(6, 2), (7, 3), (6, 0)],
        8: [(10, 2)],
        9: [(10, 0)],
        10: [(3, 3)],
        11: [(5, 5), (6, 0), (5, 3)],
    }
    for i, (lx, lz) in enumerate(zip(lxs, lzs)):
        assert not lx.commutes_with(lz), f"{i=}, {lx=}, {lz=}"
        l_overlap, r_overlap = lx.get_support_overlap(lz)
        n_overlap = len(l_overlap) + len(r_overlap)
        assert n_overlap == n_overlaps[i], f"{i=}, {n_overlap=}, {n_overlaps[i]=}"
        actual_overlap = l_overlap + r_overlap
        # print(f"{i}: [{', '.join([str(mono.as_tuple()) for mono in actual_overlap])}],")
        if i in expected_overlaps:
            assert actual_overlap == [
                aut.ring.monomial(*mono) for mono in expected_overlaps[i]
            ], f"{i=}, {actual_overlap=}, {expected_overlaps[i]=}"

    # specific overlaps


def test_commute_with_stabs():
    aut = TourBBAut.from_n(144)
    lxs = aut.get_logical_qubits("X")
    lzs = aut.get_logical_qubits("Z")
    code = aut.code

    assert np.all((code.Hx @ code.Hz.T) % 2 == 0)

    A_monos = [aut.ring.monomial(*pow) for pow in aut.code.a_pows]
    B_monos = [aut.ring.monomial(*pow) for pow in aut.code.b_pows]
    print(f"{A_monos=}, {B_monos=}")

    # pB = aut.ring.monomial(0, 0)
    pBs = []
    for B_mono in B_monos:
        for p_mono in aut.p:
            pBs.append(p_mono * B_mono)
    print(f"{pBs=}, {len(pBs)=}")

    qAs = []
    for A_mono in A_monos:
        for q_mono in aut.q:
            qAs.append(q_mono * A_mono)
    print(f"{qAs=}, {len(qAs)=}")

    pB_plus_qA = pBs + qAs

    parities: dict[Monomial, int] = {}
    for mono in pB_plus_qA:
        if mono not in parities:
            parities[mono] = 0
        parities[mono] += 1
    # print(f"{parities=}, {len(parities)=}")
    assert np.all(np.array(list(parities.values())) == 2), f"{parities=}"

    for i, lx in enumerate(lxs):
        # pauli_indices = lx.ps.pauli_indices()
        # print(f"{pauli_indices=}")
        lx_vec = np.array(lx.to_vec())
        for j, hz in enumerate(code.Hz):
            assert np.sum(lx_vec * hz) % 2 == 0, f"j={j}, {hz.pauli_indices()=}"
        # assert np.all((code.Hz @ lx_vec.reshape(-1, 1)) % 2 == 0), f"{i=}"
    for i, lz in enumerate(lzs):
        lz_vec = lz.to_vec()
        lz_vec = np.array(lz_vec)
        assert np.all((code.Hx @ lz_vec.T) % 2 == 0), f"{i=}"


def test_get_interacting_qids():
    code = BBCode.from_n(144)
    # test X checks
    for qid in range(code.lm):
        l_qids = code._get_interacting_qids("X", qid, "L")
        r_qids = code._get_interacting_qids("X", qid, "R")
        r_qids = [qid + code.lm for qid in r_qids]
        supp = sorted(code.Hx[qid, :].nonzero()[0].tolist())
        assert supp == sorted(l_qids + r_qids), f"{qid=}, {supp=}, {l_qids=}, {r_qids=}"

    # test Z checks
    for qid in range(code.lm):
        l_qids = code._get_interacting_qids("Z", qid, "L")
        r_qids = code._get_interacting_qids("Z", qid, "R")
        r_qids = [qid + code.lm for qid in r_qids]
        supp = sorted(code.Hz[qid, :].nonzero()[0].tolist())
        assert supp == sorted(l_qids + r_qids), f"{qid=}, {supp=}, {l_qids=}, {r_qids=}"

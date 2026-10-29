import numpy as np

from ..code import BBCode
from .synthesize import (
    decompose_pauli_str,
    get_distribution_of_decomposing_arbitrary_pauli_str,
)
from .tour_bb_aut import TourBBAut


def test_synthesize():
    code = BBCode.from_n(144)
    aut = TourBBAut.from_existing_paper(code)
    native_paulis_mat = aut.get_native_paulis_mat()
    native_cnts = get_distribution_of_decomposing_arbitrary_pauli_str(native_paulis_mat, n_samples=100)
    print(native_cnts)


def test_trivial():
    native_paulis_mat = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.bool_)
    target_pauli_str = np.array([1, 0, 0, 1], dtype=np.bool_)
    coeff = decompose_pauli_str(target_pauli_str, native_paulis_mat)
    print(coeff)

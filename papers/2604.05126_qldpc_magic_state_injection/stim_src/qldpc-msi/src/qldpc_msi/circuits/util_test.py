import stim

from qldpc_msi.circuits.util import measure_pauli_product


def test_mpp():
    circ = stim.Circuit()
    pauli_maps = [
        {0: "X", 1: "Z"},
        {2: "Y"},
    ]
    measure_pauli_product(circ, pauli_maps)
    assert circ == stim.Circuit("MPP X0*Z1 Y2")

import numpy as np
import stim


def measure_pauli_product(
    circ: stim.Circuit,
    pauli_maps: list[dict[int, str]],
) -> None:
    """Measure the Pauli products of the given Pauli maps.

    Args:
        circ: The circuit to append the MPP operation to.
        pauli_maps: A list of Pauli maps to measure. Each Pauli map is a dictionary of qubit indices to Pauli strings.

    Example:
        >>> circ = stim.Circuit()
        >>> pauli_maps = [
        >>>     {0: "X", 1: "Z"},
        >>>     {2: "Y"},
        >>> ]
        >>> measure_pauli_product_v1(circ, pauli_maps)
        >>> print(circ)
        MPP X0*Z1 Y2
    """
    stim_targets = []
    for pauli_map in pauli_maps:
        for uid, pauli in pauli_map.items():
            stim_targets.append(stim.target_pauli(uid, pauli))
            stim_targets.append(stim.target_combiner())
        stim_targets.pop()

    circ.append_operation("MPP", stim_targets)


def H_to_pauli_maps(H: np.ndarray, basis: str) -> list[dict[int, str]]:
    """Convert a parity check matrix to a list of Pauli maps.

    Args:
        H: A parity check matrix. Each row is a stabilizer.
        basis: The basis of the stabilizer.

    Returns:
        A list of Pauli maps.
    """
    return [{i: basis for i in row.nonzero()[0].tolist()} for row in H]

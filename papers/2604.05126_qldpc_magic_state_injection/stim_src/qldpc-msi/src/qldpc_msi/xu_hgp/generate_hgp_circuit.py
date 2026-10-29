import copy
import re
from typing import Dict

import numpy as np
import stim
from numpy.typing import NDArray

from .CircuitScheduling import ColorationCircuit


def generate_hgp_circuit(
    code, error_params: Dict[str, float], num_rounds: int, schedule: str = "coloration"
) -> stim.Circuit:
    """Generate Stim circuit for HGP code memory. The memory experiment is in
    the X basis.
    Args:
        code: HGP code object produced from the bposd library constructor.
        error_params: error parameters for simulation. The noise model is a
            somewhat specific neutral atom noise model.
        num_rounds: number of rounds of stabilizer measurements before transversal measurement.
        schedule: syndrome extraction schedule.
    """
    hx = code.hx
    hz = code.hz
    lx = code.lx
    if schedule == "coloration":
        scheduling_X = ColorationCircuit(code.hx)
        scheduling_Z = ColorationCircuit(code.hz)
    else:
        raise ValueError("Invalid schedule type")

    data_indices = list(np.arange(0, np.shape(hx)[1]))
    n = len(data_indices)
    n_Z_ancilla, n_X_ancilla = np.shape(hz)[0], np.shape(hx)[0]
    Z_ancilla_indices = list(np.arange(n, n + n_Z_ancilla))
    X_ancilla_indices = list(np.arange(n + n_Z_ancilla, n + n_Z_ancilla + n_X_ancilla))
    z_stab_weight = int(np.sum(hz[0, :]))
    x_stab_weight = int(np.sum(hx[0, :]))

    # define actual circuit using the schedule specified above
    circuit_init = stim.Circuit()
    circuit_init.append("RX", data_indices)
    circuit_init.append("R", X_ancilla_indices + Z_ancilla_indices)

    circuit_stab_meas_rep1 = stim.Circuit()
    circuit_stab_meas_rep1.append("H", X_ancilla_indices)
    circuit_stab_meas_rep1.append("DEPOLARIZE1", X_ancilla_indices, (error_params["p_state_p"]))
    circuit_stab_meas_rep1.append("TICK")

    # X stabilizers
    for time_step in range(len(scheduling_X)):
        idling_qubits = data_indices + X_ancilla_indices
        idling_data_indices = list(copy.deepcopy(data_indices))
        circuit_stab_meas_rep1.append("DEPOLARIZE1", idling_qubits, (error_params["p_idling_gate"]))
        for j in scheduling_X[time_step]:
            X_ancilla_index = X_ancilla_indices[j]
            data_index = scheduling_X[time_step][j]
            circuit_stab_meas_rep1.append("CX", [X_ancilla_index, data_index])
            if data_index in idling_data_indices:
                idling_data_indices.pop(idling_data_indices.index(data_index))
        circuit_stab_meas_rep1.append(
            "DEPOLARIZE1", idling_data_indices, (error_params["p_i"])
        )  # idling errors for qubits that are not being checked
        circuit_stab_meas_rep1.append("TICK")

    # Z stabilizers
    circuit_stab_meas_rep1.append("DEPOLARIZE1", Z_ancilla_indices, (error_params["p_state_p"]))
    circuit_stab_meas_rep1.append("TICK")
    for time_step in range(len(scheduling_Z)):
        idling_qubits = data_indices + Z_ancilla_indices
        idling_data_indices = list(copy.deepcopy(data_indices))
        circuit_stab_meas_rep1.append("DEPOLARIZE1", idling_qubits, (error_params["p_idling_gate"]))
        for j in scheduling_Z[time_step]:
            Z_ancilla_index = Z_ancilla_indices[j]
            data_index = scheduling_Z[time_step][j]
            circuit_stab_meas_rep1.append("CX", [data_index, Z_ancilla_index])
            if data_index in idling_data_indices:
                idling_data_indices.pop(idling_data_indices.index(data_index))
        circuit_stab_meas_rep1.append(
            "DEPOLARIZE1", idling_data_indices, (error_params["p_i"])
        )  # idling errors for qubits that are not being checked
        circuit_stab_meas_rep1.append("TICK")

    circuit_stab_meas_rep1.append("H", X_ancilla_indices)
    circuit_stab_meas_rep1.append(
        "DEPOLARIZE1", X_ancilla_indices, (3 / 2 * error_params["p_m"])
    )  # Add the measurement error
    circuit_stab_meas_rep1.append("MR", Z_ancilla_indices + X_ancilla_indices)

    circuit_stab_meas_rep1.append("SHIFT_COORDS", [], (1))
    for i in range(len(X_ancilla_indices)):
        circuit_stab_meas_rep1.append("DETECTOR", [stim.target_rec(-len(X_ancilla_indices) + i)], (0))
    circuit_stab_meas_rep1.append("TICK")

    # reps with difference detectors
    circuit_stab_meas_rep2 = stim.Circuit()
    circuit_stab_meas_rep2.append("H", X_ancilla_indices)
    circuit_stab_meas_rep2.append("DEPOLARIZE1", X_ancilla_indices, (error_params["p_state_p"]))
    circuit_stab_meas_rep2.append("TICK")

    # Apply CX gates for the X stabilizers
    for time_step in range(len(scheduling_X)):
        idling_qubits = data_indices + X_ancilla_indices
        circuit_stab_meas_rep2.append("DEPOLARIZE1", idling_qubits, (error_params["p_idling_gate"]))
        idling_data_indices = list(copy.deepcopy(data_indices))
        for j in scheduling_X[time_step]:
            X_ancilla_index = X_ancilla_indices[j]
            data_index = scheduling_X[time_step][j]
            # data_index = supported_data_qubits[i]
            circuit_stab_meas_rep2.append("CX", [X_ancilla_index, data_index])
            if data_index in idling_data_indices:
                idling_data_indices.pop(idling_data_indices.index(data_index))
        circuit_stab_meas_rep2.append(
            "DEPOLARIZE1", idling_data_indices, (error_params["p_i"])
        )  # idling errors for qubits that are not being checked
        circuit_stab_meas_rep2.append("TICK")

    circuit_stab_meas_rep2.append("DEPOLARIZE1", Z_ancilla_indices, (error_params["p_state_p"]))

    circuit_stab_meas_rep2.append("TICK")
    # Appy CX gates for the Z stabilziers
    for time_step in range(len(scheduling_Z)):
        idling_qubits = data_indices + Z_ancilla_indices
        circuit_stab_meas_rep2.append("DEPOLARIZE1", idling_qubits, (error_params["p_idling_gate"]))
        idling_data_indices = list(copy.deepcopy(data_indices))
        for j in scheduling_Z[time_step]:
            Z_ancilla_index = Z_ancilla_indices[j]
            data_index = scheduling_Z[time_step][j]
            # data_index = supported_data_qubits[i]
            circuit_stab_meas_rep2.append("CX", [data_index, Z_ancilla_index])
            if data_index in idling_data_indices:
                idling_data_indices.pop(idling_data_indices.index(data_index))
        circuit_stab_meas_rep2.append(
            "DEPOLARIZE1", idling_data_indices, (error_params["p_i"])
        )  # idling errors for qubits that are not being checked
        circuit_stab_meas_rep2.append("TICK")

    # Measure the ancillas
    circuit_stab_meas_rep2.append("H", X_ancilla_indices)
    circuit_stab_meas_rep2.append("DEPOLARIZE1", X_ancilla_indices, (3 / 2 * error_params["p_m"]))
    circuit_stab_meas_rep2.append("MR", Z_ancilla_indices + X_ancilla_indices)

    # only adding detectors for the X stabilizers
    for i in range(len(X_ancilla_indices)):
        circuit_stab_meas_rep2.append(
            "DETECTOR",
            [
                stim.target_rec(-len(X_ancilla_indices) + i),
                stim.target_rec(-len(X_ancilla_indices) + i - len(Z_ancilla_indices) - len(X_ancilla_indices)),
            ],
            (0),
        )
    circuit_stab_meas_rep2.append("TICK")

    ## Final projective measurement layer
    circuit_final_meas = stim.Circuit()

    circuit_final_meas.append("DEPOLARIZE1", data_indices, (error_params["p_m"]))  # Add the measurement error
    circuit_final_meas.append("MX", data_indices)
    circuit_final_meas.append("SHIFT_COORDS", [], (1))

    # Obtain the syndroms
    for i in range(len(X_ancilla_indices)):
        supported_data_indices = list(np.where(hx[X_ancilla_indices[i] - n - n_Z_ancilla, :] == 1)[0])

        # append the previous round of X stabilizer measurement
        rec_indices = [-len(data_indices) - len(X_ancilla_indices) + i]
        for data_index in supported_data_indices:
            rec_indices.append(-len(data_indices) + data_index)

        circuit_final_meas.append("Detector", [stim.target_rec(rec_index) for rec_index in rec_indices], (0))

    # Obtain the logical measurements result
    for i in range(len(lx)):
        logical_X_qubit_indices = list(np.where(lx[i, :] == 1)[0])
        circuit_final_meas.append(
            "OBSERVABLE_INCLUDE",
            [stim.target_rec(-len(data_indices) + data_index) for data_index in logical_X_qubit_indices],
            (i),
        )

    circuit = circuit_init + circuit_stab_meas_rep1 + (num_rounds - 1) * circuit_stab_meas_rep2 + circuit_final_meas

    # Add noise
    noisy_circuit = circuit
    ## Add CX gate errors
    noisy_circuit = AddCXError(noisy_circuit, "DEPOLARIZE2(%f)" % error_params["p_CX"])
    return noisy_circuit


## CX gate errors
def AddCXError(circuit: stim.Circuit, error_instruction: str) -> stim.Circuit:
    circuit_str = str(circuit)

    ## Find all the unique cx instructions
    cx_instructions = re.findall("CX.*\n", circuit_str)
    unique_cx_instructions = list(set(cx_instructions))
    unique_cx_instructions

    ## Add gate errors after each cx instruction
    for cx_ins in unique_cx_instructions:
        circuit_str = circuit_str.replace(cx_ins, cx_ins + cx_ins.replace("CX", error_instruction))

    modified_circuit = stim.Circuit(circuit_str)
    return modified_circuit


def build_xu_hgp_one_se(
    *,
    data_indices: list[int],
    X_ancilla_indices: list[int],
    Z_ancilla_indices: list[int],
    scheduling_X: ColorationCircuit,
    scheduling_Z: ColorationCircuit,
    error_params: Dict[str, float],
) -> stim.Circuit:
    """Build **one** syndrome-extraction (SE) round without any DETECTOR/SHIFT_COORDS.

    This function factors out the *common* SE body shared by
    `circuit_stab_meas_rep1` and `circuit_stab_meas_rep2` in `generate_hgp_circuit`.

    The Z ancillas are measured first, then the X ancillas.

    Notes:
        - Includes ancilla pre-rotations, scheduled CX layers, idling noise, and MR on ancillas.
        - Does **not** include any DETECTOR instructions.
        - Does **not** include SHIFT_COORDS or the trailing TICK that comes after detectors.
    """
    se = stim.Circuit()

    # DEPRECATED: Prepare X-ancillas in |+> (via H), Z-ancillas in |0> (they were reset elsewhere).
    # NEW LOGIC: init right here.
    se.append("R", X_ancilla_indices + Z_ancilla_indices)
    se.append("H", X_ancilla_indices)
    se.append("DEPOLARIZE1", X_ancilla_indices, (error_params["p_state_p"]))
    se.append("TICK")

    # X stabilizers
    for time_step in range(len(scheduling_X)):
        idling_qubits = data_indices + X_ancilla_indices
        idling_data_indices = list(copy.deepcopy(data_indices))
        se.append("DEPOLARIZE1", idling_qubits, (error_params["p_idling_gate"]))
        for j in scheduling_X[time_step]:
            X_ancilla_index = X_ancilla_indices[j]
            data_index = scheduling_X[time_step][j]
            se.append("CX", [X_ancilla_index, data_index])
            if data_index in idling_data_indices:
                idling_data_indices.pop(idling_data_indices.index(data_index))
        # idling errors for data qubits that are not being checked in this time step
        se.append("DEPOLARIZE1", idling_data_indices, (error_params["p_i"]))
        se.append("TICK")

    # Z stabilizers
    se.append("DEPOLARIZE1", Z_ancilla_indices, (error_params["p_state_p"]))
    se.append("TICK")
    for time_step in range(len(scheduling_Z)):
        idling_qubits = data_indices + Z_ancilla_indices
        idling_data_indices = list(copy.deepcopy(data_indices))
        se.append("DEPOLARIZE1", idling_qubits, (error_params["p_idling_gate"]))
        for j in scheduling_Z[time_step]:
            Z_ancilla_index = Z_ancilla_indices[j]
            data_index = scheduling_Z[time_step][j]
            se.append("CX", [data_index, Z_ancilla_index])
            if data_index in idling_data_indices:
                idling_data_indices.pop(idling_data_indices.index(data_index))
        # idling errors for data qubits that are not being checked in this time step
        se.append("DEPOLARIZE1", idling_data_indices, (error_params["p_i"]))
        se.append("TICK")

    # Measure the ancillas
    se.append("H", X_ancilla_indices)
    # Add the measurement error
    se.append("DEPOLARIZE1", X_ancilla_indices, (3 / 2 * error_params["p_m"]))
    se.append("MR", Z_ancilla_indices + X_ancilla_indices)

    return se


def build_xu_hgp_complete_se(
    Hx: NDArray[np.int_],
    Hz: NDArray[np.int_],
    Lx: NDArray[np.int_],
    Lz: NDArray[np.int_],
    error_params: Dict[str, float],
    num_rounds: int,
    schedule: str = "coloration",
) -> stim.Circuit:
    """Equivalent to `generate_hgp_circuit`, but factors out the SE body via `build_xu_hgp_one_se`."""
    hx = Hx
    hz = Hz
    lx = Lx
    if schedule == "coloration":
        scheduling_X = ColorationCircuit(Hx)
        scheduling_Z = ColorationCircuit(Hz)
    else:
        raise ValueError("Invalid schedule type")

    data_indices = list(np.arange(0, np.shape(hx)[1]))
    n = len(data_indices)
    n_Z_ancilla, n_X_ancilla = np.shape(hz)[0], np.shape(hx)[0]
    Z_ancilla_indices = list(np.arange(n, n + n_Z_ancilla))
    X_ancilla_indices = list(np.arange(n + n_Z_ancilla, n + n_Z_ancilla + n_X_ancilla))

    # init (identical to generate_hgp_circuit)
    circuit_init = stim.Circuit()
    circuit_init.append("RX", data_indices)

    # shared SE body
    se_body = build_xu_hgp_one_se(
        data_indices=data_indices,
        X_ancilla_indices=X_ancilla_indices,
        Z_ancilla_indices=Z_ancilla_indices,
        scheduling_X=scheduling_X,
        scheduling_Z=scheduling_Z,
        error_params=error_params,
    )

    # round-1 detectors (no previous round to difference against)
    circuit_stab_meas_rep1 = stim.Circuit()
    circuit_stab_meas_rep1 += se_body
    circuit_stab_meas_rep1.append("SHIFT_COORDS", [], (1))
    for i in range(len(X_ancilla_indices)):
        circuit_stab_meas_rep1.append("DETECTOR", [stim.target_rec(-len(X_ancilla_indices) + i)], (0))
    circuit_stab_meas_rep1.append("TICK")

    # later-round detectors (difference detectors)
    circuit_stab_meas_rep2 = stim.Circuit()
    circuit_stab_meas_rep2 += se_body
    for i in range(len(X_ancilla_indices)):
        circuit_stab_meas_rep2.append(
            "DETECTOR",
            [
                stim.target_rec(-len(X_ancilla_indices) + i),
                stim.target_rec(-len(X_ancilla_indices) + i - len(Z_ancilla_indices) - len(X_ancilla_indices)),
            ],
            (0),
        )
    circuit_stab_meas_rep2.append("TICK")

    # Final projective measurement layer (identical to generate_hgp_circuit)
    circuit_final_meas = stim.Circuit()
    circuit_final_meas.append("DEPOLARIZE1", data_indices, (error_params["p_m"]))
    circuit_final_meas.append("MX", data_indices)
    circuit_final_meas.append("SHIFT_COORDS", [], (1))

    # Obtain the syndromes
    for i in range(len(X_ancilla_indices)):
        supported_data_indices = list(np.where(hx[X_ancilla_indices[i] - n - n_Z_ancilla, :] == 1)[0])
        # append the previous round of X stabilizer measurement
        rec_indices = [-len(data_indices) - len(X_ancilla_indices) + i]
        for data_index in supported_data_indices:
            rec_indices.append(-len(data_indices) + data_index)
        circuit_final_meas.append("Detector", [stim.target_rec(rec_index) for rec_index in rec_indices], (0))

    # Obtain the logical measurement results
    for i in range(len(lx)):
        logical_X_qubit_indices = list(np.where(lx[i, :] == 1)[0])
        circuit_final_meas.append(
            "OBSERVABLE_INCLUDE",
            [stim.target_rec(-len(data_indices) + data_index) for data_index in logical_X_qubit_indices],
            (i),
        )

    circuit = circuit_init + circuit_stab_meas_rep1 + (num_rounds - 1) * circuit_stab_meas_rep2 + circuit_final_meas

    # Add noise (identical to generate_hgp_circuit)
    noisy_circuit = circuit
    noisy_circuit = AddCXError(noisy_circuit, "DEPOLARIZE2(%f)" % error_params["p_CX"])
    return noisy_circuit

"""Write the 5-to-1 magic state distillation circuits of the Tsim paper (Haenel, Luo, Zhao,
arXiv:2604.01059), which reproduce QuEra's logical distillation experiment (Rodriguez et al.,
arXiv:2412.15165).

The circuits follow Tsim's tutorial ``docs/demos/magic_state_distillation.ipynb`` (copied to
stim_src/): five noisy magic states |psi> = T_DAG R_X(theta)|0> with theta = -arccos(sqrt(1/3))/pi
(the distillation angle), the 5-to-1 distillation Clifford circuit, and readout of all five
qubits. They are written unencoded and encoded transversally in the d=3 Steane code
(``tsim.utils.encoder.SteaneEncoder``, 35 qubits) and the d=5 color code (``ColorEncoder5``, 85
qubits), the "d=3,5 distillation circuits" benchmarked in the paper. The tutorial's noise is used:
DEPOLARIZE1(0.05) on the injected states, p/5 = 0.01 after each distillation gate. The distilled
qubit is read out in the X, Y or Z basis (state tomography in the tutorial).

Usage: uv run python make_circuits.py
"""

import pathlib

import numpy as np
import tsim
from tsim.utils.encoder import ColorEncoder5, SteaneEncoder

HERE = pathlib.Path(__file__).parent
THETA = -np.arccos(np.sqrt(1 / 3)) / np.pi
P = 0.05
NOISE = P / 5

PREPARE = f"""
R 0 1 2 3 4
R_X({THETA}) 0 1 2 3 4
T_DAG 0 1 2 3 4
DEPOLARIZE1({P}) 0 1 2 3 4
"""

DISTILL = f"""
SQRT_X 0 1 4
DEPOLARIZE1({NOISE}) 0 1 4
CZ 0 1 2 3
DEPOLARIZE2({NOISE}) 0 1 2 3
SQRT_Y 0 3
DEPOLARIZE1({NOISE}) 0 3
CZ 0 2 3 4
DEPOLARIZE2({NOISE}) 0 2 3 4
TICK
SQRT_X_DAG 0
DEPOLARIZE1({NOISE}) 0
CZ 0 4
DEPOLARIZE2({NOISE}) 0 4
TICK
CZ 1 3
DEPOLARIZE2({NOISE}) 1 3
TICK
SQRT_X_DAG 0 1 2 3 4
DEPOLARIZE1({NOISE}) 0 1 2 3 4
"""

READOUT = """
M 0 1 2 3 4
DETECTOR rec[-5]
DETECTOR rec[-4]
DETECTOR rec[-3]
DETECTOR rec[-2]
DETECTOR rec[-1]
OBSERVABLE_INCLUDE(0) rec[-5]
OBSERVABLE_INCLUDE(1) rec[-4]
OBSERVABLE_INCLUDE(2) rec[-3]
OBSERVABLE_INCLUDE(3) rec[-2]
OBSERVABLE_INCLUDE(4) rec[-1]
"""

BASIS_CHANGE = {"X": "H 0\n", "Y": "H_YZ 0\n", "Z": ""}


def unencoded(basis):
    return tsim.Circuit(PREPARE + DISTILL + BASIS_CHANGE[basis] + READOUT)


def encoded(encoder_cls, basis):
    encoder = encoder_cls()
    encoder.initialize(PREPARE)
    encoder.encode_transversally(DISTILL + BASIS_CHANGE[basis] + READOUT)
    return encoder.circuit


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for basis in "XYZ":
        circuits = {
            f"distillation_unencoded_{basis}": unencoded(basis),
            f"distillation_steane_d3_{basis}": encoded(SteaneEncoder, basis),
            f"distillation_color_d5_{basis}": encoded(ColorEncoder5, basis),
        }
        for name, circuit in circuits.items():
            (out / f"{name}.stim").write_text(str(circuit) + "\n")
            print(f"wrote stim/{name}.stim ({circuit.num_qubits} qubits)")


if __name__ == "__main__":
    main()

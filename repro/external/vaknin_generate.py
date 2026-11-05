"""Generate Vaknin et al.'s unrotated H-cultivation circuits at noise p (runs in ``.venvs/vaknin``).

    .venvs/vaknin/bin/python repro/external/vaknin_generate.py P OUT_DIR

Uses the authors' generator (papers/2502.01743_surface_code_cultivation/stim_src/repo_ec28f6b,
tomirendo/surface-code-magic-state-cultivation at ec28f6b) in its pinned environment
(requirements.txt: qutip, pennylane, ...). Writes, for the "unrotated_H_injection-syndrome-ghz" protocol
(d1 = 3, the protocol of the paper's full-vector comparison, Fig. 26):

- ``proxy.stim``: ``to_stim_circuit(apply_non_cliffords=False, noise_model, p)``, the Clifford
  approximation with ``non_clifford_noise_strategy="CZ"``, exactly as the authors' generate_circuits.py
  makes their released ``injection-ghz`` proxies;
- ``placeholder.stim``: ``to_stim_circuit(apply_non_cliffords=True, noise_model, p)`` with each
  non-Clifford gate encoded as an otherwise unused Stim gate (``convertion_dict``);
- ``logicals.json``: the qubit indices of the logical X and Z operators.
"""

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
REPO = ROOT / "papers" / "2502.01743_surface_code_cultivation" / "stim_src" / "repo_ec28f6b" / "2025"


def main():
    p = float(sys.argv[1])
    out = pathlib.Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    os.chdir(REPO / "HCultivationSurfaceCode")
    sys.path.insert(0, str(REPO / "StateVecSimulator" / "latte"))
    sys.path.insert(0, str(REPO / "HCultivationSurfaceCode"))
    from _noise import NoiseModel
    from simulation import Simulation

    noise = NoiseModel().uniform_depolarizing(p)
    s = Simulation(d=3)
    first = s.generate_syndrome_circuit(generate_unitary=False, detect_x=False)
    injection = s.generate_injection_circuit(generate_unitary=False)
    syndrome = s.generate_syndrome_circuit(generate_unitary=False)
    double = s.generate_double_ghz(generate_unitary=False)
    # "injection-syndrome-ghz" (generate_circuits.py): the variant whose acceptance matches the paper's Fig. 26
    # (2.18 attempts per kept shot at p = 1e-3, released init-H-injection-syndrome-ghz,d1=3).
    circuit = first + injection + syndrome + double
    (out / "proxy.stim").write_text(str(circuit.to_stim_circuit(apply_non_cliffords=False, noise_model=noise, p=p, non_clifford_noise_strategy="CZ")) + "\n")
    (out / "placeholder.stim").write_text(str(circuit.to_stim_circuit(apply_non_cliffords=True, noise_model=noise, p=p)) + "\n")
    (out / "logicals.json").write_text(json.dumps({"x": [q.index for q in s.logical_x_qubits], "z": [q.index for q in s.logical_z_qubits]}))


if __name__ == "__main__":
    main()

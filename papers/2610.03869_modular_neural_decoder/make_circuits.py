"""Write the coherent measure-qubit rotation stability circuits of Lange, Fjeldså, Jonasson
Johansson, Granath (arXiv:2610.03869).

The paper introduces a stability-experiment protocol (run on ibm_berlin) that inserts R_X(alpha)
on every measure qubit immediately before its readout, an extra syndrome flip with probability
sin^2(alpha/2), swept over alpha in {0.15, ..., 1.0} rad at t = 20 and t = 100 rounds. The d=3
X-type stability circuit and its noise model come from the authors' repository
(stim_src/modular-gnn-rnn-decoder, LangeMoritz/modular-gnn-rnn-decoder at afd6e17):
``gnnrnn/circuits.stability_circuit(rounds, p)`` with uniform circuit-level depolarizing noise
(p = 0.001 here). This script inserts ``R_X(alpha/pi)`` (half turns) before every measurement of
the measure qubits 7-14.

Each circuit is sampled noiselessly in Tsim; the observable must be deterministic at alpha = 0
and the rotations make detectors random, as intended.

Usage: uv run python make_circuits.py
"""

import pathlib
import re
import sys

import numpy as np

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE / "stim_src" / "modular-gnn-rnn-decoder" / "gnnrnn"))
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import circuits  # noqa: E402  (the authors' gnnrnn/circuits.py)
import validate  # noqa: E402

MEASURE_QUBITS = set(range(7, 15))
P = 0.001
SETTINGS = [(20, 0.15), (20, 0.5), (20, 1.0), (100, 0.5)]


def insert_rotations(text, alpha):
    def rotate(match):
        indent, line = match.group(1), match.group(0)
        targets = [int(t) for t in (line.split(")")[-1] if "(" in line else line.strip()[1:]).split()]
        rotated = [t for t in targets if t in MEASURE_QUBITS]  # the final M also reads data qubits
        return f"{indent}R_X({alpha / np.pi!r}) {' '.join(map(str, rotated))}\n{line}"
    return re.sub(r"^(\s*)M(\([^)]*\))? [\d ]+$", rotate, text, flags=re.M)


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for rounds, alpha in SETTINGS:
        base = str(circuits.stability_circuit(rounds, P))
        text = insert_rotations(base, alpha)
        ref = validate.check(base, shots=512)
        assert ref["random_detectors"] == 0 and ref["observable_means"] in ([0.0], [1.0]), ref
        result = validate.check(text, shots=512)
        name = f"stability_d3_X_t{rounds}_alpha{alpha}_p{P}.stim"
        (out / name).write_text(text)
        print(f"wrote stim/{name}: noiseless random detectors {result['random_detectors']}/{result['num_detectors']}")


if __name__ == "__main__":
    main()

"""Write T-state gauging Clifford-measurement cultivation circuits (Hetényi, Brown, Williamson,
arXiv:2603.05429).

The authors' generator (stim_src/gauging_clifford_measurement, IBM/gauging_clifford_measurement at
ce90c09) builds the |+i> (Y-basis) proxy of the protocol with ``get_stim_circ_w_growing(d,
basis="Y", pipeline=True)``: unitary injection, d_int=3 stabilizer + gauging Clifford checks,
Bell-state growth to the target distance and (d+1)/2 further check pairs, then a noiseless
stabilizer round and final logical Y measurement. Noise is added with the authors'
``utils.add_noise`` (uniform p for CX, single-qubit gates, measurement/reset and idling), as in
their notebook.

As in the authors' own statevector check (``qiskit_utils.stim_to_qiskit(...,
replace_S_with_T=True)``), the T-state circuit replaces every S/S_DAG by T/T_DAG. Each circuit
is sampled noiselessly in Tsim: no detector may be random and the deterministic detector
values must equal those of the proxy. The final logical-Y observable is then random (P(1) =
(1 - 1/sqrt 2)/2 for a T state); the paper evaluates X S^dagger instead.

Usage: uv run python make_circuits.py [--noise 0.001] [--distances 3 5 7]
"""

import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "stim_src" / "gauging_clifford_measurement"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import validate  # noqa: E402
from color_code import get_stim_circ_w_growing  # noqa: E402
from utils import add_noise  # noqa: E402


def drop_targetless(text):
    """Drop gate/noise lines without targets (no-ops in Stim, rejected by Clifft's parser).

    The authors' generator and ``add_noise`` emit e.g. ``R`` and ``DEPOLARIZE1(p)`` with empty
    target lists. Annotations (TICK, DETECTOR, OBSERVABLE_INCLUDE, SHIFT_COORDS) are kept.
    """
    keep = ("TICK", "DETECTOR", "OBSERVABLE_INCLUDE", "SHIFT_COORDS")
    return re.sub(rf"^\s*(?!{'|'.join(keep)})[A-Z_0-9]+(\([^)]*\))?\s*$\n", "", text, flags=re.M)


def s_to_t(text):
    text = re.sub(r"^(\s*)S_DAG(?=\s|$)", r"\1T_DAG", text, flags=re.M)
    return re.sub(r"^(\s*)S(?=\s|$)", r"\1T", text, flags=re.M)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noise", type=float, default=0.001)
    parser.add_argument("--distances", type=int, nargs="+", default=[3, 5, 7])
    args = parser.parse_args()
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    p = args.noise
    for d in args.distances:
        proxy = add_noise(get_stim_circ_w_growing(d, basis="Y", pipeline=True),
                          CX_error=p, meas_error=p, single_qubit_error=p, gate_idle_error=p)
        proxy = drop_targetless(str(proxy))
        text = s_to_t(proxy)
        result = validate.check(text, proxy=proxy, shots=2048)
        assert result["random_detectors"] == 0 and result["matches_proxy"], (d, result)
        path = out / f"gauging_cultivation_d{d}_T_p{p}.stim"
        path.write_text(text)
        print(f"wrote {path.relative_to(HERE)}: {result}")


if __name__ == "__main__":
    main()

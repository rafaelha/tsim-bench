"""Write the d=3 T-gate cultivation circuit of Wan, Zhong, Zapirain (arXiv:2509.08658).

The companion repo (stim_src/accel-cutting-magic-state, kh428/accel-cutting-magic-state at b6f67cd)
defines the native-T circuit as text in ``d_3_circuit_definitions.py``:
``circuit_source_injection_T`` (injection + double check, with T/T_DAG) followed by the noiseless
projection ``circuit_source_projection_proj``. As in the repo's ``run.py``, noise is added by
temporarily mapping T -> S (so Stim can parse the circuit), applying the authors' vendored
``gen.NoiseModel.uniform_depolarizing(p)``, and mapping back; the projection stays noiseless.

Usage: uv run python make_circuits.py [--noise 0.001]
"""

import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "stim_src" / "accel-cutting-magic-state"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import stim  # noqa: E402

import gen  # noqa: E402
import validate  # noqa: E402
from d_3_circuit_definitions import (  # noqa: E402
    circuit_source_injection_T,
    circuit_source_projection_proj,
)


def t_to_s(text):
    text = re.sub(r"^(\s*)T_DAG(\s)", r"\1S_DAG\2", text, flags=re.M)
    return re.sub(r"^(\s*)T(\s)", r"\1S\2", text, flags=re.M)


def s_to_t(text):
    text = re.sub(r"^(\s*)S_DAG(\s)", r"\1T_DAG\2", text, flags=re.M)
    return re.sub(r"^(\s*)S(\s)", r"\1T\2", text, flags=re.M)


def make(noise):
    # The T -> S -> T round trip is only unambiguous if the source has no S gates of its own.
    assert not re.search(r"^\s*S(_DAG)?\s", circuit_source_injection_T, flags=re.M)
    injection = stim.Circuit(t_to_s(circuit_source_injection_T))
    if noise > 0:
        injection = gen.NoiseModel.uniform_depolarizing(noise).noisy_circuit_skipping_mpp_boundaries(injection)
    return s_to_t(str(injection)) + "\n" + circuit_source_projection_proj.strip() + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noise", type=float, default=0.001)
    args = parser.parse_args()
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    text = make(args.noise)
    result = validate.check(text, shots=4096)
    assert result["random_detectors"] == 0, result
    path = out / f"d3_cultivation_T_p{args.noise}.stim"
    path.write_text(text)
    print(f"wrote {path.relative_to(HERE)}: {result}")


if __name__ == "__main__":
    main()

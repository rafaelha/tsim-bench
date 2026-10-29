"""Write T-state injection circuits from "Cleaner magic states with hook injection" (Gidney,
arXiv:2302.12292).

The authors' generator (stim_src/hook-injection, Strilanc/hook-injection at cdbdcae) injects a
Y-basis state |+i> = S|+>. Each Y-basis construction contains exactly one injection gate (checked
below), which this script replaces by its T-state analogue:

- hook injection (``hook_inject_Y``, ``pregrown_hook_inject_Y``): the hook rotation ``S`` = Z^0.5
  on the measurement ancilla (``make_hook_injection_round(exponent=0.5)``) becomes ``T`` = Z^0.25.
- Li injection (``li_inject_Y``): the data qubit reset ``RY`` (|+i>) becomes ``RX`` then ``T`` (|T>).
- ZZ injection (``zz_inject_Y``): ``SQRT_ZZ`` = (ZZ)^0.5 ~ R_ZZ(0.5) becomes (ZZ)^0.25 ~ R_ZZ(0.25)
  (half-turn units).

Parameters follow step1_generate_circuits.sh (distance 15, memory rounds d, 2 postselected rounds,
postselected diameter 5 and 7, "magic verify" final MPP readout), but with uniform depolarizing
noise p = 0.001 without the SI1000 CZ conversion (``tools/gen_circuits`` only converts to CZ for
SI1000), so the injection gate is not fused into neighbouring single-qubit layers.

Each circuit is sampled noiselessly in Tsim: no detector may be random and the deterministic
detector values must equal those of the Y proxy. For ZZ injection, the proxy with SQRT_ZZ written
as R_ZZ(0.5) must also reproduce the proxy exactly (checks the R_ZZ angle convention).

Usage: uv run python make_circuits.py [--noise 0.001]
"""

import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE / "stim_src" / "hook-injection" / "src"))
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import validate  # noqa: E402
from hookinj import gen  # noqa: E402
from hookinj._make_circuit import make_circuit  # noqa: E402

# basis -> (regex matching the single injection line, replacement)
INJECTION = {
    "hook_inject_Y_magic_verify": (r"^S (\d+)$", r"T \1"),
    "pregrown_hook_inject_Y_magic_verify": (r"^S (\d+)$", r"T \1"),
    "li_inject_Y_magic_verify": (r"^RY (\d+)$", r"RX \1\nT \1"),
    "zz_inject_Y_magic_verify": (r"^SQRT_ZZ (\d+) (\d+)$", r"R_ZZ(0.25) \1 \2"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noise", type=float, default=0.001)
    args = parser.parse_args()
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for basis, (pattern, replacement) in INJECTION.items():
        for diameter in [5, 7]:
            circuit = make_circuit(
                basis=basis,
                noise=gen.NoiseModel.uniform_depolarizing(args.noise),
                postselected_rounds=2,
                postselected_diameter=diameter,
                memory_rounds=15,
                distance=15,
                convert_to_cz=False,
            )
            proxy = str(circuit.flattened())
            assert len(re.findall(pattern, proxy, flags=re.M)) == 1, basis
            if basis.startswith("zz"):
                rzz = re.sub(pattern, r"R_ZZ(0.5) \1 \2", proxy, flags=re.M)
                check = validate.check(rzz, proxy=proxy, shots=256)
                assert check["matches_proxy"] and check["random_detectors"] == 0, check
            text = re.sub(pattern, replacement, proxy, flags=re.M)
            result = validate.check(text, proxy=proxy, shots=1024)
            assert result["random_detectors"] == 0 and result["matches_proxy"], (basis, result)
            name = basis.replace("_Y_magic_verify", "_T") + f"_d15_pd{diameter}_p{args.noise}.stim"
            (out / name).write_text(text)
            print(f"wrote stim/{name}: {result}")


if __name__ == "__main__":
    main()

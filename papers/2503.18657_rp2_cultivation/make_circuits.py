"""Write T-gate RP^2 cultivation circuits (Chen et al., arXiv:2503.18657).

The released circuits (stim_src/circuit_garage, Zihan-Chen-PhMA/Cultiv_T_RP2 at 77ad9b3) are the
Clifford variant of the protocol: as stated in the paper (Sec. III and App. D), "we replace all T
(T^dagger) gates in our protocols with S (S^dagger) gates". This script reverses that: every S
becomes T and every S_DAG becomes T_DAG. Nothing else changes.

Each circuit is sampled noiselessly in Tsim: no detector may be random, and the deterministic
detector values must equal those of the S-proxy circuit. The observable (the final MPP of the
logical Y) then reads 1 with probability (1 - 1/sqrt 2)/2 = 0.146, as expected for a T state.

Usage: uv run python make_circuits.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import validate  # noqa: E402


def s_to_t(text):
    text = re.sub(r"^(\s*)S_DAG ", r"\1T_DAG ", text, flags=re.M)
    return re.sub(r"^(\s*)S ", r"\1T ", text, flags=re.M)


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for path in sorted((HERE / "stim_src" / "circuit_garage").glob("*.stim")):
        proxy = path.read_text()
        text = s_to_t(proxy)
        result = validate.check(text, proxy=proxy)
        assert result["random_detectors"] == 0 and result["matches_proxy"], (path.name, result)
        (out / path.name).write_text(text)
        print(f"wrote stim/{path.name}: {result}")


if __name__ == "__main__":
    main()

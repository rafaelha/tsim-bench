"""Write T-state injection circuits from "Low-Overhead Transversal Fault Tolerance for Universal
Quantum Computation" (Zhou, Zhao, Cain, Bluvstein, Maskara, Duckering, Hu, Wang, Kubica, Lukin,
arXiv:2406.17653).

The authors' Zenodo record 16552626 (stim_src/: README, scripts and the S-injection circuits used
here) has ``circuits/s_injection/d={d},p=0.001,p_injected={p_inj}.stim``: a noisy |Y> state
(``RY`` + ``Z_ERROR(p_inj)``) is injected into a surface code of final distance d and consumed with
transversal gates and feedforward; d = 3, 5, 7, 9 at p_inj = 0.1 are used here (the circuits for
other p_inj differ only in that one error rate).

Conversion: each ``RY q`` becomes ``RX q`` + ``T q`` (T|+> is the T state; the Z_ERROR that follows
is kept as the injection noise). Checks: sampled noiselessly in Tsim, every detector stays
deterministic and equal to the proxy's; the logical observable becomes random, as expected for a T
state read out in a Pauli basis. Target-less lines are dropped for Clifft.

Not converted: the ``s_factory`` and ``two_level_s_factory`` circuits distil |Y> states. With T the
same detectors are random as in the proxy, but the outputs are random too, since that protocol has
no T analogue.

Usage: uv run python make_circuits.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import stimtext  # noqa: E402
import validate  # noqa: E402

SRC = HERE / "stim_src" / "circuits" / "s_injection"


def ry_to_t(text):
    assert re.search(r"^RY ", text, flags=re.M)
    return re.sub(r"^RY(\([^)]*\))? ([\d ]+)$", r"RX\1 \2\nT \2", text, flags=re.M)


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for path in sorted(SRC.glob("*.stim")):
        d = re.search(r"d=(\d+)", path.name).group(1)
        proxy = path.read_text()
        text = ry_to_t(proxy)
        result = validate.check(text, proxy=proxy, shots=512)
        assert result["random_detectors"] == 0 and result["matches_proxy"], result
        name = f"s_injection_T_d{d}_p0.001_pinj0.1.stim"
        (out / name).write_text(stimtext.drop_targetless(text))
        print(f"wrote stim/{name}: {result}", flush=True)


if __name__ == "__main__":
    main()

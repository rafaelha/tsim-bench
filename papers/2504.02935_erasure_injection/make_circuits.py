"""Write T-state injection circuits from "Magic State Injection with Erasure Qubits" (Jacoby,
Vaknin, Retzker, Grimsmo, arXiv:2504.02935).

The released circuits (stim_src/injection-with-erasure-qubits/circuits, shohamjac/
injection-with-erasure-qubits at 407a678) inject |S> = S|+> instead of |T> (the paper simulates
"injection of a |S> = S|+> state"):

- ``QEC_hook_d=3.stim``: d1=3 hook injection. Its first ``S`` (on the hook ancilla, qubit 24) is
  the injection rotation Z^0.5 and becomes ``T`` = Z^0.25. The second ``S`` (qubit 35, directly
  before the final ``H``/``M``) is the basis change of the logical-Y readout and is kept.
- ``c=inject[unitary]+cultivate,...,d1=3.stim``: Gidney et al.'s d=3 inject+cultivate proxy, for
  which every S/S_DAG becomes T/T_DAG (the d=3 rule of the Clifft converter, see
  ../2409.17595_magic_state_cultivation).

The erasure model itself (``erasure_simulator.get_erased_circuit``) samples herald patterns and
inserts depolarizing noise at the erased locations of these same circuits; it does not change the
circuit structure, so the base circuits are written here.

Each circuit is sampled noiselessly in Tsim: no detector may be random and the deterministic
detector values must equal those of the S proxy.

Usage: uv run python make_circuits.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "stim_src" / "injection-with-erasure-qubits" / "circuits"
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import validate  # noqa: E402


def hook_injection_to_t(text):
    s_lines = re.findall(r"^S \d+$", text, flags=re.M)
    assert s_lines == ["S 24", "S 35"], s_lines
    return re.sub(r"^S 24$", "T 24", text, count=1, flags=re.M)


def all_s_to_t(text):
    text = re.sub(r"^(\s*)S_DAG(?=\s|$)", r"\1T_DAG", text, flags=re.M)
    return re.sub(r"^(\s*)S(?=\s|$)", r"\1T", text, flags=re.M)


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    jobs = [
        ("QEC_hook_d=3.stim", hook_injection_to_t, "hook_inject_T_d3_p0.001.stim"),
        ("c=inject[unitary]+cultivate,p=0.001,noise=uniform,g=css,q=15,b=Y,r=4,d1=3.stim", all_s_to_t,
         "inject_cultivate_T_d3_p0.001.stim"),
    ]
    for source, convert, name in jobs:
        proxy = (SRC / source).read_text()
        text = convert(proxy)
        result = validate.check(text, proxy=proxy, shots=2048)
        assert result["random_detectors"] == 0 and result["matches_proxy"], (source, result)
        (out / name).write_text(text)
        print(f"wrote stim/{name}: {result}")


if __name__ == "__main__":
    main()

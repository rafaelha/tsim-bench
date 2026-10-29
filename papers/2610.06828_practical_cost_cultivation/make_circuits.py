"""Write T-gate colour-code cultivation circuits from "The practical cost of magic state
cultivation" (Mehta, Menon, Zhou, Lukin, Bonilla Ataides, arXiv:2610.06828).

The released circuits (stim_src/MSC-data/circuits, rohanmehtagithub/MSC-data at 0db416a) are
Y-basis Clifford proxies, as stated in the paper. This script converts the colour-to-grafted-code
cultivation circuits (taken by the authors from Gidney et al.'s Zenodo record, with escape):

- ``color code cultivation f3.stim``: every S/S_DAG becomes T/T_DAG (valid at d=3).
- ``color code cultivation f5.stim``: converted with the Clifft paper's S->T converter
  (../2409.17595_magic_state_cultivation/stim_src/clifft_paper_convert_s_to_t.py,
  ``convert_circuit(is_d5=True, is_e2e=True)``), which adds the d=5 sign flips, growth feedforward
  and detector healing. A blanket S->T substitution leaves 6 random detectors here.

The fold-transversal "surface code cultivation" circuits and the escape sweep are |Y> proxies whose
controlled-Y layers do not map gate-by-gate to the native protocol (see
../2509.05212_fold_transversal_cultivation); they are not converted.

Each circuit is sampled noiselessly in Tsim: no detector may be random and the deterministic
detector values must equal those of the proxy.

Usage: uv run python make_circuits.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "stim_src" / "MSC-data" / "circuits"
GIDNEY = HERE.parent / "2409.17595_magic_state_cultivation" / "stim_src"
sys.path.insert(0, str(HERE.parent.parent / "tools"))
sys.path.insert(0, str(GIDNEY / "github_magic-state-cultivation" / "src"))
sys.path.insert(0, str(GIDNEY))

import stim  # noqa: E402

import clifft_paper_convert_s_to_t as conv  # noqa: E402
import validate  # noqa: E402


def s_to_t(text):
    text = re.sub(r"^(\s*)S_DAG(?=\s|$)", r"\1T_DAG", text, flags=re.M)
    return re.sub(r"^(\s*)S(?=\s|$)", r"\1T", text, flags=re.M)


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    jobs = {
        "color code cultivation f3.stim": s_to_t,
        "color code cultivation f5.stim": lambda t: conv.convert_circuit(stim.Circuit(t), is_d5=True, is_e2e=True) + "\n",
    }
    for source, convert in jobs.items():
        proxy = (SRC / source).read_text()
        text = convert(proxy)
        result = validate.check(text, proxy=proxy, shots=2048)
        assert result["random_detectors"] == 0 and result["matches_proxy"], (source, result)
        name = source.replace(" ", "_").replace(".stim", "_T.stim")
        (out / name).write_text(text)
        print(f"wrote stim/{name}: {result}")


if __name__ == "__main__":
    main()

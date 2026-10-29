"""Write the benchmark circuits of "Polynomial-time simulation of non-Clifford quantum error
correction" (Cercelescu, Koch, Pesah, arXiv:2610.06811).

The authors' repository (stim_src/merlin-sim, mark-koch/merlin-sim at 9799e00) builds its
benchmark workloads in ``benchmarks/protocols`` as text in the Stim dialect with native T/T_DAG and
CCZ (as accepted by Merlin, Clifft, SymFT and Tsim), and ships the cultivation workloads as files:

- ``15to1`` and Bravyi-Haah ``bh:k`` (3k+8)-to-k distillation (``build_distillation_case``), with
  the default clean noise model (independent Z noise of strength p after each physical T_DAG);
- ``bt27`` and ``bt81`` code switching between 2D bivariate-bicycle and 3D codes followed by a
  transversal CCZ layer (``build_code_switching_case``);
- ``experiments/cultivation/circuit_d{3,5}_t.stim``: Gidney-style d=3/d=5 inject+cultivate with T
  gates (the d=3 file is Clifft's documented circuit; both are copied verbatim).

All cases use p = 0.001, the value of the paper's benchmark commands (benchmarks/README.md). Each
distillation circuit is sampled noiselessly in Tsim: every detector must be deterministic. The
code-switching circuits are not sampled: their transversal CCZ layer acts on 3 x 27 / 3 x 81 qubits
and Tsim's noiseless sampling did not finish (the paper runs them only with Merlin and xtim).

Usage: uv run python make_circuits.py
"""

import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "stim_src" / "merlin-sim"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import validate  # noqa: E402
from benchmarks.protocols import build_code_switching_case, build_distillation_case  # noqa: E402

P = 0.001


def cases():
    yield "distillation_15to1", build_distillation_case("15to1", p_phys=P)
    for k in [2, 4, 6, 8, 10, 12, 14, 16, 18]:
        yield f"distillation_bh{k}", build_distillation_case("bh", k=k, p_phys=P)
    for pair in ["bt27", "bt81"]:
        yield f"code_switching_{pair}", build_code_switching_case(pair, p_phys=P)


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for name, case in cases():
        if name.startswith("code_switching"):
            result = "not sampled"
        else:
            result = validate.check(case.circuit, shots=512)
            assert result["random_detectors"] == 0, (name, result)
        (out / f"{name}_p{P}.stim").write_text(case.circuit.rstrip() + "\n")
        print(f"wrote stim/{name}_p{P}.stim ({case.n_phys} qubits): {result}", flush=True)
    for d in [3, 5]:
        source = SRC / "experiments" / "cultivation" / f"circuit_d{d}_t.stim"
        shutil.copy(source, out / f"cultivation_d{d}_t.stim")
        print(f"copied stim/cultivation_d{d}_t.stim: {validate.check(source.read_text(), shots=512)}")


if __name__ == "__main__":
    main()

"""Write T-gate magic state cultivation circuits (Gidney, Shutty, Jones, arXiv:2409.17595).

The paper's circuits (stim_src/zenodo_13777072) simulate the T-basis cultivation
with a Clifford S-gate proxy in the Y basis. This script rebuilds them with the
authors' generator (stim_src/github_magic-state-cultivation, commit 871e68f)
and converts S/S_DAG to T/T_DAG with the converter from the Clifft paper
(stim_src/clifft_paper_convert_s_to_t.py, unitaryfoundation/clifft-paper
db7dc9f), which also adds the d=5 sign flips, growth feedforward and detector
healing that the T gates require.

Each circuit is checked noiselessly with Tsim: every detector must be 0.

Usage: uv run python make_circuits.py [--noise 0.001]
"""

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE / "stim_src" / "github_magic-state-cultivation" / "src"))
sys.path.insert(0, str(HERE / "stim_src"))

import numpy as np  # noqa: E402

import clifft_paper_convert_s_to_t as conv  # noqa: E402

VARIANTS = {
    "inject_cultivate_d3": conv.make_d3_inject_cultivate,
    "inject_cultivate_d5": conv.make_d5_inject_cultivate,
    "end2end_d3_dsurface15": conv.make_d3_end2end,
    "end2end_d5_dsurface15": conv.make_d5_end2end,
}


def check_noiseless(text, shots=256):
    import tsim

    samples = tsim.Circuit(text).compile_detector_sampler(seed=0).sample(shots)
    return not np.any(samples)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noise", type=float, default=0.001)
    args = parser.parse_args()
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for name, make in VARIANTS.items():
        assert check_noiseless(make(0.0)), f"{name}: detector fired without noise"
        path = out / f"{name}_p{args.noise}.stim"
        path.write_text(make(args.noise) + "\n")
        print(f"wrote {path.relative_to(HERE)} (noiseless check passed)")


if __name__ == "__main__":
    main()

"""Copy the real-CCZ tricycle factory circuits into stim/.

Source: stim_src/circs/ is tricycle_factories/ of https://github.com/rafaelha/circs at commit e4ee58f
(built from Li, Preskill, Xu, arXiv:2510.07269, and their repository tinghui2012/transversal-dimension-jump;
see README.md). The circuits already contain physical CCZ gates, so they are copied unchanged.
``stim_src/circs/generate.py`` regenerates every circuit except ``blp_27_3_3.stim``, which is built from the
authors' own Z-syndrome round and CCZ triples.

Check: circuits with Tsim k_max <= 16 (tricycle_6/9/12/15) are sampled noiselessly in Tsim. Every detector
must be deterministic, and each of the 9 logical-X observables must be near 3/8, the exact value for
the target 9-qubit CCZ hypergraph state.

Usage: uv run python make_circuits.py
"""

import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import validate  # noqa: E402

SRC = HERE / "stim_src" / "circs"
CHECK = {"tricycle_6_3_2", "tricycle_9_3_2", "tricycle_12_3_2", "tricycle_15_3_2"}


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for path in sorted(SRC.glob("*.stim")):
        shutil.copy(path, out / path.name)
        note = "copied"
        if path.stem in CHECK:
            r = validate.check(path.read_text(), shots=512)
            obs = r["observable_means"]
            assert r["random_detectors"] == 0 and all(abs(m - 0.375) < 0.08 for m in obs), r
            note += f", noiseless: deterministic detectors, observables {[round(m, 3) for m in obs]}"
        print(f"stim/{path.name}: {note}", flush=True)


if __name__ == "__main__":
    main()

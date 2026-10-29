"""Write T-gate colour-code cultivation circuits (Chan, Strikis, Sun, Cai, arXiv:2609.17706).

The paper's package (stim_src/cliffordea, timchan0/cliffordea at 27385c6) bundles S-state proxy
references in ``cliffordea/sim/stim_files``. As in the package (``circuit_text.swap_t_and_s_gates``,
used by ``run_simulation.py``), the T-state circuit is the reference with every S/S_DAG replaced by
T/T_DAG. The distance-5 references without ``_uncorrected`` already contain the Bell-growth
feedforward and detector healing that make this substitution valid (sim/d5-correction.md); the
``_uncorrected`` sources are skipped.

Each circuit is sampled noiselessly in Tsim: no detector may be random, and the deterministic
detector values must equal those of the S proxy.

Usage: uv run python make_circuits.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
SOURCES = HERE / "stim_src" / "cliffordea" / "sim" / "stim_files"
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import validate  # noqa: E402


def s_to_t(text):
    text = re.sub(r"^(\s*)S_DAG(?=\s|$)", r"\1T_DAG", text, flags=re.M)
    return re.sub(r"^(\s*)S(?=\s|$)", r"\1T", text, flags=re.M)


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for path in sorted(SOURCES.glob("*_p1e-3.stim")):
        if "uncorrected" in path.name:
            continue
        proxy = path.read_text()
        text = s_to_t(proxy)
        result = validate.check(text, proxy=proxy, shots=2048)
        assert result["random_detectors"] == 0 and result["matches_proxy"], (path.name, result)
        name = path.name.replace("+", "_").replace("_p1e-3", "_T_p0.001")
        (out / name).write_text(text)
        print(f"wrote stim/{name}: {result}")


if __name__ == "__main__":
    main()

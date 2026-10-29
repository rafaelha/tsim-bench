"""Write T-gate Steane-code cultivation circuits with lattice-surgery escape (Hirano, Toshio,
Itogawa, Fujii, arXiv:2510.24615).

The authors' circuits (stim_src/msc-ls/data, yutakahirano/msc-ls at e4c90b0) cultivate on the
Steane code ([[7,1,3]], the d=3 colour code) with the S/S_DAG proxy of Gidney et al. Two of them
contain the magic-state part:

- ``inject-check-3.stim``: injection and double check on the Steane code.
- ``lattice-surgery-complementary-gap-3-to-5-to-7.stim``: the end-to-end protocol, with lattice
  surgery into a d=5 and then d=7 surface code.

(The other files are Clifford sub-circuits: surface-code expansion and error-detection tests.)
As for Gidney's d=3 cultivation, every S/S_DAG becomes T/T_DAG. Instruction tags (e.g.
``TICK[Encode T]``, ``DETECTOR[POST-SELECTION]``) are removed: Tsim mis-parses tags that contain the
token ``T`` and Clifft rejects tags. The indices of the ``DETECTOR[POST-SELECTION]`` detectors are
saved next to each circuit (``*.postselection.json``).

Each circuit is sampled noiselessly in Tsim: no detector may be random (except, in the end-to-end
circuit, the last detector, which repeats the logical-Y observable) and the deterministic detector
values must equal those of the S proxy.

Usage: uv run python make_circuits.py
"""

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "stim_src" / "msc-ls" / "data"
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import validate  # noqa: E402


def s_to_t(text):
    text = re.sub(r"^(\s*)S_DAG(?=\s|$)", r"\1T_DAG", text, flags=re.M)
    return re.sub(r"^(\s*)S(?=\s|$)", r"\1T", text, flags=re.M)


def strip_tags(text):
    return re.sub(r"^(\s*[A-Z_]+)\[[^\]]*\]", r"\1", text, flags=re.M)


def observable_detector(text):
    """Whether the last DETECTOR has exactly the records of OBSERVABLE_INCLUDE(0)."""
    detectors = re.findall(r"^DETECTOR(?:\([^)]*\))? (.*)$", text, flags=re.M)
    observable = re.findall(r"^OBSERVABLE_INCLUDE\(0\) (.*)$", text, flags=re.M)
    return bool(detectors and observable) and sorted(detectors[-1].split()) == sorted(observable[-1].split())


def postselected(text):
    detectors = [line.strip() for line in text.splitlines() if line.strip().startswith("DETECTOR")]
    return [k for k, line in enumerate(detectors) if line.startswith("DETECTOR[POST-SELECTION]")]


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for source in ["inject-check-3.stim", "lattice-surgery-complementary-gap-3-to-5-to-7.stim"]:
        tagged = (SRC / source).read_text()
        proxy = strip_tags(tagged)
        text = s_to_t(proxy)
        result = validate.check(text, proxy=proxy, shots=2048)
        # The end-to-end file also declares its final logical-Y readout as a detector (same records
        # as OBSERVABLE_INCLUDE(0)); for a T state that readout is random, like the observable.
        allowed = int(observable_detector(proxy))
        assert result["random_detectors"] <= allowed and result["matches_proxy"], (source, result)
        name = source.replace(".stim", "_T.stim")
        (out / name).write_text(text)
        (out / name.replace(".stim", ".postselection.json")).write_text(json.dumps(postselected(tagged)) + "\n")
        print(f"wrote stim/{name}: {result}")


if __name__ == "__main__":
    main()

"""Write T-gate "cultivation + growing" color-code circuits from Lee, Thomsen, Fazio, Brown, Bartlett,
"Low-overhead magic state distillation with color codes" (arXiv:2409.07707).

The paper feeds magic states from Gidney et al.'s cultivation, grown to a larger triangular color
code, into distillation. Its circuits are built with the authors' package color-code-stim
(stim_src/color-code-stim, seokhyung-lee/color-code-stim at 0eb3593):
``ColorCode(d=3|5, d2=..., circuit_type="cult+growing", p_circuit=p)`` (Y temporal boundary). The
cultivation part is a bundled copy of Gidney et al.'s Y-basis S-proxy inject+cultivate circuit
(``assets/cultivation_circuits/d{d}_p{p}.stim``), followed by color-code growth to distance d2 and
d2 rounds of syndrome extraction.

T gates are restored on the cultivation asset, which is then passed to the package through
``ColorCode(cultivation_circuit=...)``:

- d = 3: every S/S_DAG becomes T/T_DAG.
- d = 5: the Clifft paper's converter (../2409.17595_magic_state_cultivation/stim_src/
  clifft_paper_convert_s_to_t.py, ``convert_circuit(is_d5=True, is_e2e=True)``: d=5 sign flips,
  growth feedforward, detector healing; the final MPP is kept, the package trims it anyway).

Because the package manipulates the circuit with Stim, the T/T_DAG gates are carried as the
otherwise unused Clifford gates C_XYZ/C_ZYX (checked absent from the assets) and swapped back at
the end. Each circuit is sampled noiselessly in Tsim (with p_circuit = 0 builds): no detector may be
random and the deterministic detector values must equal those of the S proxy.

Usage: uv run python make_circuits.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
GIDNEY = HERE.parent / "2409.17595_magic_state_cultivation" / "stim_src"
sys.path.insert(0, str(HERE / "stim_src" / "color-code-stim" / "src"))
sys.path.insert(0, str(HERE.parent.parent / "tools"))
sys.path.insert(0, str(GIDNEY / "github_magic-state-cultivation" / "src"))
sys.path.insert(0, str(GIDNEY))

import stim  # noqa: E402

import clifft_paper_convert_s_to_t as conv  # noqa: E402
import color_code_stim  # noqa: E402
import validate  # noqa: E402

ASSETS = HERE / "stim_src" / "color-code-stim" / "src" / "color_code_stim" / "assets" / "cultivation_circuits"
PLACEHOLDER = {"T": "C_XYZ", "T_DAG": "C_ZYX"}
SETTINGS = [(3, 7), (3, 11), (5, 9), (5, 13)]  # (d, d2)
P = 0.001


def s_to_t(text):
    text = re.sub(r"^(\s*)S_DAG(?=\s|$)", r"\1T_DAG", text, flags=re.M)
    return re.sub(r"^(\s*)S(?=\s|$)", r"\1T", text, flags=re.M)


def to_placeholders(t_text):
    for gate, stand_in in PLACEHOLDER.items():
        t_text = re.sub(rf"^(\s*){gate}(?=\s)", rf"\g<1>{stand_in}", t_text, flags=re.M)
    return stim.Circuit(t_text)


def from_placeholders(text):
    for gate, stand_in in PLACEHOLDER.items():
        text = re.sub(rf"^(\s*){stand_in}(?=\s)", rf"\g<1>{gate}", text, flags=re.M)
    return text


def cultivation_asset(d, p):
    """The package's bundled Gidney inject+cultivate proxy (``p`` = 0 or 0.001)."""
    name = f"d{d}_p{0 if p == 0 else p}.stim"
    return stim.Circuit.from_file(ASSETS / name)


def build(d, d2, p, convert):
    proxy = cultivation_asset(d, p)
    assert not {"C_XYZ", "C_ZYX"} & {i.name for i in proxy.flattened()}
    if convert:
        t_text = s_to_t(str(proxy)) if d == 3 else conv.convert_circuit(proxy, is_d5=True, is_e2e=True)
        proxy = to_placeholders(t_text)
    code = color_code_stim.ColorCode(d=d, d2=d2, rounds=d2, circuit_type="cult+growing",
                                     p_circuit=p, cultivation_circuit=proxy)
    return from_placeholders(str(code.circuit))


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for d, d2 in SETTINGS:
        result = validate.check(build(d, d2, 0, True), proxy=build(d, d2, 0, False), shots=1024)
        assert result["random_detectors"] == 0 and result["matches_proxy"], (d, d2, result)
        name = f"cult_growing_T_d{d}_to_d{d2}_p{P}.stim"
        (out / name).write_text(build(d, d2, P, True))
        print(f"wrote stim/{name}: noiseless check {result}")


if __name__ == "__main__":
    main()

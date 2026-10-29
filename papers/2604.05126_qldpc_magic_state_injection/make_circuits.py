"""Write T-state in-situ magic state injection circuits for the [[144,12,12]] bivariate bicycle code
(Liu, Xu, Jochym-O'Connor, He, Singh, Ding, arXiv:2604.05126).

The authors' package (stim_src/qldpc-msi, kunliu7/qldpc-msi at 09b005e) builds the injection
circuit with ``build_msi_circ_v3(code, se_circ, init_cfg, n_se_cycles)`` and adds the paper's
noise model with ``get_noise_model(name, p).noisy_circuit_skipping_mpp_boundaries`` (see
``tour_bb/psel_and_dec.py``). It injects logical |Y> states: the injection data qubits are reset
with ``RY``. The paper's scheme injects any +1 eigenstate of cos(theta) X + sin(theta) Y; |Y> is
theta = pi/2 and |T> is theta = pi/4 (Sec. II). The T-state circuit therefore prepares each
injection qubit with ``RX`` followed by ``T`` (T|+> is the +1 eigenstate of (X+Y)/sqrt 2).

Two stages:

1. ``python make_circuits.py generate`` must run in an environment with the authors' package
   (``pip install -e stim_src/qldpc-msi``; it loads the pickled init configs from its data/). It
   writes the Y-injection circuits for the paper's six best init configs of the BB code
   (``prj_msi/20sim/inject_y_v2.py`` defaults: ids 369, 422, 342, 491, 328, 88; li_uniform noise,
   max_supp_protection, 3 syndrome-extraction cycles) at p = 0.001 to stim_src/y_circuits/.
2. ``uv run python make_circuits.py convert`` replaces the RY resets by RX + T and samples each
   circuit noiselessly in Tsim: no detector may be random and deterministic detector values must
   equal those of the Y proxy. Target-less lines (an empty ``RX`` reset layer) are dropped for
   Clifft.

Usage: see above.
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
Y_CIRCUITS = HERE / "stim_src" / "y_circuits"
INIT_CFG_IDS = [369, 422, 342, 491, 328, 88]
P = 0.001
NOISE = "li_uniform"
N_SE_CYCLES = 3


def generate():
    from qldpc_msi.data_mgr import InitCfgMgrV2
    from qldpc_msi.msi.generic_msi_circ_v2 import build_msi_circ_v3
    from qldpc_msi.noise_spec import get_noise_model
    from qldpc_msi.tour_bb import make_code
    from qldpc_msi.tour_bb.facade import build_se_circuit

    Y_CIRCUITS.mkdir(exist_ok=True)
    code = make_code(n=144)
    manager = InitCfgMgrV2()
    for cfg_id in INIT_CFG_IDS:
        data = manager.load(code_id=code.identifier, noise_model=NOISE, init_method="max_supp_protection",
                            remove_dummy_cnots=False, _id=cfg_id)
        init_cfg = data["init_cfg"]
        se_circ = build_se_circuit(code)
        for p in (0.0, P):
            ideal = build_msi_circ_v3(code, se_circ, init_cfg, N_SE_CYCLES)
            circuit = ideal if p == 0 else get_noise_model(NOISE, p).noisy_circuit_skipping_mpp_boundaries(ideal)
            name = f"bb144_cfg{cfg_id}_inj{len(init_cfg.inj_lids)}_Y_p{p}.stim"
            (Y_CIRCUITS / name).write_text(str(circuit) + "\n")
            print(f"generated {name} ({circuit.num_qubits} qubits, injects {len(init_cfg.inj_lids)} logicals)")


def y_to_t(text):
    # The package emits RY only for the injection qubits (``R{inj_state}`` in generic_msi_circ_v2);
    # the schedule may split that reset layer over two time steps.
    assert re.search(r"^\s*RY", text, flags=re.M)
    return re.sub(r"^(\s*)RY(\([^)]*\))? ([\d ]+)$", r"\1RX\2 \3\n\1T \3", text, flags=re.M)


def convert():
    sys.path.insert(0, str(HERE.parent.parent / "tools"))
    import stimtext
    import validate

    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for path in sorted(Y_CIRCUITS.glob(f"*_Y_p{P}.stim")):
        noisy = path.read_text()
        ideal = (Y_CIRCUITS / path.name.replace(f"_p{P}", "_p0.0")).read_text()
        result = validate.check(y_to_t(ideal), proxy=ideal, shots=512)
        assert result["random_detectors"] == 0 and result["matches_proxy"], (path.name, result)
        name = path.name.replace("_Y_", "_T_")
        # Drop target-less lines such as an empty ``RX`` (no-ops in Stim, rejected by Clifft).
        (out / name).write_text(stimtext.drop_targetless(y_to_t(noisy)))
        print(f"wrote stim/{name}: {result}")


if __name__ == "__main__":
    {"generate": generate, "convert": convert}[sys.argv[1]]()

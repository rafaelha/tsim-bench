"""Write non-Clifford surface-code cultivation circuits (Vaknin et al., arXiv:2502.01743).

The authors' generator (stim_src/repo_ec28f6b, tomirendo/surface-code-magic-state-cultivation)
can emit the *actual* circuit with ``to_stim_circuit(apply_non_cliffords=True)``. For their own
state-vector simulator it encodes each non-Clifford gate as an otherwise unused Stim gate
(``convertion_dict`` in ``StateVecSimulator/latte/vec_sim.py``):

    XCX = CH,  H_YZ = CSWAP,  SQRT_X_DAG = CCZ,  SQRT_XX = CSX,  SQRT_XX_DAG = CS_DAG·X,
    SQRT_YY = CXS,  SQRT_YY_DAG = CXS_DAG,  SQRT_Y = T,  SQRT_X = T_DAG

where (as in vec_sim.py) CSX(a,b) = CS(a,b), CX(a,b), T_DAG(a); CS_DAGX = CS_DAG, CX, T(a);
CXS = CX, CS, T_DAG(a); CXS_DAG = CX, CS_DAG, T(a). The released Clifford-proxy circuits never
use these gate names, which this script checks.

Two stages:

1. ``python make_circuits.py generate`` must run in the authors' environment
   (stim_src/repo_ec28f6b/requirements.txt: qutip, pennylane, ...). It writes the placeholder
   circuits, with the authors' uniform depolarizing noise (p=0.001) already applied, to
   stim_src/placeholder_circuits/.
2. ``uv run python make_circuits.py convert`` replaces the placeholders with T/T_DAG/CCZ/CCX
   decompositions (tools/gates.py) and checks each circuit noiselessly in Tsim (no detector may
   fire), writing stim/*.stim.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).parent
REPO = HERE / "stim_src" / "repo_ec28f6b" / "2025"
PLACEHOLDERS = HERE / "stim_src" / "placeholder_circuits"
P = 0.001
D2 = 11

PLACEHOLDER_GATES = {"XCX", "H_YZ", "SQRT_X_DAG", "SQRT_XX", "SQRT_XX_DAG", "SQRT_YY",
                     "SQRT_YY_DAG", "SQRT_Y", "SQRT_X"}


def generate():
    import os

    os.chdir(REPO / "HCultivationSurfaceCode")
    sys.path.insert(0, str(REPO / "StateVecSimulator" / "latte"))
    sys.path.insert(0, str(REPO / "HCultivationSurfaceCode"))
    from _noise import NoiseModel
    from simulation import RotatedSurfaceCodeSimulation, Simulation

    noise = NoiseModel().uniform_depolarizing(P)
    PLACEHOLDERS.mkdir(exist_ok=True)

    def save(name, circuit, **kwargs):
        proxy = circuit.to_stim_circuit(apply_non_cliffords=False, **kwargs)
        assert not {i.name for i in proxy.flattened()} & PLACEHOLDER_GATES, name
        real = circuit.to_stim_circuit(apply_non_cliffords=True, noise_model=noise, p=P, **kwargs)
        (PLACEHOLDERS / f"{name}.stim").write_text(str(real) + "\n")
        print("generated", name)

    def save_expanded(name, circuit, sim, basis):
        head = dict(post_select_syndromes=False, measure_logical_operator=False,
                    logical_measurement_basis=basis)
        proxy = circuit.to_stim_circuit(apply_non_cliffords=False, **head)
        assert not {i.name for i in proxy.flattened()} & PLACEHOLDER_GATES, name
        real = circuit.to_stim_circuit(apply_non_cliffords=True, p=P, **head) + \
            sim.stim_expansion_circuit(d2=D2, rounds=D2, logical_measurement_basis=basis)
        real = noise.noisy_circuit_skipping_mpp_boundaries(real)
        (PLACEHOLDERS / f"{name}.stim").write_text(str(real) + "\n")
        print("generated", name)

    # Unrotated d=3 surface code, H-type cultivation (generate_circuits.py, "init-H-...").
    s = Simulation(d=3)
    syndrome = s.generate_syndrome_circuit(generate_unitary=False)
    first = s.generate_syndrome_circuit(generate_unitary=False, detect_x=False)
    injection = s.generate_injection_circuit(generate_unitary=False)
    double = s.generate_double_ghz(generate_unitary=False)
    injection_hxy = s.generate_injection_circuit_HXY(generate_unitary=False, init_basis="z")
    double_hxy = s.generate_double_ghz_HXY(generate_unitary=False)
    unrotated = {
        "unrotated_H_injection-ghz": first + injection + double,
        "unrotated_H_injection-syndrome-ghz": first + injection + syndrome + double,
        "unrotated_HXY_injection-ghz": first + injection_hxy + double_hxy,
        "unrotated_HXY_injection-syndrome-ghz": first + injection_hxy + syndrome + double_hxy,
    }
    for name, circuit in unrotated.items():
        save(f"{name}_d1=3_p={P}", circuit)

    # Rotated d=3 surface code, H_XY (T-type) cultivation ("init-HXY-rotated-...").
    r = RotatedSurfaceCodeSimulation(d=3)
    r_syndrome = r.generate_syndrome_circuit()
    r_first = r.generate_syndrome_circuit(detect_x=False)
    r_ghz = r.generate_projection_circuit_HXY()
    r_double = r.generate_projection_double_ghz_HXY()
    r_inj_z = r.generate_injection_circuit_HXY(init_basis="z")
    r_inj_x = r.generate_injection_circuit_HXY(init_basis="x")
    r_init_x = r.generate_init_circuit(basis="x")
    rotated = {
        "rotated-injection-ghz-HXY": (r_first + r_inj_z + r_ghz + r_ghz, "z"),
        "rotated-injection-double-ghz-HXY": (r_first + r_inj_z + r_double, "z"),
        "rotated-injection-syndrome-double-ghz-HXY": (r_first + r_inj_z + r_syndrome + r_double, "z"),
        "rotated-init-x-injection-double-HXY": (r_init_x + r_inj_x + r_double, "x"),
        "rotated-init-x-injection-syndrome-double-ghz-HXY": (r_init_x + r_inj_x + r_syndrome + r_double, "x"),
    }
    for name, (circuit, basis) in rotated.items():
        save(f"{name}_d1=3_p={P}", circuit, logical_measurement_basis=basis)

    # Cultivation followed by expansion to a d2=11 rotated surface code ("expanded-...").
    for name in ["rotated-injection-double-ghz-HXY", "rotated-injection-syndrome-double-ghz-HXY",
                 "rotated-init-x-injection-double-HXY"]:
        circuit, basis = rotated[name]
        save_expanded(f"expanded-{name}_d1=3_d2={D2}_p={P}", circuit, r, basis)
    for name in ["unrotated_H_injection-ghz", "unrotated_H_injection-syndrome-ghz"]:
        save_expanded(f"expanded-{name}_d1=3_d2={D2}_p={P}", unrotated[name], s, "z")


def _decompositions():
    sys.path.insert(0, str(HERE.parent.parent / "tools"))
    import gates as g

    def seq(*parts):
        return [item for part in parts for item in part]

    t_a = [("T", (0,))]
    tdag_a = [("T_DAG", (0,))]
    cx = [("CX", (0, 1))]
    return g, {
        "SQRT_Y": (1, g.T),
        "SQRT_X": (1, g.T_DAG),
        "SQRT_X_DAG": (3, g.CCZ),
        "XCX": (2, g.CH),
        "H_YZ": (3, g.CSWAP),
        "SQRT_XX": (2, seq(g.CS, cx, tdag_a)),
        "SQRT_XX_DAG": (2, seq(g.CS_DAG, cx, t_a)),
        "SQRT_YY": (2, seq(cx, g.CS, tdag_a)),
        "SQRT_YY_DAG": (2, seq(cx, g.CS_DAG, t_a)),
    }


def convert_text(text):
    import stim

    g, table = _decompositions()
    out = []
    for inst in stim.Circuit(text).flattened():
        if inst.name not in table:
            out.append(str(inst))
            continue
        arity, decomposition = table[inst.name]
        targets = inst.targets_copy()
        assert all(t.is_qubit_target for t in targets), f"classically controlled {inst}"
        values = [t.value for t in targets]
        assert len(values) % arity == 0, inst
        for k in range(0, len(values), arity):
            out.extend(g.emit(decomposition, values[k:k + arity]))
    return "\n".join(out) + "\n"


def strip_noise(text):
    import stim

    noise = {"DEPOLARIZE1", "DEPOLARIZE2", "X_ERROR", "Y_ERROR", "Z_ERROR", "PAULI_CHANNEL_1",
             "PAULI_CHANNEL_2", "E", "ELSE_CORRELATED_ERROR", "CORRELATED_ERROR"}
    lines = []
    for inst in stim.Circuit(text).flattened():
        if inst.name in noise:
            continue
        if inst.name in {"M", "MX", "MY", "MR", "MRX", "MRY", "MPP"} and inst.gate_args_copy():
            inst = stim.CircuitInstruction(inst.name, inst.targets_copy())
        lines.append(str(inst))
    return "\n".join(lines) + "\n"


def convert():
    import numpy as np
    import tsim

    _decompositions()[0].verify()
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for path in sorted(PLACEHOLDERS.glob("*.stim")):
        text = convert_text(path.read_text())
        noiseless = tsim.Circuit(convert_text(strip_noise(path.read_text())))
        samples = noiseless.compile_detector_sampler(seed=0).sample(256)
        fired = int(np.any(samples, axis=0).sum())
        (out / path.name).write_text(text)
        status = "noiseless check passed" if fired == 0 else f"WARNING: {fired} detectors fire noiselessly"
        print(f"wrote stim/{path.name} ({status})")


if __name__ == "__main__":
    {"generate": generate, "convert": convert}[sys.argv[1]]()

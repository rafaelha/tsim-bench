"""Write X^(1/4) unfolded-distillation circuits (Ruiz, Guillaud, Vuillot, Mirrahimi, arXiv:2507.12511).

The authors' scripts (stim_src/, DiegoRuiz-Git/Unfolded_distillation at c20a726) build the protocol
in Stim with the transversal logical X^(1/4) rotation replaced by X^(1/2) = ``SQRT_X`` on the 15
rotation qubits (the scripts' own comment calls this layer "X^1/4 gate"). Two steps restore it:

1. ``SQRT_X rotations`` becomes ``R_X(0.25) rotations`` (half turns: R_X(0.25) ~ X^(1/4)).
2. Feedforward. The first round of X-stabilizer measurements is random and leaves Z byproducts on
   the data qubits (the scripts' ``byproducts`` table; they normalise the observables with it). With
   the X^(1/2) proxy a byproduct only changes the rotation by a Pauli, but with X^(1/4) it turns
   X^(1/4) into X^(-1/4) (the paper: "if a Z error occurs on a data qubit, its Pauli frame must be
   updated, effectively transforming the X^(-1/4) rotation into an X^(1/4) rotation"). So each
   rotation qubit q with frame bit f_q (parity of the first-round outcomes of its byproduct
   stabilizers) gets X^(1/2)^(f_q) = SQRT_X^(f_q) before the rotation. (The sign was fixed
   empirically: with SQRT_X the four distillation checks are deterministic without noise, with
   SQRT_X_DAG or without feedforward they are random.) Stim cannot condition a non-Pauli gate on
   a record, so this is done by deferred measurement: the first-round MX outcomes that enter a frame
   bit are measured through fresh record ancillas (H, CX onto the ancilla, H, measure the ancilla),
   their parity is copied onto a scratch qubit, and a quantum-controlled SQRT_X (H, CS, H) is
   applied. Because the authors' schedule measures some stabilizers for the first time only after
   the SQRT_X layer, the X^(1/4) layer is moved to just after the last record its frame depends on
   (see ``restore``; exact, since in between the rotation qubits are only CX targets).

The script runs the authors' ``CreateCircuit`` and ``AddNoise`` (everything above the "simulation"
section of each ``Logical error.py``) and transforms the result. Each circuit is sampled noiselessly
in Tsim: every detector and the four distillation-check observables must be deterministic (they are
random without the feedforward).

Usage: uv run python make_circuits.py
"""

import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "stim_src"
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import numpy as np  # noqa: E402
import stim  # noqa: E402

import gates  # noqa: E402
import validate  # noqa: E402

# (name, script directory, rounds, noise arguments of the script's AddNoise)
JOBS = [
    ("repetition_no_preselection_pz1e-3", "Repetition code simulations/Without preselection pz=1e-3", [2, 4, 6], (1e-3,)),
    ("surface_no_bitflip_pz1e-3", "Surface code simulations/no bitflip", [2, 4, 6], (1e-20, 1e-3)),
]


def load_script(directory, rounds):
    """Execute a ``Logical error.py`` up to its simulation section, from its own directory."""
    source = (SRC / directory / "Logical error.py").read_text()
    source = source.split("# simulation")[0].rsplit("# ----", 1)[0]
    source = source.replace("from stimbposd import BPOSD", "")
    namespace = {"__name__": "unfolded"}
    cwd, argv = os.getcwd(), sys.argv
    try:
        os.chdir(SRC / directory)
        sys.argv = ["Logical error.py", str(rounds), "0"]
        exec(compile(source, str(SRC / directory / "Logical error.py"), "exec"), namespace)
    finally:
        os.chdir(cwd)
        sys.argv = argv
    return namespace


def frame_records(ns, measurement_number):
    """Map each rotation qubit to the first-round records whose parity is its Z byproduct."""
    frames = {}
    for q in ns["rotations"]:
        stabs = [s for s in set(ns["byproducts"][int(q)]) if ns["byproducts"][int(q)].count(s) % 2]
        frames[int(q)] = sorted(measurement_number[s][0] for s in stabs)
    return frames


def restore(circuit, frames, rotations):
    """Return Tsim/Clifft text with feedforward-corrected X^(1/4) rotations.

    The authors' schedule is staggered: some stabilizers are measured for the first time only after
    the SQRT_X layer, so their byproducts are not known when it is applied. The X^(1/4) layer (with
    the noise channel that follows it) is therefore delayed until the last record it depends on has
    been measured, and the feedforward correction is applied right before it. This is exact for the
    noiseless circuit: in between, the rotation qubits only take part in CX gates as targets (X
    commutes with them) and in noise channels; anything else raises.
    """
    rotation_qubits = {int(q) for q in rotations}
    needed = sorted({r for recs in frames.values() for r in recs})
    flat = list(circuit.flattened())
    scratch = circuit.num_qubits
    next_ancilla = scratch + 1
    record_ancilla = {}
    out, nrec = [], 0
    deferred = None  # [rotation instruction, its noise instruction]
    done = False

    def emit_rotation():
        for q in sorted(frames):
            if frames[q]:
                out.append(f"R {scratch}")
                out.extend(f"CX {record_ancilla[r]} {scratch}" for r in frames[q])
                out.extend([f"H {q}"] + gates.emit(gates.CS, [scratch, q]) + [f"H {q}"])
        out.append("R_X(0.25) " + " ".join(str(t.value) for t in deferred[0].targets_copy()))
        out.extend(str(inst) for inst in deferred[1:])

    k = 0
    while k < len(flat):
        inst = flat[k]
        name, targets = inst.name, inst.targets_copy()
        if name == "SQRT_X" and sorted(t.value for t in targets) == sorted(rotation_qubits):
            assert deferred is None and not done
            deferred = [inst]
            if k + 1 < len(flat) and flat[k + 1].name == "DEPOLARIZE1" and \
                    {t.value for t in flat[k + 1].targets_copy()} == rotation_qubits:
                deferred.append(flat[k + 1])
                k += 1
            k += 1
            if all(r < nrec for r in needed):
                emit_rotation()
                deferred, done = None, True
            continue
        if deferred is not None:
            qubits = [t.value for t in targets if t.is_qubit_target]
            if name == "CX":
                touched = {q for q in qubits[0::2] if q in rotation_qubits}  # controls must not be rotated
            elif name in ("DEPOLARIZE1", "DEPOLARIZE2", "Z_ERROR", "X_ERROR", "PAULI_CHANNEL_1",
                          "PAULI_CHANNEL_2", "TICK", "DETECTOR", "OBSERVABLE_INCLUDE", "SHIFT_COORDS",
                          "QUBIT_COORDS"):
                touched = set()
            else:
                touched = set(qubits) & rotation_qubits
            assert not touched, f"non-commuting {inst} before the delayed rotation"
        if name == "MX" and any(nrec + j in needed for j in range(len(targets))):
            assert not inst.gate_args_copy()
            for j, t in enumerate(targets):
                if nrec + j not in needed:
                    out.append(f"MX {t.value}")
                    continue
                a = next_ancilla
                next_ancilla += 1
                record_ancilla[nrec + j] = a
                out += [f"R {a}", f"H {t.value}", f"CX {t.value} {a}", f"H {t.value}", f"M {a}"]
        else:
            out.append(str(inst))
        nrec += inst.num_measurements
        k += 1
        if deferred is not None and all(r < nrec for r in needed):
            emit_rotation()
            deferred, done = None, True
    assert done
    return "\n".join(out) + "\n"


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for name, directory, rounds_list, noise in JOBS:
        for rounds in rounds_list:
            ns = load_script(directory, rounds)
            result = ns["CreateCircuit"](rounds)
            circuit, measurement_number = result if isinstance(result, tuple) else (result, None)
            frames = frame_records(ns, measurement_number)
            noisy = ns["AddNoise"](circuit, *noise)
            text = restore(noisy, frames, ns["rotations"])
            plain = re.sub(r"^R_X\(0.25\) ", "SQRT_X ", text, flags=re.M)
            det, obs = validate.sample(text, shots=2048)
            random_det = int(((det > 0) & (det < 1)).sum())
            checks = obs[:4]
            assert random_det == 0 and np.all((checks == 0) | (checks == 1)), (name, rounds, det, obs)
            # Without the feedforward the distillation checks are random (sanity check of step 2).
            bare = re.sub(r"^SQRT_X ", "R_X(0.25) ", str(noisy.flattened()), flags=re.M)
            _, bare_obs = validate.sample(bare, shots=2048)
            path = out / f"unfolded_{name}_rounds{rounds}.stim"
            path.write_text(text)
            print(f"wrote {path.relative_to(HERE)}: detectors deterministic, check observables "
                  f"{checks.round(3).tolist()} (without feedforward: {bare_obs[:4].round(3).tolist()}), "
                  f"output observable {obs[4]:.3f}")
            del plain


if __name__ == "__main__":
    main()

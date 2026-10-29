"""Write native-T fold-transversal cultivation circuits (Sahay et al., arXiv:2509.05212).

The authors' released circuits (stim_src/MSC_foldedH/sample_circuits, kaavyas99/MSC_foldedH at
9378fd2) cultivate a |Y> state: the controlled fold-transversal H_XY checks of the T protocol are
replaced by controlled-Y (CY) layers. Turning them back into T circuits is not a gate-by-gate
substitution (each CY layer becomes CCZ and controlled-(S X) gates), so this script uses the
native-T reconstructions of Wan and Zapirain (arXiv:2609.18922, kh428/exact_ler_for_msc at
332bc04, ``data/alternatives/inputs/fold-d{3,5}/model.json``):

- fold-d3: the 374-location terminated native-T core with unitary injection (two fold-transversal
  H_XY checks, noiseless code projection, no pre-escape round, no escape).
- fold-d5: the 2,116-location native-T reconstruction with hook injection, (r1, r2) = (2, 0) and
  controlled-layer counts 3, 3, 7, 7, built from the authors' updated proxy
  ``new_cultivation_proxy.stim`` (stim_src/exact_ler_native_T_models/fold-d5/source_proxy.stim).

Those models are event lists for the authors' exact calculation. This script exports them to the
Tsim/Clifft Stim dialect:

- CSX / CS_DAG_X are controlled-(S X) / controlled-(S_DAG X) (``unitary()`` in their
  ``alternatives/calculation/pauli_polynomial.py``), decomposed into CX + CS(_DAG) and then T gates
  (tools/gates.py, checked against the unitaries).
- INJECT_HXY prepares T|+> on a fresh qubit: emitted as H then T.
- POST_Z (fold-d3) postselects a qubit on Z = +1: emitted as M plus a DETECTOR.
- MEASURE / MEASURE_PRODUCT become M/MX/MY and MPP, FEEDBACK_X/Z become classically controlled
  CX/CZ, DETECTOR events reference absolute record numbers, translated to rec[-k].
- Noise locations become DEPOLARIZE1/DEPOLARIZE2(p), X_ERROR(p) (axis-less flips act on a Z-basis
  register and are X flips), and three-qubit depolarizing noise as CORRELATED_ERROR /
  ELSE_CORRELATED_ERROR chains over the 63 non-identity Paulis (see ``depolarize3``).

Each circuit is sampled noiselessly in Tsim: no detector may be random.

Usage: uv run python make_circuits.py [--noise 0.001]
"""

import argparse
import itertools
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
MODELS = HERE / "stim_src" / "exact_ler_native_T_models"
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import gates  # noqa: E402
import validate  # noqa: E402

DIRECT = {"R", "H", "CX", "CZ", "T", "T_DAG", "S", "S_DAG", "X", "Y", "Z", "CCZ"}


def depolarize3(support, p, chain_length=9):
    """Three-qubit depolarizing noise: each of the 63 non-identity Paulis with probability p/63.

    NOTE: Tsim compiles a CORRELATED_ERROR / ELSE_CORRELATED_ERROR chain of length k into a
    2^k table, so one exact 63-element chain fails ("Maximum allowed dimension exceeded").
    The 63 Paulis are therefore split into 7 independent chains of 9. Each Pauli keeps its
    marginal probability p/63; only the O(p^2) probability of two simultaneous faults differs
    from exact three-qubit depolarizing noise.
    """
    paulis = [ps for ps in itertools.product("IXYZ", repeat=3) if ps != ("I", "I", "I")]
    lines = []
    for start in range(0, len(paulis), chain_length):
        remaining = 1.0
        for k, ps in enumerate(paulis[start:start + chain_length]):
            term = " ".join(f"{a}{q}" for a, q in zip(ps, support) if a != "I")
            prob = (p / 63) / remaining
            lines.append(f"{'E' if k == 0 else 'ELSE_CORRELATED_ERROR'}({prob!r}) {term}")
            remaining -= p / 63
    return lines


def noise_lines(channel, p):
    kind, support = channel["kind"], channel["support"]
    if kind in ("depolarizing", "depol1", "depol2", "depol3"):
        n = len(support)
        if n == 1:
            return [f"DEPOLARIZE1({p}) {support[0]}"]
        if n == 2:
            return [f"DEPOLARIZE2({p}) {support[0]} {support[1]}"]
        if n == 3:
            return depolarize3(support, p)
    if kind == "flip":
        axis = channel.get("axis") or "X"
        return [f"{axis}_ERROR({p}) {support[0]}"]
    raise ValueError(channel)


def export(model, p):
    channels = model["channels"]
    by_location = {c.get("location", i): c for i, c in enumerate(channels)}
    lines = []
    num_records = 0
    for event in model["events"]:
        name = event["name"]
        support = event.get("support", [])
        if name in DIRECT:
            lines.append(f"{name} {' '.join(map(str, support))}")
        elif name == "CSX":
            lines += gates.emit(gates.C_SX, support)
        elif name == "CS_DAG_X":
            lines += gates.emit(gates.C_SDAGX, support)
        elif name == "INJECT_HXY":
            lines += [f"H {support[0]}", f"T {support[0]}"]
        elif name == "NOISE":
            if p > 0:
                lines += noise_lines(by_location[event["location"]], p)
        elif name == "MEASURE":
            assert event["record"] == num_records, event
            gate = {"Z": "M", "X": "MX", "Y": "MY"}[event["axis"]]
            lines.append(f"{gate} {'!' if event['inverted'] else ''}{support[0]}")
            num_records += 1
        elif name == "MEASURE_PRODUCT":
            assert event["record"] == num_records, event
            lines.append("MPP " + "*".join(f"{event['axis']}{q}" for q in support))
            num_records += 1
        elif name == "POST_Z":
            lines += [f"M {support[0]}", "DETECTOR rec[-1]"]
            num_records += 1
        elif name in ("FEEDBACK_X", "FEEDBACK_Z"):
            gate = "CX" if name == "FEEDBACK_X" else "CZ"
            lines.append(f"{gate} rec[{event['record'] - num_records}] {support[0]}")
        elif name == "DETECTOR":
            lines.append("DETECTOR " + " ".join(f"rec[{r - num_records}]" for r in event["records"]))
        else:
            raise ValueError(f"unknown event {event}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noise", type=float, default=0.001)
    args = parser.parse_args()
    gates.verify()
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for name in ["fold-d3", "fold-d5"]:
        model = json.loads((MODELS / name / "model.json").read_text())
        text = export(model, args.noise)
        result = validate.check(text, shots=2048)
        assert result["random_detectors"] == 0, (name, result)
        path = out / f"{name}_native_T_p{args.noise}.stim"
        path.write_text(text)
        print(f"wrote {path.relative_to(HERE)}: {result}")


if __name__ == "__main__":
    main()

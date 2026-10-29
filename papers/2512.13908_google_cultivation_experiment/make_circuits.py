"""Write the T-gate circuits of Google's cultivation experiment (Rosenfeld, Gidney, et al.,
arXiv:2512.13908) from the published Cirq and Stim files.

Zenodo 10.5281/zenodo.17872003 stores, per experiment, the Cirq circuit that was run
(``cirq_circuit[_X|_Z].json``, with the real non-Clifford gates) and a Stim circuit
(``stim[_X|_Z].stim``) in which, per the dataset README, "non-clifford gates are removed, and
replaced with Clifford gates that make the observable values deterministic", and the H_YZ
conjugations of the non-Clifford Y rotations are replaced by identities. Only the circuit files
were extracted from the multi-GB archives (tools/remote_zip.py).

Both files have one Stim TICK per Cirq moment, so the Stim circuit is repaired moment by moment
from the Cirq circuit:

- ``ZPowGate(+-0.25)`` (the transversal T / T^dagger of the double checks) -> ``T`` / ``T_DAG`` on
  the identity placeholders of that moment;
- the H_YZ ``SingleQubitCliffordGate`` conjugating them -> ``H_YZ`` on the identity placeholders;
- the injection ``ZPowGate(2 theta)`` -> ``T``. The paper injects |theta> = exp(-i theta Y/2)|0>
  (Y rotation = H_YZ-conjugated Z rotation) and |T> corresponds to theta = pi/4, i.e. Z^(1/4).

For Fig. 2 and 3 the Stim files tag the placeholders (``I[T_gate]``, ``I[conjugate]``,
``S[injection]``, ...); the Cirq-driven repair is checked to reproduce the tag-based substitution
exactly. Remaining tags (``I[echo]``, ``M[root_measurement]``) are stripped from the output,
since Clifft rejects tags. Fig. 4 files carry no tags and are repaired from Cirq only. Every circuit is sampled
noiselessly in Tsim: no detector may be random, and detectors that are deterministic in both the
proxy and the T circuit must agree. The Stim files are noiseless (the experiment's noise is
hardware noise); uniform depolarizing noise is not added.

Usage: uv run python make_circuits.py
"""

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "stim_src" / "zenodo_17872003"
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import validate  # noqa: E402

# The H_YZ tableau as serialized by cirq.SingleQubitCliffordGate in these files.
H_YZ_TABLEAU = {"n": 1, "rs": [True, False], "xs": [[True], [True]], "zs": [[False], [True]]}


def qubit_map(stim_text):
    mapping = {}
    for m in re.finditer(r"^QUBIT_COORDS\(([-\d.]+), ([-\d.]+)\) (\d+)$", stim_text, flags=re.M):
        mapping[(int(float(m.group(1))), int(float(m.group(2))))] = int(m.group(3))
    return mapping


def moment_rewrites(cirq_json, q2i):
    """Return {moment: {qubit: gate}} for the non-Clifford gates and their conjugations."""
    rewrites = {}
    for i, moment in enumerate(cirq_json["moments"]):
        for op in moment["operations"]:
            gate = op.get("gate", {})
            kind = gate.get("cirq_type")
            qubits = [q2i[(q["row"], q["col"])] for q in op.get("qubits", [])]
            new = None
            if kind == "ZPowGate":
                e = gate["exponent"]
                if isinstance(e, dict):
                    new = "T"  # injection Z^(2 theta) at the T-state angle
                elif abs(e - 0.25) < 1e-9:
                    new = "T"
                elif abs(e + 0.25) < 1e-9:
                    new = "T_DAG"
                elif abs(e) > 1e-9:
                    raise ValueError(f"unexpected ZPowGate exponent {e}")
            elif kind == "SingleQubitCliffordGate":
                if {k: v for k, v in gate.items() if k != "cirq_type"} != H_YZ_TABLEAU:
                    raise ValueError(f"unexpected Clifford {gate}")
                new = "H_YZ"
            if new is not None:
                for q in qubits:
                    rewrites.setdefault(i, {})[q] = new
    return rewrites


def repair(stim_text, cirq_json):
    q2i = qubit_map(stim_text)
    rewrites = moment_rewrites(cirq_json, q2i)
    lines = stim_text.splitlines()
    assert sum(line == "TICK" for line in lines) == len(cirq_json["moments"])
    out, moment = [], 0
    for line in lines:
        if line == "TICK":
            moment += 1
            out.append(line)
            continue
        todo = rewrites.get(moment, {})
        # Single-qubit placeholders: I (removed gate or conjugation), S (injection stand-in),
        # H (conjugation stand-in in some Z-basis files), H_YZ (kept injection conjugation).
        m = re.match(r"^(I|S|H|H_YZ)(\[[a-zA-Z_]+\])? ([\d ]+)$", line)
        if not todo or not m:
            out.append(line)
            continue
        name, targets = m.group(1), [int(t) for t in m.group(3).split()]
        keep = [t for t in targets if t not in todo]
        changed = [t for t in targets if t in todo]
        if keep:
            out.append(f"{name}{m.group(2) or ''} {' '.join(map(str, keep))}")
        for gate in dict.fromkeys(todo[t] for t in changed):
            qs = [t for t in changed if todo[t] == gate]
            out.append(f"{gate} {' '.join(map(str, qs))}")
            for t in qs:
                del todo[t]
    assert not any(rewrites.get(k) for k in rewrites), f"unapplied rewrites {rewrites}"
    return "\n".join(out) + "\n"


def tag_based(text):
    text = re.sub(r"^(\s*)(S|I)\[injection\]", r"\1T", text, count=1, flags=re.M)
    text = re.sub(r"^(\s*)I\[conjugate\]", r"\1H_YZ", text, flags=re.M)
    text = re.sub(r"^(\s*)I\[T_gate\]", r"\1T", text, flags=re.M)
    text = re.sub(r"^(\s*)I\[T_dagger_gate\]", r"\1T_DAG", text, flags=re.M)
    return text


def strip_tags(text):
    return re.sub(r"^([A-Z_]+)\[[a-zA-Z_]+\]", r"\1", text, flags=re.M)


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for stim_path in sorted(SRC.glob("fig*/*/stim*.stim")):
        cirq_path = stim_path.with_name("cirq_circuit" + stim_path.stem[len("stim"):] + ".json")
        proxy = stim_path.read_text()
        text = repair(proxy, json.loads(cirq_path.read_text()))
        if "[T_gate]" in proxy or "[injection]" in proxy:
            assert strip_tags(text) == strip_tags(tag_based(proxy)), stim_path
        result = validate.check(text, proxy=proxy, shots=2048)
        assert result["random_detectors"] == 0 and result["matches_proxy"], (stim_path, result)
        rel = stim_path.relative_to(SRC)
        name = f"{rel.parts[0]}_{rel.parts[1]}_{rel.stem}_T.stim".replace("=", "")
        # Tags are annotations (e.g. I[echo]); Clifft only accepts them on LEVEL_TRANSITION.
        (out / name).write_text(strip_tags(text))
        print(f"wrote stim/{name}: {result}")


if __name__ == "__main__":
    main()

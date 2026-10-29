"""Convert the Magna example protocols (Wang, Gu, arXiv:2610.22315) to the Tsim/Clifft Stim dialect.

Magna's circuits (stim_src/magna/examples/*/physical.magna, itpyi/magna at 01ae9c2) are Stim-style
files with native non-Clifford gates plus classical registers (docs/software/circuit-format.md):
``CONTROL[XOR|NOT] inputs -> ctrl[k]``, classically controlled gates (``CS_DAG ctrl[0] 16``),
``det[n]`` references and ``POSTSELECT``. This script translates them:

- ``ctrl[k]`` registers and ``det[n]`` are tracked as parities of measurement records (plus a
  constant). External decoder registers (TQD memory, logical distillation) cannot be expressed in
  Stim; those examples are skipped.
- Classically controlled Pauli gates (CX/CY/CZ) become one Stim ``rec``-controlled gate per record,
  plus an unconditional Pauli for a constant 1.
- Classically controlled non-Pauli gates (CS, CS_DAG, CH, CCZ, CCX) are applied as quantum-controlled
  gates (deferred measurement). Every measurement whose record such a gate reads is performed
  through a fresh record ancilla: ``CX q -> a`` (after H / H_YZ for X / Y measurements) collapses q
  exactly as the measurement does, the inversion ``!`` and report-flip noise ``M(p)`` are applied to
  the ancilla, and the record is the measurement of the ancilla, which keeps the reported bit. At
  the correction, the parity of the record ancillas (plus a constant) is copied onto a scratch
  qubit that controls the gate. This is exact, also when the measured qubit is reused.
- Quantum CS, CS_DAG and CH are decomposed into T/T_DAG, CX, H, S (tools/gates.py).
- ``POSTSELECT`` lines (acceptance conditions) and ``CONTROL`` lines are dropped; all detectors are
  kept, so postselection can be applied on them.

Each converted circuit is sampled noiselessly in Tsim; detectors that Magna postselects must be
deterministic, and, where the task defines an ideal target circuit, undoing it on the output qubits
must leave every output in |0> (``target_check``).

Usage: uv run python make_circuits.py [example ...]
"""

import pathlib
import re
import sys
from fractions import Fraction

HERE = pathlib.Path(__file__).parent
EXAMPLES = HERE / "stim_src" / "magna" / "examples"
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import gates  # noqa: E402
import validate  # noqa: E402

REF = re.compile(r"^(!?)(ctrl|rec|det)\[(-?\d+)\]$")
SINGLE_MEASURE = {"M": "Z", "MZ": "Z", "MX": "X", "MY": "Y", "MR": "Z", "MRX": "X", "MRY": "Y", "MRZ": "Z"}
PAULI_CONTROLLED = {"CX", "CY", "CZ", "CNOT", "ZCX", "ZCY", "ZCZ"}
QUANTUM_DECOMPOSE = {"CS": gates.CS, "CS_DAG": gates.CS_DAG, "CH": gates.CH}
CONTROLLED_1Q = {"CS": gates.CS, "CS_DAG": gates.CS_DAG, "CH": gates.CH}


class Unsupported(Exception):
    pass


def decimal_args(args):
    """Magna accepts fractions such as ``(1/1000)``; Stim needs decimals."""
    if not args:
        return ""
    values = [str(float(Fraction(v.strip()))) if "/" in v else v.strip() for v in args[1:-1].split(",")]
    return "(" + ", ".join(values) + ")"


def parse(line):
    line = line.split("#")[0].strip()
    if not line:
        return None
    m = re.match(r"^([A-Z_0-9]+)(\[[A-Za-z_0-9]+\])?(\([^)]*\))?\s*(.*)$", line)
    name, tag, args, rest = m.group(1), m.group(2), m.group(3), m.group(4)
    return name, (tag or "")[1:-1], decimal_args(args), rest.split()


def num_records(name, targets):
    if name in SINGLE_MEASURE:
        return len(targets)
    if name == "MPP":
        return len(targets)
    if name in ("MXX", "MYY", "MZZ"):
        return len(targets) // 2
    return 0


def convert(text):
    """Translate one Magna circuit; see the module docstring for the rules."""
    lines = [p for p in (parse(raw) for raw in text.splitlines()) if p]
    if any(name == "REPEAT" for name, *_ in lines):
        raise Unsupported("REPEAT")
    needed = set()
    while True:
        result, used = _convert(lines, needed)
        if used <= needed:
            return result
        needed |= used


def _convert(lines, copied):
    """One translation pass. Records in ``copied`` are measured through a fresh record ancilla.

    Returns the circuit text and the set of records that non-Pauli classical controls read.
    """
    max_qubit = max((int(q) for _, _, _, ts in lines for t in ts if not REF.match(t)
                     for q in re.findall(r"\d+", t)), default=0)
    scratch = max_qubit + 1
    next_ancilla = [max_qubit + 2]
    record_ancilla = {}  # absolute record -> qubit holding its reported value

    out = []
    registers = {}
    detectors = []
    used = set()
    nrec = 0

    def resolve(token):
        """Return (frozenset of absolute record indices, constant bit) of a classical reference."""
        neg, kind, idx = REF.match(token).groups()
        idx = int(idx)
        if kind == "rec":
            recs, const = frozenset([nrec + idx]), 0
        elif kind == "det":
            recs, const = detectors[idx if idx >= 0 else len(detectors) + idx], 0
        else:
            if idx not in registers:
                raise Unsupported(f"register ctrl[{idx}] is written by an external decoder")
            recs, const = registers[idx]
        return recs, const ^ (neg == "!")

    def xor(parts):
        acc, const = set(), 0
        for recs, c in parts:
            acc ^= set(recs)
            const ^= c
        return frozenset(acc), const

    for name, tag, args, ts in lines:
        if name == "CONTROL":
            arrow = ts.index("->")
            inputs, outputs = ts[:arrow], ts[arrow + 1:]
            if tag not in ("XOR", "NOT"):
                raise Unsupported(f"external decoder CONTROL[{tag}]")
            constant = int(args.strip("()") or 0) if tag == "XOR" else 1
            value = xor([resolve(t) for t in inputs] + [(frozenset(), constant)])
            for o in outputs:
                registers[int(REF.match(o).group(3))] = value
            continue
        if name == "POSTSELECT":
            continue
        if name == "DETECTOR":
            recs, _ = xor([resolve(t) for t in ts])
            detectors.append(recs)
            out.append(f"DETECTOR{args} " + " ".join(f"rec[{r - nrec}]" for r in sorted(recs)))
            continue
        if any(REF.match(t) for t in ts) and name != "OBSERVABLE_INCLUDE":
            if name in PAULI_CONTROLLED:
                pauli = {"CX": "X", "CNOT": "X", "ZCX": "X", "CY": "Y", "ZCY": "Y", "CZ": "Z", "ZCZ": "Z"}[name]
                for a, b in zip(ts[0::2], ts[1::2]):
                    c, q = (a, b) if REF.match(a) else (b, a)
                    recs, const = resolve(c)
                    out += [f"{name} rec[{r - nrec}] {q}" for r in sorted(recs)]
                    if const:
                        out.append(f"{pauli} {q}")
                continue
            if name not in CONTROLLED_1Q and name not in ("CCZ", "CCX"):
                raise Unsupported(f"classically controlled {name}")
            arity = 3 if name in ("CCZ", "CCX") else 2
            for k in range(0, len(ts), arity):
                group = ts[k:k + arity]
                recs, const = resolve(group[0])
                used |= recs
                # Copy the control parity onto the scratch qubit and apply the controlled gate.
                out.append(f"R {scratch}")
                for r in sorted(recs):
                    if r in record_ancilla:
                        out.append(f"CX {record_ancilla[r]} {scratch}")
                if const:
                    out.append(f"X {scratch}")
                targets = [scratch] + [int(t) for t in group[1:]]
                if name in CONTROLLED_1Q:
                    out += gates.emit(CONTROLLED_1Q[name], targets)
                else:
                    out.append(f"{name} {' '.join(map(str, targets))}")
            continue
        if name in QUANTUM_DECOMPOSE:
            for k in range(0, len(ts), 2):
                out += gates.emit(QUANTUM_DECOMPOSE[name], [int(t) for t in ts[k:k + 2]])
            continue
        if name in SINGLE_MEASURE and any(nrec + k in copied for k in range(len(ts))):
            # Measure through a record ancilla: CX copies the Z value (after H for X, H_YZ for Y),
            # which collapses the qubit exactly like the measurement; the ancilla then keeps the
            # reported bit (inversion and report-flip noise applied to it) for later controls.
            basis = SINGLE_MEASURE[name]
            for k, t in enumerate(ts):
                r = nrec + k
                if r not in copied:
                    out.append(f"{name}{args} {t}")
                    continue
                q, a = int(t.lstrip("!")), next_ancilla[0]
                next_ancilla[0] += 1
                record_ancilla[r] = a
                rotate = {"Z": [], "X": [f"H {q}"], "Y": [f"H_YZ {q}"]}[basis]
                out += [f"R {a}"] + rotate + [f"CX {q} {a}"] + rotate
                if t.startswith("!"):
                    out.append(f"X {a}")
                if args:
                    out.append(f"X_ERROR{args} {a}")
                out.append(f"M {a}")
                if name.startswith("MR"):
                    out.append(f"R{basis if basis != 'Z' else ''} {q}")
            nrec += len(ts)
            continue
        out.append(f"{name}{args} {' '.join(ts)}".rstrip())
        nrec += num_records(name, ts)
    return "\n".join(out) + "\n", used


def postselected_detectors(text):
    """Indices of detectors named in POSTSELECT lines."""
    return sorted({int(i) for i in re.findall(r"det\[(\d+)\]", " ".join(
        line for line in text.splitlines() if line.startswith("POSTSELECT")))})


INVERSE = {"H": "H", "S": "S_DAG", "S_DAG": "S", "T": "T_DAG", "T_DAG": "T", "X": "X", "Z": "Z",
           "CX": "CX", "CZ": "CZ"}


def target_check(example, text):
    """Undo the task's ideal target circuit on the output qubits and measure them in Z.

    Without noise every accepted output equals the ideal target state, so each output must read 0.
    Returns the output means, or None if the task needs a recovery circuit (dk) or has no target.
    """
    import json

    task = json.loads((EXAMPLES / example / "task.json").read_text())
    if "recovery" in task or "ideal_state" not in task:
        return None
    outputs = task["outputs"]
    ideal = [p for p in (parse(raw) for raw in (EXAMPLES / example / task["ideal_state"]).read_text().splitlines()) if p]
    undo = []
    for name, _, _, ts in reversed(ideal):
        arity = 2 if name in ("CX", "CZ") else 1
        groups = [ts[k:k + arity] for k in range(0, len(ts), arity)]
        for group in reversed(groups):
            undo.append(f"{INVERSE[name]} {' '.join(str(outputs[int(t)]) for t in group)}")
    base = sum(1 for _ in re.finditer(r"^OBSERVABLE_INCLUDE", text, flags=re.M))
    probe = text + "\n".join(undo) + "\n" + f"M {' '.join(map(str, outputs))}\n" + "".join(
        f"OBSERVABLE_INCLUDE({base + k}) rec[{k - len(outputs)}]\n" for k in range(len(outputs)))
    _, obs = validate.sample(probe, shots=512)
    return obs[base:]


def main():
    import numpy as np

    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    names = sys.argv[1:] or sorted(p.name for p in EXAMPLES.iterdir() if (p / "physical.magna").exists())
    for name in names:
        source = (EXAMPLES / name / "physical.magna").read_text()
        try:
            text = convert(source)
        except Unsupported as error:
            print(f"skip {name}: {error}")
            continue
        det, _ = validate.sample(text, shots=1024)
        post = postselected_detectors(source)
        random = [d for d in post if 0 < det[d] < 1]
        assert not random, (name, random)
        target = target_check(name, text)
        assert target is None or not np.any(target), (name, target)
        (out / f"{name}.stim").write_text(text)
        print(f"wrote stim/{name}.stim: {len(det)} detectors, {len(post)} postselected, all deterministic; "
              + ("target check skipped" if target is None else f"outputs equal the ideal target state ({len(target)} qubits)"))


if __name__ == "__main__":
    main()

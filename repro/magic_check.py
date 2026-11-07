r"""Turn a random Pauli readout of a magic state into a deterministic, noiseless magic-basis check.

Many published proxies end with a noiseless logical readout that is deterministic for the Clifford
proxy state (e.g. ``Y_L`` for ``|+i>``) but random for the real magic state (``T|+>`` has
``<Y_L> = 1/sqrt 2``). We insert, right after the circuit's last noise channel, the noiseless
logical rotation ``exp(-i pi theta/2 * P_L)`` (``P_L`` a logical Pauli) that maps the magic axis onto
the measured axis, e.g. ``exp(-i pi/8 Z_L)`` maps ``(X_L + Y_L)/sqrt 2`` to ``Y_L``. The rotation is a
phase gadget (single-qubit basis changes, a CX ladder onto one qubit, ``R_Z(theta)``, undo), so it
commutes with every stabilizer of the code: detectors and Pauli-frame records are unchanged, and
the original readout now measures the magic-basis observable in every syndrome sector. This is the
standard "noiseless projection" used by the papers (Gidney's ``T ... T_DAG`` wrap is the transversal
special case).

For CSS codes a logical ``Y_L`` written as a Pauli product splits into ``X_L`` (its X/Y positions)
and ``Z_L`` (its Z/Y positions), both logical operators.
"""

import re

from repro import common

NOISE_RE = re.compile(r"^\s*(" + "|".join(common.NOISE_NAMES) + r")\b")


def parse_product(s):
    """``"Z3*Y4*X1"`` -> ``{3: "Z", 4: "Y", 1: "X"}``."""
    out = {}
    for tok in s.split("*"):
        tok = tok.strip()
        out[int(tok[1:])] = tok[0]
    return out


def split_y(y):
    xl = {q: "X" for q, p in y.items() if p in "XY"}
    zl = {q: "Z" for q, p in y.items() if p in "ZY"}
    return xl, zl


def gadget(pauli, theta):
    """Lines implementing ``R_P(theta)`` (half turns) for a multi-qubit Pauli ``{qubit: 'X'|'Y'|'Z'}``."""
    qs = sorted(pauli)
    pre = []
    for q in qs:
        if pauli[q] == "X":
            pre.append(f"H {q}")
        elif pauli[q] == "Y":
            pre.append(f"H_YZ {q}")
    pivot = qs[0]
    ladder = [f"CX {q} {pivot}" for q in qs[1:]]
    return pre + ladder + [f"R_Z({theta}) {pivot}"] + ladder[::-1] + pre[::-1]


def last_noise_index(lines):
    return max(i for i, l in enumerate(lines) if NOISE_RE.match(l) or re.match(r"^\s*M[A-Z]*\(", l))


def insert_rotation(text, pauli, theta, index=None):
    lines = text.splitlines()
    i = last_noise_index(lines) + 1 if index is None else index
    return "\n".join(lines[:i] + gadget(pauli, theta) + lines[i:]) + "\n"


def make_deterministic(text, pauli, thetas=(0.25, -0.25, 0.75, -0.75), index=None):
    """Try each rotation angle; return the first circuit whose noiseless observables are deterministic."""
    errors = []
    for th in thetas:
        cand = insert_rotation(text, pauli, th, index)
        try:
            common.noiseless_check(cand)
            return cand, th
        except ValueError as e:
            errors.append(f"theta={th}: {e}")
    raise ValueError("no rotation makes the readout deterministic: " + "; ".join(errors))

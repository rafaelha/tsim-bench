"""Decompositions of non-Clifford gates into gates both Tsim and Clifft accept.

Both simulators accept T, T_DAG, CCZ, CCX (and rotations), but not CS, CH or
CSWAP. Each decomposition below is a list of ``(gate, local_targets)`` in time
order; ``verify()`` checks every one against its unitary up to global phase.
"""

import numpy as np

T = [("T", (0,))]
T_DAG = [("T_DAG", (0,))]
CS = [("T", (0,)), ("T", (1,)), ("CX", (0, 1)), ("T_DAG", (1,)), ("CX", (0, 1))]
CS_DAG = [("T_DAG", (0,)), ("T_DAG", (1,)), ("CX", (0, 1)), ("T", (1,)), ("CX", (0, 1))]
# Controlled Hadamard: H = (S H T) X (T_DAG H S_DAG) on the target, up to phase.
CH = [("S_DAG", (1,)), ("H", (1,)), ("T_DAG", (1,)), ("CX", (0, 1)), ("T", (1,)), ("H", (1,)), ("S", (1,))]
CSWAP = [("CX", (2, 1)), ("CCX", (0, 1, 2)), ("CX", (2, 1))]
CCZ = [("CCZ", (0, 1, 2))]

DECOMPOSITIONS = {"T": T, "T_DAG": T_DAG, "CS": CS, "CS_DAG": CS_DAG, "CH": CH,
                  "CSWAP": CSWAP, "CCZ": CCZ}


def emit(decomposition, targets):
    """Return Stim-dialect lines applying ``decomposition`` to ``targets``."""
    return [f"{g} {' '.join(str(targets[i]) for i in local)}" for g, local in decomposition]


# ---------------------------------------------------------------- verification

_1Q = {
    "H": np.array([[1, 1], [1, -1]]) / np.sqrt(2),
    "S": np.diag([1, 1j]),
    "S_DAG": np.diag([1, -1j]),
    "T": np.diag([1, np.exp(1j * np.pi / 4)]),
    "T_DAG": np.diag([1, np.exp(-1j * np.pi / 4)]),
    "X": np.array([[0, 1], [1, 0]]),
}


def _op(n, gate, targets):
    """Return the 2^n x 2^n unitary of one gate (qubit 0 is the most significant bit)."""
    dim = 2**n
    u = np.zeros((dim, dim), dtype=complex)
    for col in range(dim):
        bits = [(col >> (n - 1 - q)) & 1 for q in range(n)]
        if gate in _1Q:
            (q,) = targets
            for b in (0, 1):
                new = list(bits)
                new[q] = b
                row = sum(v << (n - 1 - i) for i, v in enumerate(new))
                u[row, col] += _1Q[gate][b, bits[q]]
            continue
        new = list(bits)
        phase = 1
        if gate == "CX":
            c, t = targets
            new[t] ^= bits[c]
        elif gate == "CZ":
            phase = -1 if bits[targets[0]] and bits[targets[1]] else 1
        elif gate == "CCX":
            a, b, t = targets
            new[t] ^= bits[a] & bits[b]
        elif gate == "CCZ":
            phase = -1 if all(bits[q] for q in targets) else 1
        else:
            raise ValueError(gate)
        row = sum(v << (n - 1 - i) for i, v in enumerate(new))
        u[row, col] += phase
    return u


def unitary(decomposition, n):
    u = np.eye(2**n, dtype=complex)
    for gate, targets in decomposition:
        u = _op(n, gate, targets) @ u
    return u


def _controlled(n, v):
    """Control qubit 0 on the (n-1)-qubit unitary ``v``."""
    half = 2 ** (n - 1)
    u = np.eye(2**n, dtype=complex)
    u[half:, half:] = v
    return u


def _same(a, b):
    k = np.argmax(np.abs(b))
    phase = a.flat[k] / b.flat[k]
    return np.isclose(abs(phase), 1) and np.allclose(a, phase * b)


def reference(name):
    if name == "T":
        return 1, _1Q["T"]
    if name == "T_DAG":
        return 1, _1Q["T_DAG"]
    if name == "CS":
        return 2, np.diag([1, 1, 1, 1j])
    if name == "CS_DAG":
        return 2, np.diag([1, 1, 1, -1j])
    if name == "CH":
        return 2, _controlled(2, _1Q["H"])
    if name == "CCZ":
        return 3, np.diag([1] * 7 + [-1])
    if name == "CSWAP":
        swap = np.eye(4)[[0, 2, 1, 3]]
        return 3, _controlled(3, swap)
    raise KeyError(name)


def verify():
    for name, decomposition in DECOMPOSITIONS.items():
        n, ref = reference(name)
        assert _same(unitary(decomposition, n), ref), name
    return True


if __name__ == "__main__":
    print("all decompositions verified:", verify())

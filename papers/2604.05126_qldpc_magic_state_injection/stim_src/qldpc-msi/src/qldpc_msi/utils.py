import argparse
import itertools
from typing import Any, Sequence, TypeVar

import numpy as np
import stim

T = TypeVar("T")


def kwarg_to_str(kwargs: dict[str, Any]) -> str:
    ss = ""
    for k, v in kwargs.items():
        if isinstance(v, list):
            ss += f"{k}={','.join(map(str, v))}-"
        else:
            ss += f"{k}={v}-"
    return ss[:-1]


def args_to_dicts(parser: argparse.ArgumentParser, args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    general_dict = {}
    decoder_dict = {}

    for action in parser._actions:
        # Skip help action
        if action.dest in ["help"]:
            continue

        value = getattr(args, action.dest)

        # Get the shortest option string (the abbreviation)
        abbr = min(action.option_strings, key=len) if action.option_strings else action.dest
        abbr = abbr.lstrip("-")  # Remove leading dashes

        # Check if argument belongs to decoder group
        if hasattr(action, "container") and action.container.title == "decoder":  # type: ignore
            decoder_dict[abbr] = value
        else:
            general_dict[abbr] = value

    return general_dict, decoder_dict


def split_xz(v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n2 = v.shape[-1]
    assert n2 % 2 == 0, "symplectic vector length must be 2*n"
    n = n2 // 2
    return v[:n].astype(np.uint8), v[n:].astype(np.uint8)


def anticommutes(a: np.ndarray, b: np.ndarray) -> bool:
    xa, za = split_xz(a)
    xb, zb = split_xz(b)
    sp = (xa @ zb + za @ xb) & 1
    return bool(sp)


def conjugate_sparse_pauli_by_symp_C(ps_sparse: dict[int, str], C_symp: np.ndarray, nq_per_mod: int) -> dict[int, str]:
    """Conjugate a sparse Pauli by a native quarter-turn about C: P -> C P C†."""
    v = to_symp_vec(ps_sparse, nq_per_mod)
    if anticommutes(v, C_symp):
        v = v ^ C_symp  # multiply by C up to phase
    return to_sparse_ps(v)


def get_anticomm_overlap(a: stim.PauliString, b: stim.PauliString) -> set[int]:
    """K(a, b): the set of qubits with uid i s.t. a[i] and b[i] anticommute.
    E.g., if a[i] and b[i] anticommute, then i is in the return set.
    """
    overlap = set(a.pauli_indices()) & set(b.pauli_indices())
    K = set()
    for i in overlap:
        if not a[i : i + 1].commutes(b[i : i + 1]):
            K.add(i)
    return K


def get_random_paulis(n_qubits: int, n_samples: int, seed: int, p_id: float = 0.25) -> list[stim.PauliString]:
    rng = np.random.default_rng(seed)
    paulis = []
    pauli_choices = np.array(["I", "X", "Y", "Z"])
    pauli_probs = [p_id, (1 - p_id) / 3, (1 - p_id) / 3, (1 - p_id) / 3]
    for _ in range(n_samples):
        pauli_str = "".join(rng.choice(pauli_choices, size=n_qubits, p=pauli_probs))
        if set(pauli_str) == {"I"}:
            continue
        paulis.append(stim.PauliString(pauli_str))
    return paulis


def to_stim_ps(symp: np.ndarray) -> stim.PauliString:
    """Convert a symplectic vector to a Pauli string."""
    n = symp.shape[0] // 2
    xs, zs = symp[:n], symp[n:]
    return stim.PauliString.from_numpy(xs=xs.astype(bool), zs=zs.astype(bool), num_qubits=n)


def get_pauli_string_from_sparse(sparse_term: dict[int, str], n_qubits: int) -> stim.PauliString:
    """Get Pauli string from sparse term."""
    xs = np.zeros(n_qubits, dtype=np.bool_)
    zs = np.zeros(n_qubits, dtype=np.bool_)
    for i, p in sparse_term.items():
        if p == "X":
            xs[i] = True
        elif p == "Z":
            zs[i] = True
        elif p == "Y":
            xs[i] = True
            zs[i] = True
        else:
            raise ValueError(f"Invalid Pauli string: {p}")
    ps = stim.PauliString.from_numpy(xs=xs, zs=zs)
    return ps


def sparse_ps_to_compact_str(ps: dict[int, str]) -> str:
    ss = ""
    for i, p in ps.items():
        ss += f"{p}{i}"
    ss = ss.strip()
    return ss


def to_symp_vec(ps: stim.PauliString | dict[int, str] | str, n_qubits: int | None = None) -> np.ndarray:
    """Convert a Pauli string to a symplectic vector.
    The Pauli string can be in one of the following formats:
    1. stim.PauliString
    2. dict[int, str]
    3. str

    Args:
        ps: Pauli string in one of the above formats.
        n_qubits: Number of qubits. Only used if ps is a dict.

    Returns:
        Symplectic vector.
    """
    if isinstance(ps, stim.PauliString):
        xs, zs = ps.to_numpy()
        return np.concatenate((xs, zs))
    elif isinstance(ps, dict) and n_qubits is not None:
        xs, zs = np.zeros(n_qubits, dtype=np.bool_), np.zeros(n_qubits, dtype=np.bool_)
        for i, p in ps.items():
            if p == "X":
                xs[i] = True
            elif p == "Z":
                zs[i] = True
            elif p == "Y":
                xs[i] = True
                zs[i] = True
        return np.concatenate((xs, zs))
    elif isinstance(ps, str):
        return to_symp_vec(stim.PauliString(ps))
    else:
        raise ValueError(f"Invalid Pauli string: {ps}")


def to_sparse_ps(ps: np.ndarray | stim.PauliString) -> dict[int, str]:
    # TODO: support other format of Pauli string
    """Convert a symplectic vector to a sparse Pauli string."""
    if isinstance(ps, stim.PauliString):
        ps = to_symp_vec(ps)
    n = ps.shape[0] // 2
    xs, zs = ps[:n], ps[n:]
    stim_ps = stim.PauliString.from_numpy(xs=xs.astype(bool), zs=zs.astype(bool))
    str_ps = str(stim_ps)[1:]
    sparse_ps = {}
    for i, p in enumerate(str_ps):
        if p in {"X", "Y", "Z"}:
            sparse_ps[i] = p
        elif p in {"I", "_"}:
            pass
        else:
            raise ValueError(f"Invalid Pauli string: {p} in {str_ps}")
    return sparse_ps


def powerset(s: Sequence[T]) -> list[tuple[T, ...]]:
    """
    Generates the powerset of a sequence.

    Args:
        s: A sequence (e.g., a list, tuple, or set).

    Returns:
        An list of tuples representing the subsets.
    """
    return list(itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s) + 1)))

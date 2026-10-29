"""
Moment-scheduled circuit utilities for JIT (just-in-time) resets and activation-aware noise.

Core idea:
- Represent a circuit as a list of "moments" (one moment per TICK interval).
- Insert resets as late as possible (right before first use) without adding bubbles.
- Apply Gidney-style NoiseModel moment-by-moment using a time-varying system_qubit_indices
  so qubits that haven't been reset yet do NOT receive idle depolarization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AbstractSet, Any, Iterable

import stim

# Keep in sync with the NoiseModel's notion of annotations.
ANNOTATION_OPS: set[str] = {
    "DETECTOR",
    "OBSERVABLE_INCLUDE",
    "QUBIT_COORDS",
    "SHIFT_COORDS",
    "TICK",
    "MPAD",
}


def occurs_in_classical_control_system(op: stim.CircuitInstruction) -> bool:
    """True if op is an annotation or a purely-classical control-system update.

    Example: CX rec[-1] 0 is a classical-control update, not a quantum gate.
    """
    if op.name in ANNOTATION_OPS:
        return True

    gate_data = stim.gate_data(op.name)
    if gate_data.is_unitary and gate_data.is_two_qubit_gate:
        targets = op.targets_copy()
        for k in range(0, len(targets), 2):
            a = targets[k]
            b = targets[k + 1]
            classical_0 = a.is_measurement_record_target or a.is_sweep_bit_target
            classical_1 = b.is_measurement_record_target or b.is_sweep_bit_target
            if not (classical_0 or classical_1):
                return False
        return True
    return False


def iter_quantum_qubit_targets(op: stim.CircuitInstruction) -> Iterable[int]:
    """Iterate qubit indices that are touched by this instruction (ignoring combiners)."""
    for t in op.targets_copy():
        if t.is_combiner:
            continue
        # Treat Pauli-product targets (MPP) as qubit touches too.
        if t.is_qubit_target or t.is_x_target or t.is_y_target or t.is_z_target:
            yield t.value


def moment_used_qubits(moment: stim.Circuit) -> set[int]:
    """Return the set of qubits that are operated on in this moment.

    Notes:
    - Ignores annotations and purely-classical control-system updates.
    - Counts resets/measurements as "use" (important for collision-avoidance when inserting resets).
    """
    used: set[int] = set()
    for op in moment:
        if isinstance(op, stim.CircuitRepeatBlock):
            raise NotImplementedError(
                "Repeat blocks inside a moment are not supported. "
                "Expand the schedule first or construct moments without repeats."
            )
        if not isinstance(op, stim.CircuitInstruction):
            continue
        if occurs_in_classical_control_system(op):
            continue
        for q in iter_quantum_qubit_targets(op):
            used.add(q)
    return used


def circuit_to_moments(circuit: stim.Circuit, *, keep_trailing_empty: bool = False) -> list[stim.Circuit]:
    """Split a stim circuit into a list of moments (subcircuits between TICKs).

    Consecutive TICKs become empty moments, preserving intentional idle time steps.

    Args:
        keep_trailing_empty: if the circuit ends in TICK, keep the final empty moment.

    Raises:
        NotImplementedError: if repeat blocks appear (split+rewrite into moments becomes ambiguous).
    """
    moments: list[stim.Circuit] = []
    cur = stim.Circuit()
    ended_with_tick = False

    for op in circuit:
        ended_with_tick = False
        if isinstance(op, stim.CircuitRepeatBlock):
            raise NotImplementedError(
                "Repeat blocks are not supported by circuit_to_moments. "
                "Either expand them or generate moment schedules directly."
            )
        if not isinstance(op, stim.CircuitInstruction):
            continue
        if op.name == "TICK":
            moments.append(cur)
            cur = stim.Circuit()
            ended_with_tick = True
        else:
            cur.append(op)

    if cur:
        moments.append(cur)
    elif keep_trailing_empty and ended_with_tick:
        moments.append(cur)

    return moments


def moments_to_circuit(moments: list[stim.Circuit]) -> stim.Circuit:
    """Join moments into a stim circuit with explicit TICK separators."""
    out = stim.Circuit()
    for k, m in enumerate(moments):
        if k:
            out.append("TICK")
        out += m
    return out


def _compute_first_use(used_per_moment: list[set[int]], qubits: AbstractSet[int]) -> dict[int, int]:
    """Earliest moment index where each qubit is used. Raises if a qubit is never used."""
    first: dict[int, int] = {}
    for q in qubits:
        first[q] = -1
    for t, used in enumerate(used_per_moment):
        hit = qubits & used
        for q in hit:
            if first[q] == -1:
                first[q] = t
    missing = [q for q, t in first.items() if t == -1]
    if missing:
        raise ValueError(f"Some qubits were never used, cannot JIT-reset them: {missing}")
    return first


def _prepend_ops(moment: stim.Circuit, op_name: str, targets: list[int]) -> stim.Circuit:
    """Return a new moment with `op_name targets` prepended before existing ops."""
    if not targets:
        return moment
    new = stim.Circuit()
    new.append(op_name, targets)
    new += moment
    return new


@dataclass(frozen=True)
class JitResetPlan:
    """Result of inserting JIT resets."""

    moments: list[stim.Circuit]
    activation_time: dict[int, int]  # qubit -> moment index where it becomes 'live'


def insert_jit_resets(
    moments: list[stim.Circuit],
    *,
    reset_gate_by_qubit: dict[int, str],
    jit_qubits: AbstractSet[int] | None = None,
) -> JitResetPlan:
    """Insert resets as late as possible, without introducing new TICK bubbles when avoidable.

    Policy:
    - For each qubit q in jit_qubits:
        place its reset in the latest moment strictly before its first quantum use,
        subject to: that moment must not already use q.
    - If a qubit is first-used in moment 0, a new moment is inserted at the front (one bubble),
      and all such qubits are reset there.

    Args:
        moments: list of moment circuits (no internal TICK).
        reset_gate_by_qubit: mapping q -> reset gate name, e.g. "RZ", "RX", "RY", "R".
        jit_qubits: which qubits to JIT. Default: keys of reset_gate_by_qubit.

    Returns:
        JitResetPlan with updated moments and activation times.

    Notes:
    - This function does not move resets that are already present in the moments.
      It's intended for data/injection qubits whose resets were previously placed in a dedicated layer.
    """
    if jit_qubits is None:
        jit_qubits = set(reset_gate_by_qubit.keys())
    else:
        jit_qubits = set(jit_qubits)

    # Copy moments so caller's list isn't mutated.
    out_moments = [m.copy() for m in moments]

    used_per = [moment_used_qubits(m) for m in out_moments]
    # print(f"used_per: {used_per}")
    # exit()
    first_use = _compute_first_use(used_per, jit_qubits)

    # If any jit qubit is first used in moment 0, we must create a new moment at the front.
    need_front = {q for q in jit_qubits if first_use[q] == 0}
    if need_front:
        out_moments.insert(0, stim.Circuit())
        used_per.insert(0, set())
        # Recompute after shifting.
        used_per = [moment_used_qubits(m) for m in out_moments]
        first_use = _compute_first_use(used_per, jit_qubits)

    # Decide insertion index for each qubit.
    insert_at: dict[int, int] = {}
    for q in jit_qubits:
        t = first_use[q]
        idx = t - 1
        while idx >= 0 and q in used_per[idx]:
            idx -= 1
        if idx < 0:
            # Extremely rare: q is used in every earlier moment; add a new front bubble.
            out_moments.insert(0, stim.Circuit())
            used_per.insert(0, set())
            used_per = [moment_used_qubits(m) for m in out_moments]
            first_use = _compute_first_use(used_per, jit_qubits)
            t = first_use[q]
            idx = t - 1
            while idx >= 0 and q in used_per[idx]:
                idx -= 1
            if idx < 0:
                raise RuntimeError(f"Failed to find a safe slot to reset qubit {q}.")
        insert_at[q] = idx

    # Group resets by (moment idx, gate name).
    resets_by_moment: dict[int, dict[str, list[int]]] = {}
    for q, idx in insert_at.items():
        gate = reset_gate_by_qubit[q]
        resets_by_moment.setdefault(idx, {}).setdefault(gate, []).append(q)

    # Apply (prepend) resets.
    for idx, gate_to_qs in resets_by_moment.items():
        # For determinism, apply in sorted gate name order and sorted qubit lists.
        for gate in sorted(gate_to_qs.keys()):
            qs = sorted(gate_to_qs[gate])
            out_moments[idx] = _prepend_ops(out_moments[idx], gate, qs)

    activation_time = {q: insert_at[q] for q in jit_qubits}
    return JitResetPlan(moments=out_moments, activation_time=activation_time)


def apply_noise_per_moment(
    moments: list[stim.Circuit],
    *,
    noise_model: Any,  # expected to provide .noisy_circuit(circuit, system_qubit_indices=..., immune_qubit_indices=...)
    activation_time: dict[int, int] | None = None,
    default_activation_time: int = 0,
    immune_qubits: AbstractSet[int] | None = None,
) -> stim.Circuit:
    """Apply a Gidney-style NoiseModel with activation-aware idling.

    Key point:
      The noise model's `system_qubit_indices` determines which qubits are eligible for idling noise.
      To avoid "pre-reset idling noise", pass only qubits that have been activated (reset) by time t.

    Args:
        moments: list of moment circuits (no internal TICK).
        noise_model: instance compatible with the NoiseModel interface.
        activation_time: optional mapping q -> moment index when q becomes live.
            If None, all qubits are live from t=0 (equivalent to noise_model.noisy_circuit on whole circuit).
        default_activation_time: activation time for qubits not listed in activation_time.
            Use 0 for "always live" (good for check ancillas).
        immune_qubits: passed through to noise_model as immune_qubit_indices.

    Returns:
        A noisy stim.Circuit with explicit TICKs between moments.
    """
    if immune_qubits is None:
        immune_qubits = set()
    if activation_time is None:
        activation_time = {}

    # Determine the universe of qubits by scanning all moments.
    all_qubits: set[int] = set()
    for m in moments:
        all_qubits |= moment_used_qubits(m)

    out = stim.Circuit()
    for t, m in enumerate(moments):
        if t:
            out.append("TICK")

        active = {q for q in all_qubits if activation_time.get(q, default_activation_time) <= t}

        # Ensure the noise model sees a moment even if `m` is empty by appending a TICK to a temporary circuit.
        tmp = stim.Circuit()
        tmp += m
        tmp.append("TICK")
        out += noise_model.noisy_circuit(
            tmp,
            system_qubit_indices=active,
            immune_qubit_indices=immune_qubits,
        )
    return out

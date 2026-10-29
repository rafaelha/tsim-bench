from __future__ import annotations

from codecs import ascii_encode
from dataclasses import dataclass
from functools import cached_property
from typing import Callable, Iterable, Literal

import numpy as np
import stim

from ..qec_toolkit.se._measurement_tracker import MeasurementTracker
from .CircuitScheduling import ColorationCircuit


class CheckTracker:
    """Track gates of stabilizer.
    For a given check qubit uid, record the 2q gate operations that are applied to it.
    In this way, we can know whether a check qubit could be measured early or not.
    """

    def __init__(self, chk_weights: dict[int, int], x_chk_uids: set[int], z_chk_uids: set[int]) -> None:
        self._CHK_WEIGHTS = chk_weights
        self._X_CHK_UIDS = x_chk_uids
        self._Z_CHK_UIDS = z_chk_uids
        self.chk_to_dat_uids: dict[int, set[int]] = {_uid: set() for _uid in chk_weights.keys()}

    def record(self, gates: list[tuple[int, int]]) -> None:
        for op1, op2 in gates:
            if op1 in self._CHK_WEIGHTS:
                chk_uid = op1
                dat_uid = op2
            elif op2 in self._CHK_WEIGHTS:
                chk_uid = op2
                dat_uid = op1
            else:
                raise ValueError(f"Invalid gate: {op1}, {op2}. One of them must be a check qubit.")

            if dat_uid in self.chk_to_dat_uids[chk_uid]:
                raise ValueError(f"Duplicate gate: {chk_uid} -> {dat_uid}.")

            self.chk_to_dat_uids[chk_uid].add(dat_uid)
        print(f"[CheckTracker] Recorded {gates}.")

    def measurables(self, chk_type: Literal["X", "Z"], *, reset: bool = False) -> list[int]:
        """Get the list of check qubit uids that can be measured early."""
        assert chk_type in ["X", "Z"]

        # print(f"[CheckTracker] chk_to_dat_uids: {self.chk_to_dat_uids}")

        measurables = []
        for chk_uid, dat_uids in self.chk_to_dat_uids.items():
            if len(dat_uids) == self._CHK_WEIGHTS[chk_uid]:
                measurables.append(chk_uid)

        # print(f"[CheckTracker] Measurables: {measurables}")

        if chk_type == "X":
            measurables = list(self._X_CHK_UIDS & set(measurables))
        elif chk_type == "Z":
            measurables = list(self._Z_CHK_UIDS & set(measurables))

        if reset and measurables:
            # print(f"[CheckTracker] Resetting {measurables}.")
            self.reset(measurables)

        print(f"[CheckTracker] {chk_type} Measured: {measurables}")
        return sorted(measurables)

    def reset(self, chk_uids: list[int]) -> None:
        for chk_uid in chk_uids:
            assert self._CHK_WEIGHTS[chk_uid] == len(
                self.chk_to_dat_uids[chk_uid]
            ), f"{chk_uid} has {len(self.chk_to_dat_uids[chk_uid])} data qubits, but should have {self._CHK_WEIGHTS[chk_uid]} data qubits."
            self.chk_to_dat_uids[chk_uid] = set()


@dataclass(frozen=True)
class XuHgpUidLayout:
    """UID layout that matches Fig. 5(a) of Xu et al.

    Let H have shape (nC, nV):
      - nV = number of classical bits (V)
      - nC = number of classical checks (C)

    Fig. 5 uses:
      - TOP axis (red box): horizontal code nodes V_h then C_h
      - LEFT axis:          vertical code nodes C_v then V_v

    We encode this as a (nC+nV) x (nV+nC) grid:

      rows:  C_v (0..nC-1)     | V_v (nC..nC+nV-1)
      cols:  V_h (0..nV-1)     | C_h (nV..nV+nC-1)

    Quadrants:
      - (C_v, V_h): Z ancillas
      - (C_v, C_h): CC data
      - (V_v, V_h): VV data
      - (V_v, C_h): X ancillas

    UID assignment is row-major:
      uid(row, col) = row * Ncol + col
    where Ncol = nV + nC.
    """

    nV: int
    nC: int
    Nrow: int
    Ncol: int

    data_vv_uids: tuple[int, ...]
    data_cc_uids: tuple[int, ...]
    data_all_uids: tuple[int, ...]

    z_anc_uids: tuple[int, ...]
    x_anc_uids: tuple[int, ...]

    uid_to_rc: dict[int, tuple[int, int]]

    def uid(self, row: int, col: int) -> int:
        return row * self.Ncol + col

    @cached_property
    def col_idx_to_uid(self) -> list[int]:
        # Must match the column order of Hx/Hz you pass to qldpc.
        # Here we use (VV | CC), which matches qldpc.get_matrix_product.
        return list(self.data_vv_uids) + list(self.data_cc_uids)


def compute_xz_chk_weights(
    H: np.ndarray,
    layout: XuHgpUidLayout,
) -> tuple[dict[int, int], dict[int, int]]:
    nC, nV = H.shape
    deg_row = np.asarray(H, dtype=np.uint8).sum(axis=1)
    deg_col = np.asarray(H, dtype=np.uint8).sum(axis=0)

    z_chk_weights = {layout.uid(a, j): int(deg_row[a]) + int(deg_col[j]) for a in range(nC) for j in range(nV)}
    x_chk_weights = {
        layout.uid(nC + i, nV + b): int(deg_row[b]) + int(deg_col[i]) for b in range(nC) for i in range(nV)
    }
    return x_chk_weights, z_chk_weights


def compute_chk_weights(
    H: np.ndarray,
    layout: XuHgpUidLayout,
) -> tuple[dict[int, int], dict[int, int], dict[int, int]]:
    """
    Returns:
      chk_w: total weight for each check ancilla uid (Z and X)
      z_w:   total weight for Z ancilla uids only
      x_w:   total weight for X ancilla uids only

    Weight model matches the *full* HGP stabilizer supported across both
    vertical + horizontal interactions in Xu Alg.3 pipelined SE.
    """
    H = (np.asarray(H) != 0).astype(np.uint8)
    nC, nV = H.shape
    if nC != layout.nC or nV != layout.nV:
        raise ValueError(f"H shape {H.shape} mismatches layout (nC={layout.nC}, nV={layout.nV})")

    row_deg = H.sum(axis=1)  # (nC,)   deg_row[a]
    col_deg = H.sum(axis=0)  # (nV,)   deg_col[j]

    z_w: dict[int, int] = {}
    for a in range(nC):
        ra = int(row_deg[a])
        for j in range(nV):
            z_uid = layout.uid(a, j)  # Z(a,j)
            z_w[z_uid] = ra + int(col_deg[j])

    x_w: dict[int, int] = {}
    for i in range(nV):
        ci = int(col_deg[i])
        for b in range(nC):
            x_uid = layout.uid(nC + i, nV + b)  # X(i,b)
            x_w[x_uid] = ci + int(row_deg[b])

    chk_w = {**z_w, **x_w}
    return chk_w, z_w, x_w


def visualize_layout(layout: XuHgpUidLayout, *, show_uid: bool = False) -> None:
    """Print a command-line visualization of the Fig.5 HGP grid layout.

    Fig.5 axes (as implemented in pipelined_se.py):
      - rows: C_v (checks) on top, then V_v (bits) on bottom
      - cols: V_h (bits) on left,  then C_h (checks) on right

    Quadrants:
      - (C_v rows, V_h cols): Z ancillas  -> 'Z'
      - (C_v rows, C_h cols): CC data     -> 'C'
      - (V_v rows, V_h cols): VV data     -> 'V'
      - (V_v rows, C_h cols): X ancillas  -> 'X'

    Args:
        layout: XuHgpUidLayout returned by make_xu_hgp_uid_layout_from_H.
        show_uid: If True, prints "symbol(uid)" per cell. This is wider output.
    """
    nC, nV = layout.nC, layout.nV
    Nrow, Ncol = layout.Nrow, layout.Ncol

    z = set(layout.z_anc_uids)
    x = set(layout.x_anc_uids)
    vv = set(layout.data_vv_uids)
    cc = set(layout.data_cc_uids)

    def cell(u: int) -> str:
        if u in z:
            s = "Z"
        elif u in x:
            s = "X"
        elif u in vv:
            s = "V"
        elif u in cc:
            s = "C"
        else:
            s = "?"  # should never happen because the four blocks cover the whole grid

        if not show_uid:
            return s

        return f"{s}({u})"

    # Column header
    print(f"rows: C_v(0..{nC-1}) then V_v({nC}..{nC+nV-1})")
    print(f"cols: V_h(0..{nV-1}) then C_h({nV}..{nV+nC-1})")
    print()

    # Build lines
    for r in range(Nrow):
        parts = []
        for c in range(Ncol):
            u = layout.uid(r, c)
            parts.append(cell(u))

        # Insert vertical bar between V_h and C_h.
        left = parts[:nV]
        right = parts[nV:]
        row_str = " ".join(left) + " | " + " ".join(right)

        # Optional row label
        if r < nC:
            prefix = f"Cv[{r:>2}] "
        else:
            prefix = f"Vv[{r-nC:>2}] "
        print(prefix + row_str)

        # Insert horizontal separator between C_v and V_v.
        if r == nC - 1:
            if show_uid:
                # separator length is approximate; keep it simple
                print("-" * 80)
            else:
                print("-" * (len(prefix) + (2 * Ncol - 1) + 3))


def make_xu_hgp_uid_layout_from_H(H: np.ndarray) -> XuHgpUidLayout:
    """Construct a Fig. 5-faithful XuHgpUidLayout from a classical check matrix H.

    Args:
        H: Binary matrix of shape (nC, nV).

    Returns:
        XuHgpUidLayout with region uid lists matching Fig. 5 quadrants.

    Notes:
        This only defines a naming/layout convention. It does not model movement.
    """
    H = np.asarray(H)
    if H.ndim != 2:
        raise ValueError(f"H must be 2D, got {H.shape}")
    nC, nV = H.shape

    Nrow = nC + nV
    Ncol = nV + nC

    def uid(row: int, col: int) -> int:
        return row * Ncol + col

    # Row/col splits.
    # rows: [0..nC-1]=C_v, [nC..nC+nV-1]=V_v
    # cols: [0..nV-1]=V_h, [nV..nV+nC-1]=C_h

    # VV data: (V_v rows, V_h cols) => bottom-left
    data_vv = tuple(uid(nC + i, j) for i in range(nV) for j in range(nV))
    # CC data: (C_v rows, C_h cols) => top-right
    data_cc = tuple(uid(a, nV + b) for a in range(nC) for b in range(nC))
    data_all = data_vv + data_cc

    # Z ancillas: (C_v rows, V_h cols) => top-left
    z_anc = tuple(uid(a, j) for a in range(nC) for j in range(nV))
    # X ancillas: (V_v rows, C_h cols) => bottom-right
    x_anc = tuple(uid(nC + i, nV + b) for i in range(nV) for b in range(nC))

    used = set(data_all + z_anc + x_anc)
    uid_to_rc = {u: (u // Ncol, u % Ncol) for u in used}

    return XuHgpUidLayout(
        nV=nV,
        nC=nC,
        Nrow=Nrow,
        Ncol=Ncol,
        data_vv_uids=data_vv,
        data_cc_uids=data_cc,
        data_all_uids=data_all,
        z_anc_uids=z_anc,
        x_anc_uids=x_anc,
        uid_to_rc=uid_to_rc,
    )


def xu_color_matchings_from_H(H: np.ndarray) -> list[dict[int, int]]:
    """Edge-coloring matchings from authors' CircuitScheduling.ColorationCircuit(H).

    Returns:
        A list of matchings; each is {check_index -> bit_index}.
        Indices are 0-based in both domains.
    """
    return ColorationCircuit(np.asarray(H))


def lift_horizontal_pairs_for_color(
    layout: XuHgpUidLayout,
    color: dict[int, int],
    *,
    include_z_cc: bool = True,
) -> list[tuple[int, int]]:
    """Horizontal-direction CZ pairs (Fig. 5-faithful).

    Horizontal direction uses the *horizontal* Tanner graph edges (C_h <-> V_h),
    replicated across all rows.

    For each matched edge (b in C_h) <-> (j in V_h):
      - For each V_v row i: pair X(i,b) -- VV(i,j)
      - For each C_v row a: pair Z(a,j) -- CC(a,b)   (optional; excluded in Alg.3 prelude)

    Args:
        include_z_cc: If False, omit Z(a,j)--CC(a,b) pairs (Alg.3 / Fig.7 first step).

    Returns:
        List of (uid1, uid2) pairs for CZ.
    """
    nV, nC = layout.nV, layout.nC
    pairs: list[tuple[int, int]] = []
    for b, j in color.items():
        # X(i,b) at (row=nC+i, col=nV+b), VV(i,j) at (row=nC+i, col=j)
        for i in range(nV):
            pairs.append((layout.uid(nC + i, nV + b), layout.uid(nC + i, j)))
        if include_z_cc:
            # Z(a,j) at (row=a, col=j), CC(a,b) at (row=a, col=nV+b)
            for a in range(nC):
                pairs.append((layout.uid(a, j), layout.uid(a, nV + b)))
    return pairs


def lift_vertical_pairs_for_color(
    layout: XuHgpUidLayout,
    color: dict[int, int],
    *,
    include_x_cc: bool,
) -> list[tuple[int, int]]:
    """Vertical-direction CZ pairs (Fig. 5-faithful).

    Vertical direction uses the *vertical* Tanner graph edges (C_v <-> V_v),
    replicated across all columns.

    For each matched edge (a in C_v) <-> (i in V_v):
      - For each V_h col j: pair Z(a,j) -- VV(i,j)
      - For each C_h col b: pair X(i,b) -- CC(a,b)   (optional)

    include_x_cc:
        In a "Z-only" final drain (after X ancillas are removed), set False.

    Returns:
        List of (uid1, uid2) pairs for CZ.
    """
    nV, nC = layout.nV, layout.nC
    pairs: list[tuple[int, int]] = []
    for a, i in color.items():
        # Z(a,j) at (row=a, col=j), VV(i,j) at (row=nC+i, col=j)
        for j in range(nV):
            pairs.append((layout.uid(a, j), layout.uid(nC + i, j)))
        if include_x_cc:
            # X(i,b) at (row=nC+i, col=nV+b), CC(a,b) at (row=a, col=nV+b)
            for b in range(nC):
                pairs.append((layout.uid(nC + i, nV + b), layout.uid(a, nV + b)))
    return pairs


def make_xu_hgp_pipelined_se_circuit_uid(
    H: np.ndarray,
    *,
    n_cycles: int = 2,
    include_qubit_coords: bool = False,
    add_time_detectors: bool = True,
    validate_keys: bool = True,
) -> tuple[stim.Circuit, MeasurementTracker, XuHgpUidLayout]:
    """Build a pipelined-style HGP SE circuit with Fig. 5-faithful layout.

    This remains a *clean* n_cycles builder (each X ancilla and each Z ancilla is
    measured exactly n_cycles times), but now:
      - VV is truly the bottom-left block (orange) per Fig. 5 / Alg. 3.
      - Horizontal/vertical CZ lifts match the Fig. 5 row/column semantics.
      - Alg.3 prelude has NO Z ancillas: we delay Z-ancilla preparation and exclude Z--CC
        horizontal CZs in the first horizontal sweep.

    Args:
        H: Classical check matrix (nC, nV).
        n_cycles: number of times each check ancilla is measured.
        include_qubit_coords: emit QUBIT_COORDS(x=col, y=row) for debugging.
        add_time_detectors: add detector between consecutive rounds per ancilla.
        validate_keys: assert all expected keys exist.

    Returns:
        (stim circuit, tracker, layout)
    """
    if n_cycles < 1:
        raise ValueError(f"n_cycles must be >= 1, got {n_cycles}")

    layout = make_xu_hgp_uid_layout_from_H(H)
    visualize_layout(layout, show_uid=True)
    colors = xu_color_matchings_from_H(H)

    c = stim.Circuit()
    tracker = MeasurementTracker()
    chk_weights, z_chk_weights, x_chk_weights = compute_chk_weights(H, layout)
    print(f"x_chk_weights: {x_chk_weights}")
    print(f"z_chk_weights: {z_chk_weights}")
    print(f"layout.x_anc_uids: {layout.x_anc_uids}")
    print(f"layout.z_anc_uids: {layout.z_anc_uids}")
    chk_tracker = CheckTracker(
        chk_weights=chk_weights, x_chk_uids=set(layout.x_anc_uids), z_chk_uids=set(layout.z_anc_uids)
    )

    if include_qubit_coords:
        for u in sorted(layout.uid_to_rc):
            r, col = layout.uid_to_rc[u]
            c.append("QUBIT_COORDS", [u], [float(col), float(r)])

    def x_key(u: int, r: int) -> tuple[str, int, int]:
        return ("X", u, r)

    def z_key(u: int, r: int) -> tuple[str, int, int]:
        return ("Z", u, r)

    def append_cz_layer(pairs: list[tuple[int, int]]) -> None:
        if not pairs:
            return
        flat: list[int] = []
        for a, b in pairs:
            flat.append(a)
            flat.append(b)
        chk_tracker.record(pairs)
        c.append_operation("CZ", flat)

    def measure_reset_x_basis(chk_type: Literal["X", "Z"], *, key_fn: Callable[[int], object]) -> None:
        """Measure in X basis then reset to |+> (RX). Correct for CZ-based SE with |+> ancillas."""
        ulist = chk_tracker.measurables(chk_type, reset=True)
        # print(f"[CheckTracker] Measuring {ulist} in {chk_type} basis.")
        c.append_operation("MX", ulist)
        for u in ulist:
            tracker.record_measurement(key_fn(u))
        c.append_operation("TICK")
        c.append_operation("RX", ulist)
        c.append_operation("TICK")

    def append_detector(keys: list[object]) -> None:
        targets = tracker.current_measurement_record_targets_for(keys)
        if targets is None:
            raise ValueError(f"Cannot form detector due to obstacle in keys={keys!r}")
        c.append_operation("DETECTOR", targets)

    # --- Initialization ---
    # Alg.3 prelude: include X ancillas, but do NOT include Z ancillas yet.
    c.append_operation("RX", list(layout.x_anc_uids))
    c.append_operation("TICK")

    # Prelude basis rotation: Fig.5/Alg.3 says bottom-left (VV, orange) is special.
    c.append_operation("H", list(layout.data_vv_uids))
    c.append_operation("TICK")

    # Prelude: first horizontal CZ sweep is X--VV only (no Z ancillas / no Z--CC pairs).
    for col in colors:
        append_cz_layer(lift_horizontal_pairs_for_color(layout, col, include_z_cc=False))
        c.append_operation("TICK")

    x_round = 0
    z_round = 0
    z_started = False  # becomes True once we first prepare Z ancillas

    for cycle_id in range(1, n_cycles):
        print(f"cycle_id: {cycle_id}")

        for direction in ["ver", "hor"]:
            # if cycle_id == n_cycles - 1 and direction == "hor":
            #     continue
            # --- vertical sweep (Alg. 3, line 7) ---
            if direction == "ver":
                c.append_operation("H", list(layout.data_all_uids))
                c.append_operation("TICK")

                if z_started:
                    # Normal pipeline: measure old Z ancillas in X basis, then reset to |+>.
                    measure_reset_x_basis("Z", key_fn=lambda u, r=z_round: z_key(u, r))
                    z_round += 1
                else:
                    # First appearance of Z ancillas: prepare fresh |+> only (no measurement).
                    c.append_operation("RX", list(layout.z_anc_uids))
                    c.append_operation("TICK")
                    z_started = True

                for col in colors:
                    append_cz_layer(lift_vertical_pairs_for_color(layout, col, include_x_cc=True))
                    c.append_operation("TICK")
            else:  # hor
                # --- horizontal sweep (Alg. 3, line 7) ---
                c.append_operation("H", list(layout.data_all_uids))
                c.append_operation("TICK")

                # X ancillas are always in the pipeline from the prelude.
                measure_reset_x_basis("X", key_fn=lambda u, r=x_round: x_key(u, r))
                x_round += 1

                # print(c)
                for col in colors:
                    append_cz_layer(lift_horizontal_pairs_for_color(layout, col))
                    c.append_operation("TICK")

    print(c)
    # --- Drain ---
    # Measure X to complete the last X round.
    measure_reset_x_basis("X", key_fn=lambda u, r=x_round: x_key(u, r))
    x_round += 1

    # Final Z-only vertical sweep.
    # If Z has already been introduced (n_cycles>=2), we must first read out the
    # "previous" Z round to keep exactly n_cycles Z measurements without a dummy at t=0.
    c.append_operation("H", list(layout.data_all_uids))
    c.append_operation("TICK")

    if z_started:
        # This readout corresponds to the most recent Z interaction layer before the final sweep.
        measure_reset_x_basis("Z", key_fn=lambda u, r=z_round: z_key(u, r))
        z_round += 1
    else:
        # n_cycles==1 case: Z ancillas were never introduced; introduce them now.
        c.append_operation("RX", list(layout.z_anc_uids))
        c.append_operation("TICK")
        z_started = True

    for col in colors:
        append_cz_layer(lift_vertical_pairs_for_color(layout, col, include_x_cc=False))
        c.append_operation("TICK")

    # Final Z measurement (after the last vertical interaction layer).
    measure_reset_x_basis("Z", key_fn=lambda u, r=z_round: z_key(u, r))
    z_round += 1

    if validate_keys:
        if x_round != n_cycles or z_round != n_cycles:
            raise AssertionError(f"Round count mismatch: expected {n_cycles=}, got {x_round=}, {z_round=}")

    print(f"tracker.recorded: {tracker.recorded}")

    if add_time_detectors and n_cycles >= 2:
        for u in layout.x_anc_uids:
            for r in range(n_cycles - 1):
                append_detector([x_key(u, r), x_key(u, r + 1)])
        for u in layout.z_anc_uids:
            for r in range(n_cycles - 1):
                append_detector([z_key(u, r), z_key(u, r + 1)])

    return c, tracker, layout

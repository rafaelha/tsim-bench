from __future__ import annotations

from typing import Callable

import numpy as np
import stim

from ..qec_toolkit.se._measurement_tracker import MeasurementTracker
from .pipelined_se import (
    XuHgpUidLayout,
    make_xu_hgp_uid_layout_from_H,
    xu_color_matchings_from_H,
)


def make_xu_hgp_product_coloration_se_circuit_uid(
    H: np.ndarray,
    *,
    n_rounds: int = 1,
    colors_h: list[dict[int, int]] | None = None,
    colors_v: list[dict[int, int]] | None = None,
    include_qubit_coords: bool = False,
    add_time_detectors: bool = True,
    validate_keys: bool = True,
) -> tuple[stim.Circuit, MeasurementTracker, XuHgpUidLayout]:
    """Algorithm 2 (Xu et al.): Product Coloration Circuit for HGP Syndrome Extraction.

    Measures X stabilizers and Z stabilizers in two separate phases:

      X phase:
        1) H on all data qubits
        2) prepare X ancillas in |+>
        3) sweep horizontal colors: CZ on X--VV pairs
        4) sweep vertical colors:   CZ on X--CC pairs
        5) H on all data qubits
        6) measure X ancillas in X basis

      Z phase:
        1) prepare Z ancillas in |+>
        2) sweep horizontal colors: CZ on Z--CC pairs
        3) sweep vertical colors:   CZ on Z--VV pairs
        4) measure Z ancillas in X basis

    Notes:
      - We do NOT explicitly model the movement (Algorithm 1); we assume the
        layout already places qubits on the LDPC grid and we just schedule CZ layers.
      - If you want separate edge-colorations for the horizontal/vertical Tanner graphs,
        pass colors_h / colors_v. Otherwise we reuse xu_color_matchings_from_H(H) for both.

    Args:
        H: classical check matrix of shape (nC, nV).
        n_rounds: repeat the whole Alg.2 X-phase then Z-phase this many times.
        colors_h: list of matchings for horizontal edges (C_h <-> V_h), each dict {b -> j}.
        colors_v: list of matchings for vertical edges (C_v <-> V_v), each dict {a -> i}.
        include_qubit_coords: emit QUBIT_COORDS.
        add_time_detectors: if n_rounds>=2, add DETECTOR between consecutive rounds for each ancilla uid.
        validate_keys: sanity-check that we recorded exactly n_rounds results per ancilla type.

    Returns:
        (stim circuit, tracker, layout)
    """
    if n_rounds < 1:
        raise ValueError(f"n_rounds must be >= 1, got {n_rounds}")

    layout = make_xu_hgp_uid_layout_from_H(H)
    if colors_h is None:
        colors_h = xu_color_matchings_from_H(H)
    if colors_v is None:
        colors_v = xu_color_matchings_from_H(H)

    c = stim.Circuit()
    tracker = MeasurementTracker()

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
        c.append_operation("CZ", flat)

    def measure_x_basis(uids: tuple[int, ...], *, key_fn: Callable[[int], object]) -> None:
        """Measure in X basis (MX) and record into tracker. Does NOT reset."""
        if not uids:
            return
        ulist = list(uids)
        c.append_operation("MX", ulist)
        for u in ulist:
            tracker.record_measurement(key_fn(u))
        c.append_operation("TICK")

    def append_detector(keys: list[object]) -> None:
        targets = tracker.current_measurement_record_targets_for(keys)
        if targets is None:
            raise ValueError(f"Cannot form detector due to obstacle in keys={keys!r}")
        c.append_operation("DETECTOR", targets)

    # --- Pair generators for Alg.2 (X-only or Z-only) ---

    def x_horizontal_pairs_for_color(color: dict[int, int]) -> list[tuple[int, int]]:
        # For each matched edge (b in C_h) <-> (j in V_h):
        #   for each i in V_v: X(i,b) -- VV(i,j)
        nV, nC = layout.nV, layout.nC
        pairs: list[tuple[int, int]] = []
        for b, j in color.items():
            for i in range(nV):
                x_uid = layout.uid(nC + i, nV + b)  # X(i,b)
                vv_uid = layout.uid(nC + i, j)  # VV(i,j)
                pairs.append((x_uid, vv_uid))
        return pairs

    def x_vertical_pairs_for_color(color: dict[int, int]) -> list[tuple[int, int]]:
        # For each matched edge (a in C_v) <-> (i in V_v):
        #   for each b in C_h: X(i,b) -- CC(a,b)
        nV, nC = layout.nV, layout.nC
        pairs: list[tuple[int, int]] = []
        for a, i in color.items():
            for b in range(nC):
                x_uid = layout.uid(nC + i, nV + b)  # X(i,b)
                cc_uid = layout.uid(a, nV + b)  # CC(a,b)
                pairs.append((x_uid, cc_uid))
        return pairs

    def z_horizontal_pairs_for_color(color: dict[int, int]) -> list[tuple[int, int]]:
        # For each matched edge (b in C_h) <-> (j in V_h):
        #   for each a in C_v: Z(a,j) -- CC(a,b)
        nV, nC = layout.nV, layout.nC
        pairs: list[tuple[int, int]] = []
        for b, j in color.items():
            for a in range(nC):
                z_uid = layout.uid(a, j)  # Z(a,j)
                cc_uid = layout.uid(a, nV + b)  # CC(a,b)
                pairs.append((z_uid, cc_uid))
        return pairs

    def z_vertical_pairs_for_color(color: dict[int, int]) -> list[tuple[int, int]]:
        # For each matched edge (a in C_v) <-> (i in V_v):
        #   for each j in V_h: Z(a,j) -- VV(i,j)
        nV, nC = layout.nV, layout.nC
        pairs: list[tuple[int, int]] = []
        for a, i in color.items():
            for j in range(nV):
                z_uid = layout.uid(a, j)  # Z(a,j)
                vv_uid = layout.uid(nC + i, j)  # VV(i,j)
                pairs.append((z_uid, vv_uid))
        return pairs

    # --- Main loop: repeat Alg.2 rounds ---
    x_round = 0
    z_round = 0

    for _ in range(n_rounds):
        # ---------------- X stabilizers ----------------
        # Step 1: H on all data
        c.append_operation("H", list(layout.data_all_uids))
        c.append_operation("TICK")

        # Step 2: prepare X ancillas in |+>
        c.append_operation("RX", list(layout.x_anc_uids))
        c.append_operation("TICK")

        # Steps 3-6: for direction in {horizontal, vertical}, for each color: CZ
        for col in colors_h:
            append_cz_layer(x_horizontal_pairs_for_color(col))
            c.append_operation("TICK")

        for col in colors_v:
            append_cz_layer(x_vertical_pairs_for_color(col))
            c.append_operation("TICK")

        # Step 7: H on all data (undo)
        c.append_operation("H", list(layout.data_all_uids))
        c.append_operation("TICK")

        # Step 8: measure X ancillas in X basis
        measure_x_basis(layout.x_anc_uids, key_fn=lambda u, r=x_round: x_key(u, r))
        x_round += 1

        # ---------------- Z stabilizers ----------------
        # Step 9: prepare Z ancillas in |+>
        c.append_operation("RX", list(layout.z_anc_uids))
        c.append_operation("TICK")

        # Steps 10-13: horizontal then vertical sweeps
        for col in colors_h:
            append_cz_layer(z_horizontal_pairs_for_color(col))
            c.append_operation("TICK")

        for col in colors_v:
            append_cz_layer(z_vertical_pairs_for_color(col))
            c.append_operation("TICK")

        # Step 14: measure Z ancillas in X basis
        measure_x_basis(layout.z_anc_uids, key_fn=lambda u, r=z_round: z_key(u, r))
        z_round += 1

    if validate_keys:
        if x_round != n_rounds or z_round != n_rounds:
            raise AssertionError(
                f"Round count mismatch: expected n_rounds={n_rounds}, got x_round={x_round}, z_round={z_round}"
            )

    if add_time_detectors and n_rounds >= 2:
        for u in layout.x_anc_uids:
            for r in range(n_rounds - 1):
                append_detector([x_key(u, r), x_key(u, r + 1)])
        for u in layout.z_anc_uids:
            for r in range(n_rounds - 1):
                append_detector([z_key(u, r), z_key(u, r + 1)])

    return c, tracker, layout

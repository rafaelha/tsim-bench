# pipelined_se_test.py
#
# Tests for Fig.5-faithful Xu-style HGP pipelined SE circuit construction.
#
# Assumptions:
#   - pipelined_se.py is in the SAME folder as this test file.
#   - pipelined_se.py defines:
#       * make_xu_hgp_pipelined_se_circuit_uid
#       * make_xu_hgp_uid_layout_from_H
#       * XuHgpUidLayout
#
# Run:
#   pytest -q pipelined_se_test.py
#
# Notes on the toy "d=3 surface code" example:
#   A standard small HGP toy is obtained from the length-3 repetition code:
#     H = [[1,1,0],
#          [0,1,1]]
#   This produces a small (nC=2, nV=3) instance that is enough to validate:
#     - Fig.5 quadrant membership
#     - n_cycles measurement keying via MeasurementTracker
#     - time-like detectors between consecutive rounds

from __future__ import annotations

import numpy as np
import stim

from .pipelined_se import (
    XuHgpUidLayout,
    make_xu_hgp_pipelined_se_circuit_uid,
    make_xu_hgp_uid_layout_from_H,
)


def H_rep3() -> np.ndarray:
    """Parity-check matrix for repetition code of length 3.

    checks: (b0 ⊕ b1)=0, (b1 ⊕ b2)=0
    shape: (nC=2, nV=3)
    """
    return np.array(
        [
            [1, 1, 0],
            [0, 1, 1],
        ],
        dtype=np.uint8,
    )


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


def count_targets(c: stim.Circuit, gate: str) -> int:
    """Count total number of targets over all instructions with name == gate."""
    total = 0
    for inst in c:
        if inst.name == gate:
            total += len(inst.targets_copy())
    return total


def collect_detectors(c: stim.Circuit) -> list[tuple[str, ...]]:
    """Collect DETECTOR targets as tuples of stringified stim targets (e.g., 'rec[-12]')."""
    out: list[tuple[str, ...]] = []
    for inst in c:
        if inst.name == "DETECTOR":
            out.append(tuple(str(t) for t in inst.targets_copy()))
    return out


def assert_no_mpp(c: stim.Circuit) -> None:
    for inst in c:
        assert inst.name != "MPP"


# ------------------------------------------------------------------------------
# Layout tests (Fig.5-faithful quadrant membership)
# ------------------------------------------------------------------------------


def test_fig5_quadrants_rep3_partition_the_entire_grid():
    H = H_rep3()
    layout = make_xu_hgp_uid_layout_from_H(H)
    print("layout:")
    visualize_layout(layout, show_uid=True)

    nC, nV = layout.nC, layout.nV
    assert (nC, nV) == (2, 3)

    # Expected block sizes:
    # VV: nV*nV, CC: nC*nC, Z: nC*nV, X: nV*nC
    assert len(layout.data_vv_uids) == nV * nV
    assert len(layout.data_cc_uids) == nC * nC
    assert len(layout.z_anc_uids) == nC * nV
    assert len(layout.x_anc_uids) == nV * nC

    # The 4 blocks cover the whole (nC+nV) x (nV+nC) grid.
    N = nC + nV
    assert layout.Nrow == N
    assert layout.Ncol == N

    all_uids = set(layout.data_vv_uids) | set(layout.data_cc_uids) | set(layout.z_anc_uids) | set(layout.x_anc_uids)
    assert len(all_uids) == N * N

    # Quadrant membership (row/col ranges) must match Fig.5:
    # rows: C_v = [0..nC-1], V_v = [nC..nC+nV-1]
    # cols: V_h = [0..nV-1], C_h = [nV..nV+nC-1]
    for u in layout.z_anc_uids:
        r, c = layout.uid_to_rc[u]
        assert 0 <= r < nC
        assert 0 <= c < nV

    for u in layout.data_cc_uids:
        r, c = layout.uid_to_rc[u]
        assert 0 <= r < nC
        assert nV <= c < nV + nC

    for u in layout.data_vv_uids:
        r, c = layout.uid_to_rc[u]
        assert nC <= r < nC + nV
        assert 0 <= c < nV

    for u in layout.x_anc_uids:
        r, c = layout.uid_to_rc[u]
        assert nC <= r < nC + nV
        assert nV <= c < nV + nC


# ------------------------------------------------------------------------------
# Circuit + tracker tests (n_cycles=2 and detectors)
# ------------------------------------------------------------------------------


def test_rep3_ncycles2_measurement_and_detector_counts():
    H = H_rep3()
    c, tracker, layout = make_xu_hgp_pipelined_se_circuit_uid(
        H,
        n_cycles=2,
        include_qubit_coords=False,
        add_time_detectors=True,
        validate_keys=True,
    )

    assert_no_mpp(c)

    # Total MX results must be:
    #   n_cycles * (|X anc| + |Z anc|)
    mx = count_targets(c, "MX")
    assert mx == 2 * (len(layout.x_anc_uids) + len(layout.z_anc_uids))

    # Tracker must have recorded exactly one key per MX result.
    assert tracker.next_measurement_index == mx
    assert len(tracker.recorded) == mx

    # Time-like detectors count:
    #   (n_cycles-1) * (|X anc| + |Z anc|)
    dets = collect_detectors(c)
    assert len(dets) == (2 - 1) * (len(layout.x_anc_uids) + len(layout.z_anc_uids))


def test_rep3_detector_targets_match_tracker_keys_exactly():
    H = H_rep3()
    c, tracker, layout = make_xu_hgp_pipelined_se_circuit_uid(
        H,
        n_cycles=2,
        include_qubit_coords=False,
        add_time_detectors=True,
        validate_keys=True,
    )

    # The constructor is expected to key measurements as:
    #   ("X", anc_uid, round) and ("Z", anc_uid, round)
    def x_key(u: int, r: int) -> tuple[str, int, int]:
        return ("X", u, r)

    def z_key(u: int, r: int) -> tuple[str, int, int]:
        return ("Z", u, r)

    expected: set[tuple[str, ...]] = set()

    # For n_cycles=2, each detector should be parity between rounds 0 and 1 for each ancilla.
    for u in layout.x_anc_uids:
        t = tracker.current_measurement_record_targets_for([x_key(u, 0), x_key(u, 1)])
        assert t is not None
        expected.add(tuple(str(x) for x in t))

    for u in layout.z_anc_uids:
        t = tracker.current_measurement_record_targets_for([z_key(u, 0), z_key(u, 1)])
        assert t is not None
        expected.add(tuple(str(x) for x in t))

    got = set(collect_detectors(c))
    assert got == expected


def test_rep3_ncycles1_has_no_time_detectors_and_correct_measurements():
    H = H_rep3()
    c, tracker, layout = make_xu_hgp_pipelined_se_circuit_uid(
        H,
        n_cycles=1,
        include_qubit_coords=False,
        add_time_detectors=True,  # should be ignored since n_cycles < 2
        validate_keys=True,
    )
    visualize_layout(layout, show_uid=True)

    assert_no_mpp(c)

    mx = count_targets(c, "MX")
    assert mx == (len(layout.x_anc_uids) + len(layout.z_anc_uids))
    assert tracker.next_measurement_index == mx
    assert len(collect_detectors(c)) == 0


def test_rep3_compiles_detector_sampler():
    H = H_rep3()
    c, _, layout = make_xu_hgp_pipelined_se_circuit_uid(
        H,
        n_cycles=2,
        include_qubit_coords=False,
        add_time_detectors=True,
        validate_keys=True,
    )
    visualize_layout(layout, show_uid=True)
    print("c:")
    print(c)

    # This catches many wiring mistakes by forcing stim to validate detector references.
    _ = c.compile_detector_sampler()

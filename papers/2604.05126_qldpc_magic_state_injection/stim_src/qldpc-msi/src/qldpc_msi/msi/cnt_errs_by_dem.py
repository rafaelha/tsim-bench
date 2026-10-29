"""Count error mechanisms by detector error model."""

import collections
from typing import FrozenSet, Iterable, Tuple

import stim

from ..utils import powerset


def count_1st_order_errs(
    circ: stim.Circuit, logical_obs_ids: list[int], verbose: bool = False
) -> dict[tuple[int, ...], tuple[int, float]]:
    """Count the number of 1st-order error mechanisms that can flip the logical operators without triggering specific detectors.

    Args:
        circ: The circuit to count the error mechanisms.
        logical_obs_ids: The ids of the logical observables.
        verbose: Whether to print the error locations.

    Returns:
        A dictionary mapping a subset of logical observable ids to the number of
        1-qubit error mechanisms that can flip the logical operators
        without triggering specific detectors.
        e.g. {(0,): (1, 0.001), (0, 1): (3, 0.003)} means:
        - 1 error mechanism can flip the logical operator L0 without triggering any detectors, with probability 0.001
        - 3 error mechanisms can flip the logical operators L0 and L1 without triggering any detectors, with probability 0.003
    """

    out: dict[tuple[int, ...], tuple[int, float]] = {}
    # TODO: use logical_obs_ids instead of range(len(logical_obs_ids))
    psets = powerset(range(len(logical_obs_ids)))
    for pset in psets:
        if len(pset) == 0:
            continue

        L_str = " ".join(f"L{lid}" for lid in pset)
        (d1_errs,) = circ.explain_detector_error_model_errors(
            dem_filter=stim.DetectorErrorModel(f"""error(1) {L_str}"""),
            reduce_to_one_representative_error=False,
        )
        err_locs = d1_errs.circuit_error_locations
        if len(err_locs) == 0:
            continue

        p_total = 0.0
        for err_loc in err_locs:
            assert len(err_loc.instruction_targets.args) == 1
            p = err_loc.instruction_targets.args[0]
            if err_loc.instruction_targets.gate == "DEPOLARIZE1":
                p_total += p / 3
            elif err_loc.instruction_targets.gate == "DEPOLARIZE2":
                p_total += p / 15
            elif err_loc.instruction_targets.gate == "X_ERROR":
                p_total += p
            elif err_loc.instruction_targets.gate == "Y_ERROR":
                p_total += p
            elif err_loc.instruction_targets.gate == "Z_ERROR":
                p_total += p
            else:
                raise ValueError(f"Unknown gate: {err_loc.instruction_targets.gate}")

        if verbose:
            for err_loc in err_locs:
                print(err_loc)

        out[pset] = (len(err_locs), p_total)
    return out


def dem_error_symptoms(inst: stim.DemInstruction) -> Tuple[int, FrozenSet[int]]:
    """Same helper as Gidney: returns (logical_mask, detector_set) with XOR semantics."""
    targets = inst.targets_copy()
    logical_mask = 0
    detectors = set()
    for t in targets:
        if t.is_relative_detector_id():
            if t.val in detectors:
                detectors.remove(t.val)
            else:
                detectors.add(t.val)
        elif t.is_logical_observable_id():
            logical_mask ^= 1 << t.val
    return logical_mask, frozenset(detectors)


def compute_union_proxy_discard_rates(
    circ: stim.Circuit,
    postsel_det_ids: Iterable[int],
    fixed_stab_det_ids: Iterable[int],
    verbose: bool = False,
) -> tuple[int, float, dict[int, float], float, float, float]:
    """
    First-order approximation:
        r_disc^UP ≈ 1 - \\prod_{DEM mechanisms that touch any postselected detector} (1 - p_e)

    Returns:
        (num_mechanisms, r_disc^UP, per_detector_p)

    Notes:
        - r_disc^UP is the event-level first-order discard estimated upper bound.
        - per_detector_p[d] = sum of p_e over mechanisms that flip detector d.
          (This is NOT a discard probability; it is a useful attribution diagnostic.)
    """
    P = set(postsel_det_ids)
    fixed_stab_det_ids = set(fixed_stab_det_ids)

    dem = circ.detector_error_model()
    num = 0
    product_of_1_minus_p = 1.0
    prod_of_fixed_stabs = 1.0
    prod_of_parity_checks = 1.0
    # acc_parity_conditioned_fixed = 1.0
    acc_detected_by_both = 1.0

    # Attribution: how much first-order weight hits each detector
    per_det = collections.defaultdict(float)

    for inst in dem.flattened():
        if inst.type != "error":
            continue
        assert isinstance(inst, stim.DemInstruction)

        p = inst.args_copy()[0]
        if p == 0:
            continue

        _logi, dets = dem_error_symptoms(inst)
        hit = dets.intersection(P)
        if not hit:
            continue

        # First-order: count the mechanism once if it can trigger discard.
        num += 1
        # sum_p += p
        product_of_1_minus_p = product_of_1_minus_p * (1 - p)

        # Attribution only (useful to see which detectors dominate).
        if hit.intersection(fixed_stab_det_ids):
            # will be postselected by fixed stab detectors
            prod_of_fixed_stabs = prod_of_fixed_stabs * (1 - p)
            if hit.difference(fixed_stab_det_ids):
                acc_detected_by_both = acc_detected_by_both * (1 - p)
        else:
            # will be postselected by round parity
            prod_of_parity_checks = prod_of_parity_checks * (1 - p)

        # for d in hit:
        #     per_det[d] += p

    r_disc_upper_bound = 1 - product_of_1_minus_p

    if verbose:
        top = sorted(per_det.items(), key=lambda kv: kv[1], reverse=True)[:10]
        print(f"[first_order_discard_from_dem] mechanisms counted: {num}")
        print(f"[first_order_discard_from_dem] r_disc^UP : {r_disc_upper_bound}")
        print("[first_order_discard_from_dem] top detectors by summed p:")
        # for d, v in top:
        #     print(f"  D{d}: {v}")

    return (
        num,
        r_disc_upper_bound,
        dict(per_det),
        prod_of_fixed_stabs,
        prod_of_parity_checks,
        acc_detected_by_both,
    )

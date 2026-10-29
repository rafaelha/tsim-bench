"""Count error mechanisms that can flip the logical operators without triggering specific detectors.
using the detector error model of stim.

This file is modified from https://github.com/Strilanc/hook-injection/blob/main/tools/compute_error_bound.py
"""

import collections
from typing import FrozenSet, Iterable, Tuple

import stim


def dem_error_symptoms(inst: stim.DemInstruction) -> Tuple[int, FrozenSet[int]]:
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


def bernoulli_add(p1: float, p2: float) -> float:
    return p1 * (1 - p2) + p2 * (1 - p1)


def approx_pair_probability(probabilities: Iterable[float]) -> float:
    probabilities = list(probabilities)
    n = len(probabilities)
    t = 0
    for i in range(n):
        for j in range(i + 1, n):
            t = bernoulli_add(t, probabilities[i] * probabilities[j])
    return t


def bernoulli_sum(probs: Iterable[float]) -> float:
    p = 0
    for p2 in probs:
        p = bernoulli_add(p, p2)
    return p


def calc_case(circuit: stim.Circuit):
    dem = circuit.detector_error_model()
    (d1_errs,) = circuit.explain_detector_error_model_errors(
        dem_filter=stim.DetectorErrorModel(
            """
        error(0.1) L0
    """
        )
    )
    num_d1 = len(d1_errs.circuit_error_locations)
    p_d1 = 0

    d2_groups = collections.defaultdict(lambda: collections.defaultdict(float))
    d2_dem_err_groups = collections.defaultdict(lambda: collections.defaultdict(stim.DetectorErrorModel))

    for inst in dem.flattened():
        if inst.type != "error":
            continue
        assert isinstance(
            inst, stim.DemInstruction
        ), f"inst must be a stim.DemInstruction after dem.flattened(), but got {type(inst)}"
        p = inst.args_copy()[0]
        logi, dets = dem_error_symptoms(inst)
        if len(dets) == 0 and logi != 0:
            # errors that can flip the logical operators without triggering specific detectors
            p_d1 = bernoulli_add(p_d1, p)
        else:
            d2_dem_err_groups[dets][logi].append(inst)
            d2_groups[dets][logi] = bernoulli_add(d2_groups[dets][logi], p)

    d2_dem_errs = stim.DetectorErrorModel()
    for d2_group in d2_dem_err_groups.values():
        if len(d2_group) > 1:
            for d2_dem in d2_group.values():
                d2_dem_errs += d2_dem
    d2_circuit_errs = circuit.explain_detector_error_model_errors(dem_filter=d2_dem_errs)
    num_d2 = sum(len(e.circuit_error_locations) for e in d2_circuit_errs)

    p_d2 = 0
    for d2_group in d2_groups.values():
        if len(d2_group) > 1:
            p_pair = approx_pair_probability(d2_group.values())
            p_d2 = bernoulli_add(p_pair, p_d2)

    return f"    {num_d1=}, {num_d2=}, e1={p_d1}, e2={p_d2}, e1+e2={bernoulli_add(p_d1, p_d2)}"

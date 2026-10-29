import math

import numpy as np
from numpy.typing import NDArray


def LER_postselect_all_obs_v2(
    det_samples: NDArray[np.bool_], obs_samples: NDArray[np.bool_], det_ids: list[int] | None = None
) -> tuple[float, float]:
    """
    Args:
        samples: bool array of shape (num_shots, num_detectors + num_observables),
                 with detector bits first, then observable bits.
        num_observables: number of observable columns at the end.

    Returns:
        ler_post_all_obs: LER after post-selection (nan if no shots survive).
        postselected_rate: fraction of shots that survived post-selection.
    """

    # Keep shots where all detectors are zero
    if det_ids is not None:
        det_samples = det_samples[:, det_ids]
    mask = np.all(det_samples == 0, axis=1)
    print(f"{mask.shape=}")
    postselected_obs = obs_samples[mask]
    print(f"{postselected_obs.shape=}")

    n_total = det_samples.shape[0]

    if postselected_obs.shape[0] > 0:  # denominator is not zero
        errors = np.any(postselected_obs == 1, axis=1)
        print(f"{errors.shape=}")
        ler_post_all_obs = errors.mean()
    else:
        ler_post_all_obs = np.nan

    postselected_rate = postselected_obs.shape[0] / n_total

    # number of discards due to post-selection
    return ler_post_all_obs, postselected_rate


def get_postsel_mask(num_dets: int, postsel_det_ids: list[int]):
    post_selection_mask = np.zeros(dtype=np.uint8, shape=math.ceil(num_dets / 8))
    for det_id in postsel_det_ids:
        post_selection_mask[det_id // 8] |= 1 << (det_id % 8)
    return post_selection_mask

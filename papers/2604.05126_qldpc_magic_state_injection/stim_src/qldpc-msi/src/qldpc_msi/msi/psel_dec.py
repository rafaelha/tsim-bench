import os

import sinter
from stimbposd import SinterDecoder_BPOSD

from .postsel import get_postsel_mask


def process_stats(collected_stats: list[sinter.TaskStats], n_inj_lids: int):
    ler_posts_per_obs = []
    ler_posts_all_obs = []
    postsel_rates = []
    ps = []
    errors = []
    discards = []
    shots = []
    for stat in sorted(collected_stats, key=lambda x: x.json_metadata["p"]):
        p = stat.json_metadata["p"]
        postsel_rate = 1 - stat.discards / stat.shots
        ler_post_all_obs = stat.errors / (stat.shots - stat.discards)
        ler_post_per_obs = ler_post_all_obs / n_inj_lids
        ler_posts_per_obs.append(ler_post_per_obs)
        ler_posts_all_obs.append(ler_post_all_obs)
        postsel_rates.append(postsel_rate)
        ps.append(p)
        errors.append(stat.errors)
        discards.append(stat.discards)
        shots.append(stat.shots)

    data = {
        "ler_posts_per_obs": ler_posts_per_obs,
        "ler_posts_all_obs": ler_posts_all_obs,
        "postsel_rates": postsel_rates,
        "ps": ps,
        "errors": errors,
        "discards": discards,
        "shots": shots,
    }
    return data


def _resolve_num_workers(num_workers: int | None) -> int:
    if num_workers is None:
        num_workers = os.cpu_count()
        assert num_workers is not None
    return num_workers


def _get_postsel_det_ids(*, n_psel_cycles: int, n_fixed_stabs: int, num_checks: int, num_detectors: int) -> list[int]:
    if n_psel_cycles == 1:
        return list(range(n_fixed_stabs))
    if n_psel_cycles == 2:
        return list(range(n_fixed_stabs + num_checks))
    if n_psel_cycles == -1:
        return list(range(num_detectors))
    raise ValueError(f"Invalid postsel_n_cycles: {n_psel_cycles}")


def _build_bposd_decoder() -> SinterDecoder_BPOSD:
    return SinterDecoder_BPOSD(
        max_bp_iters=1000,
        bp_method="ms",
        osd_order=10,
        osd_method="osd_cs",
        ms_scaling_factor=0,
    )


def _collect_with_bposd(
    tasks: list[sinter.Task],
    *,
    n_shots: int,
    num_workers: int,
    ana_corr_err: bool,
    verbose: bool,
) -> list[sinter.TaskStats]:
    decoder = _build_bposd_decoder()
    return sinter.collect(
        num_workers=num_workers,
        tasks=tasks,
        decoders=["bposd"],
        max_shots=n_shots,
        max_errors=None,
        custom_decoders={"bposd": decoder},
        count_observable_error_combos=ana_corr_err,
        print_progress=verbose,
    )


__all__ = ["process_stats", "get_postsel_mask"]

import sinter

from ..msi.generic_msi_circ_v2 import build_msi_circ_v3
from ..msi.init_cfgs import InitCfg
from ..msi.psel_dec import (
    _collect_with_bposd,
    _get_postsel_det_ids,
    _resolve_num_workers,
    get_postsel_mask,
)
from ..noise_spec import get_noise_model
from .code import BBCode
from .facade import build_se_circuit


def psel_and_dec(
    ps: list[float],
    code: BBCode,
    init_cfg: InitCfg,
    n_se_cycles: int,
    inj_method: str,
    n_psel_cycles: int,
    n_shots: int,
    noise_model_name: str,
    *,
    ana_corr_err: bool = False,
    num_workers: int | None = None,
    verbose: bool = True,
) -> list[sinter.TaskStats]:
    num_workers = _resolve_num_workers(num_workers)
    tasks = []
    for p in ps:
        noise_model = get_noise_model(noise_model_name, p)
        se_circ = build_se_circuit(code)
        ideal_circ = build_msi_circ_v3(code, se_circ, init_cfg, n_se_cycles)
        circ = noise_model.noisy_circuit_skipping_mpp_boundaries(ideal_circ)
        postsel_det_ids = _get_postsel_det_ids(
            n_psel_cycles=n_psel_cycles,
            n_fixed_stabs=len(init_cfg.fixed_stab_uids),
            num_checks=code.num_checks,
            num_detectors=circ.num_detectors,
        )
        postsel_mask = get_postsel_mask(circ.num_detectors, postsel_det_ids)
        tasks.append(
            sinter.Task(
                circuit=circ,
                json_metadata={
                    "code_id": code.identifier,
                    "p": p,
                    "inj_method": inj_method,
                    "noise_model": noise_model_name,
                    "n_psel_cycles": n_psel_cycles,
                    "n_se_cycles": n_se_cycles,
                    "ana_corr_err": ana_corr_err,
                },
                decoder="bposd",
                postselection_mask=postsel_mask,
            )
        )
    return _collect_with_bposd(
        tasks,
        n_shots=n_shots,
        num_workers=num_workers,
        ana_corr_err=ana_corr_err,
        verbose=verbose,
    )


__all__ = ["psel_and_dec"]

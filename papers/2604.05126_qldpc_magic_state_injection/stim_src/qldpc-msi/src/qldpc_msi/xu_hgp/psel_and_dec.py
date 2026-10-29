import sinter

from ..msi.init_cfgs import InitCfg
from ..msi.psel_dec import (
    _collect_with_bposd,
    _get_postsel_det_ids,
    _resolve_num_workers,
    get_postsel_mask,
)
from .code import XuHgpCode
from .facade import build_msi_circuit


def psel_and_dec(
    ps: list[float],
    code: XuHgpCode,
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
        error_params = {
            "p_i": p,
            "p_state_p": p,
            "p_m": p,
            "p_CX": p,
            "p_idling_gate": p,
        }
        circ = build_msi_circuit(code, init_cfg=init_cfg, n_cycles=n_se_cycles, error_params=error_params)
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

"""Stable public facade for BB-family workflows."""

import stim

from ..circuits.backends import BaseBackend
from ..circuits.moment_schedule import circuit_to_moments
from ..msi.generic_msi_circ_v2 import build_msi_circ_v3, build_msi_circ_v4
from ..msi.init_cfgs import InitCfg
from ..tour_bb.se import BBMemSimulator
from .code import BBCode
from .layout import get_cell_layout


def make_code(*, n: int) -> BBCode:
    """Construct a supported BB code instance."""
    return BBCode.from_n(n)


def build_se_circuit(
    code: BBCode,
    *,
    se_variant: str = "interleaved",
    dat_uid_to_reset_basis: dict[int, str] | None = None,
) -> list[stim.Circuit]:
    """Build a one-round BB syndrome-extraction schedule."""
    if se_variant == "interleaved":
        se_circ = stim.Circuit()
        sim = BBMemSimulator(code, 1, BaseBackend.from_noise_level(0))
        # sim.apply_all_checks(se_circ)
        sim.apply_all_checks_compactly(se_circ, dat_uid_to_reset_basis=dat_uid_to_reset_basis)
        se_moments = circuit_to_moments(se_circ)
        return se_moments
    raise ValueError(f"Unknown BB SE variant: {se_variant}")


def build_msi_circuit(
    code: BBCode,
    *,
    init_cfg: InitCfg,
    n_cycles: int,
    remove_dummy_cnots: bool = False,
    se_variant: str = "interleaved",
) -> stim.Circuit:
    """Build a BB MSI circuit via the stable family facade."""
    se_for_repeat = build_se_circuit(code, se_variant=se_variant)
    if remove_dummy_cnots:
        dat_uid_to_reset_basis = {uid: "Z" for uid in init_cfg.dat_uids_init_in_z}
        dat_uid_to_reset_basis.update({uid: "X" for uid in init_cfg.dat_uids_init_in_x})
        se_1st_cycle = build_se_circuit(
            code,
            se_variant=se_variant,
            dat_uid_to_reset_basis=dat_uid_to_reset_basis,
        )
        return build_msi_circ_v4(code, se_1st_cycle, se_for_repeat, init_cfg, n_cycles)
    else:
        return build_msi_circ_v3(code, se_for_repeat, init_cfg, n_cycles)


def get_layout(code: BBCode) -> dict[int, tuple[int, int]]:
    """Return coordinates for the standard BB layout."""
    return get_cell_layout(code)


__all__ = [
    "BBCode",
    "build_msi_circuit",
    "build_se_circuit",
    "get_layout",
    "make_code",
]

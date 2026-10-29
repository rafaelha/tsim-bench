"""Stable public facade for Xu-HGP-family workflows."""

import stim

from ..msi.generic_msi_circ_v2 import build_msi_circ_v2
from ..msi.init_cfgs import InitCfg
from .code import XuHgpCode
from .se_product_coloration import build_product_coloration_se_circ


def make_code(*, n: int) -> XuHgpCode:
    """Construct a supported Xu-HGP code instance."""
    return XuHgpCode(n)


def build_se_circuit(
    code: XuHgpCode,
    *,
    se_variant: str = "product_coloration",
    error_params: dict[str, float],
) -> stim.Circuit:
    """Build a one-round Xu-HGP syndrome-extraction circuit."""
    if se_variant == "product_coloration":
        return build_product_coloration_se_circ(code, error_params=error_params)
    raise ValueError(f"Unknown Xu-HGP SE variant: {se_variant}")


def build_msi_circuit(
    code: XuHgpCode,
    *,
    init_cfg: InitCfg,
    n_cycles: int,
    error_params: dict[str, float],
    se_variant: str = "product_coloration",
    uid_to_coord: dict[int, tuple[int, int]] | None = None,
) -> stim.Circuit:
    """Build a Xu-HGP MSI circuit via the stable family facade."""
    se_circ = build_se_circuit(code, se_variant=se_variant, error_params=error_params)
    return build_msi_circ_v2(code, se_circ, init_cfg, n_cycles, uid_to_coord)


__all__ = [
    "XuHgpCode",
    "build_msi_circuit",
    "build_se_circuit",
    "make_code",
]

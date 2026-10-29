"""Product-coloration SE helpers for Xu-HGP."""

from typing import Any

import numpy as np
import stim

from .CircuitScheduling import ColorationCircuit
from .code import XuHgpCode
from .generate_hgp_circuit import build_xu_hgp_one_se


def build_product_coloration_se_circ(
    code: XuHgpCode,
    *,
    error_params: dict[str, float],
    **_: Any,
) -> stim.Circuit:
    """Build one Xu-HGP product-coloration SE round."""
    hx = code.Hx
    hz = code.Hz
    data_indices = list(np.arange(0, np.shape(hx)[1]))
    n = len(data_indices)
    n_z_ancilla, n_x_ancilla = np.shape(hz)[0], np.shape(hx)[0]
    x_ancilla_indices = list(np.arange(n, n + n_x_ancilla))
    z_ancilla_indices = list(np.arange(n + n_x_ancilla, n + n_x_ancilla + n_z_ancilla))
    return build_xu_hgp_one_se(
        data_indices=data_indices,
        X_ancilla_indices=x_ancilla_indices,
        Z_ancilla_indices=z_ancilla_indices,
        scheduling_X=ColorationCircuit(hx),
        scheduling_Z=ColorationCircuit(hz),
        error_params=error_params,
    )

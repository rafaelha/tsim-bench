from pathlib import Path

import numpy as np
import stim
from numpy.typing import NDArray

from ..codes.base_code import CSSSpec
from ..qec_toolkit.logicals.reduce_wt_test import (
    build_hgp_css_checks,
    derive_css_logicals,
)


class XuHgpCode(CSSSpec):
    def __init__(self, n: int) -> None:
        current_dir = Path(__file__).parent
        if n == 225:
            self.classical_H = np.loadtxt(current_dir / "codes_lib" / "hgp_34_n225_d4_h.txt")
        else:
            raise ValueError(f"Unknown code: {n}")

        self._Hx, self._Hz = build_hgp_css_checks(self.classical_H)

    @property
    def Hx(self) -> NDArray[np.int_]:
        return self._Hx

    @property
    def Hz(self) -> NDArray[np.int_]:
        return self._Hz

    @property
    def all_dat_uids(self) -> list[int]:
        return list(self.get_circ_layout().col_id_to_dat_uid)

    @property
    def all_chk_uids(self) -> list[int]:
        return list(self.get_circ_layout().check_uids)

    def get_logical_ops_stim(self) -> tuple[list[stim.PauliString], list[stim.PauliString]]:
        lxs, lzs = derive_css_logicals(self._Hx, self._Hz)
        lxs_stim = []
        lzs_stim = []

        all_zeros = np.zeros(self.num_dat_qubits, dtype=np.bool_)
        for lx, lz in zip(lxs, lzs):
            lxs_stim.append(stim.PauliString.from_numpy(xs=np.array(lx, dtype=np.bool_), zs=all_zeros))
            lzs_stim.append(stim.PauliString.from_numpy(xs=all_zeros, zs=np.array(lz, dtype=np.bool_)))
        return lxs_stim, lzs_stim

    @property
    def identifier(self) -> str:
        return f"xu_hgp_n{self.num_dat_qubits}"


__all__ = ["XuHgpCode"]

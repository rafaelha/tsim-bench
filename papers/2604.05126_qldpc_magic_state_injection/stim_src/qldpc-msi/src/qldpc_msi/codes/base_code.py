from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import stim
from numpy.typing import NDArray

from .css_circ_layout import CSSCircLayout


class CSSSpec(ABC):
    """Intrinsic description of a CSS code, independent of circuit labeling."""

    @property
    @abstractmethod
    def Hx(self) -> NDArray[np.int_]:
        """Get the X-type parity check matrix."""
        raise NotImplementedError

    @property
    @abstractmethod
    def Hz(self) -> NDArray[np.int_]:
        """Get the Z-type parity check matrix."""
        raise NotImplementedError

    @property
    def num_dat_qubits(self) -> int:
        n = int(self.Hx.shape[1])
        if self.Hz.shape[1] != n:
            raise ValueError(
                f"Hx and Hz must have the same number of columns, got {self.Hx.shape[1]} and {self.Hz.shape[1]}"
            )
        return n

    @property
    def num_x_checks(self) -> int:
        return int(self.Hx.shape[0])

    @property
    def num_z_checks(self) -> int:
        return int(self.Hz.shape[0])

    @property
    def num_checks(self) -> int:
        return self.num_x_checks + self.num_z_checks

    @property
    def num_logicals(self) -> int:
        raise NotImplementedError

    def get_circ_layout(self) -> CSSCircLayout:
        """Return the canonical circuit layout for this CSS code."""
        return CSSCircLayout.canonical_for(self)

    @abstractmethod
    def get_logical_ops_stim(self) -> tuple[list[stim.PauliString], list[stim.PauliString]]:
        """Get the logical operators of the code."""
        raise NotImplementedError

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Get the unique identifier of the code."""
        raise NotImplementedError

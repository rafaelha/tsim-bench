import itertools

import numpy as np
import stim


class BaseBackend:
    def __init__(
        self,
        p1: float,
        p2: float,
        p_idle: float,
        p_init: float,
        p_meas: float,
    ):
        self.p1 = p1
        self.p2 = p2
        self.p_idle = p_idle
        self.p_init = p_init
        self.p_meas = p_meas

    def apply_depol1_err(self, c: stim.Circuit, uids: list[int]):
        if np.isclose(self.p1, 0):
            return
        c.append("DEPOLARIZE1", uids, self.p1)

    def apply_depol2_err(self, c: stim.Circuit, uid_pair: tuple[int, int] | list[tuple[int, int]]):
        """Apply two-qubit depolarizing error to the given qubits."""
        if np.isclose(self.p2, 0):
            return
        if isinstance(uid_pair, tuple):
            uid_pair = [uid_pair]
        c.append("DEPOLARIZE2", list(itertools.chain(*uid_pair)), self.p2)

    def apply_meas_err(self, c: stim.Circuit, uids: list[int], meas_base: str):
        if np.isclose(self.p_meas, 0):
            return
        assert meas_base in ["X", "Z"]
        error_gate = "Z" if meas_base == "X" else "X"
        c.append(f"{error_gate}_ERROR", uids, self.p_meas)

    def apply_idle_err(self, c: stim.Circuit, uids: list[int]):
        """Apply idle error to the given qubits."""
        if np.isclose(self.p_idle, 0):
            return
        c.append("DEPOLARIZE1", uids, self.p_idle)

    def apply_init_err(self, c: stim.Circuit, uids: list[int], init_basis: str):
        """Apply reset error to the given qubits."""
        if np.isclose(self.p_init, 0):
            return
        match init_basis:
            case "X":
                error_gate = "Z"
            case "Z":
                error_gate = "X"
            case "Y":
                # TODO: more general noise model
                error_gate = "X"
            case _:
                raise ValueError(f"Invalid init basis: {init_basis}")
        c.append(f"{error_gate}_ERROR", uids, self.p_init)

    def __repr__(self) -> str:
        return f"BaseBackend(p1={self.p1}, p2={self.p2}, p_idle={self.p_idle}, p_meas={self.p_meas})"

    @staticmethod
    def from_noise_level(noise_level: float, p2_over_p_meas: float = 1.0, p2_over_p_init: float = 1.0) -> "BaseBackend":
        return BaseBackend(
            p1=noise_level,
            p2=noise_level,
            p_init=noise_level / p2_over_p_init,
            p_idle=noise_level,
            p_meas=noise_level / p2_over_p_meas,
        )

    @staticmethod
    def li_noise_model(noise_level: float) -> "BaseBackend":
        return BaseBackend(
            p1=noise_level / 10,
            p2=noise_level,
            p_init=noise_level / 10,
            p_idle=noise_level / 10,
            p_meas=noise_level / 10,
        )

    def to_dict(self) -> dict:
        return {
            "p1": self.p1,
            "p2": self.p2,
            "p_idle": self.p_idle,
            "p_init": self.p_init,
            "p_meas": self.p_meas,
        }

from dataclasses import dataclass
from typing import Callable, Iterable

import stim

from qldpc_msi.msi.cnt_errs_by_dem import count_1st_order_errs
from qldpc_msi.utils import powerset

from .noise import NoiseModel, NoiseRule


@dataclass(frozen=True)
class LiMsiNoiseSpec:
    p_2q: float
    ratio_init_over_2q: float
    ratio_1q_over_2q: float
    ratio_meas_over_2q: float

    @property
    def p_1q(self) -> float:
        return self.p_2q * self.ratio_1q_over_2q

    @property
    def p_meas(self) -> float:
        return self.p_2q * self.ratio_meas_over_2q

    @property
    def p_init(self) -> float:
        return self.p_2q * self.ratio_init_over_2q

    def partial_model(self, family: str) -> NoiseModel:
        # Create a model where only one family is “active” at p_ref
        if family == "2Q":
            return self._to_model(0, self.p_2q, 0, 0)
        if family == "1Q":
            return self._to_model(self.p_1q, 0, 0, 0)
        if family == "INIT":
            return self._to_model(0, 0, self.p_init, 0)
        raise ValueError(f"Unknown family {family!r}")

    def analytical_1st_order_LER_breakdown(
        self,
        build_ideal: Callable[[], stim.Circuit],
        inj_lids: list[int],
        *,
        families: Iterable[str] = ("1Q", "2Q", "INIT"),
    ) -> dict[tuple[int, ...], dict[str, float]]:
        ideal = build_ideal()
        # print(f"{ideal=}")
        out: dict[tuple[int, ...], dict[str, float]] = {}
        p_ref = self.p_2q

        # Compute coefficients
        coeffs_by_family: dict[str, dict[tuple[int, ...], float]] = {}
        for fam in families:
            m = self.partial_model(fam)
            noisy = m.noisy_circuit_skipping_mpp_boundaries(ideal)
            first_order = count_1st_order_errs(noisy, inj_lids)
            coeffs_by_family[fam] = {J: (p_total / p_ref) for J, (_, p_total) in first_order.items()}

        # Assemble by J
        for J in powerset(range(len(inj_lids))):
            if not J:
                continue
            out[J] = {}
            for fam in families:
                out[J][f"c_{fam.lower()}"] = coeffs_by_family.get(fam, {}).get(J, 0.0)

        return out

    @staticmethod
    def li_msi_uniform(p: float) -> "LiMsiNoiseSpec":
        return LiMsiNoiseSpec(p, 1.0, 1.0, 1.0)

    @staticmethod
    def li_msi_twoq_dominant(p2: float, ratio_other_over_2q: float) -> "LiMsiNoiseSpec":
        return LiMsiNoiseSpec(p2, ratio_other_over_2q, ratio_other_over_2q, ratio_other_over_2q)

    def complete_model(self) -> "NoiseModel":
        return self._to_model(self.p_1q, self.p_2q, self.p_init, self.p_meas)

    def _to_model(self, p_1q: float, p_2q: float, p_init: float, p_meas: float) -> "NoiseModel":
        """Li MSI noise model. Reference: http://arxiv.org/abs/1410.7808."""
        return NoiseModel(
            idle_depolarization=p_1q,
            any_clifford_1q_rule=NoiseRule(after={"DEPOLARIZE1": p_1q}),
            any_clifford_2q_rule=NoiseRule(after={"DEPOLARIZE2": p_2q}),
            measure_rules={
                "X": NoiseRule(flip_result=p_meas),
                "Y": NoiseRule(flip_result=p_meas),
                "Z": NoiseRule(flip_result=p_meas),
            },
            gate_rules={
                "RX": NoiseRule(after={"Z_ERROR": p_init}),
                "RY": NoiseRule(after={"X_ERROR": p_init}),
                "R": NoiseRule(after={"X_ERROR": p_init}),
            },
        )


def get_noise_model(noise_model_name: str, p: float) -> NoiseModel:
    if noise_model_name == "li_uniform":
        return LiMsiNoiseSpec.li_msi_uniform(p).complete_model()
    elif noise_model_name == "li_twoq_dominant":
        return LiMsiNoiseSpec.li_msi_twoq_dominant(p, 0.1).complete_model()
    else:
        raise ValueError(f"Unknown noise model: {noise_model_name}")


def dummy_analytical_1st_order_LER_breakdown(
    build_noisy_circ: Callable[[dict[str, float]], stim.Circuit],
    p_ref: float,
    inj_lids: list[int],
    families: Iterable[str],
) -> dict[tuple[int, ...], dict[str, float]]:
    out: dict[tuple[int, ...], dict[str, float]] = {}

    coeffs_by_family: dict[str, dict[tuple[int, ...], float]] = {}

    ideal_params = {fam: 0.0 for fam in families}
    for fam in families:
        error_params = ideal_params.copy()
        error_params[fam] = p_ref
        noisy_circ = build_noisy_circ(error_params)
        first_order = count_1st_order_errs(noisy_circ, inj_lids)
        coeffs_by_family[fam] = {J: (p_total / p_ref) for J, (_, p_total) in first_order.items()}

    for J in powerset(range(len(inj_lids))):
        if not J:
            continue
        out[J] = {}
        for fam in families:
            out[J][f"c_{fam.lower()}"] = coeffs_by_family.get(fam, {}).get(J, 0.0)
    return out

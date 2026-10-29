import collections
import sys
from typing import AbstractSet, List

import stim
sys.path.append('./gidney_code/src')
from typing import AbstractSet, List
from hookinj.gen import NoiseModel, NoiseRule


class SparseIdlingNoiseModel(NoiseModel):
    @staticmethod
    def uniform_depolarizing(p: float) -> 'SparseIdlingNoiseModel':
        # Assuming all properties and methods required to create a proper instance are available
        return SparseIdlingNoiseModel(
            idle_depolarization=p/10,
            any_clifford_1q_rule=NoiseRule(after={'DEPOLARIZE1': p}),
            any_clifford_2q_rule=NoiseRule(after={'DEPOLARIZE2': p}),
            measure_rules={
                'X': NoiseRule(after={'DEPOLARIZE1': p}, flip_result=p),
                'Y': NoiseRule(after={'DEPOLARIZE1': p}, flip_result=p),
                'Z': NoiseRule(after={'DEPOLARIZE1': p}, flip_result=p),
                'XX': NoiseRule(after={'DEPOLARIZE2': p}, flip_result=p),
                'YY': NoiseRule(after={'DEPOLARIZE2': p}, flip_result=p),
                'ZZ': NoiseRule(after={'DEPOLARIZE2': p}, flip_result=p),
            },
            gate_rules={
                'RX': NoiseRule(after={'Z_ERROR': p}),
                'RY': NoiseRule(after={'X_ERROR': p}),
                'R': NoiseRule(after={'X_ERROR': p}),
            }
        )

    @staticmethod
    def sj_model(p: float) -> 'SparseIdlingNoiseModel':
        # Assuming all properties and methods required to create a proper instance are available
        return SparseIdlingNoiseModel(
            idle_depolarization=p/10,
            any_clifford_1q_rule=NoiseRule(after={'DEPOLARIZE1': p/10}),
            any_clifford_2q_rule=NoiseRule(after={'DEPOLARIZE2': p}),
            measure_rules={
                'X': NoiseRule(after={'DEPOLARIZE1': p}, flip_result=p),
                'Y': NoiseRule(after={'DEPOLARIZE1': p}, flip_result=p),
                'Z': NoiseRule(after={'DEPOLARIZE1': p}, flip_result=p),
                'XX': NoiseRule(after={'DEPOLARIZE2': p}, flip_result=p),
                'YY': NoiseRule(after={'DEPOLARIZE2': p}, flip_result=p),
                'ZZ': NoiseRule(after={'DEPOLARIZE2': p}, flip_result=p),
            },
            gate_rules={
                'RX': NoiseRule(after={'Z_ERROR': p}),
                'RY': NoiseRule(after={'X_ERROR': p}),
                'R': NoiseRule(after={'X_ERROR': p}),
            }
        )

    def _append_idle_error(self,
                           *,
                           moment_split_ops: List[stim.CircuitInstruction],
                           out: stim.Circuit,
                           system_qubits: AbstractSet[int],
                           immune_qubits: AbstractSet[int],
                           ) -> None:
        """
        Add idle errors only if there is a measurement in this moment.
        """
        measurements = sum([split_op.num_measurements for split_op in moment_split_ops])
        if measurements == 0:
            return
        return super()._append_idle_error(
            moment_split_ops=moment_split_ops,
            out=out,
            system_qubits=system_qubits,
            immune_qubits=immune_qubits
        )
import sinter
import matplotlib.pyplot as plt
import numpy as np
from erasure_simulator import *
import pandas as pd
import multiprocessing


import sys
sys.path.append('./gidney_code/src')
from hookinj._make_circuit import *

from datetime import date
from itertools import chain, product

import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('expand.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

import collections
from typing import AbstractSet, List
from hookinj.gen import NoiseModel, NoiseRule
import stim


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

def main():
    logger.info('Starting')
    logger.info(f'cores: {multiprocessing.cpu_count()}')
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_circuits", type=int, required=True)
    parser.add_argument("--shots_per_circuit", type=int, required=True)
    args = parser.parse_args()
    num_circuits = args.num_circuits
    shots_per_circuit = args.shots_per_circuit
    
    basis = 'hook_inject_Y'
    grown_distance = 15
    debug_out_dir = None
    postselected_rounds = 2
    memory_rounds = 15
    convert_to_cz = False
    batch_size = 500

    today_date = date.today()

    
    N = 10
    
    e_list = [0, 1e-3]  # [0, 1e-3]
    p_list = np.logspace(-4, -2, N)
    d_list = [3,5,7,9]  # [3, 5, 7, 9]
    r_list = [2]  # [2, 3]
    
    # Use zip to create pairs of (e, p)
    # ep_list = list(zip(np.zeros(N), p_list)) + list(zip(p_list, 0.1 * p_list))
    # ep_list = list(list(zip(10 * p_list, 0.1 * p_list)))
    
    # overhead = [1, 4, 10]
    overhead = [10]
    # p_values = [1e-3]
    p_values = np.logspace(-4,-3,10)
    
    ep_list = [(0, p) for p in p_values] + [(R*p, p/10) for p, R in product(p_values, overhead)]
    
    # Generate the product of d_list, r_list, and ep_list
    param_list = [(d, r, p, e) for d, r, (e, p) in product(d_list, r_list, ep_list)]
    
    circuits = [remove_errors_from_injection(
                    make_circuit(
                        basis=basis,
                        distance=grown_distance,
                        noise=SparseIdlingNoiseModel.sj_model(p),
                        debug_out_dir=debug_out_dir,
                        postselected_rounds=r,
                        postselected_diameter=d,
                        memory_rounds=memory_rounds,
                        convert_to_cz=convert_to_cz,
                    ) , injection_rounds=r, #noisy_rounds = 10
                ) for d, r, p, e in param_list
                ]
    
    df_total = pd.DataFrame()
    
    for i in range(0,-(-num_circuits//batch_size)):
        logger.info(f'round: {i=} out of {num_circuits//batch_size}')
        circuit_generator_list = [
            erasure_circuit_generator(
                circuit=circuit,
                e=1 - (1 - e)**0.5,  # convert to e_star
                e1=e/10,
                e_SPAM = e,
                r=r, 
                num_circuits=batch_size,  # if e > 0 else 1,
                runs_per_circuit=0,  # if e > 0 else 100_000, 
                json_metadata={
                    'd': d, 'e': e, 'p': p, 'r': r,
                },
                post_mask=sinter.post_selection_mask_from_4th_coord(circuit)
            ) 
            for circuit, (d, r, p ,e) in zip(circuits, param_list)]
        circuit_generator = chain(*circuit_generator_list)

        collected_surface_code_stats = []

        for generator in circuit_generator_list:
            collected_surface_code_stats += sinter.collect(
                num_workers=multiprocessing.cpu_count(),
                tasks=generator,
                decoders=['pymatching'],
                max_shots=shots_per_circuit,
                max_errors=5_000,
                print_progress=True,
            )

        
        # df = pd.DataFrame([vars(stat) | stat.json_metadata for stat in collected_surface_code_stats])
        # metadata = collected_surface_code_stats[0].json_metadata
        # # df.head()
        # df['json_metadata'] = df['json_metadata'].astype(str)
        # df_grouped = df.groupby('json_metadata').agg({'shots': 'sum', 'errors': 'sum', 'discards': 'sum', 'seconds': 'sum', 'decoder': 'first'} 
        #                                              | {key: 'first' for key in metadata.keys()})
        # df_grouped['error_rate'] = df_grouped['errors'] / (df_grouped['shots'] - df_grouped['discards'])
        df = pd.DataFrame([vars(stat) | stat.json_metadata for stat in collected_surface_code_stats])
        df.to_csv(f"out/collection/expand_raw,{i},{today_date},{batch_size=}.csv")
        metadata = collected_surface_code_stats[0].json_metadata
        df['json_metadata'].apply(lambda d: d.pop('id', None))  # Since dict is mutable, we can modify it in place
        df['json_metadata'] = df['json_metadata'].astype(str)
        df['error_rate_per_circuit'] = df['errors'] / (df['shots'] - df['discards'])
        df['var_per_circuit'] = df['error_rate_per_circuit'] * (1- df['error_rate_per_circuit']) / (df['shots'] - df['discards'])
    
        df_grouped = df.groupby('json_metadata').agg(
            {
                'shots': 'sum',
                'errors': 'sum',
                'discards': 'sum',
                'seconds': 'sum',
                'decoder': 'first',
                'var_per_circuit': 'mean', 
                'error_rate_per_circuit': 'var'
            } | {key: 'first' for key in metadata.keys()})
        df_grouped = df_grouped.rename(columns={'error_rate_per_circuit': 'Var(E(X|Y))', 'var_per_circuit': 'E(Var(Y|X))'})
        df_grouped['error_rate'] = df_grouped['errors'] / (df_grouped['shots'] - df_grouped['discards'])
        df_total = pd.concat([df_total, df_grouped])
    df_total.to_csv(f"out/collection/expand_simulation,{date.today()},{num_circuits=}.csv")

    logger.info('Finished')


if __name__ == '__main__':
    main()
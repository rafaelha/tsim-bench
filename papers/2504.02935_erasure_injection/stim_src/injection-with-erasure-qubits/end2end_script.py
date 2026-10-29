from erasure_simulator import *
import sinter
import stim
import argparse
import pandas as pd

import sys
sys.path.append('./gidney_code/src')
from hookinj.gen import NoiseModel
from hookinj._make_circuit import *

from itertools import chain, product
from multiprocessing import cpu_count
from datetime import date
from expand_script import SparseIdlingNoiseModel

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)



def get_qubit_number(d):
    return d**2 + (d-1)**2 + 2*(d-1)

def get_cost(d: int, r: int, success_rate: float) -> float:
    return get_qubit_number(d) * r / success_rate

def main():
    logger.info('Starting')
    logger.info(f'cores: {cpu_count()}')
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_circuits", type=int, required=True)
    parser.add_argument("--shots_per_circuit", type=int, required=True)
    args = parser.parse_args()
    num_circuits = args.num_circuits
    shots_per_circuit = args.shots_per_circuit

    basis = 'hook_inject_Y'
    grown_distance = 15
    # p = 0.001
    # noise_model_obj = NoiseModel.uniform_depolarizing(p)
    debug_out_dir = None
    # postselected_rounds = 2
    # postselected_diameter = 5
    memory_rounds = 15
    convert_to_cz = False
    batch_size = 500


    today_date = date.today()
    # e=0

    e_list = [0, 1e-3, 4e-3, 1e-2]  # [0, 1e-3]
    p_list = [1e-3, 1e-4, 1e-4, 1e-4] # [1e-3, 1e-4]
    d_list = [3,4,5,6,7]  # [3, 5, 7, 9]
    r_list = [2,3,4]  # [2, 3]

    # Use zip to create pairs of (e, p)
    ep_list = list(zip(e_list, p_list))

    # Generate the product of d_list, r_list, and ep_list
    param_list = [(d, r, p, e) for d, r, (e, p) in product(d_list, r_list, ep_list)]

    # param_list = list(product(d_list, r_list, p_list, e_list))

    circuits = [make_circuit(
                basis=basis,
                distance=grown_distance,
                noise=SparseIdlingNoiseModel.sj_model(p),
                debug_out_dir=debug_out_dir,
                postselected_rounds=r,
                postselected_diameter=d,
                memory_rounds=memory_rounds,
                convert_to_cz=convert_to_cz,
                ) for d, r, p, e in param_list]


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
                num_circuits=num_circuits,  # if e > 0 else 1,
                runs_per_circuit=0,  # if e > 0 else 100_000, 
                json_metadata={
                    'd': d, 'e': e, 'p': p, 'r': r, 'd2': grown_distance,
                    'erasure_post_rate': get_erasure_post_rate(
                        circuit, 
                        e=1 - (1 - e)**0.5,  # convert to e_star 
                        e1=e/10, 
                        e_SPAM = e, 
                        r=r, 
                        erasure_post_qubits = get_small_patch_qubits(circuit)
                    ) if e > 0 else 1
                },
                post_mask=sinter.post_selection_mask_from_4th_coord(circuit)
            ) 
            for circuit, (d, r, p ,e) in zip(circuits, param_list)]
        # circuit_generator = chain(*circuit_generator_list)
    
        collected_surface_code_stats = []

        for generator in circuit_generator_list:
            collected_surface_code_stats += sinter.collect(
                num_workers=cpu_count(),
                tasks=generator,
                decoders=['pymatching'],
                max_shots=shots_per_circuit,
                max_errors=5_000,
                print_progress=True,
            )

        df = pd.DataFrame([vars(stat) | stat.json_metadata for stat in collected_surface_code_stats])
        df.to_csv(f"out/collection/pareto_raw,{i},{today_date},{batch_size=}.csv")
    
    logger.info('Finished')


if __name__ == '__main__':
    main()

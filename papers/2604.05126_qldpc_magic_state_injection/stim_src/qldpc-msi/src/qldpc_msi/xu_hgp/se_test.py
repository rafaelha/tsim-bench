import numpy as np

from .code import XuHgpCode
from .generate_hgp_circuit import build_xu_hgp_complete_se, build_xu_hgp_one_se


def test_xu_hgp_memory_experiment():
    code = XuHgpCode(225)
    error_params = {"p_i": 1e-3, "p_state_p": 1e-3, "p_m": 1e-3, "p_CX": 1e-3, "p_idling_gate": 1e-3}
    num_cycles = 3
    circuit_type = "coloration"
    lxs_stim, lzs_stim = code.get_logical_ops_stim()
    lxs = np.array([lx.to_numpy()[0] for lx in lxs_stim])
    lzs = np.array([lz.to_numpy()[1] for lz in lzs_stim])
    circ = build_xu_hgp_complete_se(code.Hx, code.Hz, lxs, lzs, error_params, num_cycles, circuit_type)
    dem = circ.detector_error_model()

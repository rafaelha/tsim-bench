# Validating quantum computers using randomized model circuits

Cross, Bishop, Sheldon, Nation, Gambetta (2019), [arXiv:1811.12926](https://arxiv.org/abs/1811.12926).

Not a QEC circuit: a dense non-Clifford benchmark with no detectors, sampled with the measurement
sampler. Its active width equals the qubit count, so it stresses Tsim's state-vector kernels.

## Where the circuit is

`stim/qv_q10.stim` comes from Tsim's development benchmark registry (`dev/circuits/` of
[QuEraComputing/tsim#281](https://github.com/QuEraComputing/tsim/pull/281)): 10 qubits,
400 `U3` gates and 150 `CX` gates, a final `M` on every qubit and one observable. It is
a quantum-volume-style model circuit (random two-qubit layers decomposed into U3 and CX); the seed
and generator were not recorded.

## Active width k_max

See `k_max.json` (`tools/measure_k.py`).

# Tsim: Fast Universal Simulator for Quantum Error Correction

Rafael Haenel, Xiuzhe Luo, Chen Zhao (2026), [arXiv:2604.01059](https://arxiv.org/abs/2604.01059).

This folder also covers **Experimental Demonstration of Logical Magic State Distillation** (Rodriguez et al., QuEra/Harvard, 2024,
[arXiv:2412.15165](https://arxiv.org/abs/2412.15165)). That paper links no circuits or data. Its 5-to-1 logical distillation protocol is
reproduced in the Tsim paper ("d=3,5 distillation circuits from [sales2025experimental]") and in Tsim's distillation tutorial.

## Where the circuits are

[QuEraComputing/tsim](https://github.com/QuEraComputing/tsim), `docs/demos/magic_state_distillation.ipynb`, builds the circuits with Tsim's
`tsim.utils.encoder` (`SteaneEncoder` for d=3 and `ColorEncoder5` for d=5). The paper's other benchmarks (Gidney d=3 cultivation and
a d=7 surface code) are covered in [`../2409.17595_magic_state_cultivation`](../2409.17595_magic_state_cultivation) and
[`../2604.27058_clifft`](../2604.27058_clifft).

## What I did

- `tex/`: arXiv source of 2604.01059. I removed the figures.
- `stim_src/`: the tutorial notebook and `tsim/utils/encoder.py` from tsim main@4b951f3.
- `make_circuits.py` follows the tutorial and builds three versions: unencoded (5 qubits), the Steane code d=3 (35 qubits) and the colour
  code d=5 (85 qubits). Each version is written with an X, Y and Z readout basis for state tomography.
  - Inputs: five noisy magic states T_DAG·R_X(θ)|0⟩ with θ = −arccos(√(1/3))/π and DEPOLARIZE1(0.05).
  - Then the 5-to-1 distillation Clifford circuit, with p/5 = 0.01 gate noise, and readout.
  - These are native non-Clifford circuits, so no conversion is needed.
- The 85-qubit Z-basis circuit corresponds to the `distillation.stim` benchmark of Clifft and SymFT, which has the same k values. The two
  files are not byte-identical.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `distillation_color_d5_X.stim` | 5 R_X, 5 T_DAG | 4 | 4 | 5 |
| `distillation_color_d5_Y.stim` | 5 R_X, 5 T_DAG | 3 | 3 | 5 |
| `distillation_color_d5_Z.stim` | 5 R_X, 5 T_DAG | 3 | 3 | 5 |
| `distillation_steane_d3_X.stim` | 5 R_X, 5 T_DAG | 4 | 4 | 5 |
| `distillation_steane_d3_Y.stim` | 5 R_X, 5 T_DAG | 3 | 3 | 5 |
| `distillation_steane_d3_Z.stim` | 5 R_X, 5 T_DAG | 3 | 3 | 5 |
| `distillation_unencoded_X.stim` | 5 R_X, 5 T_DAG | 4 | 4 | 5 |
| `distillation_unencoded_Y.stim` | 5 R_X, 5 T_DAG | 3 | 3 | 5 |
| `distillation_unencoded_Z.stim` | 5 R_X, 5 T_DAG | 3 | 3 | 5 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

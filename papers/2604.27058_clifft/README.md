# Clifft: Fast Exact Simulation of Near-Clifford Quantum Circuits

Bradley A. Chase, Farrokh Labib (2026), [arXiv:2604.27058](https://arxiv.org/abs/2604.27058).

## Where the circuits are

The paper links to [unitaryfoundation/clifft-paper](https://github.com/unitaryfoundation/clifft-paper), which I used at commit `db7dc9f`.
- `qec_bench/circuits/` holds the eight circuits from the throughput table. They contain native non-Clifford gates (T/T_DAG, R_Z,
  R_X), and the table's playground deep links point at them.
- `magic_state_cultivation/` reproduces Gidney et al.'s cultivation with real T gates. Its S→T converter is used in
  [`../2409.17595_magic_state_cultivation`](../2409.17595_magic_state_cultivation), so those circuits are measured there.
- `qv_bench/` (random quantum-volume circuits, not QEC) is not included.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/`: `qec_bench/circuits/`, the generators (`run_all.py`, `save_table_circuits.py`), README and LICENSE (Apache-2.0).
- `stim/`: verbatim copies of the eight circuits. They already contain non-Clifford gates, so no conversion script is needed.
  `surface_d7_r7` is a Clifford control circuit.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `coherent_d3_r1.stim` | 65 R_Z | 0 | 0 | 4 |
| `coherent_d3_r3.stim` | 130 R_Z | 4 | 4 | 5 |
| `coherent_d5_r1.stim` | 209 R_Z | 0 | 0 | 12 |
| `coherent_d5_r5.stim` | 418 R_Z | 11 | 13 | 13 |
| `cultivation_d3.stim` | 15 T_DAG, 14 T | 4 | 4 | 4 |
| `cultivation_d5.stim` | 46 T_DAG, 45 T | 6 | 10 | 10 |
| `distillation.stim` | 5 R_X, 5 T_DAG | 3 | 3 | 5 |
| `surface_d7_r7.stim` | none | 0 | 0 | 0 |

Gate counts treat each `REPEAT` body once.
Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

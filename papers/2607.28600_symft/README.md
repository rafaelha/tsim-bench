# SymFT: Universal Fault-Tolerant Quantum Circuit Simulation via Symbolic Clifford–Pauli Frames and Stabilizer Coordinates

Wang Fang, Huazhe Lou, Riling Li (2026), [arXiv:2607.28600](https://arxiv.org/abs/2607.28600).

## Where the circuits are

The paper points to [haoliri0/SymFT_Test](https://github.com/haoliri0/SymFT_Test), which I used at commit `9ec5790`, and to
[haoliri0/SOFT](https://github.com/haoliri0/SOFT). Both repos hold the same `benchmark/circuit/` corpus: native non-Clifford circuits in the
Stim-like dialect shared by Tsim, Clifft and SymFT, with rotation angles in half-turns. `benchmark/README.md` documents where each
circuit comes from.

## What I did

- `tex/`: arXiv source.
- `stim_src/SymFT_Test_benchmark/`: the benchmark directory (circuits, `manifest.json` with SHA-256 hashes, harnesses), plus the repo
  README and LICENSE.
- `stim/`: verbatim copies of the circuits. No conversion is needed. Some files are byte-identical to circuits in other folders:
  - `msc_d3/d5_inject_cultivate` = Clifft's `cultivation_d3/d5` = `../2409.17595_magic_state_cultivation/stim/inject_cultivate_d3/d5_p0.001.stim`
  - `distillation`, `coherent_surface_d3_r1`, `coherent_surface_d5_r1` and `pure_surface_d7_r7` equal the corresponding Clifft-paper files
  - `coherent_surface_d3_r3` and `coherent_surface_d5_r5` are SymFT's own constructions: Stim `rotated_memory_z` with every DEPOLARIZE replaced by
    R_Z(0.02)
  - `msc_proxy_d7_unverified` is a d=7 performance proxy that the authors explicitly label unverified
  - `MSC_circuit_d7_p0.0005` is the exploratory d=7 MSC workload (paper Table: `k_max^S = 19`)
  - `pure_surface_*` are Clifford controls

The paper reports SymFT active widths `k_max^S` = 4 / 10 / 19 for MSC d=3/5/7. These match Clifft below.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `coherent_surface_d3_r1_p1e-3_rz0p02.stim` | 65 R_Z | 0 | 0 | 4 |
| `coherent_surface_d3_r3_p1e-3_rz0p02.stim` | 130 R_Z | 4 | 4 | 5 |
| `coherent_surface_d5_r1_p1e-3_rz0p02.stim` | 209 R_Z | 0 | 0 | 12 |
| `coherent_surface_d5_r5_p1e-3_rz0p02.stim` | 418 R_Z | 11 | 13 | 13 |
| `distillation.stim` | 5 R_X, 5 T_DAG | 3 | 3 | 5 |
| `MSC_circuit_d7_p0.0005.stim` | 64 T_DAG, 63 T | 8 | 19 | 19 |
| `msc_d3_inject_cultivate_p1e-3.stim` | 15 T_DAG, 14 T | 4 | 4 | 4 |
| `msc_d5_inject_cultivate_p1e-3.stim` | 46 T_DAG, 45 T | 6 | 10 | 10 |
| `msc_proxy_d7_unverified_p1e-3.stim` | 34 T_DAG, 33 T | 6 | 10 | 10 |
| `pure_surface_d7_r7_p1e-3.stim` | none | 0 | 0 | 0 |
| `pure_surface_d9_r9_p1e-3.stim` | none | 0 | 0 | 0 |

Gate counts treat each `REPEAT` body once.
Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

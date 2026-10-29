# SOFT: a high-performance simulator for universal fault-tolerant quantum circuits

Riling Li, Keli Zheng, Yiming Zhang, Huazhe Lou, Shenggang Ying, Ke Liu, Xiaoming Sun (2025),
[arXiv:2512.23037](https://arxiv.org/abs/2512.23037).

## Where the circuits are

The paper points to [haoliri0/SOFT](https://github.com/haoliri0/SOFT), which I used at commit `81d2849`. The circuits behind the paper's
d=3 and d=5 MSC simulations (inject + cultivate, 22 and 72 T/T† gates, no escape stage) are in `legacy/softv1/magic_state_cultivation/circuits/`
as `circuit_d{3,5}_p*.stim`. They contain native T/T_DAG and are an independent T-gate conversion of Gidney et al.'s circuits: they differ from
Clifft's `cultivation_d5` (75 vs 83 CX instructions). The repo's newer `benchmark/circuit/` corpus is identical to SymFT's and is covered in
[`../2607.28600_symft`](../2607.28600_symft).

## What I did

- `tex/`: arXiv source.
- `stim_src/softv1_magic_state_cultivation/`: the legacy circuits for d=3 at p=0.001 and d=5 at p=0.0005–0.005, plus their README. I left
  out the `.compiled` files and the `erroneous/` shot records. The repo README and LICENSE are in `stim_src/`.
- `stim/`: verbatim copies of `circuit_d3_p0.001.stim` and `circuit_d5_p0.001.stim`. They already contain non-Clifford gates, so no
  conversion is needed.
- Check: each circuit is sampled noiselessly in Tsim (4096 shots). All detectors are deterministic, and the observable is always 0.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `circuit_d3_p0.001.stim` | 15 T_DAG, 14 T | 4 | 4 | 4 |
| `circuit_d5_p0.001.stim` | 33 T_DAG, 39 T | 6 | 10 | 10 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

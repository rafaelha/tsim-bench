# Diagnosing and Restoring the Degraded Fault Distance of Magic State Cultivation

Tim Chan, Armands Strikis, Zhu Sun, Zhenyu Cai (2026), [arXiv:2609.17706](https://arxiv.org/abs/2609.17706).

The literature scouts did not find this paper. I found it through the exact-LER repo of
[`../2609.18922_exact_ler_cultivation`](../2609.18922_exact_ler_cultivation), which analyses its circuits.

## Where the circuits are

The paper's code is on GitHub at [timchan0/cliffordea](https://github.com/timchan0/cliffordea); I used commit `27385c6`.
`cliffordea/sim/stim_files/` bundles inject+cultivate references with no escape stage:
- d=3: unflagged and Z-flagged.
- d=5: three- and four-round schedules, each unflagged and Z-flagged.
- `_uncorrected` d=5 sources: the raw inputs before correction.

All are S-state proxies. The package builds the T circuit in memory by swapping S/S_DAG for T/T_DAG
(`circuit_text.swap_t_and_s_gates`). The corrected d=5 references already include the Bell-growth feedforward and detector healing that make
the swap valid (`sim/d5-correction.md`, based on Clifft's `convert_s_to_t.py`).

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/cliffordea/`: README, LICENSE, `sim/` (circuits, conversion and correction code, docs) and the enumeration circuits
  (`enum_circuits/`).
- `make_circuits.py` applies the package's S→T swap to every corrected `_p1e-3` reference and skips the `_uncorrected` ones.
- Check: each T circuit is sampled noiselessly in Tsim (2048 shots). No detector is random, every detector value equals the S-proxy
  value, and the observable is always 0.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `d3a6f2_inject_cultivate_T_p0.001.stim` | 15 T_DAG, 14 T | 4 | 4 | 4 |
| `d3a6_inject_cultivate_T_p0.001.stim` | 15 T_DAG, 14 T | 4 | 4 | 4 |
| `d5a19f13_inject_cultivate_T_p0.001.stim` | 46 T, 45 T_DAG | 6 | 10 | 10 |
| `d5a19_inject_cultivate_T_p0.001.stim` | 46 T, 45 T_DAG | 6 | 10 | 10 |
| `d5a19r4f13_inject_cultivate_T_p0.001.stim` | 46 T, 45 T_DAG | 6 | 10 | 10 |
| `d5a19r4_inject_cultivate_T_p0.001.stim` | 46 T, 45 T_DAG | 6 | 10 | 10 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

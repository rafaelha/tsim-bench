# Fast correlated decoding of transversal logical algorithms

Madelyn Cain, Dolev Bluvstein, Chen Zhao, Shouzhen Gu, Nishad Maskara, Marcin Kalinowski, Alexandra A. Geim, Aleksander Kubica,
Mikhail D. Lukin, Hengyun Zhou (2025), [arXiv:2505.13587](https://arxiv.org/abs/2505.13587).

## Where the circuits are

Zenodo record [15702016](https://doi.org/10.5281/zenodo.15702016) ("Data for Fast correlated decoding…") has `memory.zip`,
`random_clifford_depth_14.zip`, `random_clifford_depth_18.zip` and `distillation.zip`. The last holds the circuits of the paper's magic
state distillation benchmark:
- 15-to-1 distillation with transversal CNOTs between 16 rotated surface-code patches;
- distance d = 5, 9, 13, 17, 21, 25 (1,568 to 39,968 qubits), with SD6 noise at p = 0.001.

The paper assumes "reliable" |T⟩ inputs, for example from cultivation. Stim cannot hold |T⟩, so in the circuits:
- each of the 15 input states is prepared by `RX` on its patch's qubits and `S` on one qubit (a |Y⟩ = S|+⟩ proxy);
- one more patch is prepared the same way as the reference for the output check;
- the logical readouts (`MPP`) enter `DETECTOR`s, and there is no `OBSERVABLE_INCLUDE`.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/distillation_5.stim`: the d = 5 circuit as released. `make_circuits.py` downloads the full `distillation.zip` (8.8 MB) into
  `stim_src/_download/`, which is not tracked.
- `make_circuits.py`:
  - **Conversion:** both `S` lines (the 15 inputs and the output reference) become `T`.
  - **Check (d = 5 and 9):** sampled noiselessly in Tsim (256 shots). Every detector that is deterministic in the S proxy stays
    deterministic with the same value. The random detectors are exactly the proxy's 32 logical readouts.
  - The larger circuits use the same construction and are not sampled.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) |
|---|---|---|---|
| `distillation_15to1_T_d13_p0.001.stim` | 16 T | 4 | 4 |
| `distillation_15to1_T_d17_p0.001.stim` | 16 T | 4‡ | timeout |
| `distillation_15to1_T_d21_p0.001.stim` | 16 T | 4‡ | timeout |
| `distillation_15to1_T_d25_p0.001.stim` | 16 T | 4‡ | timeout |
| `distillation_15to1_T_d5_p0.001.stim` | 16 T | 4 | 4 |
| `distillation_15to1_T_d9_p0.001.stim` | 16 T | 4 | 4 |

Tsim 1.0.0, default `active_statevector` strategy, largest statevector component width. Clifft 0.13.0: default HIR passes +
`ActiveWidthSchedulePass()` (default settings), `peak_active_width`. Compile only, from `results/benchmark.json`
(`tools/benchmark.py`). Each simulator ran in its own process, capped at 40 GB of memory and 30 min.

‡ Tsim [PR #270](https://github.com/QuEraComputing/tsim/pull/270) (`96b86e8b`). Tsim 1.0.0 runs out of memory compiling d = 17–25:
`transform_error_basis` builds a dense vertices × error-bits matrix (121 GiB at d = 25). With the PR's sparse error basis, all three
compile at k = 4 in 1.8 / 2.7 / 4.5 GB (56 / 120 / 231 s). Clifft's compile still exceeds 30 min.

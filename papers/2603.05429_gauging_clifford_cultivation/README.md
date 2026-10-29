# Constant-depth magic state cultivation with Clifford measurements by gauging

Bence Hetényi, Benjamin J. Brown, Dominic J. Williamson (2026), [arXiv:2603.05429](https://arxiv.org/abs/2603.05429).

## Where the circuits are

The paper links to [IBM/gauging_clifford_measurement](https://github.com/IBM/gauging_clifford_measurement), which I used at commit `ce90c09`.
- **The paper's protocol:** `color_code.py` (`get_stim_circ_w_growing`) generates its circuits as |+i⟩ (Y-basis) proxies.
- **Noise:** added with `utils.add_noise`.
- **T-state version:** the authors' Qiskit statevector check builds it by replacing S/S_DAG with T/T_DAG (`qiskit_utils.stim_to_qiskit(...,
  replace_S_with_T=True)`).
- **`cultivation_stim_circuits/`:** noiseless Gidney-style cultivation circuits for d=3–11, used only for the comparison with cultivation.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/gauging_clifford_measurement/`: the generator modules, `cultivation_stim_circuits/`, README, LICENSE and requirements.
- `make_circuits.py` does three things for each distance:
  - Builds the pipelined Y-proxy for d=3, 5, 7 with uniform p=0.001 noise, the same settings as the notebook.
  - Drops target-less gate and noise lines. The generator emits lines such as `R` and `DEPOLARIZE1(p)` with no targets; Stim treats them as
    no-ops, but Clifft's parser rejects them.
  - Replaces S/S_DAG with T/T_DAG.
- Checks: each circuit is sampled noiselessly in Tsim (2048 shots). No detector is random, and every detector value equals the proxy's. The
  final logical-Y observable reads 1 with probability 0.147 / 0.139 / 0.856 at d=3/5/7, i.e. ⟨Y_L⟩ = ±1/√2 as expected for a T state.
- Not included: blanket S→T does **not** work for the bundled `cultivation_stim_circuits`. After the swap, 1/3/11 detectors at d=3/5/7 become
  random, so those circuits would need Gidney-style corrections (see `../2409.17595_magic_state_cultivation`).

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `gauging_cultivation_d3_T_p0.001.stim` | 15 T_DAG, 14 T | 4 | 4 | 4 |
| `gauging_cultivation_d5_T_p0.001.stim` | 65 T_DAG, 64 T | 6 | 10 | 10 |
| `gauging_cultivation_d7_T_p0.001.stim` | 175 T_DAG, 174 T | 8 | 19 | 19 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

# In-Situ Simultaneous Magic State Injection on Arbitrary CSS qLDPC Codes

Kun Liu, Shifan Xu, Tomas Jochym-O'Connor, Zhiyang He, Shraddha Singh, Yongshan Ding (2026),
[arXiv:2604.05126](https://arxiv.org/abs/2604.05126).

## Where the circuits are

The paper links to [kunliu7/qldpc-msi](https://github.com/kunliu7/qldpc-msi), which I used at commit `09b005e`. The repository has no LICENSE file.
- **Circuit construction:** the package's `build_msi_circ_v3`, with the paper's noise models from `noise_spec.get_noise_model`. The optimized
  injection configurations are pickled in `data/init_cfgs_v2/`; `prj_msi/20sim/inject_y_v2.py` runs the paper's simulations.
- **Injected state:** logical |Y⟩ (`RY` on the injection qubits). The scheme injects any +1 eigenstate of cos θ X + sin θ Y. |Y⟩ is θ = π/2
  and the T state is θ = π/4 (Sec. II).

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/qldpc-msi/`: README, pyproject, `src/`, `data/` (the init configs) and `prj_msi/`.
- `stim_src/y_circuits/`: the Y-injection circuits written by `make_circuits.py generate`, noiseless and at p=0.001. This step runs in a
  separate environment with the authors' package installed (`pip install -e stim_src/qldpc-msi`).
  - Code and configs: the [[144,12,12]] bivariate bicycle code with the paper's six best init configs (ids 369, 422, 342, 491, 328, 88),
    which inject 1 to 6 logical qubits.
  - Settings: li_uniform noise, max_supp_protection, 3 syndrome-extraction cycles, as in `inject_y_v2.py`.
- `make_circuits.py convert` replaces each `RY` injection reset with `RX` followed by `T` (T|+⟩ is the (X+Y)/√2 eigenstate). It also drops
  an empty `RX` line that Clifft rejects.
- Check: each circuit is sampled noiselessly in Tsim (512 shots). No detector is random, every detector value equals the Y proxy's, and every
  injected logical's Y readout gives P(1) ≈ 0.146 or 0.854, as expected for a logical T state.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `bb144_cfg328_inj5_T_p0.001.stim` | 5 T | 1 | 1 | 5 |
| `bb144_cfg342_inj3_T_p0.001.stim` | 3 T | 1 | 1 | 3 |
| `bb144_cfg369_inj1_T_p0.001.stim` | 1 T | 1 | 1 | 1 |
| `bb144_cfg422_inj2_T_p0.001.stim` | 2 T | 1 | 1 | 2 |
| `bb144_cfg491_inj4_T_p0.001.stim` | 4 T | 1 | 1 | 4 |
| `bb144_cfg88_inj6_T_p0.001.stim` | 6 T | 1 | 1 | 6 |

Each logical is injected by one physical T. Clifft without `ActiveWidthSchedulePass` holds all of them at once (k = number of injected
logicals); with the scheduler it holds one, like Tsim.
Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

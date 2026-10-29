# Efficient Magic State Cultivation on the Surface Code

Vaknin, Jacoby, Grimsmo, Retzker (2025), [arXiv:2502.01743](https://arxiv.org/abs/2502.01743).

## Where the circuits are

The paper links to [tomirendo/surface-code-magic-state-cultivation](https://github.com/tomirendo/surface-code-magic-state-cultivation),
which I used at commit `ec28f6b`. The circuits released in that repo (`2025/HCultivationSurfaceCode/circuits/`) are Clifford proxies: each
non-Clifford gate is replaced by noise or by a CZ/CX phase-kickback stand-in. The generator can also emit the real circuit through
`Circuit.to_stim_circuit(apply_non_cliffords=True)`. For the authors' state-vector simulator, that output encodes each non-Clifford
gate as an otherwise unused Stim gate (`convertion_dict` in `StateVecSimulator/latte/vec_sim.py`, e.g. `XCX` = CH and
`SQRT_X_DAG` = CCZ).

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/repo_ec28f6b/`: the generator code (`simulation.py`, `_noise.py`, `generate_circuits.py`, `vec_sim.py`) and the repo
  `requirements.txt`.
- `stim_src/released_circuits_p0.001/`: the released Clifford-proxy circuits at p=0.001, uniform noise, kept for reference.
- `stim_src/placeholder_circuits/`: the circuits the authors' generator writes with `apply_non_cliffords=True` and uniform depolarizing
  p=0.001. These are the same protocols `generate_circuits.py` builds: unrotated H-type and H_XY-type cultivation, rotated H_XY
  (T-type) cultivation, and cultivation followed by expansion to a d2=11 surface code. All use d1=3.
- `make_circuits.py generate` produces these placeholder circuits. It must run in the authors' environment (qutip, pennylane).
  `make_circuits.py convert` then replaces the placeholders with T/T_DAG/CCZ/CCX decompositions from `../../tools/gates.py`
  (checked against the unitaries) and writes `stim/`. Each converted circuit is also sampled noiselessly in Tsim (256 shots): no
  detector fires.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `expanded-rotated-init-x-injection-double-HXY_d1=3_d2=11_p=0.001.stim` | 21 T, 20 T_DAG, 8 CCZ | 8 | 10 | 14 |
| `expanded-rotated-injection-double-ghz-HXY_d1=3_d2=11_p=0.001.stim` | 21 T_DAG, 20 T, 8 CCZ | 8 | 10 | 14 |
| `expanded-rotated-injection-syndrome-double-ghz-HXY_d1=3_d2=11_p=0.001.stim` | 21 T_DAG, 20 T, 8 CCZ | 8 | 10 | 14 |
| `expanded-unrotated_H_injection-ghz_d1=3_d2=11_p=0.001.stim` | 27 T, 26 T_DAG, 8 CCX | 9 | 15 | 18 |
| `expanded-unrotated_H_injection-syndrome-ghz_d1=3_d2=11_p=0.001.stim` | 27 T, 26 T_DAG, 8 CCX | 9 | 15 | 18 |
| `rotated-init-x-injection-double-HXY_d1=3_p=0.001.stim` | 21 T, 20 T_DAG, 8 CCZ | 8 | 10 | 14 |
| `rotated-init-x-injection-syndrome-double-ghz-HXY_d1=3_p=0.001.stim` | 21 T, 20 T_DAG, 8 CCZ | 8 | 10 | 14 |
| `rotated-injection-double-ghz-HXY_d1=3_p=0.001.stim` | 21 T_DAG, 20 T, 8 CCZ | 8 | 10 | 14 |
| `rotated-injection-ghz-HXY_d1=3_p=0.001.stim` | 21 T_DAG, 20 T, 8 CCZ | 6 | 8 | 9 |
| `rotated-injection-syndrome-double-ghz-HXY_d1=3_p=0.001.stim` | 21 T_DAG, 20 T, 8 CCZ | 8 | 10 | 14 |
| `unrotated_H_injection-ghz_d1=3_p=0.001.stim` | 27 T, 26 T_DAG, 8 CCX | 9 | 15 | 18 |
| `unrotated_H_injection-syndrome-ghz_d1=3_p=0.001.stim` | 27 T, 26 T_DAG, 8 CCX | 9 | 15 | 18 |
| `unrotated_HXY_injection-ghz_d1=3_p=0.001.stim` | 21 T_DAG, 20 T, 8 CCZ | 7 | 10 | 14 |
| `unrotated_HXY_injection-syndrome-ghz_d1=3_p=0.001.stim` | 21 T_DAG, 20 T, 8 CCZ | 7 | 10 | 14 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

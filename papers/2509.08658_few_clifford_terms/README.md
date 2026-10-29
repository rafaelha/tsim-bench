# Simulating magic state cultivation with few Clifford terms

Kwok Ho Wan, Zhenghao Zhong, Ainhoa Zapirain (2025), [arXiv:2509.08658](https://arxiv.org/abs/2509.08658).

## Where the circuits are

The paper's companion code is [kh428/accel-cutting-magic-state](https://github.com/kh428/accel-cutting-magic-state), which I used at
commit `b6f67cd`. It is an accelerated sampling pipeline built on `bloqade-tsim`. The native-T d=3 cultivation circuit is defined as text in
`d_3_circuit_definitions.py` and assembled in `run.py`. The paper's d=5 analysis uses Gidney et al.'s d=5 circuit (see
[`../2409.17595_magic_state_cultivation`](../2409.17595_magic_state_cultivation)).

## What I did

- `tex/`: arXiv source. I removed the figures but kept the TikZ sources.
- `stim_src/accel-cutting-magic-state/`: `d_3_circuit_definitions.py`, `run.py` and the vendored `gen/` noise model, plus README, LICENSE and
  requirements.
- `make_circuits.py` assembles the circuit exactly as `run.py` does:
  - The injection plus double check gets uniform depolarizing noise at p=0.001. To apply it, the script maps T→S, runs the authors'
    `gen.NoiseModel`, and maps S→T back.
  - The noiseless T-projection readout is appended.
  - The result is checked noiselessly in Tsim (4096 shots): every detector is deterministic and the observable is always 0.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `d3_cultivation_T_p0.001.stim` | 8 T_DAG, 8 T | 4 | 4 | 4 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

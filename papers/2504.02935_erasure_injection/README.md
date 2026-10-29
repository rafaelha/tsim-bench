# Magic State Injection with Erasure Qubits

Shoham Jacoby, Yotam Vaknin, Alex Retzker, Arne L. Grimsmo (2025), [arXiv:2504.02935](https://arxiv.org/abs/2504.02935).

## Where the circuits are

The code is on GitHub at [shohamjac/injection-with-erasure-qubits](https://github.com/shohamjac/injection-with-erasure-qubits), which I used at
commit `407a678`. The data is on Zenodo [10.5281/zenodo.15874462](https://zenodo.org/records/15874462), a 248 MB archive of sampled
statistics.

`circuits/` holds the two base circuits, both injecting |S⟩ = S|+⟩ as the paper states:
- `QEC_hook_d=3.stim`: d1=3 hook injection;
- Gidney et al.'s d=3 inject+cultivate proxy.

Two further protocols are not shipped as files:
- Surface-code hook-injection circuits come from Gidney's hook-injection generator (`step0_clone_Gidney_repo`; see
  [`../2302.12292_hook_injection`](../2302.12292_hook_injection)).
- I found no generator or file for the Lao–Criger injection circuits.

Erasures are simulated by sampling herald patterns and inserting depolarizing noise into these circuits
(`erasure_simulator.get_erased_circuit`). This does not change the circuit structure.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/injection-with-erasure-qubits/`: README, requirements, `circuits/`, the erasure simulator, noise models and sampling scripts. I did not
  copy the 970 MB `out/` folder.
- `make_circuits.py` makes two T-state circuits:
  - **Hook circuit:** the injection `S 24` (hook ancilla) becomes `T 24`. The second `S 35` is the basis change for the final logical-Y readout
    and is kept.
  - **Cultivation proxy:** every S/S_DAG becomes T/T_DAG, the d=3 rule.
- Checks: both are sampled noiselessly in Tsim (2048 shots). No detector is random, every detector value equals the proxy's, and the logical-Y
  observable gives P(1) ≈ 0.146 or 0.854, i.e. ⟨Y_L⟩ = ±1/√2 for a T state.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `hook_inject_T_d3_p0.001.stim` | 1 T | 1 | 1 | 1 |
| `inject_cultivate_T_d3_p0.001.stim` | 8 T_DAG, 7 T | 4 | 4 | 4 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

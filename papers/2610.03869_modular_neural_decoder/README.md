# Modular Neural Decoder for Surface Code Memory and Logic on Superconducting Processors

Moritz Lange, Ole Fjeldså, Gustaf Jonasson Johansson, Mats Granath (2026), [arXiv:2610.03869](https://arxiv.org/abs/2610.03869).

## Where the circuits are

The paper links to [LangeMoritz/modular-gnn-rnn-decoder](https://github.com/LangeMoritz/modular-gnn-rnn-decoder), which I used at commit `afd6e17`.
The simulated circuits are `circuits/stability_d3_X.stim` and the ZZ-merge circuits, with noise added by `gnnrnn/circuits.py`. All of them
are Clifford.

The paper's non-Clifford protocol is a coherent-rotation sweep on ibm_berlin. It inserts R_X(α) on every measure qubit immediately before
its readout, for α ∈ {0.15, …, 1.0} rad at t = 20 and 100 rounds. This sweep ran only on hardware; the repo has no Stim circuit for it.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/modular-gnn-rnn-decoder/`: README, LICENSE, CITATION, requirements, `circuits/` and `gnnrnn/circuits.py`.
- `make_circuits.py` builds the d=3 X-type stability circuit with the authors' `stability_circuit(rounds, p=0.001)` and inserts
  `R_X(α/π)` (half turns) on measure qubits 7–14 before every readout. The settings are (t, α) = (20, 0.15), (20, 0.5), (20, 1.0) and
  (100, 0.5).
- Check: the unrotated circuit is deterministic without noise. With the rotations nearly every detector becomes random, which is the
  intended effect: each readout flips with probability sin²(α/2).

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `stability_d3_X_t100_alpha0.5_p0.001.stim` | 24 R_X | 3 | 6 | 6 |
| `stability_d3_X_t20_alpha0.15_p0.001.stim` | 24 R_X | 3 | 6 | 6 |
| `stability_d3_X_t20_alpha0.5_p0.001.stim` | 24 R_X | 3 | 6 | 6 |
| `stability_d3_X_t20_alpha1.0_p0.001.stim` | 24 R_X | 3 | 6 | 6 |

Compiling the t=100 circuit takes Tsim 44 s, against 0.9 s at t=20.
Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

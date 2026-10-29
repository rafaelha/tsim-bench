# Magic state cultivation on a superconducting quantum processor

Emma Rosenfeld, Craig Gidney, Gabrielle Roberts, et al. (Google Quantum AI, 2025), [arXiv:2512.13908](https://arxiv.org/abs/2512.13908).

## Where the circuits are

The paper's supplement links Crumble views of the circuits, and the data is on Zenodo
[10.5281/zenodo.17872003](https://zenodo.org/records/17872003). It consists of `fig2.zip`, `fig3.zip` and `fig4.zip` (0.7–1.6 GB each, mostly
measurement data), a README and an example notebook. Each experiment directory holds:
- the Cirq circuit that was run (`cirq_circuit[_X|_Z].json`), with the real non-Clifford gates: transversal `ZPowGate(±1/4)` conjugated
  by H_YZ, and a symbolic injection `ZPowGate(2θ)`;
- a Stim circuit in which those gates are replaced by Clifford stand-ins or identities. Some Stim files tag them (`I[T_gate]`,
  `I[conjugate]`, `S[injection]`); the Fig. 4 files do not.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/zenodo_17872003/`: the README, the example notebook, and only the `cirq_circuit*.json`, `stim*.stim`, `.dem` and
  `decoder_properties.json` files. I pulled these out of the remote zips with HTTP range requests (`../../tools/remote_zip.py`) rather than
  downloading 3.2 GB.
- `make_circuits.py` repairs every Stim circuit from its Cirq circuit, moment by moment (both files have one TICK per Cirq moment):
  - ZPowGate(±1/4) → T/T_DAG;
  - the H_YZ conjugations → H_YZ (their placeholders are I, or H in some Z-basis files);
  - the injection → T, i.e. θ = π/4, the T state |θ⟩ = e^{−iθY/2}|0⟩ of the paper;
  - remaining annotation tags are stripped, because Clifft rejects tags.
- Checks:
  - For the tagged Fig. 2/3 files, the Cirq-driven repair is identical to the tag-based substitution.
  - Every circuit is sampled noiselessly in Tsim (2048 shots). No detector is random, and every detector that is deterministic in both
    the proxy and the T circuit agrees. In the Z-basis cultivation files, one check detector is random only in the Clifford proxy.
  - Where the logical readout is in the T/H basis, P(1) ≈ 0.146.
- The circuits are noiseless, since the experiment's noise came from the hardware. I did not add any noise model.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `fig2_cultivation_stim_X_T.stim` | 8 T, 7 T_DAG | 4 | 4 | 4 |
| `fig2_cultivation_stim_Z_T.stim` | 8 T, 7 T_DAG | 4 | 4 | 4 |
| `fig2_injection_stim_X_T.stim` | 1 T | 1 | 1 | 1 |
| `fig2_injection_stim_Z_T.stim` | 1 T | 1 | 1 | 1 |
| `fig2_simulation_stim_X_T.stim` | 8 T, 7 T_DAG | 4 | 4 | 4 |
| `fig2_simulation_stim_Z_T.stim` | 8 T, 7 T_DAG | 4 | 4 | 4 |
| `fig3_injection_stim_T.stim` | 15 T, 14 T_DAG | 4 | 4 | 4 |
| `fig3_simulation_stim_T.stim` | 22 T, 21 T_DAG | 4 | 4 | 4 |
| `fig3_simulation_zoom_stim_T.stim` | 22 T, 21 T_DAG | 4 | 4 | 4 |
| `fig3_with_idle_rounds_stim_T.stim` | 22 T, 21 T_DAG | 4 | 4 | 4 |
| `fig3_with_idle_rounds_zoom_stim_T.stim` | 22 T, 21 T_DAG | 4 | 4 | 4 |
| `fig3_without_idle_rounds_stim_T.stim` | 22 T, 21 T_DAG | 4 | 4 | 4 |
| `fig4_cultivation_N2_stim_X_T.stim` | 8 T, 7 T_DAG | 4 | 4 | 4 |
| `fig4_cultivation_N2_stim_Z_T.stim` | 8 T, 7 T_DAG | 4 | 4 | 4 |
| `fig4_cultivation_N3_stim_X_T.stim` | 8 T, 7 T_DAG | 4 | 4 | 4 |
| `fig4_cultivation_N3_stim_Z_T.stim` | 8 T, 7 T_DAG | 4 | 4 | 4 |
| `fig4_injection_N2_stim_X_T.stim` | 1 T | 1 | 1 | 1 |
| `fig4_injection_N2_stim_Z_T.stim` | 1 T | 1 | 1 | 1 |
| `fig4_simulation_injection_N2_stim_X_T.stim` | 1 T | 1 | 1 | 1 |
| `fig4_simulation_injection_N2_stim_Z_T.stim` | 1 T | 1 | 1 | 1 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

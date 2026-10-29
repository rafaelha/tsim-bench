# Fold-transversal surface code cultivation

Kaavya Sahay, Pei-Kai Tsai, Kathleen Chang, Qile Su, Thomas B. Smith, Shraddha Singh, Shruti Puri (2025),
[arXiv:2509.05212](https://arxiv.org/abs/2509.05212).

## Where the circuits are

The paper links to [kaavyas99/MSC_foldedH](https://github.com/kaavyas99/MSC_foldedH), which I used at commit `9378fd2`. Its
`sample_circuits/` (fd3 baseline, fd5) and `src/` generator produce **|Y⟩-state proxies**: each controlled fold-transversal H_XY check
of the T protocol is simulated with controlled-Y (CY) layers. Converting a CY layer back into native gates needs CCZ and controlled-(S X)
gates, so a gate-by-gate swap does not work.

Native-T reconstructions of this protocol were built by Wan and Zapirain for their exact logical-error-rate calculation
([arXiv:2609.18922](https://arxiv.org/abs/2609.18922), [kh428/exact_ler_for_msc](https://github.com/kh428/exact_ler_for_msc) at `332bc04`,
`data/alternatives/inputs/fold-d{3,5}/model.json`). They are stored as event-list models, not Stim files.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/MSC_foldedH/`: README, `sample_circuits/` (Y-proxy Stim circuits) and `src/` from the authors' repo.
- `stim_src/exact_ler_native_T_models/fold-d{3,5}/`: the native-T event models and the d=5 source proxy
  (`new_cultivation_proxy.stim`, an updated author proxy).
- `make_circuits.py` exports both models to Stim. It maps CSX/CS_DAG_X to controlled-(S X)/(S_DAG X), using the definition in
  `pauli_polynomial.unitary()`, then to CX + CS(_DAG) and T gates (`../../tools/gates.py`). It also translates the measurement, feedback,
  detector and noise events (uniform p=0.001, using the model's noise locations).
- Checks: both circuits are sampled noiselessly in Tsim (2048 shots) and every detector is deterministic. For fold-d5, all 118 detector values
  equal the model's `reference_parity`.
- Scope, from the models:
  - fold-d3 is injection plus two fold-transversal H_XY checks and a noiseless code projection, with no pre-escape round and no escape.
  - fold-d5 is hook injection, (r1, r2) = (2, 0), controlled-layer counts 3, 3, 7, 7, and a noiseless terminal projection.
  - Neither circuit has an `OBSERVABLE_INCLUDE`.
- Noise caveat: a Tsim limitation forced one approximation. Tsim compiles an `ELSE_CORRELATED_ERROR` chain of length k into a 2^k table,
  so the exact 63-term 3-qubit depolarizing chain fails with "Maximum allowed dimension exceeded". The script therefore splits it into
  7 chains of 9. The marginals are exact; only O(p²) double-fault terms differ.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `fold-d3_native_T_p0.001.stim` | 17 T, 8 CCZ, 16 T_DAG | 6 | 8 | 8 |
| `fold-d5_native_T_p0.001.stim` | 45 T, 40 CCZ, 44 T_DAG | 8 | 22 | 22 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

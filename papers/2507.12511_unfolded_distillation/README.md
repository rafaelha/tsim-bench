# Unfolded distillation: very low-cost magic state preparation for biased-noise qubits

Diego Ruiz, Jérémie Guillaud, Christophe Vuillot, Mazyar Mirrahimi (2025), [arXiv:2507.12511](https://arxiv.org/abs/2507.12511).

## Where the circuits are

The paper links to [DiegoRuiz-Git/Unfolded_distillation](https://github.com/DiegoRuiz-Git/Unfolded_distillation), which I used at commit `c20a726`. Its
`Logical error.py` scripts build the circuits in Stim. There are three families:
- the unfolded code merged with a repetition code, with and without preselection;
- the unfolded code merged with a surface code;
- a Toffoli bottom-up scheme.

The transversal logical X^(1/4) rotation is simulated as X^(1/2) = `SQRT_X` on the 15 rotation qubits; the scripts' comment calls this layer
"X^1/4 gate".

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/`: README, LICENSE, and the simulation scripts and code files of the three families. I left out `Results/` (45 MB) and the
  notebooks.
- `make_circuits.py` runs the authors' `CreateCircuit` and `AddNoise` (the scripts up to their "simulation" section). It covers the
  repetition-code variant without preselection at p_Z=1e-3 and the surface-code variant without bit flips, each for 2, 4 and 6 rounds. It
  then restores the real gates in two steps:
  1. `SQRT_X` → `R_X(0.25)`, i.e. X^(1/4) in half-turn units.
  2. **Feedforward.** The first round of X stabilizers is random and leaves Z byproducts (the scripts' `byproducts` table). With X^(1/4) a
     byproduct is no longer a Pauli frame change, as the paper notes, so each rotation qubit gets SQRT_X^(f) with f = the parity of its
     byproduct records.
     - Stim cannot condition a non-Pauli gate on a record, so this uses deferred measurement: the needed MX outcomes go through record
       ancillas, their parity is copied to a scratch qubit, and a controlled SQRT_X (H·CS·H) is applied.
     - The authors' schedule measures some stabilizers for the first time only after the rotation layer. So the X^(1/4) layer is moved to just
       after the last record it depends on. This is exact, because in between the rotation qubits are only CX targets.
- Checks: each circuit is sampled noiselessly in Tsim (2048 shots).
  - All detectors are deterministic.
  - The four distillation-check observables are always 0. They are random (≈0.47) without the feedforward and with the opposite sign, which
    fixes the sign of the correction.
  - The output's logical-Y readout gives P(1) = 0.857 ≈ 1 − (1 − 1/√2)/2, as expected for a magic state.
- Not converted: the Toffoli bottom-up scheme. Its released proxy replaces the Toffoli of the X₁(CX)₂₃ GHZ measurement with two CNOTs, and
  the native gate placement is not specified.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `unfolded_repetition_no_preselection_pz1e-3_rounds2.stim` | 22 T, 11 T_DAG, 15 R_X | 4 | 4 | 5 |
| `unfolded_repetition_no_preselection_pz1e-3_rounds4.stim` | 22 T, 11 T_DAG, 15 R_X | 4 | 5 | 5 |
| `unfolded_repetition_no_preselection_pz1e-3_rounds6.stim` | 22 T, 11 T_DAG, 15 R_X | 4 | 5 | 5 |
| `unfolded_surface_no_bitflip_pz1e-3_rounds2.stim` | 20 T, 10 T_DAG, 15 R_X | 4 | 4 | 5 |
| `unfolded_surface_no_bitflip_pz1e-3_rounds4.stim` | 20 T, 10 T_DAG, 15 R_X | 4 | 4 | 5 |
| `unfolded_surface_no_bitflip_pz1e-3_rounds6.stim` | 20 T, 10 T_DAG, 15 R_X | 4 | 4 | 5 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

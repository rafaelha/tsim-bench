# Magna: simulating magic state factories as cheaply as Clifford circuits

Yifei Wang, Yingfei Gu (2026), [arXiv:2610.22315](https://arxiv.org/abs/2610.22315).

## Where the circuits are

The paper links to [itpyi/magna](https://github.com/itpyi/magna), which I used at commit `01ae9c2`. Every directory under `examples/` is one benchmark
task from the paper: a `physical.magna` circuit, an ideal target circuit, `task.json` and `run.json`.
- **Bravyi–Haah (3k+8)-to-k distillation:** `bh{2,4,6,10,20,40,60,80,100}-T`, each with an `-S` Clifford control.
- **Cultivation:** colour-code `color3`/`color5` and RP² `rp2-d3`/`rp2-d5` (with `-S` controls).
- **Code switching:** `dk` (Daguerre–Kim) and `wg-T`/`wg-S` (Wang et al.).
- **TQD memory:** `tqd3–5`.
- **Logical-level distillation:** `logical-distillation`.

The `.magna` format is Stim plus native T/CS/CCZ, classical registers (`CONTROL`), classically controlled gates, `det[n]` references and
`POSTSELECT` (`docs/software/circuit-format.md`). The Zenodo deposit [10.5281/zenodo.23386778](https://doi.org/10.5281/zenodo.23386778) holds data
and figure scripts only, no circuits.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/magna/`: `examples/`, README, LICENSE (MPL-2.0), THIRD_PARTY_NOTICES and the circuit-format documentation.
- `make_circuits.py` translates `physical.magna` to the Tsim/Clifft Stim dialect. The full rules are in its docstring; in short:
  - registers are tracked as parities of records;
  - classically controlled Pauli gates become `rec`-controlled Stim gates;
  - classically controlled S/S†/CCZ corrections are applied as quantum-controlled gates by deferred measurement, through record ancillas;
  - CS/CS†/CH are decomposed into T gates;
  - fractional noise arguments become decimals;
  - `POSTSELECT` is dropped, but all detectors are kept.
- Not converted: `tqd3–5` and `logical-distillation`, because they call external decoders.
- Checks: each circuit is sampled noiselessly in Tsim. Every postselected detector is deterministic. Where the task defines an ideal target
  circuit (all except `dk`), undoing it on the task's output qubits leaves them in |0⟩; for example, bh100-T outputs 100 ideal T states.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `bh100-S.stim` | none | 0 | 0 | 0 |
| `bh100-T.stim` | 616 T, 616 T_DAG | 3 | ≥60 (overflow) | ≥60 (overflow) |
| `bh10-S.stim` | none | 0 | 0 | 0 |
| `bh10-T.stim` | 76 T, 76 T_DAG | 3 | 12 | 12 |
| `bh20-S.stim` | none | 0 | 0 | 0 |
| `bh20-T.stim` | 136 T, 136 T_DAG | 3 | 22 | 22 |
| `bh2-S.stim` | none | 0 | 0 | 0 |
| `bh2-T.stim` | 28 T, 28 T_DAG | 3 | 4 | 4 |
| `bh40-S.stim` | none | 0 | 0 | 0 |
| `bh40-T.stim` | 256 T, 256 T_DAG | 3 | 42 | 42 |
| `bh4-S.stim` | none | 0 | 0 | 0 |
| `bh4-T.stim` | 40 T, 40 T_DAG | 3 | 6 | 6 |
| `bh60-S.stim` | none | 0 | 0 | 0 |
| `bh60-T.stim` | 376 T, 376 T_DAG | 3 | ≥60 (overflow) | ≥60 (overflow) |
| `bh6-S.stim` | none | 0 | 0 | 0 |
| `bh6-T.stim` | 52 T, 52 T_DAG | 3 | 8 | 8 |
| `bh80-S.stim` | none | 0 | 0 | 0 |
| `bh80-T.stim` | 496 T, 496 T_DAG | 3 | ≥60 (overflow) | ≥60 (overflow) |
| `color3.stim` | 8 T_DAG, 8 T | 4 | 4 | 4 |
| `color5.stim` | 33 T_DAG, 39 T | 6 | 10 | 10 |
| `dk.stim` | 8 T, 7 T_DAG | 4 | 4 | 5 |
| `rp2-d3-S.stim` | none | 0 | 0 | 0 |
| `rp2-d3.stim` | 16 T, 15 T_DAG | 4 | 8 | 8 |
| `rp2-d5-S.stim` | none | 0 | 0 | 0 |
| `rp2-d5.stim` | 51 T, 50 T_DAG | 9 | 18 | 18 |
| `wg-S.stim` | none | 0 | 0 | 0 |
| `wg-T.stim` | 26 T_DAG, 22 T | 4 | 5 | 5 |

Clifft reports "≥60 (overflow)" when its planner would need an active width above its dense-state limit.
Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

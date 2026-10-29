# Polynomial-time simulation of non-Clifford quantum error correction (Merlin)

Serban Cercelescu, Mark Koch, Arthur Pesah (2026), [arXiv:2610.06811](https://arxiv.org/abs/2610.06811).

## Where the circuits are

The paper's simulator is [mark-koch/merlin-sim](https://github.com/mark-koch/merlin-sim), which I used at commit `9799e00`.
- **Benchmark workloads:** built in Python by `benchmarks/protocols` (numpy only) as text in the Stim dialect with native T/T_DAG/CCZ:
  - 15-to-1 and Bravyi–Haah (3k+8)-to-k distillation (`build_distillation_case`);
  - BB/BT code switching with a transversal CCZ layer (`build_code_switching_case`, cases `bt27` and `bt81`).
- **Cultivation workloads:** shipped as files, `experiments/cultivation/circuit_d{3,5}_t.stim`.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/merlin-sim/`: README, LICENCE, CITATION, docs, `benchmarks/` (`models.py`, `protocols/`, README) and `experiments/cultivation/`.
- `make_circuits.py` builds the cases from `benchmarks/README.md` (`15to1`, `bh:2…18`, `bt27`, `bt81`) at p=0.001, using the default "clean" noise
  model (Z noise after each physical T_DAG). It copies the two cultivation circuits verbatim.
- Checks:
  - The distillation and cultivation circuits are sampled noiselessly in Tsim: every detector is deterministic and every observable is 0.
  - I did not sample the code-switching circuits. Tsim's noiseless sampling of bt27 did not finish, and the paper runs these only with Merlin
    and xtim.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `code_switching_bt27_p0.001.stim` | 240 T, 180 T_DAG | 26 | 27 | 28 |
| `code_switching_bt81_p0.001.stim` | 672 T, 504 T_DAG | 63 (> limit 30) | 52 | 56 |
| `cultivation_d3_t.stim` | 15 T_DAG, 14 T | 4 | 4 | 4 |
| `cultivation_d5_t.stim` | 46 T_DAG, 45 T | 6 | 10 | 10 |
| `distillation_15to1_p0.001.stim` | 16 T_DAG | 4 | 0 | 0 |
| `distillation_bh10_p0.001.stim` | 48 T_DAG | 4 | 0 | 0 |
| `distillation_bh12_p0.001.stim` | 56 T_DAG | 4 | 0 | 0 |
| `distillation_bh14_p0.001.stim` | 64 T_DAG | 4 | 0 | 0 |
| `distillation_bh16_p0.001.stim` | 72 T_DAG | 4 | 0 | 0 |
| `distillation_bh18_p0.001.stim` | 80 T_DAG | 4 | 0 | 0 |
| `distillation_bh2_p0.001.stim` | 16 T_DAG | 4 | 0 | 0 |
| `distillation_bh4_p0.001.stim` | 24 T_DAG | 4 | 0 | 0 |
| `distillation_bh6_p0.001.stim` | 32 T_DAG | 4 | 0 | 0 |
| `distillation_bh8_p0.001.stim` | 40 T_DAG | 4 | 0 | 0 |

**Distillation note.** Clifft reports k=0 for these distillation circuits. In this "clean" model the only noise is Z after the T_DAG gates,
which commutes with them. The circuit also undoes the ideal output state for scoring. Clifft's `PhasePolynomialPass` then cancels all
T gates: bh2 gives k=5 with no HIR passes and k=0 with `PhasePolynomialPass` alone. Tsim does not do this cancellation and gives k=4. Compare
Magna's Bravyi–Haah circuits ([`../2610.22315_magna`](../2610.22315_magna)), which use T-teleportation with conditional S corrections:
there Tsim gives k=3 and Clifft grows with k.

**bt81 note.** Tsim's `active_statevector` strategy refuses bt81, because one component would need 63 active qubits (limit 30).

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

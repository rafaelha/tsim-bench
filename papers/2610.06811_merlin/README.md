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

**Why Clifft reports k=0 for the distillation circuits.** Every intermediate state of these circuits is a genuine
non-stabilizer state, with stabilizer rank ≥ 2. The k=0 comes from Clifft not simulating the circuit as written: its
`PhasePolynomialPass` first rewrites it into an equivalent circuit, and for this benchmark that rewritten circuit has no T gates.
1. The 15-to-1 and Bravyi–Haah codes are triorthogonal. Encoder, transversal `T_DAG` on all physical qubits and decoder together act as
   logical `T_DAG` on the outputs. The leftover Clifford phases are removed by the explicit Z/CZ corrections in `distillation.py`.
2. With `target_scoring=True` (the default), the script then applies another `T_DAG` to every output before the X measurement. This
   undoes the ideal output state, so a perfect run reads 0.
3. As a phase polynomial the whole sequence collapses, with every parity term getting a multiple of π/2. The circuit is Clifford as an
   operator.
4. In the default "clean" noise model the only noise is Z after each physical `T_DAG`. Z is diagonal and commutes with all T gates, so it
   passes through the cancellation and stays a Pauli error.

The full noisy circuit is therefore exactly Clifford plus Pauli noise, and its detector and observable distribution can be sampled with k=0.
Tsim does no global phase-polynomial rewriting and simulates the T gates as written (k=4). This k=0 is a correct exact simulation that
exploits a special feature of the scored observable and the noise model. It does not show that simulating the distillation protocol is cheap.

Switching off either ingredient removes the effect (`variants.py`; 15-to-1 and Bravyi–Haah k=6, p=0.001):

| variant | 15-to-1: Clifft (all passes) | 15-to-1: Clifft (no passes) | 15-to-1: Tsim | bh6: Clifft (all passes) | bh6: Clifft (no passes) | bh6: Tsim |
|---|---|---|---|---|---|---|
| Z noise + target scoring (benchmark default) | **0** | 5 | 4 | **0** | 9 | 4 |
| Z noise, no target scoring | 1 | 5 | 4 | 6 | 9 | 3 |
| depolarizing noise + target scoring | 4 | 5 | 4 | 4 | 9 | 4 |
| depolarizing noise, no target scoring | 4 | 5 | 4 | 8 | 9 | 3 |

- **Without target scoring,** Clifft's k equals the number of distilled outputs (1 and 6). Each output is a real T state and needs at least
  one active qubit.
- **With depolarizing noise,** X/Y errors do not commute with T, so the cancellation fails and k = 4.
- **With no HIR passes,** Clifft's k is at or above Tsim's.

Magna's Bravyi–Haah circuits ([`../2610.22315_magna`](../2610.22315_magna)) teleport T gates with conditional S corrections, so this
cancellation cannot happen there: Tsim gives k=3 and Clifft's k grows to 42.

**bt81 note.** Tsim's `active_statevector` strategy refuses bt81, because one component would need 63 active qubits (limit 30).

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

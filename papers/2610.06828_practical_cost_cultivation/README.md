# The practical cost of magic state cultivation

Rohan Mehta, Varun Menon, Hengyun Zhou, Mikhail D. Lukin, J. Pablo Bonilla Ataides (2026),
[arXiv:2610.06828](https://arxiv.org/abs/2610.06828).

## Where the circuits are

The paper links to [rohanmehtagithub/MSC-data](https://github.com/rohanmehtagithub/MSC-data), which I used at commit `0db416a`. Its `circuits/`
folder holds:
- colour-to-grafted-code cultivation at fault distance f3/f5 with escape, taken from Gidney et al.'s Zenodo record;
- fold-transversal surface-code cultivation at f3/f5 (f3 from Sahay et al.'s repo, f5 reconstructed by the authors);
- an f3 fold-transversal escape sweep: 40 circuits escaping into d=7–15 surface codes with 1–12 rounds.

All of them are Y-basis Clifford proxies.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/MSC-data/`: README, LICENSE and `circuits/`, all of them.
- `make_circuits.py` converts the colour-code circuits:
  - **f3:** blanket S→T.
  - **f5:** Clifft's d=5 converter (`convert_circuit(is_d5=True, is_e2e=True)`, from
    [`../2409.17595_magic_state_cultivation`](../2409.17595_magic_state_cultivation)). A blanket S→T leaves 6 random detectors here.
- Checks: both are sampled noiselessly in Tsim (2048 shots). No detector is random, every detector value equals the proxy's, and the
  observable reads 1 with probability ≈ 0.85 = 1 − (1 − 1/√2)/2, as expected for a T state.
- Not converted: the fold-transversal circuits and the escape sweep. Their controlled-Y layers do not map gate-by-gate to the native-T
  protocol (CCZ and controlled-(S X) layers). Native-T versions of fold-transversal cultivation are in
  [`../2509.05212_fold_transversal_cultivation`](../2509.05212_fold_transversal_cultivation).

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `color_code_cultivation_f3_T.stim` | 8 T_DAG, 7 T | 4 | 4 | 4 |
| `color_code_cultivation_f5_T.stim` | 27 T_DAG, 26 T | 6 | 10 | 10 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

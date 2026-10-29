# Low-overhead magic state distillation with color codes

Seok-Hyung Lee, Felix Thomsen, Nicholas Fazio, Benjamin J. Brown, Stephen D. Bartlett (2024),
[arXiv:2409.07707](https://arxiv.org/abs/2409.07707).

This folder also covers the authors' package from **Color code decoder with improved scaling for correcting circuit-level noise** (Lee, Li,
Bartlett, [arXiv:2404.07482](https://arxiv.org/abs/2404.07482)). The circuits of that paper itself are Clifford memory circuits.

## Where the circuits are

The paper links three repositories:
- [seokhyung-lee/color-code-stim](https://github.com/seokhyung-lee/color-code-stim), which I used at commit `0eb3593`, is the circuit
  generator.
- [msd-magic-state-prep-cycle-simulation](https://github.com/seokhyung-lee/msd-magic-state-prep-cycle-simulation), which I used at `c5613ff`,
  holds the logical-level cycle simulation, with no circuits.
- [color-code-msd-data](https://github.com/seokhyung-lee/color-code-msd-data) holds the data.

The paper's second scheme feeds cultivated magic states, grown to a larger colour code, into distillation. These circuits come from
`ColorCode(d, d2, circuit_type="cult+growing")`:
1. a bundled copy of Gidney et al.'s inject+cultivate circuit (`assets/cultivation_circuits`, a Y-basis S proxy) at d=3 or 5;
2. colour-code growth to d2;
3. d2 rounds of syndrome extraction.

The distillation itself is simulated at the logical level and has no Stim circuit.

## What I did

- `tex/`: arXiv source of 2409.07707. I removed the figures.
- `stim_src/`: `color-code-stim` (README, LICENSE, requirements, `src/` including the cultivation assets) and the cycle-simulation repo.
- `make_circuits.py` converts the cultivation asset to T gates and passes it to the package via `ColorCode(cultivation_circuit=...)`:
  - d=3 by blanket S→T; d=5 by Clifft's d=5 converter (`../2409.17595_magic_state_cultivation`).
  - Because the package processes the circuit with Stim, T/T_DAG are carried as the otherwise unused C_XYZ/C_ZYX and swapped back at the end.
  - Settings: (d, d2) = (3, 7), (3, 11), (5, 9), (5, 13), with p_circuit = 0.001.
- Check: noiseless builds are sampled in Tsim (1024 shots). No detector is random, every detector value equals the proxy's, and the final
  logical-Y observable reads 1 with probability ≈ 0.14 or 0.85 (T state).

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `cult_growing_T_d3_to_d11_p0.001.stim` | 8 T_DAG, 7 T | 4 | 4 | 4 |
| `cult_growing_T_d3_to_d7_p0.001.stim` | 8 T_DAG, 7 T | 4 | 4 | 4 |
| `cult_growing_T_d5_to_d13_p0.001.stim` | 27 T_DAG, 26 T | 6 | 10 | 10 |
| `cult_growing_T_d5_to_d9_p0.001.stim` | 27 T_DAG, 26 T | 6 | 10 | 10 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

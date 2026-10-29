# Magic state cultivation: growing T states as cheap as CNOT gates

Gidney, Shutty, Jones (2024), [arXiv:2409.17595](https://arxiv.org/abs/2409.17595).

## Where the circuits are

The paper's code/data statement points to Zenodo [10.5281/zenodo.13777072](https://doi.org/10.5281/zenodo.13777072)
(`circuits.zip`, `code.zip`, `stats.csv`). The code is also on GitHub at
[Strilanc/magic-state-cultivation](https://github.com/Strilanc/magic-state-cultivation).
All released circuits are **Clifford proxies**: the T-basis cultivation is simulated in the Y basis, with S/S_DAG
standing in for T/T_DAG (`b=Y` in the file names).

## What I did

- `tex/`: arXiv source (`.tex`, `.bib`, class file). I removed the images and other binary assets.
- `stim_src/zenodo_13777072/circuits/`: the Zenodo circuits. I left out `for_correlated_matching/` (23 MB of Clifford
  surface-code CNOT circuits).
- `stim_src/github_magic-state-cultivation/`: the authors' generator (`src/`) at commit `871e68f`.
- `stim_src/clifft_paper_convert_s_to_t.py`: the S→T converter from
  [unitaryfoundation/clifft-paper](https://github.com/unitaryfoundation/clifft-paper) (`magic_state_cultivation/convert_s_to_t.py`
  at `db7dc9f`, Apache-2.0). Beyond the plain S→T, S_DAG→T_DAG substitution it handles the d=5 errata sign flips, the growth-stage
  feedforward that the T gates make necessary, detector healing, and wrapping the final Y_L measurement in T…T_DAG.
- `make_circuits.py` regenerates the circuits with the authors' generator, converts them, and checks each circuit noiselessly in Tsim
  (256 shots, every detector must be 0). It then writes uniform-depolarizing p=0.001 versions to `stim/`.

Run: `uv run python make_circuits.py`, then `uv run python ../../tools/measure_k.py stim/*.stim --json k_max.json`.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `end2end_d3_dsurface15_p0.001.stim` | 8 T_DAG, 7 T | 4 | 4 | 4 |
| `end2end_d5_dsurface15_p0.001.stim` | 27 T_DAG, 26 T | 6 | 10 | 10 |
| `inject_cultivate_d3_p0.001.stim` | 15 T_DAG, 14 T | 4 | 4 | 4 |
| `inject_cultivate_d5_p0.001.stim` | 46 T_DAG, 45 T | 6 | 10 | 10 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

Cross-check: `stim/inject_cultivate_d3_p0.001.stim` and `stim/inject_cultivate_d5_p0.001.stim` are byte-identical to the
Clifft paper's published `qec_bench/circuits/cultivation_d3.stim` / `cultivation_d5.stim` (also SymFT's `msc_d3/d5_inject_cultivate`).

# Transversal dimension jump for product qLDPC codes

Christine Li, John Preskill, Qian Xu (2025), [arXiv:2510.07269](https://arxiv.org/abs/2510.07269).

## Where the circuits are

The paper links to [tinghui2012/transversal-dimension-jump](https://github.com/tinghui2012/transversal-dimension-jump).
- Notebook `3_ccz_error_detection_simulations.ipynb` holds the saved Stim circuit of the CCZ error-detection experiment on three
  [[27,3,3]] tricycle ("d3_blp") blocks. The generator is `src/CCZCircuit.py`.
- In those circuits the CCZ is **not a gate**: its effect is modelled by correlated Pauli-Z error channels (`E(...)` weight-5 Z
  strings), so the circuits are Clifford.
- The same [[27,3,3]] tricycle code is the factory code in Lukin-group papers: Menon et al., *Magic tricycles* (2508.10714);
  Xiao et al., 2610.03605; Menon et al., 2610.10731.

## What I did

The real-CCZ circuits were built in a separate session and published as `tricycle_factories/` of
[rafaelha/circs](https://github.com/rafaelha/circs) (commit `e4ee58f`). That repo's README, copied here as
`stim_src/circs/README_circs.md`, has the details. In short:

- **Physical CCZ gates:** the CCZ triples recovered from the `E(...)` lines form a valid depth-2 transversal CCZ (54 physical CCZs for
  [[27,3,3]]). It acts as logical CCZ on the 6 logical triples (a, b, c) with a, b, c in different blocks and distinct.
- **Circuit steps:**
  1. Data qubits start in |+⟩, followed by one Z-syndrome round.
  2. A feed-forward X correction, `CX rec[...] q`, follows. A real CCZ needs it: without it the CCZ acts on X^e|+̄⟩. The redundant Z
     checks become meta-check detectors.
  3. The transversal CCZ is applied, with the paper's weight-5 Z noise after it.
  4. Transversal MX, then the X-check detectors and the 9 logical-X observables. Each observable has P = 3/8 noiselessly, since the
     output is a CCZ hypergraph state.
- **Noise:** the paper's model at p = 1e-3.
- **Codes:**
  - `blp_27_3_3`: the paper's code, using the authors' syndrome round and CCZ triples.
  - `toric_81_3_3`, `toric_375_3_5`: the paper's 3D toric codes.
  - Eight smaller tricycle codes on 3-torus quotients, from [[6,3,2]] to [[27,3,3]], written by `stim_src/circs/generate.py`.

In this folder:
- `tex/`: the arXiv source, figures removed.
- `stim_src/circs/`: the published circuits, `generate.py` and the README.
- `make_circuits.py`: copies the circuits to `stim/`. It also samples the four smallest noiselessly in Tsim (512 shots): all detectors are
  deterministic and every observable is ≈ 3/8.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) |
|---|---|---|---|
| `blp_27_3_3.stim` | 54 CCZ | 26 | 26 |
| `toric_375_3_5.stim` | 750 CCZ | 186 (refused, limit 30) | ≥60 (overflow) |
| `toric_81_3_3.stim` | 162 CCZ | 63 (refused, limit 30) | 59 |
| `tricycle_12_3_2.stim` | 24 CCZ | 16 | 16 |
| `tricycle_15_3_2.stim` | 30 CCZ | 16 | 16 |
| `tricycle_18_3_2.stim` | 36 CCZ | 20 | 20 |
| `tricycle_21_3_3.stim` | 42 CCZ | 23 | 23 |
| `tricycle_24_3_2.stim` | 48 CCZ | 20 | 20 |
| `tricycle_27_3_3.stim` | 54 CCZ | 24 | 24 |
| `tricycle_6_3_2.stim` | 12 CCZ | 9 | 9 |
| `tricycle_9_3_2.stim` | 18 CCZ | 11 | 13 |

Tsim 1.0.0, default `active_statevector` strategy, largest statevector component width. Clifft 0.13.0: default HIR passes +
`ActiveWidthSchedulePass()` (default settings), `peak_active_width`. Compile only, from `results/benchmark.json`
(`tools/benchmark.py`). Each simulator ran in its own process, capped at 40 GB of memory and 30 min.

The circs README also lists Clifft with `ActiveWidthSchedulePass(beam_width=8)` and `(beam_width=128)`, measured with Clifft 0.12.0:
- `tricycle_6_3_2`: 9 and 9;
- `tricycle_9_3_2`: 12 and 12;
- `tricycle_12_3_2`: 15 and 14;
- `tricycle_15_3_2`: 16 and 15;
- `blp_27_3_3`: 26 and 26.

The table here uses the default scheduler settings, like every other paper.

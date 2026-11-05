# Papers with Mikhail D. Lukin that publish Stim circuits with non-Clifford gates (or convertible proxies)

## How the papers were found

- **Search:** arXiv API author queries `"Mikhail Lukin"`, `"Mikhail D. Lukin"`, `"M. D. Lukin"`, and `Lukin` combined with QEC keywords
  (2026-11-04). That gives 482 papers.
- **Filter:** the 43 papers from 2019 on that mention error correction, fault tolerance, magic states, logical qubits, transversal gates,
  codes or decoding. Their arXiv sources and code/data links (GitHub, Zenodo) were checked.
- **Kept:** only papers that **publish Stim circuits** containing non-Clifford gates, or Clifford proxies (S for T, |Y⟩ for |T⟩) that
  convert to real T gates.

## Result

Three papers qualify.

| arXiv | paper | published circuits | conversion to real T | Tsim k | Clifft k |
|---|---|---|---|---|---|
| [2610.06828](https://arxiv.org/abs/2610.06828) | The practical cost of magic state cultivation (Mehta et al.) | colour-code T cultivation f=3/5 (already in this repo: `papers/2610.06828_practical_cost_cultivation`) | native T | 4 (f3), 6 (f5) | 4, 10 |
| [2505.13587](https://arxiv.org/abs/2505.13587) | Fast correlated decoding of transversal logical algorithms (Cain et al.) | Zenodo [15702016](https://doi.org/10.5281/zenodo.15702016) `distillation.zip`: encoded 15-to-1 distillation with transversal CNOTs on 16 surface-code patches, d = 5, 9, 13, 17, 21, 25 (1.6k–40k qubits) | the 15 injected states are `RX`+`S` (\|Y⟩ proxy): S→T. Noiseless check of d=5: every deterministic detector matches the proxy; the only random detectors are the 32 that are already random in the proxy (the logical `MPP` readouts the authors define as gauge "detectors") | 4 (d=5, 9) | 4 (d=5, 9) |
| [2406.17653](https://arxiv.org/abs/2406.17653) | Low-overhead transversal fault tolerance for universal QC (Zhou et al.) | Zenodo [16552626](https://zenodo.org/records/16552626): `s_injection` d=3–9, `s_factory` d=3–9, `two_level_s_factory` d=9 | `RY` (\|Y⟩ injection) → `RX`+`T`. **s_injection:** a valid T injection into the surface code; all 62 detectors stay deterministic and the logical observable becomes random (0.78 / 0.30), as expected for a T state. **s_factory / two-level:** the same 16 / 0 gauge detectors are random as in the proxy, but the protocol is \|Y⟩ (S-state) distillation, which has no T analogue; its four outputs become random (≈0.36), so the converted circuit is not a T factory | s_injection 1; s_factory 3; two-level 7 | s_injection 2; s_factory 7; two-level (not measured) |

k values: Tsim 1.0.0 (`compile_detector_sampler()`, largest statevector component) and Clifft 0.13.0 (`default_hir_pass_manager()` +
`ActiveWidthSchedulePass()`), compile only. Clifft needs `tools/stimtext.py` to drop target-less `DEPOLARIZE1` lines first.

Both new papers now have folders and are in the benchmark: `papers/2505.13587_correlated_decoding_distillation` and
`papers/2406.17653_transversal_algorithmic_ft`. Throughput is in the README table and in SUMMARY.md. The tricycle factory code of
2508.10714 / 2610.03605 / 2610.10731 is benchmarked through the real-CCZ circuits in `papers/2510.07269_transversal_dimension_jump`.

**Is Tsim good and fast for these?** Yes, for all of them:
- k is at most 7.
- The cultivation circuits (2610.06828) run at 1.2e6 (f3) and 3.1e5 (f5) shots/s on one CPU core (README table).
- The 2505.13587 distillation is the most interesting new workload. It is real T-state 15-to-1 distillation at circuit level, with
  surface-code patches up to d=25 (40k qubits), at k=4.
- 2406.17653 `s_injection` is a small T-injection benchmark (k=1).

## Lukin papers with non-Clifford content but no published circuits (excluded)

| arXiv | paper | why excluded |
|---|---|---|
| [2412.15165](https://arxiv.org/abs/2412.15165) | Logical magic state distillation experiment | no circuits; the Tsim paper's reproduction is in `papers/2604.01059_tsim` |
| [2312.03982](https://arxiv.org/abs/2312.03982) | Logical quantum processor | [[8,3,2]] IQP circuits with transversal CCZ, no Stim files |
| [2404.19005](https://arxiv.org/abs/2404.19005) | Fault-tolerant compiling of classically hard IQP circuits | only Clifford circuits simulated; no files |
| [2610.03605](https://arxiv.org/abs/2610.03605) | Efficient fidelity simulation of high-rate magic distillation circuits | simulator paper; no circuits released |
| [2508.10714](https://arxiv.org/abs/2508.10714) | Magic tricycles | no circuits released |
| [2610.10731](https://arxiv.org/abs/2610.10731) | Single-shot magic state factories for qLDPC codes | Stim simulations with the CCZ traced out (Clifford proxy); no circuits or code released (the only ancillary file is an atom-movement animation) |

For the [[8,3,2]] IQP papers, [`iqp_832_k.py`](iqp_832_k.py) compiles a toy reconstruction (not the authors' circuits). At 48 logicals
it gives Tsim k ≤ 9 against Clifft k up to 42.

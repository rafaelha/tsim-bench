# Active width of published non-Clifford Stim circuits

A literature survey of papers that release Stim circuits with non-Clifford gates, or Clifford proxies that convert to real T/CCZ/CS
gates. For each one I measured the peak active width `k_max` that Tsim and Clifft reach on its circuits.

- **Tsim:** `bloqade-tsim==1.0.0`. `compile_detector_sampler()` with the default `active_statevector` strategy; k = largest statevector
  component width (compile only, no sampling).
- **Clifft 0.13.0:** `default_hir_pass_manager()` + `ActiveWidthSchedulePass()` with default settings; k = `peak_active_width`.

Results: the table below, and [`SUMMARY.md`](SUMMARY.md) with Clifft's numbers as well. Regenerate both with
`uv run python tools/benchmark.py table` and `uv run python tools/summary.py`. The per-folder `k_max.json` files of the original 24
papers were measured earlier with Tsim main@883d787 and Clifft 0.12.0, and also include Clifft without the scheduler.

## Throughput and k_max (Tsim 1.0.0, Tsim GPU draft, Tsim Metal prototype, Clifft 0.13.0)

Produced by [`tools/benchmark.py`](tools/benchmark.py) (`uv run python tools/benchmark.py all`); raw data in
[`results/benchmark.json`](results/benchmark.json).

- **Tsim single-core CPU:** `bloqade-tsim==1.0.0`, run with `NUMBA_NUM_THREADS=1` and pinned with `taskset` to one physical core of a
  Ryzen 9 9900X, with one circuit at a time (`--jobs 1`). Running 8–10 single-core jobs side by side halved Tsim's rate on d=5
  end-to-end cultivation (540 k → 265 k shots/s; Clifft 21.7 k → 18.0 k), so the CPU columns come from serial runs.
- **Tsim GPU:** draft PR [#219](https://github.com/QuEraComputing/tsim/pull/219) (`cuda-statevector-executor` at `a2af975f`) on an
  RTX 5090.
- **Tsim Metal:** the Metal prototype (local branch `metal-statevector-executor` at `3c01b549`, built on the CUDA draft) on an
  Apple M4 Pro (20-core GPU, 48 GB unified memory). Measured like the GPU column: same calls, 0.5 s target, 2 GiB output cap, and
  only circuits with Tsim k_max ≤ 11. "unsupported" marks circuits whose rows (55–487 shot words) don't fit the prototype's
  14 KB of noise-kernel threadgroup memory.
- **What the rates measure:** detector sampler `sample(n, append_observables=True, bit_packed=True)`, with no postselection and every
  shot returned to the host. Compilation and the warm-up call are excluded, and each rate is the best of three calls of at least 1 s
  (CPU) or 0.5 s (GPU).
- **GPU copy limit:** GPU calls are capped at 2 GiB of output, so for circuits with many detectors the GPU rate is limited by the copy
  to the host.
- **Skipped (–):** circuits with Tsim k_max > 15 (CPU) or > 11 (GPU and Metal, the executors' limit).
- **GPU shared-memory workaround:** on the draft as is, the four d=15 hook-injection circuits (6,577 output columns) fail with
  `CUDA_ERROR_INVALID_VALUE`. The cause is the `gather_columns` kernel: it needs about 26 KB of static plus 26 KB of dynamic shared memory
  per block of 32 shots, above the 48 KB default, and unlike the noise kernel it has no size check. The benchmark worker lets the packing
  kernels use the device's opt-in maximum (`allow_large_shared_memory` in `tools/bench_worker.py`). On `li_inject_T_d15_pd5` the
  per-column rates then agree with Tsim 1.0.0 on the CPU (2^18 shots each, max |z| = 4.0 over 6,577 columns).
- **GPU "unsupported":** for the 2505.13587 distillation at d = 9 and 13, the draft's noise kernel itself refuses the rows (232 and
  487 shot words "do not fit the noise kernel's shared memory").
- **GPU speedup:** Tsim GPU rate over Tsim single-core rate.
- **Metal speedup vs CPU:** Tsim Metal rate (M4 Pro) over the same Tsim single-core rate (Ryzen 9 9900X).
- **‡:** measured with Tsim [PR #270](https://github.com/QuEraComputing/tsim/pull/270) (`96b86e8b`, sparse error basis) instead of
  1.0.0. It is used only where 1.0.0 runs out of memory while compiling (2505.13587 at d = 17–25). The PR leaves sampling unchanged:
  seeded samples are bit-identical to 1.0.0 on 26 test circuits. The GPU draft and the Metal prototype lack the fix, so their
  compile of these circuits still runs out of memory (not run on Metal).
- **k_max:** Tsim 1.0.0 `compile_detector_sampler()` (largest statevector component).
- **Clifft:** [`SUMMARY.md`](SUMMARY.md) has, per circuit, the same columns plus Clifft 0.13.0's single-core throughput and k_max. Clifft
  always runs with `default_hir_pass_manager()` + `ActiveWidthSchedulePass()` at default settings, and samples with
  `sample(threads=1)`.

<!-- benchmark-table:begin -->
| paper / circuit | Tsim single-core CPU (shots/s) | Tsim GPU (shots/s) | GPU speedup | Tsim Metal (shots/s) | Metal speedup vs CPU | Tsim k_max |
|---|---|---|---|---|---|---|
| **[2302.12292](https://arxiv.org/abs/2302.12292)** Gidney (2023), *Cleaner magic states with hook injection* | | | | | | |
| [`hook_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/hook_inject_T_d15_pd5_p0.001.stim) | 1.51 M | 122 M | 81x | unsupported | – | 1 |
| [`hook_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/hook_inject_T_d15_pd7_p0.001.stim) | 1.48 M | 119 M | 80x | unsupported | – | 1 |
| [`li_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/li_inject_T_d15_pd5_p0.001.stim) | 800 k | 63.9 M | 80x | unsupported | – | 1 |
| [`li_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/li_inject_T_d15_pd7_p0.001.stim) | 788 k | 62.6 M | 80x | unsupported | – | 1 |
| [`pregrown_hook_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/pregrown_hook_inject_T_d15_pd5_p0.001.stim) | 1.33 M | 108 M | 81x | unsupported | – | 1 |
| [`pregrown_hook_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/pregrown_hook_inject_T_d15_pd7_p0.001.stim) | 1.34 M | 108 M | 81x | unsupported | – | 1 |
| [`zz_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/zz_inject_T_d15_pd5_p0.001.stim) | 807 k | 68 M | 84x | unsupported | – | 1 |
| [`zz_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/zz_inject_T_d15_pd7_p0.001.stim) | 798 k | 67.9 M | 85x | unsupported | – | 1 |
| **[2406.17653](https://arxiv.org/abs/2406.17653)** Zhou et al. (2024), *Low-Overhead Transversal Fault Tolerance for Universal Quantum Computation* | | | | | | |
| [`s_injection_T_d3_p0.001_pinj0.1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2406.17653_transversal_algorithmic_ft/stim/s_injection_T_d3_p0.001_pinj0.1.stim) | 52 M | 6.7 B | 129x | 1.74 B | 33x | 1 |
| [`s_injection_T_d5_p0.001_pinj0.1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2406.17653_transversal_algorithmic_ft/stim/s_injection_T_d5_p0.001_pinj0.1.stim) | 44.4 M | 3.36 B | 76x | 1.38 B | 31x | 1 |
| [`s_injection_T_d7_p0.001_pinj0.1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2406.17653_transversal_algorithmic_ft/stim/s_injection_T_d7_p0.001_pinj0.1.stim) | 37 M | 1.95 B | 53x | 708 M | 19x | 1 |
| [`s_injection_T_d9_p0.001_pinj0.1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2406.17653_transversal_algorithmic_ft/stim/s_injection_T_d9_p0.001_pinj0.1.stim) | 30.1 M | 1.24 B | 41x | 479 M | 16x | 1 |
| **[2409.07707](https://arxiv.org/abs/2409.07707)** Lee et al. (2024), *Low-overhead magic state distillation with color codes* | | | | | | |
| [`cult_growing_T_d3_to_d11_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d3_to_d11_p0.001.stim) | 3.16 M | 425 M | 134x | 119 M | 38x | 4 |
| [`cult_growing_T_d3_to_d7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d3_to_d7_p0.001.stim) | 9.65 M | 1.55 B | 161x | 470 M | 49x | 4 |
| [`cult_growing_T_d5_to_d13_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d5_to_d13_p0.001.stim) | 662 k | 245 M | 370x | 64.5 M | 97x | 6 |
| [`cult_growing_T_d5_to_d9_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d5_to_d9_p0.001.stim) | 890 k | 673 M | 756x | 128 M | 143x | 6 |
| **[2409.17595](https://arxiv.org/abs/2409.17595)** Gidney et al. (2024), *Magic state cultivation: growing T states as cheap as CNOT gates* | | | | | | |
| [`end2end_d3_dsurface15_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.17595_magic_state_cultivation/stim/end2end_d3_dsurface15_p0.001.stim) | 1.39 M | 198 M | 142x | 67.3 M | 48x | 4 |
| [`end2end_d5_dsurface15_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.17595_magic_state_cultivation/stim/end2end_d5_dsurface15_p0.001.stim) | 539 k | 155 M | 288x | 43.9 M | 81x | 6 |
| [`inject_cultivate_d3_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.17595_magic_state_cultivation/stim/inject_cultivate_d3_p0.001.stim) | 29.4 M | 13.4 B | 456x | 1.33 B | 45x | 4 |
| [`inject_cultivate_d5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.17595_magic_state_cultivation/stim/inject_cultivate_d5_p0.001.stim) | 1.26 M | 1.4 B | 1115x | 166 M | 132x | 6 |
| **[2502.01743](https://arxiv.org/abs/2502.01743)** Vaknin et al. (2025), *Efficient Magic State Cultivation on the Surface Code* | | | | | | |
| [`expanded-rotated-init-x-injection-double-HXY_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-rotated-init-x-injection-double-HXY_d1=3_d2=11_p=0.001.stim) | 2.04 M | 209 M | 103x | 34.7 M | 17x | 8 |
| [`expanded-rotated-injection-double-ghz-HXY_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-rotated-injection-double-ghz-HXY_d1=3_d2=11_p=0.001.stim) | 1.93 M | 252 M | 131x | 36.5 M | 19x | 8 |
| [`expanded-rotated-injection-syndrome-double-ghz-HXY_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-rotated-injection-syndrome-double-ghz-HXY_d1=3_d2=11_p=0.001.stim) | 1.83 M | 252 M | 138x | 36.4 M | 20x | 8 |
| [`expanded-unrotated_H_injection-ghz_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-unrotated_H_injection-ghz_d1=3_d2=11_p=0.001.stim) | 105 k | 57.1 M | 542x | 7.02 M | 67x | 9 |
| [`expanded-unrotated_H_injection-syndrome-ghz_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-unrotated_H_injection-syndrome-ghz_d1=3_d2=11_p=0.001.stim) | 95.3 k | 57 M | 598x | 7.01 M | 74x | 9 |
| [`rotated-init-x-injection-double-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-init-x-injection-double-HXY_d1=3_p=0.001.stim) | 4.52 M | 327 M | 72x | 52.6 M | 12x | 8 |
| [`rotated-init-x-injection-syndrome-double-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-init-x-injection-syndrome-double-ghz-HXY_d1=3_p=0.001.stim) | 4.02 M | 329 M | 82x | 52.1 M | 13x | 8 |
| [`rotated-injection-double-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-injection-double-ghz-HXY_d1=3_p=0.001.stim) | 4.17 M | 332 M | 80x | 52.5 M | 13x | 8 |
| [`rotated-injection-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-injection-ghz-HXY_d1=3_p=0.001.stim) | 7.63 M | 1 B | 131x | 184 M | 24x | 6 |
| [`rotated-injection-syndrome-double-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-injection-syndrome-double-ghz-HXY_d1=3_p=0.001.stim) | 3.78 M | 332 M | 88x | 52.3 M | 14x | 8 |
| [`unrotated_HXY_injection-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_HXY_injection-ghz_d1=3_p=0.001.stim) | 5.9 M | 738 M | 125x | 110 M | 19x | 7 |
| [`unrotated_HXY_injection-syndrome-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_HXY_injection-syndrome-ghz_d1=3_p=0.001.stim) | 5.11 M | 733 M | 143x | 109 M | 21x | 7 |
| [`unrotated_H_injection-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_H_injection-ghz_d1=3_p=0.001.stim) | 205 k | 105 M | 511x | 14.6 M | 71x | 9 |
| [`unrotated_H_injection-syndrome-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_H_injection-syndrome-ghz_d1=3_p=0.001.stim) | 172 k | 105 M | 608x | 14.5 M | 84x | 9 |
| **[2503.18657](https://arxiv.org/abs/2503.18657)** Chen et al. (2025), *Efficient Magic State Cultivation on RP²* | | | | | | |
| [`rp_3_T_cult`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_T_cult.stim) | 13.3 M | 8.42 B | 632x | 843 M | 63x | 4 |
| [`rp_3_rp_5_T_cult`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_rp_5_T_cult.stim) | 15.6 k | 44 M | 2815x | 6.81 M | 436x | 10 |
| [`rp_3_rp_5_sc_11_end2end_6_full_rds`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_rp_5_sc_11_end2end_6_full_rds.stim) | 24.1 k | 94.5 M | 3921x | 11.2 M | 467x | 9 |
| [`rp_3_sc_7_end2end_4_full_rds`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_sc_7_end2end_4_full_rds.stim) | 9.72 M | 1.7 B | 175x | 435 M | 45x | 4 |
| **[2504.02935](https://arxiv.org/abs/2504.02935)** Jacoby et al. (2025), *Magic State Injection with Erasure Qubits* | | | | | | |
| [`hook_inject_T_d3_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2504.02935_erasure_injection/stim/hook_inject_T_d3_p0.001.stim) | 81.6 M | 17.9 B | 219x | 2.47 B | 30x | 1 |
| [`inject_cultivate_T_d3_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2504.02935_erasure_injection/stim/inject_cultivate_T_d3_p0.001.stim) | 33 M | 16.7 B | 508x | 1.62 B | 49x | 4 |
| **[2505.13587](https://arxiv.org/abs/2505.13587)** Cain et al. (2025), *Fast correlated decoding of transversal logical algorithms* | | | | | | |
| [`distillation_15to1_T_d13_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d13_p0.001.stim) | 211 k | unsupported | – | unsupported | – | 4 |
| [`distillation_15to1_T_d17_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d17_p0.001.stim) | 106 k‡ | OOM | – | – | – | 4‡ |
| [`distillation_15to1_T_d21_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d21_p0.001.stim) | 54.1 k‡ | OOM | – | – | – | 4‡ |
| [`distillation_15to1_T_d25_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d25_p0.001.stim) | 43.2 k‡ | OOM | – | – | – | 4‡ |
| [`distillation_15to1_T_d5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d5_p0.001.stim) | 1.74 M | 95.6 M | 55x | unsupported | – | 4 |
| [`distillation_15to1_T_d9_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d9_p0.001.stim) | 484 k | unsupported | – | unsupported | – | 4 |
| **[2507.12511](https://arxiv.org/abs/2507.12511)** Ruiz et al. (2025), *Unfolded distillation: very low-cost magic state preparation for biased-noise qubits* | | | | | | |
| [`unfolded_repetition_no_preselection_pz1e-3_rounds2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_repetition_no_preselection_pz1e-3_rounds2.stim) | 33.6 M | 8.95 B | 267x | 1.41 B | 42x | 4 |
| [`unfolded_repetition_no_preselection_pz1e-3_rounds4`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_repetition_no_preselection_pz1e-3_rounds4.stim) | 21.3 M | 4.13 B | 194x | 1.05 B | 49x | 4 |
| [`unfolded_repetition_no_preselection_pz1e-3_rounds6`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_repetition_no_preselection_pz1e-3_rounds6.stim) | 16.2 M | 2.7 B | 166x | 794 M | 49x | 4 |
| [`unfolded_surface_no_bitflip_pz1e-3_rounds2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_surface_no_bitflip_pz1e-3_rounds2.stim) | 21.3 M | 3.17 B | 149x | 849 M | 40x | 4 |
| [`unfolded_surface_no_bitflip_pz1e-3_rounds4`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_surface_no_bitflip_pz1e-3_rounds4.stim) | 13.7 M | 1.65 B | 120x | 511 M | 37x | 4 |
| [`unfolded_surface_no_bitflip_pz1e-3_rounds6`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_surface_no_bitflip_pz1e-3_rounds6.stim) | 10.1 M | 1.12 B | 111x | 348 M | 34x | 4 |
| **[2509.05212](https://arxiv.org/abs/2509.05212)** Sahay et al. (2025), *Fold-transversal surface code cultivation* | | | | | | |
| [`fold-d3_native_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.05212_fold_transversal_cultivation/stim/fold-d3_native_T_p0.001.stim) | 16.5 M | 1.33 B | 81x | 182 M | 11x | 6 |
| [`fold-d5_native_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.05212_fold_transversal_cultivation/stim/fold-d5_native_T_p0.001.stim) | 90.2 k | 82 M | 910x | 13.6 M | 151x | 8 |
| **[2509.08658](https://arxiv.org/abs/2509.08658)** Wan et al. (2025), *Simulating magic state cultivation with few Clifford terms* | | | | | | |
| [`d3_cultivation_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.08658_few_clifford_terms/stim/d3_cultivation_T_p0.001.stim) | 30.8 M | 10.7 B | 347x | 1.5 B | 49x | 4 |
| **[2509.18294](https://arxiv.org/abs/2509.18294)** Ismail et al. (2025), *Transversal architecture for megaquop-scale quantum simulation with neutral atoms (transversal STAR)* | | | | | | |
| [`star_d=11`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=11.stim) | 2.92 M | 242 M | 83x | 91.3 M | 31x | 2 |
| [`star_d=13`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=13.stim) | 1.81 M | 144 M | 79x | 49.7 M | 27x | 2 |
| [`star_d=15`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=15.stim) | 1.18 M | 100 M | 85x | unsupported | – | 2 |
| [`star_d=3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=3.stim) | 37.7 M | 6.72 B | 178x | 1.8 B | 48x | 2 |
| [`star_d=5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=5.stim) | 17.2 M | 1.94 B | 113x | 617 M | 36x | 2 |
| [`star_d=7`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=7.stim) | 9.02 M | 817 M | 91x | 281 M | 31x | 2 |
| [`star_d=9`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=9.stim) | 4.99 M | 419 M | 84x | 149 M | 30x | 2 |
| **[2510.07269](https://arxiv.org/abs/2510.07269)** Li et al. (2025), *Transversal dimension jump for product qLDPC codes* | | | | | | |
| [`blp_27_3_3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/blp_27_3_3.stim) | – | – | – | – | – | 26 |
| [`toric_375_3_5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/toric_375_3_5.stim) | – | – | – | – | – | 186 (refused, limit 30) |
| [`toric_81_3_3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/toric_81_3_3.stim) | – | – | – | – | – | 63 (refused, limit 30) |
| [`tricycle_12_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_12_3_2.stim) | – | – | – | – | – | 16 |
| [`tricycle_15_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_15_3_2.stim) | – | – | – | – | – | 16 |
| [`tricycle_18_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_18_3_2.stim) | – | – | – | – | – | 20 |
| [`tricycle_21_3_3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_21_3_3.stim) | – | – | – | – | – | 23 |
| [`tricycle_24_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_24_3_2.stim) | – | – | – | – | – | 20 |
| [`tricycle_27_3_3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_27_3_3.stim) | – | – | – | – | – | 24 |
| [`tricycle_6_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_6_3_2.stim) | 2.3 M | 138 M | 60x | 13.4 M | 5.8x | 9 |
| [`tricycle_9_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_9_3_2.stim) | 116 k | 19.1 M | 165x | 443 k | 3.8x | 11 |
| **[2510.24615](https://arxiv.org/abs/2510.24615)** Hirano et al. (2025), *Efficient magic state cultivation with lattice surgery* | | | | | | |
| [`inject-check-3_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.24615_lattice_surgery_cultivation/stim/inject-check-3_T.stim) | 32.7 M | 14.2 B | 435x | 1.53 B | 47x | 4 |
| [`lattice-surgery-complementary-gap-3-to-5-to-7_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.24615_lattice_surgery_cultivation/stim/lattice-surgery-complementary-gap-3-to-5-to-7_T.stim) | 16.5 M | 2.46 B | 149x | 721 M | 44x | 4 |
| **[2512.13908](https://arxiv.org/abs/2512.13908)** Rosenfeld et al. (2025), *Magic state cultivation on a superconducting quantum processor* | | | | | | |
| [`fig2_cultivation_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_cultivation_stim_X_T.stim) | 97.7 M | 26.7 B | 273x | 2.93 B | 30x | 4 |
| [`fig2_cultivation_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_cultivation_stim_Z_T.stim) | 97.7 M | 26.5 B | 272x | 2.92 B | 30x | 4 |
| [`fig2_injection_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_injection_stim_X_T.stim) | 98 M | 36.9 B | 377x | 3.15 B | 32x | 1 |
| [`fig2_injection_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_injection_stim_Z_T.stim) | 97.9 M | 36.9 B | 377x | 3.17 B | 32x | 1 |
| [`fig2_simulation_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_simulation_stim_X_T.stim) | 97.7 M | 26.7 B | 273x | 2.92 B | 30x | 4 |
| [`fig2_simulation_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_simulation_stim_Z_T.stim) | 97.8 M | 26.4 B | 270x | 2.93 B | 30x | 4 |
| [`fig3_injection_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_injection_stim_T.stim) | 97.5 M | 13.2 B | 135x | 1.76 B | 18x | 4 |
| [`fig3_simulation_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_simulation_stim_T.stim) | 97.2 M | 7.55 B | 78x | 1.18 B | 12x | 4 |
| [`fig3_simulation_zoom_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_simulation_zoom_stim_T.stim) | 97 M | 7.55 B | 78x | 1.18 B | 12x | 4 |
| [`fig3_with_idle_rounds_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_with_idle_rounds_stim_T.stim) | 97 M | 7.55 B | 78x | 1.19 B | 12x | 4 |
| [`fig3_with_idle_rounds_zoom_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_with_idle_rounds_zoom_stim_T.stim) | 97.2 M | 7.55 B | 78x | 1.18 B | 12x | 4 |
| [`fig3_without_idle_rounds_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_without_idle_rounds_stim_T.stim) | 97.7 M | 13.1 B | 134x | 2.18 B | 22x | 4 |
| [`fig4_cultivation_N2_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N2_stim_X_T.stim) | 89.7 M | 5.83 B | 65x | 1.91 B | 21x | 4 |
| [`fig4_cultivation_N2_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N2_stim_Z_T.stim) | 89.6 M | 5.83 B | 65x | 1.9 B | 21x | 4 |
| [`fig4_cultivation_N3_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N3_stim_X_T.stim) | 89.7 M | 4.33 B | 48x | 1.7 B | 19x | 4 |
| [`fig4_cultivation_N3_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N3_stim_Z_T.stim) | 89.2 M | 4.34 B | 49x | 1.67 B | 19x | 4 |
| [`fig4_injection_N2_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_injection_N2_stim_X_T.stim) | 97.9 M | 6.53 B | 67x | 1.92 B | 20x | 1 |
| [`fig4_injection_N2_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_injection_N2_stim_Z_T.stim) | 93.3 M | 6.53 B | 70x | 2.03 B | 22x | 1 |
| [`fig4_simulation_injection_N2_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_simulation_injection_N2_stim_X_T.stim) | 98 M | 6.54 B | 67x | 2.06 B | 21x | 1 |
| [`fig4_simulation_injection_N2_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_simulation_injection_N2_stim_Z_T.stim) | 98 M | 6.51 B | 66x | 2.03 B | 21x | 1 |
| **[2512.23037](https://arxiv.org/abs/2512.23037)** Li et al. (2025), *SOFT: a high-performance simulator for universal fault-tolerant quantum circuits* | | | | | | |
| [`circuit_d3_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.23037_soft/stim/circuit_d3_p0.001.stim) | 29.4 M | 13.4 B | 457x | 1.33 B | 45x | 4 |
| [`circuit_d5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.23037_soft/stim/circuit_d5_p0.001.stim) | 270 k | 1.74 B | 6431x | 204 M | 754x | 6 |
| **[2603.05429](https://arxiv.org/abs/2603.05429)** Hetényi et al. (2026), *Constant-depth magic state cultivation with Clifford measurements by gauging* | | | | | | |
| [`gauging_cultivation_d3_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2603.05429_gauging_clifford_cultivation/stim/gauging_cultivation_d3_T_p0.001.stim) | 13.6 M | 7.65 B | 562x | 900 M | 66x | 4 |
| [`gauging_cultivation_d5_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2603.05429_gauging_clifford_cultivation/stim/gauging_cultivation_d5_T_p0.001.stim) | 204 k | 504 M | 2472x | 72.3 M | 354x | 6 |
| [`gauging_cultivation_d7_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2603.05429_gauging_clifford_cultivation/stim/gauging_cultivation_d7_T_p0.001.stim) | 14.1 k | 55.4 M | 3935x | 7.2 M | 511x | 8 |
| **[2604.01059](https://arxiv.org/abs/2604.01059)** Haenel et al. (2026), *Tsim: Fast Universal Simulator for Quantum Error Correction* | | | | | | |
| [`distillation_color_d5_X`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_color_d5_X.stim) | 16.8 M | 8.93 B | 531x | 1.22 B | 73x | 4 |
| [`distillation_color_d5_Y`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_color_d5_Y.stim) | 17 M | 8.78 B | 516x | 1.34 B | 79x | 3 |
| [`distillation_color_d5_Z`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_color_d5_Z.stim) | 14.5 M | 8.95 B | 617x | 1.16 B | 80x | 3 |
| [`distillation_steane_d3_X`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_steane_d3_X.stim) | 27.1 M | 16.3 B | 602x | 1.66 B | 61x | 4 |
| [`distillation_steane_d3_Y`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_steane_d3_Y.stim) | 27.1 M | 18 B | 663x | 1.75 B | 64x | 3 |
| [`distillation_steane_d3_Z`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_steane_d3_Z.stim) | 22.1 M | 15.5 B | 702x | 1.52 B | 69x | 3 |
| [`distillation_unencoded_X`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_unencoded_X.stim) | 42.7 M | 17.6 B | 412x | 1.88 B | 44x | 4 |
| [`distillation_unencoded_Y`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_unencoded_Y.stim) | 42.8 M | 20.2 B | 472x | 2.03 B | 48x | 3 |
| [`distillation_unencoded_Z`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_unencoded_Z.stim) | 34.2 M | 16.7 B | 489x | 1.7 B | 50x | 3 |
| **[2604.05126](https://arxiv.org/abs/2604.05126)** Liu et al. (2026), *In-Situ Simultaneous Magic State Injection on Arbitrary CSS qLDPC Codes* | | | | | | |
| [`bb144_cfg328_inj5_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg328_inj5_T_p0.001.stim) | 6 M | 923 M | 154x | 304 M | 51x | 1 |
| [`bb144_cfg342_inj3_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg342_inj3_T_p0.001.stim) | 6.82 M | 892 M | 131x | 310 M | 46x | 1 |
| [`bb144_cfg369_inj1_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg369_inj1_T_p0.001.stim) | 7.9 M | 925 M | 117x | 314 M | 40x | 1 |
| [`bb144_cfg422_inj2_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg422_inj2_T_p0.001.stim) | 7.28 M | 912 M | 125x | 280 M | 38x | 1 |
| [`bb144_cfg491_inj4_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg491_inj4_T_p0.001.stim) | 6.39 M | 924 M | 145x | 303 M | 47x | 1 |
| [`bb144_cfg88_inj6_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg88_inj6_T_p0.001.stim) | 5.71 M | 947 M | 166x | 306 M | 54x | 1 |
| **[2604.27058](https://arxiv.org/abs/2604.27058)** Chase and Labib (2026), *Clifft: Fast Exact Simulation of Near-Clifford Quantum Circuits* | | | | | | |
| [`coherent_d3_r1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/coherent_d3_r1.stim) | 1.27 B | 23.4 B | 18x | 3.77 B | 3.0x | 0 |
| [`coherent_d3_r3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/coherent_d3_r3.stim) | 20.8 M | 10.3 B | 494x | 877 M | 42x | 4 |
| [`coherent_d5_r1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/coherent_d5_r1.stim) | 630 M | 12.9 B | 20x | 3.18 B | 5.0x | 0 |
| [`coherent_d5_r5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/coherent_d5_r5.stim) | 1.82 k | 2.53 M | 1390x | 455 k | 250x | 11 |
| [`cultivation_d3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/cultivation_d3.stim) | 29.4 M | 13.4 B | 455x | 1.33 B | 45x | 4 |
| [`cultivation_d5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/cultivation_d5.stim) | 1.21 M | 1.4 B | 1164x | 166 M | 137x | 6 |
| [`distillation`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/distillation.stim) | 14.5 M | 8.93 B | 616x | 1.18 B | 81x | 3 |
| [`surface_d7_r7`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/surface_d7_r7.stim) | 18.5 M | 1.27 B | 69x | 545 M | 29x | 0 |
| **[2607.28600](https://arxiv.org/abs/2607.28600)** Fang et al. (2026), *SymFT: Universal Fault-Tolerant Quantum Circuit Simulation via Symbolic Clifford–Pauli Frames and Stabilizer Coordinates* | | | | | | |
| [`MSC_circuit_d7_p0.0005`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/MSC_circuit_d7_p0.0005.stim) | 35.4 k | 240 M | 6789x | 31.7 M | 896x | 8 |
| [`coherent_surface_d3_r1_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/coherent_surface_d3_r1_p1e-3_rz0p02.stim) | 1.28 B | 25.1 B | 20x | 3.76 B | 2.9x | 0 |
| [`coherent_surface_d3_r3_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/coherent_surface_d3_r3_p1e-3_rz0p02.stim) | 20.9 M | 9.84 B | 472x | 891 M | 43x | 4 |
| [`coherent_surface_d5_r1_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/coherent_surface_d5_r1_p1e-3_rz0p02.stim) | 627 M | 13.1 B | 21x | 3.1 B | 4.9x | 0 |
| [`coherent_surface_d5_r5_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/coherent_surface_d5_r5_p1e-3_rz0p02.stim) | 1.82 k | 2.53 M | 1390x | 455 k | 250x | 11 |
| [`distillation`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/distillation.stim) | 14.2 M | 8.76 B | 616x | 1.21 B | 85x | 3 |
| [`msc_d3_inject_cultivate_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/msc_d3_inject_cultivate_p1e-3.stim) | 29.4 M | 13.4 B | 455x | 1.32 B | 45x | 4 |
| [`msc_d5_inject_cultivate_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/msc_d5_inject_cultivate_p1e-3.stim) | 1.23 M | 1.4 B | 1142x | 166 M | 135x | 6 |
| [`msc_proxy_d7_unverified_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/msc_proxy_d7_unverified_p1e-3.stim) | 466 k | 1.09 B | 2335x | 134 M | 288x | 6 |
| [`pure_surface_d7_r7_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/pure_surface_d7_r7_p1e-3.stim) | 18.5 M | 1.27 B | 68x | 558 M | 30x | 0 |
| [`pure_surface_d9_r9_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/pure_surface_d9_r9_p1e-3.stim) | 8.38 M | 602 M | 72x | 267 M | 32x | 0 |
| **[2609.17706](https://arxiv.org/abs/2609.17706)** Chan et al. (2026), *Diagnosing and Restoring the Degraded Fault Distance of Magic State Cultivation* | | | | | | |
| [`d3a6_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d3a6_inject_cultivate_T_p0.001.stim) | 29.4 M | 13.7 B | 467x | 1.31 B | 44x | 4 |
| [`d3a6f2_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d3a6f2_inject_cultivate_T_p0.001.stim) | 27.3 M | 13.6 B | 500x | 1.31 B | 48x | 4 |
| [`d5a19_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19_inject_cultivate_T_p0.001.stim) | 1.04 M | 1.13 B | 1080x | 146 M | 140x | 6 |
| [`d5a19f13_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19f13_inject_cultivate_T_p0.001.stim) | 952 k | 1.12 B | 1177x | 128 M | 135x | 6 |
| [`d5a19r4_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19r4_inject_cultivate_T_p0.001.stim) | 966 k | 1.13 B | 1165x | 143 M | 148x | 6 |
| [`d5a19r4f13_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19r4f13_inject_cultivate_T_p0.001.stim) | 876 k | 1.1 B | 1257x | 138 M | 157x | 6 |
| **[2609.18922](https://arxiv.org/abs/2609.18922)** Wan and Zapirain (2026), *Exact logical error rates for magic state cultivation* | | | | | | |
| [`clifft_d3_p001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.18922_exact_ler_cultivation/stim/clifft_d3_p001.stim) | 29.5 M | 13.5 B | 458x | 1.29 B | 44x | 4 |
| [`soft_cultivation_d5_p0005`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.18922_exact_ler_cultivation/stim/soft_cultivation_d5_p0005.stim) | 140 k | 1.5 B | 10733x | 170 M | 1215x | 6 |
| **[2610.03869](https://arxiv.org/abs/2610.03869)** Lange et al. (2026), *Modular Neural Decoder for Surface Code Memory and Logic on Superconducting Processors* | | | | | | |
| [`stability_d3_X_t100_alpha0.5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t100_alpha0.5_p0.001.stim) | 53.2 k | 283 M | 5322x | 12.9 M | 243x | 3 |
| [`stability_d3_X_t20_alpha0.15_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t20_alpha0.15_p0.001.stim) | 1.67 M | 1.56 B | 929x | 105 M | 62x | 3 |
| [`stability_d3_X_t20_alpha0.5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t20_alpha0.5_p0.001.stim) | 373 k | 1.5 B | 4032x | 104 M | 278x | 3 |
| [`stability_d3_X_t20_alpha1.0_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t20_alpha1.0_p0.001.stim) | 200 k | 974 M | 4880x | 81.5 M | 409x | 3 |
| **[2610.06811](https://arxiv.org/abs/2610.06811)** Cercelescu et al. (2026), *Polynomial-time simulation of non-Clifford quantum error correction (Merlin)* | | | | | | |
| [`code_switching_bt27_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/code_switching_bt27_p0.001.stim) | – | – | – | – | – | 26 |
| [`code_switching_bt81_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/code_switching_bt81_p0.001.stim) | – | – | – | – | – | 63 (refused, limit 30) |
| [`cultivation_d3_t`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/cultivation_d3_t.stim) | 29.4 M | 13.4 B | 458x | 1.3 B | 44x | 4 |
| [`cultivation_d5_t`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/cultivation_d5_t.stim) | 1.23 M | 1.4 B | 1140x | 164 M | 134x | 6 |
| [`distillation_15to1_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_15to1_p0.001.stim) | 117 M | 25.9 B | 222x | 2.77 B | 24x | 4 |
| [`distillation_bh10_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh10_p0.001.stim) | 111 M | 10.4 B | 94x | 1.04 B | 9.4x | 4 |
| [`distillation_bh12_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh12_p0.001.stim) | 71.7 M | 6.09 B | 85x | 668 M | 9.3x | 4 |
| [`distillation_bh14_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh14_p0.001.stim) | 108 M | 7.52 B | 70x | 723 M | 6.7x | 4 |
| [`distillation_bh16_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh16_p0.001.stim) | 71.3 M | 5.09 B | 71x | 531 M | 7.4x | 4 |
| [`distillation_bh18_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh18_p0.001.stim) | 105 M | 6.58 B | 62x | 571 M | 5.4x | 4 |
| [`distillation_bh2_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh2_p0.001.stim) | 117 M | 25.8 B | 221x | 2.77 B | 24x | 4 |
| [`distillation_bh4_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh4_p0.001.stim) | 74.9 M | 13.9 B | 186x | 1.41 B | 19x | 4 |
| [`distillation_bh6_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh6_p0.001.stim) | 114 M | 13.1 B | 115x | 1.6 B | 14x | 4 |
| [`distillation_bh8_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh8_p0.001.stim) | 74.2 M | 9.23 B | 124x | 921 M | 12x | 4 |
| **[2610.06828](https://arxiv.org/abs/2610.06828)** Mehta et al. (2026), *The practical cost of magic state cultivation* | | | | | | |
| [`color_code_cultivation_f3_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06828_practical_cost_cultivation/stim/color_code_cultivation_f3_T.stim) | 1.39 M | 199 M | 143x | 64.1 M | 46x | 4 |
| [`color_code_cultivation_f5_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06828_practical_cost_cultivation/stim/color_code_cultivation_f5_T.stim) | 540 k | 154 M | 286x | 43.3 M | 80x | 6 |
| **[2610.22315](https://arxiv.org/abs/2610.22315)** Wang and Gu (2026), *Magna: simulating magic state factories as cheaply as Clifford circuits* | | | | | | |
| [`bh10-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh10-S.stim) | 1.22 B | 48.3 B | 40x | 4.2 B | 3.4x | 0 |
| [`bh10-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh10-T.stim) | 30.1 M | 17.5 B | 583x | 1.98 B | 66x | 3 |
| [`bh100-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh100-S.stim) | 292 M | 47.8 B | 164x | 4.2 B | 14x | 0 |
| [`bh100-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh100-T.stim) | 310 k | 1.66 B | 5376x | 324 M | 1045x | 3 |
| [`bh2-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh2-S.stim) | 1.77 B | 47.8 B | 27x | 4.2 B | 2.4x | 0 |
| [`bh2-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh2-T.stim) | 80.5 M | 29.5 B | 366x | 2.98 B | 37x | 3 |
| [`bh20-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh20-S.stim) | 884 M | 47.9 B | 54x | 4.18 B | 4.7x | 0 |
| [`bh20-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh20-T.stim) | 1.54 M | 11.1 B | 7178x | 1.25 B | 813x | 3 |
| [`bh4-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh4-S.stim) | 1.6 B | 47.7 B | 30x | 4.2 B | 2.6x | 0 |
| [`bh4-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh4-T.stim) | 60.8 M | 26.1 B | 430x | 2.67 B | 44x | 3 |
| [`bh40-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh40-S.stim) | 576 M | 47.8 B | 83x | 4.17 B | 7.2x | 0 |
| [`bh40-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh40-T.stim) | 805 k | 5.94 B | 7373x | 750 M | 931x | 3 |
| [`bh6-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh6-S.stim) | 1.44 B | 47.7 B | 33x | 4.22 B | 2.9x | 0 |
| [`bh6-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh6-T.stim) | 48.6 M | 23 B | 474x | 2.39 B | 49x | 3 |
| [`bh60-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh60-S.stim) | 431 M | 47.6 B | 111x | 4.19 B | 9.7x | 0 |
| [`bh60-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh60-T.stim) | 548 k | 3.66 B | 6676x | 523 M | 955x | 3 |
| [`bh80-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh80-S.stim) | 346 M | 47.5 B | 137x | 4.18 B | 12x | 0 |
| [`bh80-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh80-T.stim) | 384 k | 2.85 B | 7432x | 399 M | 1039x | 3 |
| [`color3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/color3.stim) | 33.3 M | 16 B | 480x | 1.58 B | 47x | 4 |
| [`color5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/color5.stim) | 271 k | 1.72 B | 6368x | 201 M | 743x | 6 |
| [`dk`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/dk.stim) | 41.6 M | 16.9 B | 406x | 1.97 B | 47x | 4 |
| [`rp2-d3-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/rp2-d3-S.stim) | 36.9 M | 8.04 B | 218x | 2.33 B | 63x | 0 |
| [`rp2-d3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/rp2-d3.stim) | 14.7 M | 8.41 B | 572x | 941 M | 64x | 4 |
| [`rp2-d5-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/rp2-d5-S.stim) | 15.6 M | 2.99 B | 192x | 1.08 B | 70x | 0 |
| [`rp2-d5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/rp2-d5.stim) | 69.2 k | 126 M | 1825x | 18.8 M | 272x | 9 |
| [`wg-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/wg-S.stim) | 79.3 M | 4.23 B | 53x | 1.85 B | 23x | 0 |
| [`wg-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/wg-T.stim) | 8.28 M | 4.21 B | 509x | 831 M | 100x | 4 |
<!-- benchmark-table:end -->

## Layout

    papers/<arxiv-id>_<name>/
        README.md          where the circuits are, what was done, k_max table
        tex/               arXiv source (.tex/.bib/.bbl/.cls; figures and other binaries removed)
        stim_src/          the authors' released circuits and/or generator code (subset, with commit/DOI)
        make_circuits.py   writes stim/ (conversion to real non-Clifford gates + noiseless Tsim checks)
        stim/              the non-Clifford circuits that were measured
        k_max.json         raw measurements (tools/measure_k.py)
    tools/
        measure_k.py       k_max in Tsim and Clifft (each in a child process with a timeout)
        validate.py        noiseless Tsim checks (deterministic detectors, agreement with the Clifford proxy)
        gates.py           CS, CS_DAG, CH, CSWAP, controlled-(S X) decompositions into T/CX/H/CCX, verified against unitaries
        stimtext.py        clean-ups for Clifft (target-less lines, tags)
        remote_zip.py      extract single files from remote zips with HTTP range requests (multi-GB Zenodo archives)
        fetch_arxiv.sh     download and unpack an arXiv source, list code/data links
        arxiv_meta.py      title/authors/year from the arXiv API
        ktable.py, summary.py
    _search/               brief, the 20 GPT-6.1 Terra scout reports, merged candidate list

Run `uv sync` once. Then `uv run python papers/<folder>/make_circuits.py` and `uv run python tools/measure_k.py papers/<folder>/stim/*.stim`.
A few generators need the authors' own environment; the folder README says when.

## Papers not processed

| arXiv | paper | reason |
|---|---|---|
| 2505.23567 | Scalable decoding for fast transversal logic (Turner et al.) | Zenodo "T gate proxy" circuits are logical-level proxies with \|0⟩ inputs, no S feedforward and no H layers; real T gates need encoded \|T⟩ preparation and logical S corrections |
| 2608.23819 | CircLS (Zhang) | Lattice-surgery compilations with every magic state replaced by a logical \|+⟩ patch; real T gates need encoded \|T⟩ preparation and conditional logical S |
| 2412.14256 | Scaling and logic in the colour code (Google) | The Zenodo data has only X/Z memory circuits, no injection circuits |
| 2412.15187 | Measurement-free universal QC (Veroni et al.) | Stim files are Clifford concatenation cycles; the CCZ/universality part is Julia (SparseStates.jl) |
| 2412.15165 | Logical magic state distillation experiment (QuEra) | No released circuits; covered through the Tsim paper's reproduction in `papers/2604.01059_tsim` |
| 2404.07482 | Colour code decoder (Lee et al.) | Clifford memory circuits; the package's cultivation circuits are covered in `papers/2409.07707_color_code_msd` |
| 2412.01446 | Magic state injection on IBM processors | Code Ocean capsule with Qiskit code; no Stim circuit |
| 2506.20661 | Architectural mechanisms of a universal FTQC (Harvard/QuEra) | Coherent-error experiments are hardware schedules; no Stim circuits |
| 2403.13732 | Experimental fault-tolerant code switching | Qiskit circuits; would need a manual translation, including feedforward |
| 2601.10964 | Code-generic universal FTQC | The T protocol is in Cirq; Stim is used only for Clifford parts |
| 2604.02033, 2610.06730 | Non-Pauli codes / CSS codes with universal transversal gates | No Stim generator; reconstruction from the paper only |
| 2309.08663, 2608.09727, 2605.21867, 2403.03991 | [[8,3,2]] CCZ; binary-extension-field MSD; zero-level CCZ; zero-level distillation | No Stim circuits; reconstruction from figures or notebooks |
| 1905.06903 | Magic state distillation: not as costly as you think | Resource-count code only |
| 2303.04672, 2303.17380, 2509.23642 | Coherent errors (FLO); arbitrary-rotation preparation; multi-level injection | Fermionic-linear-optics or Julia simulations; no Stim circuits |
| 2412.01391 | Transversal Clifford gates on rotated surface codes | Logical S-gate memory benchmarks; not a magic-state circuit |
| 2402.17761, 2508.14200, 2408.11894 | FT state-preparation synthesis | Stabilizer-state preparation only |
| 2405.00146 | Burst errors in magic state factories | Clifford lattice-surgery memory |
| tqec | tqec package | Clifford block-graph compiler; no non-Clifford resource |

## Simulator observations

- **Width comparison:** across the 180 circuits measured by both simulators (Tsim 1.0.0, Clifft 0.13.0 with `ActiveWidthSchedulePass`), Tsim's k is
  smaller on 60, equal on 110, and larger on 10.
  - Tsim much smaller: Bravyi–Haah distillation with T teleportation (Magna) stays at k=3 for every size, while Clifft grows to 42 and
    overflows from bh60 on. Fold-transversal d=5 gives 8 vs 22, gauging d=7 8 vs 19, and RP² d=5 10 vs 18.
  - Tsim larger: the 10 circuits are Merlin's "clean" distillation workloads (Tsim 4, Clifft 0). The intermediate states are non-stabilizer,
    but the only noise is Z after the T_DAG gates and the ideal output is undone before readout. By triorthogonality the whole circuit is then
    Clifford as an operator, and Clifft's `PhasePolynomialPass` cancels every T gate. Switching off either ingredient brings Clifft back to
    k ≥ 1 (variant table in `papers/2610.06811_merlin/README.md`).
  - Not measured by both:
    - Clifft overflows on Magna bh60/80/100 (Tsim 3).
    - Tsim's `active_statevector` refuses Merlin's bt81 (it would need 63 active qubits, against a limit of 30; Clifft 52) and the
      3D toric tricycle factories: `toric_81_3_3`, where Tsim would need 63 and Clifft gets 59, and `toric_375_3_5`, where Tsim would
      need 186 and Clifft overflows.
    - The 2505.13587 distillation at d = 17, 21, 25 (18k–40k qubits):
      - **Tsim 1.0.0:** cannot compile it. A dense vertices × error-bits matrix exceeds the 40 GB cap (d = 25 asks for 121 GiB).
      - **Tsim with [PR #270](https://github.com/QuEraComputing/tsim/pull/270)**, which keeps that matrix sparse: compiles all three at
        k = 4, in 1.8–4.5 GB and 56–231 s. These cells are marked ‡.
      - **Clifft:** its compile takes more than 30 min. At d = 13 Tsim compiles in 28 s and Clifft in 22 min, both to k = 4.
  - `ActiveWidthSchedulePass` matters most on the STAR circuits, where it brings Clifft from k=d down to 2.

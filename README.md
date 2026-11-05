# Active width of published non-Clifford Stim circuits

A literature survey of papers that release Stim circuits with non-Clifford gates, or Clifford proxies that convert to real T/CCZ/CS
gates. For each one I measured the peak active width `k_max` that Tsim and Clifft reach on its circuits.

- **Tsim:** `QuEraComputing/tsim` main at `883d787`. `compile_detector_sampler()` with the default `active_statevector` strategy;
  k = largest statevector component width (compile only, no sampling).
- **Clifft 0.12.0:** `default_hir_pass_manager()` + `ActiveWidthSchedulePass()` with default settings; k = `peak_active_width`. The width
  without the scheduler is also recorded.

Results: [`SUMMARY.md`](SUMMARY.md), with a per-paper overview and a per-circuit table. Regenerate it with `uv run python tools/summary.py`.

## Throughput and k_max (Tsim 1.0.0, Tsim GPU draft, Clifft 0.13.0)

Produced by [`tools/benchmark.py`](tools/benchmark.py) (`uv run python tools/benchmark.py all`); raw data in
[`results/benchmark.json`](results/benchmark.json).

- **Tsim single-core CPU:** `bloqade-tsim==1.0.0`, run with `NUMBA_NUM_THREADS=1` and pinned with `taskset` to one physical core of a
  Ryzen 9 9900X; several circuits ran at once, on distinct cores.
- **Tsim GPU:** draft PR [#219](https://github.com/QuEraComputing/tsim/pull/219) (`cuda-statevector-executor` at `a2af975f`) on an
  RTX 5090.
- **What the rates measure:** detector sampler `sample(n, append_observables=True, bit_packed=True)`, with no postselection and every
  shot returned to the host. Compilation and the warm-up call are excluded, and each rate is the best of three calls of at least 1 s
  (CPU) or 0.5 s (GPU).
- **GPU copy limit:** GPU calls are capped at 2 GiB of output, so for circuits with many detectors the GPU rate is limited by the copy
  to the host.
- **Skipped (–):** circuits with Tsim k_max > 15 (CPU) or > 11 (GPU, the CUDA executor's limit).
- **GPU "error":** the four d=15 hook-injection circuits (6,577 output columns) fail with `CUDA_ERROR_INVALID_VALUE` in the draft's
  `gather_columns` kernel. Its static plus dynamic shared memory (about 26 + 26 KB per block of 32 shots) exceeds the 48 KB default,
  and unlike the noise kernel it has no size check.
- **k_max:** Tsim 1.0.0 `compile_detector_sampler()` (largest statevector component), and Clifft 0.13.0
  `default_hir_pass_manager()` + `ActiveWidthSchedulePass()` with default settings.

<!-- benchmark-table:begin -->
| arXiv / circuit | Tsim single-core CPU (shots/s) | Tsim GPU (shots/s) | Tsim k_max | Clifft k_max |
|---|---|---|---|---|
| [2302.12292](https://arxiv.org/abs/2302.12292) / [`hook_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2302.12292_hook_injection/stim/hook_inject_T_d15_pd5_p0.001.stim) | 1.12 M | 122 M | 1 | 1 |
| [2302.12292](https://arxiv.org/abs/2302.12292) / [`hook_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2302.12292_hook_injection/stim/hook_inject_T_d15_pd7_p0.001.stim) | 1.1 M | 119 M | 1 | 1 |
| [2302.12292](https://arxiv.org/abs/2302.12292) / [`li_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2302.12292_hook_injection/stim/li_inject_T_d15_pd5_p0.001.stim) | 401 k | error | 1 | 1 |
| [2302.12292](https://arxiv.org/abs/2302.12292) / [`li_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2302.12292_hook_injection/stim/li_inject_T_d15_pd7_p0.001.stim) | 400 k | error | 1 | 1 |
| [2302.12292](https://arxiv.org/abs/2302.12292) / [`pregrown_hook_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2302.12292_hook_injection/stim/pregrown_hook_inject_T_d15_pd5_p0.001.stim) | 999 k | 108 M | 1 | 1 |
| [2302.12292](https://arxiv.org/abs/2302.12292) / [`pregrown_hook_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2302.12292_hook_injection/stim/pregrown_hook_inject_T_d15_pd7_p0.001.stim) | 998 k | 108 M | 1 | 1 |
| [2302.12292](https://arxiv.org/abs/2302.12292) / [`zz_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2302.12292_hook_injection/stim/zz_inject_T_d15_pd5_p0.001.stim) | 444 k | error | 1 | 1 |
| [2302.12292](https://arxiv.org/abs/2302.12292) / [`zz_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2302.12292_hook_injection/stim/zz_inject_T_d15_pd7_p0.001.stim) | 429 k | error | 1 | 1 |
| [2409.07707](https://arxiv.org/abs/2409.07707) / [`cult_growing_T_d3_to_d11_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d3_to_d11_p0.001.stim) | 2.57 M | 425 M | 4 | 4 |
| [2409.07707](https://arxiv.org/abs/2409.07707) / [`cult_growing_T_d3_to_d7_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d3_to_d7_p0.001.stim) | 7.97 M | 1.55 B | 4 | 4 |
| [2409.07707](https://arxiv.org/abs/2409.07707) / [`cult_growing_T_d5_to_d13_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d5_to_d13_p0.001.stim) | 450 k | 245 M | 6 | 10 |
| [2409.07707](https://arxiv.org/abs/2409.07707) / [`cult_growing_T_d5_to_d9_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d5_to_d9_p0.001.stim) | 467 k | 673 M | 6 | 10 |
| [2409.17595](https://arxiv.org/abs/2409.17595) / [`end2end_d3_dsurface15_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2409.17595_magic_state_cultivation/stim/end2end_d3_dsurface15_p0.001.stim) | 1.24 M | 198 M | 4 | 4 |
| [2409.17595](https://arxiv.org/abs/2409.17595) / [`end2end_d5_dsurface15_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2409.17595_magic_state_cultivation/stim/end2end_d5_dsurface15_p0.001.stim) | 265 k | 155 M | 6 | 10 |
| [2409.17595](https://arxiv.org/abs/2409.17595) / [`inject_cultivate_d3_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2409.17595_magic_state_cultivation/stim/inject_cultivate_d3_p0.001.stim) | 27.6 M | 13.4 B | 4 | 4 |
| [2409.17595](https://arxiv.org/abs/2409.17595) / [`inject_cultivate_d5_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2409.17595_magic_state_cultivation/stim/inject_cultivate_d5_p0.001.stim) | 799 k | 1.4 B | 6 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`expanded-rotated-init-x-injection-double-HXY_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-rotated-init-x-injection-double-HXY_d1=3_d2=11_p=0.001.stim) | 1.68 M | 209 M | 8 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`expanded-rotated-injection-double-ghz-HXY_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-rotated-injection-double-ghz-HXY_d1=3_d2=11_p=0.001.stim) | 1.65 M | 252 M | 8 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`expanded-rotated-injection-syndrome-double-ghz-HXY_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-rotated-injection-syndrome-double-ghz-HXY_d1=3_d2=11_p=0.001.stim) | 1.29 M | 252 M | 8 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`expanded-unrotated_H_injection-ghz_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-unrotated_H_injection-ghz_d1=3_d2=11_p=0.001.stim) | 57.5 k | 57.1 M | 9 | 15 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`expanded-unrotated_H_injection-syndrome-ghz_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-unrotated_H_injection-syndrome-ghz_d1=3_d2=11_p=0.001.stim) | 53.1 k | 57 M | 9 | 15 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`rotated-init-x-injection-double-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-init-x-injection-double-HXY_d1=3_p=0.001.stim) | 3.86 M | 327 M | 8 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`rotated-init-x-injection-syndrome-double-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-init-x-injection-syndrome-double-ghz-HXY_d1=3_p=0.001.stim) | 3.16 M | 329 M | 8 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`rotated-injection-double-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-injection-double-ghz-HXY_d1=3_p=0.001.stim) | 3.5 M | 332 M | 8 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`rotated-injection-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-injection-ghz-HXY_d1=3_p=0.001.stim) | 6.82 M | 1 B | 6 | 8 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`rotated-injection-syndrome-double-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-injection-syndrome-double-ghz-HXY_d1=3_p=0.001.stim) | 3.2 M | 332 M | 8 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`unrotated_HXY_injection-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_HXY_injection-ghz_d1=3_p=0.001.stim) | 5.18 M | 738 M | 7 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`unrotated_HXY_injection-syndrome-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_HXY_injection-syndrome-ghz_d1=3_p=0.001.stim) | 4.38 M | 733 M | 7 | 10 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`unrotated_H_injection-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_H_injection-ghz_d1=3_p=0.001.stim) | 82.4 k | 105 M | 9 | 15 |
| [2502.01743](https://arxiv.org/abs/2502.01743) / [`unrotated_H_injection-syndrome-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_H_injection-syndrome-ghz_d1=3_p=0.001.stim) | 90.3 k | 105 M | 9 | 15 |
| [2503.18657](https://arxiv.org/abs/2503.18657) / [`rp_3_T_cult`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_T_cult.stim) | 11.7 M | 8.42 B | 4 | 8 |
| [2503.18657](https://arxiv.org/abs/2503.18657) / [`rp_3_rp_5_T_cult`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_rp_5_T_cult.stim) | 6.93 k | 44 M | 10 | 18 |
| [2503.18657](https://arxiv.org/abs/2503.18657) / [`rp_3_rp_5_sc_11_end2end_6_full_rds`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_rp_5_sc_11_end2end_6_full_rds.stim) | 15.3 k | 94.5 M | 9 | 18 |
| [2503.18657](https://arxiv.org/abs/2503.18657) / [`rp_3_sc_7_end2end_4_full_rds`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_sc_7_end2end_4_full_rds.stim) | 8.44 M | 1.7 B | 4 | 8 |
| [2504.02935](https://arxiv.org/abs/2504.02935) / [`hook_inject_T_d3_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2504.02935_erasure_injection/stim/hook_inject_T_d3_p0.001.stim) | 76.2 M | 17.9 B | 1 | 1 |
| [2504.02935](https://arxiv.org/abs/2504.02935) / [`inject_cultivate_T_d3_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2504.02935_erasure_injection/stim/inject_cultivate_T_d3_p0.001.stim) | 30.5 M | 16.7 B | 4 | 4 |
| [2507.12511](https://arxiv.org/abs/2507.12511) / [`unfolded_repetition_no_preselection_pz1e-3_rounds2`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_repetition_no_preselection_pz1e-3_rounds2.stim) | 31.2 M | 8.95 B | 4 | 4 |
| [2507.12511](https://arxiv.org/abs/2507.12511) / [`unfolded_repetition_no_preselection_pz1e-3_rounds4`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_repetition_no_preselection_pz1e-3_rounds4.stim) | 19.3 M | 4.13 B | 4 | 4 |
| [2507.12511](https://arxiv.org/abs/2507.12511) / [`unfolded_repetition_no_preselection_pz1e-3_rounds6`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_repetition_no_preselection_pz1e-3_rounds6.stim) | 14.5 M | 2.7 B | 4 | 4 |
| [2507.12511](https://arxiv.org/abs/2507.12511) / [`unfolded_surface_no_bitflip_pz1e-3_rounds2`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_surface_no_bitflip_pz1e-3_rounds2.stim) | 19.2 M | 3.17 B | 4 | 4 |
| [2507.12511](https://arxiv.org/abs/2507.12511) / [`unfolded_surface_no_bitflip_pz1e-3_rounds4`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_surface_no_bitflip_pz1e-3_rounds4.stim) | 11.6 M | 1.65 B | 4 | 4 |
| [2507.12511](https://arxiv.org/abs/2507.12511) / [`unfolded_surface_no_bitflip_pz1e-3_rounds6`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_surface_no_bitflip_pz1e-3_rounds6.stim) | 8.6 M | 1.12 B | 4 | 4 |
| [2509.05212](https://arxiv.org/abs/2509.05212) / [`fold-d3_native_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.05212_fold_transversal_cultivation/stim/fold-d3_native_T_p0.001.stim) | 15 M | 1.33 B | 6 | 8 |
| [2509.05212](https://arxiv.org/abs/2509.05212) / [`fold-d5_native_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.05212_fold_transversal_cultivation/stim/fold-d5_native_T_p0.001.stim) | 63.9 k | 82 M | 8 | 22 |
| [2509.08658](https://arxiv.org/abs/2509.08658) / [`d3_cultivation_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.08658_few_clifford_terms/stim/d3_cultivation_T_p0.001.stim) | 28.6 M | 10.7 B | 4 | 4 |
| [2509.18294](https://arxiv.org/abs/2509.18294) / [`star_d=11`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.18294_transversal_star/stim/star_d=11.stim) | 2.38 M | 242 M | 2 | 2 |
| [2509.18294](https://arxiv.org/abs/2509.18294) / [`star_d=13`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.18294_transversal_star/stim/star_d=13.stim) | 1.26 M | 144 M | 2 | 2 |
| [2509.18294](https://arxiv.org/abs/2509.18294) / [`star_d=15`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.18294_transversal_star/stim/star_d=15.stim) | 829 k | 100 M | 2 | 2 |
| [2509.18294](https://arxiv.org/abs/2509.18294) / [`star_d=3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.18294_transversal_star/stim/star_d=3.stim) | 33.9 M | 6.72 B | 2 | 2 |
| [2509.18294](https://arxiv.org/abs/2509.18294) / [`star_d=5`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.18294_transversal_star/stim/star_d=5.stim) | 14.9 M | 1.94 B | 2 | 2 |
| [2509.18294](https://arxiv.org/abs/2509.18294) / [`star_d=7`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.18294_transversal_star/stim/star_d=7.stim) | 7.83 M | 817 M | 2 | 2 |
| [2509.18294](https://arxiv.org/abs/2509.18294) / [`star_d=9`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2509.18294_transversal_star/stim/star_d=9.stim) | 4.17 M | 419 M | 2 | 2 |
| [2510.24615](https://arxiv.org/abs/2510.24615) / [`inject-check-3_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2510.24615_lattice_surgery_cultivation/stim/inject-check-3_T.stim) | 29.5 M | 14.2 B | 4 | 4 |
| [2510.24615](https://arxiv.org/abs/2510.24615) / [`lattice-surgery-complementary-gap-3-to-5-to-7_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2510.24615_lattice_surgery_cultivation/stim/lattice-surgery-complementary-gap-3-to-5-to-7_T.stim) | 14.7 M | 2.46 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig2_cultivation_stim_X_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_cultivation_stim_X_T.stim) | 88.6 M | 26.7 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig2_cultivation_stim_Z_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_cultivation_stim_Z_T.stim) | 90.4 M | 26.5 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig2_injection_stim_X_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_injection_stim_X_T.stim) | 89.4 M | 36.9 B | 1 | 1 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig2_injection_stim_Z_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_injection_stim_Z_T.stim) | 89.4 M | 36.9 B | 1 | 1 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig2_simulation_stim_X_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_simulation_stim_X_T.stim) | 89.7 M | 26.7 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig2_simulation_stim_Z_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_simulation_stim_Z_T.stim) | 90 M | 26.4 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig3_injection_stim_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_injection_stim_T.stim) | 89.7 M | 13.2 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig3_simulation_stim_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_simulation_stim_T.stim) | 88.2 M | 7.55 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig3_simulation_zoom_stim_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_simulation_zoom_stim_T.stim) | 88.5 M | 7.55 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig3_with_idle_rounds_stim_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_with_idle_rounds_stim_T.stim) | 91.4 M | 7.55 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig3_with_idle_rounds_zoom_stim_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_with_idle_rounds_zoom_stim_T.stim) | 91.7 M | 7.55 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig3_without_idle_rounds_stim_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_without_idle_rounds_stim_T.stim) | 90.2 M | 13.1 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig4_cultivation_N2_stim_X_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N2_stim_X_T.stim) | 78.3 M | 5.83 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig4_cultivation_N2_stim_Z_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N2_stim_Z_T.stim) | 79.5 M | 5.83 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig4_cultivation_N3_stim_X_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N3_stim_X_T.stim) | 78.7 M | 4.33 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig4_cultivation_N3_stim_Z_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N3_stim_Z_T.stim) | 82.4 M | 4.34 B | 4 | 4 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig4_injection_N2_stim_X_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_injection_N2_stim_X_T.stim) | 90.9 M | 6.53 B | 1 | 1 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig4_injection_N2_stim_Z_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_injection_N2_stim_Z_T.stim) | 90.5 M | 6.53 B | 1 | 1 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig4_simulation_injection_N2_stim_X_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_simulation_injection_N2_stim_X_T.stim) | 92.1 M | 6.54 B | 1 | 1 |
| [2512.13908](https://arxiv.org/abs/2512.13908) / [`fig4_simulation_injection_N2_stim_Z_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_simulation_injection_N2_stim_Z_T.stim) | 91.9 M | 6.51 B | 1 | 1 |
| [2512.23037](https://arxiv.org/abs/2512.23037) / [`circuit_d3_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.23037_soft/stim/circuit_d3_p0.001.stim) | 27.1 M | 13.4 B | 4 | 4 |
| [2512.23037](https://arxiv.org/abs/2512.23037) / [`circuit_d5_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2512.23037_soft/stim/circuit_d5_p0.001.stim) | 181 k | 1.74 B | 6 | 10 |
| [2603.05429](https://arxiv.org/abs/2603.05429) / [`gauging_cultivation_d3_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2603.05429_gauging_clifford_cultivation/stim/gauging_cultivation_d3_T_p0.001.stim) | 12.6 M | 7.65 B | 4 | 4 |
| [2603.05429](https://arxiv.org/abs/2603.05429) / [`gauging_cultivation_d5_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2603.05429_gauging_clifford_cultivation/stim/gauging_cultivation_d5_T_p0.001.stim) | 102 k | 504 M | 6 | 10 |
| [2603.05429](https://arxiv.org/abs/2603.05429) / [`gauging_cultivation_d7_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2603.05429_gauging_clifford_cultivation/stim/gauging_cultivation_d7_T_p0.001.stim) | 8.02 k | 55.4 M | 8 | 19 |
| [2604.01059](https://arxiv.org/abs/2604.01059) / [`distillation_color_d5_X`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.01059_tsim/stim/distillation_color_d5_X.stim) | 15.6 M | 8.93 B | 4 | 4 |
| [2604.01059](https://arxiv.org/abs/2604.01059) / [`distillation_color_d5_Y`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.01059_tsim/stim/distillation_color_d5_Y.stim) | 15.8 M | 8.78 B | 3 | 3 |
| [2604.01059](https://arxiv.org/abs/2604.01059) / [`distillation_color_d5_Z`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.01059_tsim/stim/distillation_color_d5_Z.stim) | 13.3 M | 8.95 B | 3 | 3 |
| [2604.01059](https://arxiv.org/abs/2604.01059) / [`distillation_steane_d3_X`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.01059_tsim/stim/distillation_steane_d3_X.stim) | 25.8 M | 16.3 B | 4 | 4 |
| [2604.01059](https://arxiv.org/abs/2604.01059) / [`distillation_steane_d3_Y`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.01059_tsim/stim/distillation_steane_d3_Y.stim) | 26 M | 18 B | 3 | 3 |
| [2604.01059](https://arxiv.org/abs/2604.01059) / [`distillation_steane_d3_Z`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.01059_tsim/stim/distillation_steane_d3_Z.stim) | 21 M | 15.5 B | 3 | 3 |
| [2604.01059](https://arxiv.org/abs/2604.01059) / [`distillation_unencoded_X`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.01059_tsim/stim/distillation_unencoded_X.stim) | 39.1 M | 17.6 B | 4 | 4 |
| [2604.01059](https://arxiv.org/abs/2604.01059) / [`distillation_unencoded_Y`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.01059_tsim/stim/distillation_unencoded_Y.stim) | 40.6 M | 20.2 B | 3 | 3 |
| [2604.01059](https://arxiv.org/abs/2604.01059) / [`distillation_unencoded_Z`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.01059_tsim/stim/distillation_unencoded_Z.stim) | 31.8 M | 16.7 B | 3 | 3 |
| [2604.05126](https://arxiv.org/abs/2604.05126) / [`bb144_cfg328_inj5_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg328_inj5_T_p0.001.stim) | 5.49 M | 923 M | 1 | 1 |
| [2604.05126](https://arxiv.org/abs/2604.05126) / [`bb144_cfg342_inj3_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg342_inj3_T_p0.001.stim) | 6.3 M | 892 M | 1 | 1 |
| [2604.05126](https://arxiv.org/abs/2604.05126) / [`bb144_cfg369_inj1_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg369_inj1_T_p0.001.stim) | 7.27 M | 925 M | 1 | 1 |
| [2604.05126](https://arxiv.org/abs/2604.05126) / [`bb144_cfg422_inj2_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg422_inj2_T_p0.001.stim) | 6.74 M | 912 M | 1 | 1 |
| [2604.05126](https://arxiv.org/abs/2604.05126) / [`bb144_cfg491_inj4_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg491_inj4_T_p0.001.stim) | 5.98 M | 924 M | 1 | 1 |
| [2604.05126](https://arxiv.org/abs/2604.05126) / [`bb144_cfg88_inj6_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg88_inj6_T_p0.001.stim) | 5.42 M | 947 M | 1 | 1 |
| [2604.27058](https://arxiv.org/abs/2604.27058) / [`coherent_d3_r1`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.27058_clifft/stim/coherent_d3_r1.stim) | 1.12 B | 23.4 B | 0 | 0 |
| [2604.27058](https://arxiv.org/abs/2604.27058) / [`coherent_d3_r3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.27058_clifft/stim/coherent_d3_r3.stim) | 18.6 M | 10.3 B | 4 | 4 |
| [2604.27058](https://arxiv.org/abs/2604.27058) / [`coherent_d5_r1`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.27058_clifft/stim/coherent_d5_r1.stim) | 551 M | 12.9 B | 0 | 0 |
| [2604.27058](https://arxiv.org/abs/2604.27058) / [`coherent_d5_r5`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.27058_clifft/stim/coherent_d5_r5.stim) | 930 | 2.53 M | 11 | 13 |
| [2604.27058](https://arxiv.org/abs/2604.27058) / [`cultivation_d3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.27058_clifft/stim/cultivation_d3.stim) | 27 M | 13.4 B | 4 | 4 |
| [2604.27058](https://arxiv.org/abs/2604.27058) / [`cultivation_d5`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.27058_clifft/stim/cultivation_d5.stim) | 713 k | 1.4 B | 6 | 10 |
| [2604.27058](https://arxiv.org/abs/2604.27058) / [`distillation`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.27058_clifft/stim/distillation.stim) | 13.4 M | 8.93 B | 3 | 3 |
| [2604.27058](https://arxiv.org/abs/2604.27058) / [`surface_d7_r7`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2604.27058_clifft/stim/surface_d7_r7.stim) | 16.1 M | 1.27 B | 0 | 0 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`MSC_circuit_d7_p0.0005`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/MSC_circuit_d7_p0.0005.stim) | 18.6 k | 240 M | 8 | 19 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`coherent_surface_d3_r1_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/coherent_surface_d3_r1_p1e-3_rz0p02.stim) | 846 M | 25.1 B | 0 | 0 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`coherent_surface_d3_r3_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/coherent_surface_d3_r3_p1e-3_rz0p02.stim) | 18.5 M | 9.84 B | 4 | 4 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`coherent_surface_d5_r1_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/coherent_surface_d5_r1_p1e-3_rz0p02.stim) | 530 M | 13.1 B | 0 | 0 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`coherent_surface_d5_r5_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/coherent_surface_d5_r5_p1e-3_rz0p02.stim) | 831 | 2.53 M | 11 | 13 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`distillation`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/distillation.stim) | 13.4 M | 8.76 B | 3 | 3 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`msc_d3_inject_cultivate_p1e-3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/msc_d3_inject_cultivate_p1e-3.stim) | 26.7 M | 13.4 B | 4 | 4 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`msc_d5_inject_cultivate_p1e-3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/msc_d5_inject_cultivate_p1e-3.stim) | 511 k | 1.4 B | 6 | 10 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`msc_proxy_d7_unverified_p1e-3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/msc_proxy_d7_unverified_p1e-3.stim) | 215 k | 1.09 B | 6 | 10 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`pure_surface_d7_r7_p1e-3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/pure_surface_d7_r7_p1e-3.stim) | 16.8 M | 1.27 B | 0 | 0 |
| [2607.28600](https://arxiv.org/abs/2607.28600) / [`pure_surface_d9_r9_p1e-3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2607.28600_symft/stim/pure_surface_d9_r9_p1e-3.stim) | 7.67 M | 602 M | 0 | 0 |
| [2609.17706](https://arxiv.org/abs/2609.17706) / [`d3a6_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d3a6_inject_cultivate_T_p0.001.stim) | 25.7 M | 13.7 B | 4 | 4 |
| [2609.17706](https://arxiv.org/abs/2609.17706) / [`d3a6f2_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d3a6f2_inject_cultivate_T_p0.001.stim) | 24.4 M | 13.6 B | 4 | 4 |
| [2609.17706](https://arxiv.org/abs/2609.17706) / [`d5a19_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19_inject_cultivate_T_p0.001.stim) | 667 k | 1.13 B | 6 | 10 |
| [2609.17706](https://arxiv.org/abs/2609.17706) / [`d5a19f13_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19f13_inject_cultivate_T_p0.001.stim) | 527 k | 1.12 B | 6 | 10 |
| [2609.17706](https://arxiv.org/abs/2609.17706) / [`d5a19r4_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19r4_inject_cultivate_T_p0.001.stim) | 493 k | 1.13 B | 6 | 10 |
| [2609.17706](https://arxiv.org/abs/2609.17706) / [`d5a19r4f13_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19r4f13_inject_cultivate_T_p0.001.stim) | 290 k | 1.1 B | 6 | 10 |
| [2609.18922](https://arxiv.org/abs/2609.18922) / [`clifft_d3_p001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2609.18922_exact_ler_cultivation/stim/clifft_d3_p001.stim) | 26.4 M | 13.5 B | 4 | 4 |
| [2609.18922](https://arxiv.org/abs/2609.18922) / [`soft_cultivation_d5_p0005`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2609.18922_exact_ler_cultivation/stim/soft_cultivation_d5_p0005.stim) | 112 k | 1.5 B | 6 | 10 |
| [2610.03869](https://arxiv.org/abs/2610.03869) / [`stability_d3_X_t100_alpha0.5_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t100_alpha0.5_p0.001.stim) | 54.2 k | 283 M | 3 | 6 |
| [2610.03869](https://arxiv.org/abs/2610.03869) / [`stability_d3_X_t20_alpha0.15_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t20_alpha0.15_p0.001.stim) | 1.56 M | 1.56 B | 3 | 6 |
| [2610.03869](https://arxiv.org/abs/2610.03869) / [`stability_d3_X_t20_alpha0.5_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t20_alpha0.5_p0.001.stim) | 260 k | 1.5 B | 3 | 6 |
| [2610.03869](https://arxiv.org/abs/2610.03869) / [`stability_d3_X_t20_alpha1.0_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t20_alpha1.0_p0.001.stim) | 164 k | 974 M | 3 | 6 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`code_switching_bt27_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/code_switching_bt27_p0.001.stim) | – | – | 26 | 27 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`code_switching_bt81_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/code_switching_bt81_p0.001.stim) | – | – | 63 (refused, limit 30) | 52 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`cultivation_d3_t`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/cultivation_d3_t.stim) | 26.9 M | 13.4 B | 4 | 4 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`cultivation_d5_t`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/cultivation_d5_t.stim) | 640 k | 1.4 B | 6 | 10 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_15to1_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_15to1_p0.001.stim) | 108 M | 25.9 B | 4 | 0 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_bh10_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_bh10_p0.001.stim) | 98.5 M | 10.4 B | 4 | 0 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_bh12_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_bh12_p0.001.stim) | 63.7 M | 6.09 B | 4 | 0 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_bh14_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_bh14_p0.001.stim) | 99.1 M | 7.52 B | 4 | 0 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_bh16_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_bh16_p0.001.stim) | 64.1 M | 5.09 B | 4 | 0 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_bh18_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_bh18_p0.001.stim) | 100 M | 6.58 B | 4 | 0 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_bh2_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_bh2_p0.001.stim) | 105 M | 25.8 B | 4 | 0 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_bh4_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_bh4_p0.001.stim) | 66.4 M | 13.9 B | 4 | 0 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_bh6_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_bh6_p0.001.stim) | 103 M | 13.1 B | 4 | 0 |
| [2610.06811](https://arxiv.org/abs/2610.06811) / [`distillation_bh8_p0.001`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06811_merlin/stim/distillation_bh8_p0.001.stim) | 68.7 M | 9.23 B | 4 | 0 |
| [2610.06828](https://arxiv.org/abs/2610.06828) / [`color_code_cultivation_f3_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06828_practical_cost_cultivation/stim/color_code_cultivation_f3_T.stim) | 1.16 M | 199 M | 4 | 4 |
| [2610.06828](https://arxiv.org/abs/2610.06828) / [`color_code_cultivation_f5_T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.06828_practical_cost_cultivation/stim/color_code_cultivation_f5_T.stim) | 306 k | 154 M | 6 | 10 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh10-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh10-S.stim) | 926 M | 48.3 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh10-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh10-T.stim) | 26.6 M | 17.5 B | 3 | 13 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh100-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh100-S.stim) | 269 M | 47.8 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh100-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh100-T.stim) | 273 k | 1.66 B | 3 | ≥60 (overflow) |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh2-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh2-S.stim) | 1.37 B | 47.8 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh2-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh2-T.stim) | 74.5 M | 29.5 B | 3 | 5 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh20-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh20-S.stim) | 693 M | 47.9 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh20-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh20-T.stim) | 1.37 M | 11.1 B | 3 | 22 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh4-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh4-S.stim) | 1.05 B | 47.7 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh4-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh4-T.stim) | 55.9 M | 26.1 B | 3 | 7 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh40-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh40-S.stim) | 497 M | 47.8 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh40-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh40-T.stim) | 707 k | 5.94 B | 3 | 42 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh6-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh6-S.stim) | 1.03 B | 47.7 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh6-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh6-T.stim) | 45.1 M | 23 B | 3 | 9 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh60-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh60-S.stim) | 403 M | 47.6 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh60-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh60-T.stim) | 495 k | 3.66 B | 3 | ≥60 (overflow) |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh80-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh80-S.stim) | 323 M | 47.5 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`bh80-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/bh80-T.stim) | 348 k | 2.85 B | 3 | ≥60 (overflow) |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`color3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/color3.stim) | 30.3 M | 16 B | 4 | 4 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`color5`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/color5.stim) | 163 k | 1.72 B | 6 | 10 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`dk`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/dk.stim) | 39.7 M | 16.9 B | 4 | 4 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`rp2-d3-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/rp2-d3-S.stim) | 34.7 M | 8.04 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`rp2-d3`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/rp2-d3.stim) | 13.5 M | 8.41 B | 4 | 8 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`rp2-d5-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/rp2-d5-S.stim) | 14.2 M | 2.99 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`rp2-d5`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/rp2-d5.stim) | 60 k | 126 M | 9 | 18 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`wg-S`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/wg-S.stim) | 71.6 M | 4.23 B | 0 | 0 |
| [2610.22315](https://arxiv.org/abs/2610.22315) / [`wg-T`](https://github.com/rafaelha/tsim-active-width/blob/master/papers/2610.22315_magna/stim/wg-T.stim) | 7.9 M | 4.21 B | 4 | 5 |
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

## How the candidates were found

Twenty GPT-6.1 Terra scouts each searched one area (`_search/BRIEF.md`, `_search/scout_*.json`):
- cultivation
- distillation
- code switching
- injection
- fold-transversal gates
- coherent errors
- simulator benchmarks
- CCZ/CS
- experiments
- gauging and lattice surgery
- small codes
- STAR and rotations
- qLDPC
- neutral atoms
- Zenodo
- GitHub
- zero-level distillation and layouts
- logical algorithms and compilers
- colour codes
- recent cost studies

The merged, deduplicated list has 50 entries (`_search/candidates.json`). I found Chan et al. (2609.17706) separately, through the exact-LER
repository.

## Papers not processed

| arXiv | paper | reason |
|---|---|---|
| 2510.07269 | Transversal dimension jump for product qLDPC codes | CCZ is modelled by a weight-5 Pauli surrogate; regenerating needs bposd/ldpc and notebook-generated code matrices |
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

- **Tsim tag bug:** at 883d787, Tsim mis-parses any instruction tag that contains the token ` T`, e.g. `TICK[Encode T]` or
  `H[my T tag] 0` ("Targets must be separated by spacing"). main@4b951f3 ("stop rewriting tags", #218) fixes it; I checked.
- **Tsim correlated-error chains:** Tsim compiles a `CORRELATED_ERROR`/`ELSE_CORRELATED_ERROR` chain of length k into a 2^k table, so a
  63-term chain (exact 3-qubit depolarizing noise) fails with "Maximum allowed dimension exceeded". See
  `papers/2509.05212_fold_transversal_cultivation`.
- **Clifft parser strictness:** Clifft rejects target-less instructions such as `DEPOLARIZE1(0.001)` and `R`, and any tag outside
  `LEVEL_TRANSITION`, so several published files needed `tools/stimtext.py`.
- **Width comparison:** across the 164 circuits measured by both simulators, Tsim's k is smaller on 57, equal on 97, and larger on 10.
  - Tsim much smaller: Bravyi–Haah distillation with T teleportation (Magna) stays at k=3 for every size, while Clifft grows to 42 and
    overflows from bh60 on. Fold-transversal d=5 gives 8 vs 22, gauging d=7 8 vs 19, and RP² d=5 10 vs 18.
  - Tsim larger: the 10 circuits are Merlin's "clean" distillation workloads (Tsim 4, Clifft 0). The intermediate states are non-stabilizer,
    but the only noise is Z after the T_DAG gates and the ideal output is undone before readout. By triorthogonality the whole circuit is then
    Clifford as an operator, and Clifft's `PhasePolynomialPass` cancels every T gate. Switching off either ingredient brings Clifft back to
    k ≥ 1 (variant table in `papers/2610.06811_merlin/README.md`).
  - Not measured by both: Clifft overflows on Magna bh60/80/100 (Tsim 3), and Tsim's `active_statevector` refuses Merlin's bt81, which
    would need 63 active qubits against a limit of 30 (Clifft 52).
  - `ActiveWidthSchedulePass` matters most on the STAR circuits, where it brings Clifft from k=d down to 2.

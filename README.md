# Tsim on published non-Clifford QEC circuits

Shots per second and active width (k_max) for 189 circuits from 27 papers. Every circuit has real T, CCZ or CS gates: the authors'
own non-Clifford circuits, or their Clifford stand-ins (S for T, |Y⟩ for |T⟩) converted back to real gates. Click a circuit to see
its `.stim` file; each paper's folder explains where the circuits came from and how they were converted.

The GPU columns show the speedup over one CPU core in brackets. The CUDA and Metal kernels currently support only circuits with
k_max ≤ 11; larger circuits show – there. [`SUMMARY.md`](SUMMARY.md) has the same table with
Clifft's numbers added.

<!-- benchmark-table:begin -->
| circuit | k_max | CPU&nbsp;(single-core) | T-deferral | RTX&nbsp;5090 | M4&nbsp;Pro&nbsp;(GPU/Metal) |
|---|---|---|---|---|---|
| **[2302.12292](https://arxiv.org/abs/2302.12292)** Gidney (2023), *Cleaner magic states with hook injection* | | | | | |
| [`hook_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/hook_inject_T_d15_pd5_p0.001.stim) | 1 | 1.51&nbsp;M | 1.52&nbsp;M | 122&nbsp;M&nbsp;(81x) | 54.6&nbsp;M&nbsp;(36x) |
| [`hook_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/hook_inject_T_d15_pd7_p0.001.stim) | 1 | 1.48&nbsp;M | 1.5&nbsp;M | 119&nbsp;M&nbsp;(80x) | 50.1&nbsp;M&nbsp;(34x) |
| [`li_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/li_inject_T_d15_pd5_p0.001.stim) | 1 | 800&nbsp;k | 809&nbsp;k | 63.9&nbsp;M&nbsp;(80x) | 21.6&nbsp;M&nbsp;(27x) |
| [`li_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/li_inject_T_d15_pd7_p0.001.stim) | 1 | 788&nbsp;k | 792&nbsp;k | 62.6&nbsp;M&nbsp;(80x) | 21.9&nbsp;M&nbsp;(28x) |
| [`pregrown_hook_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/pregrown_hook_inject_T_d15_pd5_p0.001.stim) | 1 | 1.33&nbsp;M | 1.35&nbsp;M | 108&nbsp;M&nbsp;(81x) | 43.4&nbsp;M&nbsp;(33x) |
| [`pregrown_hook_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/pregrown_hook_inject_T_d15_pd7_p0.001.stim) | 1 | 1.34&nbsp;M | 1.35&nbsp;M | 108&nbsp;M&nbsp;(81x) | 44&nbsp;M&nbsp;(33x) |
| [`zz_inject_T_d15_pd5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/zz_inject_T_d15_pd5_p0.001.stim) | 1 | 807&nbsp;k | 811&nbsp;k | 68&nbsp;M&nbsp;(84x) | 21.1&nbsp;M&nbsp;(26x) |
| [`zz_inject_T_d15_pd7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2302.12292_hook_injection/stim/zz_inject_T_d15_pd7_p0.001.stim) | 1 | 798&nbsp;k | 802&nbsp;k | 67.9&nbsp;M&nbsp;(85x) | 21.3&nbsp;M&nbsp;(27x) |
| **[2406.17653](https://arxiv.org/abs/2406.17653)** Zhou et al. (2024), *Low-Overhead Transversal Fault Tolerance for Universal Quantum Computation* | | | | | |
| [`s_injection_T_d3_p0.001_pinj0.1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2406.17653_transversal_algorithmic_ft/stim/s_injection_T_d3_p0.001_pinj0.1.stim) | 1 | 52&nbsp;M | 58.1&nbsp;M | 6.7&nbsp;B&nbsp;(129x) | 3.04&nbsp;B&nbsp;(59x) |
| [`s_injection_T_d5_p0.001_pinj0.1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2406.17653_transversal_algorithmic_ft/stim/s_injection_T_d5_p0.001_pinj0.1.stim) | 1 | 44.4&nbsp;M | 46.5&nbsp;M | 3.36&nbsp;B&nbsp;(76x) | 2.69&nbsp;B&nbsp;(60x) |
| [`s_injection_T_d7_p0.001_pinj0.1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2406.17653_transversal_algorithmic_ft/stim/s_injection_T_d7_p0.001_pinj0.1.stim) | 1 | 37&nbsp;M | 36.5&nbsp;M | 1.95&nbsp;B&nbsp;(53x) | 1.27&nbsp;B&nbsp;(34x) |
| [`s_injection_T_d9_p0.001_pinj0.1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2406.17653_transversal_algorithmic_ft/stim/s_injection_T_d9_p0.001_pinj0.1.stim) | 1 | 30.1&nbsp;M | 28.4&nbsp;M | 1.24&nbsp;B&nbsp;(41x) | 846&nbsp;M&nbsp;(28x) |
| **[2409.07707](https://arxiv.org/abs/2409.07707)** Lee et al. (2024), *Low-overhead magic state distillation with color codes* | | | | | |
| [`cult_growing_T_d3_to_d11_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d3_to_d11_p0.001.stim) | 4 | 3.16&nbsp;M | 2.37&nbsp;M | 425&nbsp;M&nbsp;(134x) | 231&nbsp;M&nbsp;(73x) |
| [`cult_growing_T_d3_to_d7_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d3_to_d7_p0.001.stim) | 4 | 9.65&nbsp;M | 5.45&nbsp;M | 1.55&nbsp;B&nbsp;(161x) | 603&nbsp;M&nbsp;(62x) |
| [`cult_growing_T_d5_to_d13_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d5_to_d13_p0.001.stim) | 6 | 662&nbsp;k | 49.8&nbsp;k | 245&nbsp;M&nbsp;(370x) | 104&nbsp;M&nbsp;(158x) |
| [`cult_growing_T_d5_to_d9_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.07707_color_code_msd/stim/cult_growing_T_d5_to_d9_p0.001.stim) | 6 | 890&nbsp;k | 54.8&nbsp;k | 673&nbsp;M&nbsp;(756x) | 150&nbsp;M&nbsp;(168x) |
| **[2409.17595](https://arxiv.org/abs/2409.17595)** Gidney et al. (2024), *Magic state cultivation: growing T states as cheap as CNOT gates* | | | | | |
| [`end2end_d3_dsurface15_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.17595_magic_state_cultivation/stim/end2end_d3_dsurface15_p0.001.stim) | 4 | 1.39&nbsp;M | 1.2&nbsp;M | 198&nbsp;M&nbsp;(142x) | 115&nbsp;M&nbsp;(82x) |
| [`end2end_d5_dsurface15_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.17595_magic_state_cultivation/stim/end2end_d5_dsurface15_p0.001.stim) | 6 | 539&nbsp;k | 47.7&nbsp;k | 155&nbsp;M&nbsp;(288x) | 68.3&nbsp;M&nbsp;(127x) |
| [`inject_cultivate_d3_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.17595_magic_state_cultivation/stim/inject_cultivate_d3_p0.001.stim) | 4 | 29.4&nbsp;M | 15.4&nbsp;M | 13.4&nbsp;B&nbsp;(456x) | 1.49&nbsp;B&nbsp;(51x) |
| [`inject_cultivate_d5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2409.17595_magic_state_cultivation/stim/inject_cultivate_d5_p0.001.stim) | 6 | 1.26&nbsp;M | 60.6&nbsp;k | 1.4&nbsp;B&nbsp;(1115x) | 170&nbsp;M&nbsp;(136x) |
| **[2502.01743](https://arxiv.org/abs/2502.01743)** Vaknin et al. (2025), *Efficient Magic State Cultivation on the Surface Code* | | | | | |
| [`expanded-rotated-init-x-injection-double-HXY_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-rotated-init-x-injection-double-HXY_d1=3_d2=11_p=0.001.stim) | 8 | 2.04&nbsp;M | 1.39&nbsp;M | 209&nbsp;M&nbsp;(103x) | 40.2&nbsp;M&nbsp;(20x) |
| [`expanded-rotated-injection-double-ghz-HXY_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-rotated-injection-double-ghz-HXY_d1=3_d2=11_p=0.001.stim) | 8 | 1.93&nbsp;M | 1.23&nbsp;M | 252&nbsp;M&nbsp;(131x) | 42.1&nbsp;M&nbsp;(22x) |
| [`expanded-rotated-injection-syndrome-double-ghz-HXY_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-rotated-injection-syndrome-double-ghz-HXY_d1=3_d2=11_p=0.001.stim) | 8 | 1.83&nbsp;M | 1.15&nbsp;M | 252&nbsp;M&nbsp;(138x) | 42.5&nbsp;M&nbsp;(23x) |
| [`expanded-unrotated_H_injection-ghz_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-unrotated_H_injection-ghz_d1=3_d2=11_p=0.001.stim) | 9 | 105&nbsp;k | 74.3&nbsp;k | 57.1&nbsp;M&nbsp;(542x) | 7.4&nbsp;M&nbsp;(70x) |
| [`expanded-unrotated_H_injection-syndrome-ghz_d1=3_d2=11_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/expanded-unrotated_H_injection-syndrome-ghz_d1=3_d2=11_p=0.001.stim) | 9 | 95.3&nbsp;k | 60.4&nbsp;k | 57&nbsp;M&nbsp;(598x) | 7.39&nbsp;M&nbsp;(77x) |
| [`rotated-init-x-injection-double-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-init-x-injection-double-HXY_d1=3_p=0.001.stim) | 8 | 4.52&nbsp;M | 3.45&nbsp;M | 327&nbsp;M&nbsp;(72x) | 52.5&nbsp;M&nbsp;(12x) |
| [`rotated-init-x-injection-syndrome-double-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-init-x-injection-syndrome-double-ghz-HXY_d1=3_p=0.001.stim) | 8 | 4.02&nbsp;M | 3.04&nbsp;M | 329&nbsp;M&nbsp;(82x) | 52&nbsp;M&nbsp;(13x) |
| [`rotated-injection-double-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-injection-double-ghz-HXY_d1=3_p=0.001.stim) | 8 | 4.17&nbsp;M | 2.81&nbsp;M | 332&nbsp;M&nbsp;(80x) | 52.4&nbsp;M&nbsp;(13x) |
| [`rotated-injection-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-injection-ghz-HXY_d1=3_p=0.001.stim) | 6 | 7.63&nbsp;M | 2.79&nbsp;M | 1&nbsp;B&nbsp;(131x) | 186&nbsp;M&nbsp;(24x) |
| [`rotated-injection-syndrome-double-ghz-HXY_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/rotated-injection-syndrome-double-ghz-HXY_d1=3_p=0.001.stim) | 8 | 3.78&nbsp;M | 2.54&nbsp;M | 332&nbsp;M&nbsp;(88x) | 52.1&nbsp;M&nbsp;(14x) |
| [`unrotated_HXY_injection-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_HXY_injection-ghz_d1=3_p=0.001.stim) | 7 | 5.9&nbsp;M | 2.87&nbsp;M | 738&nbsp;M&nbsp;(125x) | 110&nbsp;M&nbsp;(19x) |
| [`unrotated_HXY_injection-syndrome-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_HXY_injection-syndrome-ghz_d1=3_p=0.001.stim) | 7 | 5.11&nbsp;M | 2.16&nbsp;M | 733&nbsp;M&nbsp;(143x) | 110&nbsp;M&nbsp;(21x) |
| [`unrotated_H_injection-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_H_injection-ghz_d1=3_p=0.001.stim) | 9 | 205&nbsp;k | 126&nbsp;k | 105&nbsp;M&nbsp;(511x) | 14.5&nbsp;M&nbsp;(71x) |
| [`unrotated_H_injection-syndrome-ghz_d1=3_p=0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2502.01743_surface_code_cultivation/stim/unrotated_H_injection-syndrome-ghz_d1=3_p=0.001.stim) | 9 | 172&nbsp;k | 123&nbsp;k | 105&nbsp;M&nbsp;(608x) | 14.3&nbsp;M&nbsp;(83x) |
| **[2503.18657](https://arxiv.org/abs/2503.18657)** Chen et al. (2025), *Efficient Magic State Cultivation on RP²* | | | | | |
| [`rp_3_T_cult`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_T_cult.stim) | 4 | 13.3&nbsp;M | 2.09&nbsp;M | 8.42&nbsp;B&nbsp;(632x) | 978&nbsp;M&nbsp;(73x) |
| [`rp_3_rp_5_T_cult`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_rp_5_T_cult.stim) | 10 | 15.6&nbsp;k | 10.4&nbsp;k | 44&nbsp;M&nbsp;(2815x) | 6.78&nbsp;M&nbsp;(434x) |
| [`rp_3_rp_5_sc_11_end2end_6_full_rds`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_rp_5_sc_11_end2end_6_full_rds.stim) | 9 | 24.1&nbsp;k | 9.05&nbsp;k | 94.5&nbsp;M&nbsp;(3921x) | 11.6&nbsp;M&nbsp;(480x) |
| [`rp_3_sc_7_end2end_4_full_rds`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2503.18657_rp2_cultivation/stim/rp_3_sc_7_end2end_4_full_rds.stim) | 4 | 9.72&nbsp;M | 3.22&nbsp;M | 1.7&nbsp;B&nbsp;(175x) | 636&nbsp;M&nbsp;(65x) |
| **[2504.02935](https://arxiv.org/abs/2504.02935)** Jacoby et al. (2025), *Magic State Injection with Erasure Qubits* | | | | | |
| [`hook_inject_T_d3_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2504.02935_erasure_injection/stim/hook_inject_T_d3_p0.001.stim) | 1 | 81.6&nbsp;M | 103&nbsp;M | 17.9&nbsp;B&nbsp;(219x) | 3.32&nbsp;B&nbsp;(41x) |
| [`inject_cultivate_T_d3_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2504.02935_erasure_injection/stim/inject_cultivate_T_d3_p0.001.stim) | 4 | 33&nbsp;M | 18.8&nbsp;M | 16.7&nbsp;B&nbsp;(508x) | 1.87&nbsp;B&nbsp;(57x) |
| **[2505.13587](https://arxiv.org/abs/2505.13587)** Cain et al. (2025), *Fast correlated decoding of transversal logical algorithms* | | | | | |
| [`distillation_15to1_T_d13_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d13_p0.001.stim) | 4 | 211&nbsp;k | 12.5&nbsp;k | unsupported | 3.36&nbsp;M&nbsp;(16x) |
| [`distillation_15to1_T_d17_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d17_p0.001.stim) | 4‡ | 106&nbsp;k‡ | 11.7&nbsp;k‡ | OOM | 1.77&nbsp;M&nbsp;(17x) |
| [`distillation_15to1_T_d21_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d21_p0.001.stim) | 4‡ | 54.1&nbsp;k‡ | 11.2&nbsp;k‡ | OOM | 925&nbsp;k&nbsp;(17x) |
| [`distillation_15to1_T_d25_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d25_p0.001.stim) | 4‡ | 43.2&nbsp;k‡ | 10.2&nbsp;k‡ | OOM | 537&nbsp;k&nbsp;(12x) |
| [`distillation_15to1_T_d5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d5_p0.001.stim) | 4 | 1.74&nbsp;M | 13.3&nbsp;k | 95.6&nbsp;M&nbsp;(55x) | 47.7&nbsp;M&nbsp;(27x) |
| [`distillation_15to1_T_d9_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2505.13587_correlated_decoding_distillation/stim/distillation_15to1_T_d9_p0.001.stim) | 4 | 484&nbsp;k | 13.2&nbsp;k | unsupported | 8.62&nbsp;M&nbsp;(18x) |
| **[2507.12511](https://arxiv.org/abs/2507.12511)** Ruiz et al. (2025), *Unfolded distillation: very low-cost magic state preparation for biased-noise qubits* | | | | | |
| [`unfolded_repetition_no_preselection_pz1e-3_rounds2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_repetition_no_preselection_pz1e-3_rounds2.stim) | 4 | 33.6&nbsp;M | 20.6&nbsp;M | 8.95&nbsp;B&nbsp;(267x) | 1.75&nbsp;B&nbsp;(52x) |
| [`unfolded_repetition_no_preselection_pz1e-3_rounds4`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_repetition_no_preselection_pz1e-3_rounds4.stim) | 4 | 21.3&nbsp;M | 9.29&nbsp;M | 4.13&nbsp;B&nbsp;(194x) | 1.3&nbsp;B&nbsp;(61x) |
| [`unfolded_repetition_no_preselection_pz1e-3_rounds6`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_repetition_no_preselection_pz1e-3_rounds6.stim) | 4 | 16.2&nbsp;M | 6.86&nbsp;M | 2.7&nbsp;B&nbsp;(166x) | 1.16&nbsp;B&nbsp;(71x) |
| [`unfolded_surface_no_bitflip_pz1e-3_rounds2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_surface_no_bitflip_pz1e-3_rounds2.stim) | 4 | 21.3&nbsp;M | 9.69&nbsp;M | 3.17&nbsp;B&nbsp;(149x) | 1.08&nbsp;B&nbsp;(51x) |
| [`unfolded_surface_no_bitflip_pz1e-3_rounds4`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_surface_no_bitflip_pz1e-3_rounds4.stim) | 4 | 13.7&nbsp;M | 6.49&nbsp;M | 1.65&nbsp;B&nbsp;(120x) | 674&nbsp;M&nbsp;(49x) |
| [`unfolded_surface_no_bitflip_pz1e-3_rounds6`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2507.12511_unfolded_distillation/stim/unfolded_surface_no_bitflip_pz1e-3_rounds6.stim) | 4 | 10.1&nbsp;M | 4.89&nbsp;M | 1.12&nbsp;B&nbsp;(111x) | 479&nbsp;M&nbsp;(47x) |
| **[2509.05212](https://arxiv.org/abs/2509.05212)** Sahay et al. (2025), *Fold-transversal surface code cultivation* | | | | | |
| [`fold-d3_native_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.05212_fold_transversal_cultivation/stim/fold-d3_native_T_p0.001.stim) | 6 | 16.5&nbsp;M | 8.04&nbsp;M | 1.33&nbsp;B&nbsp;(81x) | 184&nbsp;M&nbsp;(11x) |
| [`fold-d5_native_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.05212_fold_transversal_cultivation/stim/fold-d5_native_T_p0.001.stim) | 8 | 90.2&nbsp;k | timeout | 82&nbsp;M&nbsp;(910x) | 13.5&nbsp;M&nbsp;(150x) |
| **[2509.08658](https://arxiv.org/abs/2509.08658)** Wan et al. (2025), *Simulating magic state cultivation with few Clifford terms* | | | | | |
| [`d3_cultivation_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.08658_few_clifford_terms/stim/d3_cultivation_T_p0.001.stim) | 4 | 30.8&nbsp;M | 15.9&nbsp;M | 10.7&nbsp;B&nbsp;(347x) | 1.77&nbsp;B&nbsp;(57x) |
| **[2509.18294](https://arxiv.org/abs/2509.18294)** Ismail et al. (2025), *Transversal architecture for megaquop-scale quantum simulation with neutral atoms (transversal STAR)* | | | | | |
| [`star_d=11`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=11.stim) | 2 | 2.92&nbsp;M | 2.35&nbsp;M | 242&nbsp;M&nbsp;(83x) | 158&nbsp;M&nbsp;(54x) |
| [`star_d=13`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=13.stim) | 2 | 1.81&nbsp;M | 1.49&nbsp;M | 144&nbsp;M&nbsp;(79x) | 103&nbsp;M&nbsp;(57x) |
| [`star_d=15`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=15.stim) | 2 | 1.18&nbsp;M | 795&nbsp;k | 100&nbsp;M&nbsp;(85x) | 41.1&nbsp;M&nbsp;(35x) |
| [`star_d=3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=3.stim) | 2 | 37.7&nbsp;M | 34.6&nbsp;M | 6.72&nbsp;B&nbsp;(178x) | 2.55&nbsp;B&nbsp;(68x) |
| [`star_d=5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=5.stim) | 2 | 17.2&nbsp;M | 10.7&nbsp;M | 1.94&nbsp;B&nbsp;(113x) | 1e+03&nbsp;M&nbsp;(58x) |
| [`star_d=7`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=7.stim) | 2 | 9.02&nbsp;M | 6&nbsp;M | 817&nbsp;M&nbsp;(91x) | 368&nbsp;M&nbsp;(41x) |
| [`star_d=9`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2509.18294_transversal_star/stim/star_d=9.stim) | 2 | 4.99&nbsp;M | 3.55&nbsp;M | 419&nbsp;M&nbsp;(84x) | 215&nbsp;M&nbsp;(43x) |
| **[2510.07269](https://arxiv.org/abs/2510.07269)** Li et al. (2025), *Transversal dimension jump for product qLDPC codes* | | | | | |
| [`blp_27_3_3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/blp_27_3_3.stim) | 26 | 35.1&nbsp;s/shot | 4.08&nbsp;k | – | – |
| [`toric_375_3_5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/toric_375_3_5.stim) | 186* | – | OOM | – | – |
| [`toric_81_3_3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/toric_81_3_3.stim) | 63* | – | 574 | – | – |
| [`tricycle_12_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_12_3_2.stim) | 16 | 451 | 44.6&nbsp;k | – | – |
| [`tricycle_15_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_15_3_2.stim) | 16 | 195 | 20.4&nbsp;k | – | – |
| [`tricycle_18_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_18_3_2.stim) | 20 | 10.4 | 12.3&nbsp;k | – | – |
| [`tricycle_21_3_3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_21_3_3.stim) | 23 | 4.11&nbsp;s/shot | 8.07&nbsp;k | – | – |
| [`tricycle_24_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_24_3_2.stim) | 20 | 3.19 | 6.38&nbsp;k | – | – |
| [`tricycle_27_3_3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_27_3_3.stim) | 24 | 11.5&nbsp;s/shot | 5.17&nbsp;k | – | – |
| [`tricycle_6_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_6_3_2.stim) | 9 | 2.3&nbsp;M | 2.94&nbsp;M | 138&nbsp;M&nbsp;(60x) | 13.5&nbsp;M&nbsp;(5.9x) |
| [`tricycle_9_3_2`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.07269_transversal_dimension_jump/stim/tricycle_9_3_2.stim) | 11 | 116&nbsp;k | 105&nbsp;k | 19.1&nbsp;M&nbsp;(165x) | 894&nbsp;k&nbsp;(7.7x) |
| **[2510.24615](https://arxiv.org/abs/2510.24615)** Hirano et al. (2025), *Efficient magic state cultivation with lattice surgery* | | | | | |
| [`inject-check-3_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.24615_lattice_surgery_cultivation/stim/inject-check-3_T.stim) | 4 | 32.7&nbsp;M | 14.6&nbsp;M | 14.2&nbsp;B&nbsp;(435x) | 1.78&nbsp;B&nbsp;(55x) |
| [`lattice-surgery-complementary-gap-3-to-5-to-7_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2510.24615_lattice_surgery_cultivation/stim/lattice-surgery-complementary-gap-3-to-5-to-7_T.stim) | 4 | 16.5&nbsp;M | 6.97&nbsp;M | 2.46&nbsp;B&nbsp;(149x) | 927&nbsp;M&nbsp;(56x) |
| **[2512.13908](https://arxiv.org/abs/2512.13908)** Rosenfeld et al. (2025), *Magic state cultivation on a superconducting quantum processor* | | | | | |
| [`fig2_cultivation_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_cultivation_stim_X_T.stim) | 4 | 97.7&nbsp;M | 98.6&nbsp;M | 26.7&nbsp;B&nbsp;(273x) | 3.9&nbsp;B&nbsp;(40x) |
| [`fig2_cultivation_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_cultivation_stim_Z_T.stim) | 4 | 97.7&nbsp;M | 89.9&nbsp;M | 26.5&nbsp;B&nbsp;(272x) | 3.91&nbsp;B&nbsp;(40x) |
| [`fig2_injection_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_injection_stim_X_T.stim) | 1 | 98&nbsp;M | 129&nbsp;M | 36.9&nbsp;B&nbsp;(377x) | 4.36&nbsp;B&nbsp;(45x) |
| [`fig2_injection_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_injection_stim_Z_T.stim) | 1 | 97.9&nbsp;M | 129&nbsp;M | 36.9&nbsp;B&nbsp;(377x) | 4.39&nbsp;B&nbsp;(45x) |
| [`fig2_simulation_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_simulation_stim_X_T.stim) | 4 | 97.7&nbsp;M | 100&nbsp;M | 26.7&nbsp;B&nbsp;(273x) | 3.91&nbsp;B&nbsp;(40x) |
| [`fig2_simulation_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig2_simulation_stim_Z_T.stim) | 4 | 97.8&nbsp;M | 89.7&nbsp;M | 26.4&nbsp;B&nbsp;(270x) | 3.9&nbsp;B&nbsp;(40x) |
| [`fig3_injection_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_injection_stim_T.stim) | 4 | 97.5&nbsp;M | 48.4&nbsp;M | 13.2&nbsp;B&nbsp;(135x) | 2.09&nbsp;B&nbsp;(21x) |
| [`fig3_simulation_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_simulation_stim_T.stim) | 4 | 97.2&nbsp;M | 31.6&nbsp;M | 7.55&nbsp;B&nbsp;(78x) | 1.35&nbsp;B&nbsp;(14x) |
| [`fig3_simulation_zoom_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_simulation_zoom_stim_T.stim) | 4 | 97&nbsp;M | 31.5&nbsp;M | 7.55&nbsp;B&nbsp;(78x) | 1.36&nbsp;B&nbsp;(14x) |
| [`fig3_with_idle_rounds_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_with_idle_rounds_stim_T.stim) | 4 | 97&nbsp;M | 31.4&nbsp;M | 7.55&nbsp;B&nbsp;(78x) | 1.36&nbsp;B&nbsp;(14x) |
| [`fig3_with_idle_rounds_zoom_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_with_idle_rounds_zoom_stim_T.stim) | 4 | 97.2&nbsp;M | 31.6&nbsp;M | 7.55&nbsp;B&nbsp;(78x) | 1.35&nbsp;B&nbsp;(14x) |
| [`fig3_without_idle_rounds_stim_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig3_without_idle_rounds_stim_T.stim) | 4 | 97.7&nbsp;M | 74.9&nbsp;M | 13.1&nbsp;B&nbsp;(134x) | 2.65&nbsp;B&nbsp;(27x) |
| [`fig4_cultivation_N2_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N2_stim_X_T.stim) | 4 | 89.7&nbsp;M | 59.8&nbsp;M | 5.83&nbsp;B&nbsp;(65x) | 2.48&nbsp;B&nbsp;(28x) |
| [`fig4_cultivation_N2_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N2_stim_Z_T.stim) | 4 | 89.6&nbsp;M | 59.8&nbsp;M | 5.83&nbsp;B&nbsp;(65x) | 2.49&nbsp;B&nbsp;(28x) |
| [`fig4_cultivation_N3_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N3_stim_X_T.stim) | 4 | 89.7&nbsp;M | 61&nbsp;M | 4.33&nbsp;B&nbsp;(48x) | 2.96&nbsp;B&nbsp;(33x) |
| [`fig4_cultivation_N3_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_cultivation_N3_stim_Z_T.stim) | 4 | 89.2&nbsp;M | 59.5&nbsp;M | 4.34&nbsp;B&nbsp;(49x) | 2.98&nbsp;B&nbsp;(33x) |
| [`fig4_injection_N2_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_injection_N2_stim_X_T.stim) | 1 | 97.9&nbsp;M | 127&nbsp;M | 6.53&nbsp;B&nbsp;(67x) | 3.24&nbsp;B&nbsp;(33x) |
| [`fig4_injection_N2_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_injection_N2_stim_Z_T.stim) | 1 | 93.3&nbsp;M | 126&nbsp;M | 6.53&nbsp;B&nbsp;(70x) | 3.22&nbsp;B&nbsp;(34x) |
| [`fig4_simulation_injection_N2_stim_X_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_simulation_injection_N2_stim_X_T.stim) | 1 | 98&nbsp;M | 125&nbsp;M | 6.54&nbsp;B&nbsp;(67x) | 3.21&nbsp;B&nbsp;(33x) |
| [`fig4_simulation_injection_N2_stim_Z_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.13908_google_cultivation_experiment/stim/fig4_simulation_injection_N2_stim_Z_T.stim) | 1 | 98&nbsp;M | 126&nbsp;M | 6.51&nbsp;B&nbsp;(66x) | 3.21&nbsp;B&nbsp;(33x) |
| **[2512.23037](https://arxiv.org/abs/2512.23037)** Li et al. (2025), *SOFT: a high-performance simulator for universal fault-tolerant quantum circuits* | | | | | |
| [`circuit_d3_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.23037_soft/stim/circuit_d3_p0.001.stim) | 4 | 29.4&nbsp;M | 15.5&nbsp;M | 13.4&nbsp;B&nbsp;(457x) | 1.49&nbsp;B&nbsp;(51x) |
| [`circuit_d5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2512.23037_soft/stim/circuit_d5_p0.001.stim) | 6 | 270&nbsp;k | 24.9&nbsp;k | 1.74&nbsp;B&nbsp;(6431x) | 211&nbsp;M&nbsp;(778x) |
| **[2603.05429](https://arxiv.org/abs/2603.05429)** Hetényi et al. (2026), *Constant-depth magic state cultivation with Clifford measurements by gauging* | | | | | |
| [`gauging_cultivation_d3_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2603.05429_gauging_clifford_cultivation/stim/gauging_cultivation_d3_T_p0.001.stim) | 4 | 13.6&nbsp;M | 1.64&nbsp;M | 7.65&nbsp;B&nbsp;(562x) | 1&nbsp;B&nbsp;(74x) |
| [`gauging_cultivation_d5_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2603.05429_gauging_clifford_cultivation/stim/gauging_cultivation_d5_T_p0.001.stim) | 6 | 204&nbsp;k | 14.4&nbsp;k | 504&nbsp;M&nbsp;(2472x) | 73.9&nbsp;M&nbsp;(362x) |
| [`gauging_cultivation_d7_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2603.05429_gauging_clifford_cultivation/stim/gauging_cultivation_d7_T_p0.001.stim) | 8 | 14.1&nbsp;k | 2.37&nbsp;k | 55.4&nbsp;M&nbsp;(3935x) | 7.19&nbsp;M&nbsp;(511x) |
| **[2604.01059](https://arxiv.org/abs/2604.01059)** Haenel et al. (2026), *Tsim: Fast Universal Simulator for Quantum Error Correction* | | | | | |
| [`distillation_color_d5_X`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_color_d5_X.stim) | 4 | 16.8&nbsp;M | 12.4&nbsp;M | 8.93&nbsp;B&nbsp;(531x) | 1.46&nbsp;B&nbsp;(87x) |
| [`distillation_color_d5_Y`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_color_d5_Y.stim) | 3 | 17&nbsp;M | 12.4&nbsp;M | 8.78&nbsp;B&nbsp;(516x) | 1.56&nbsp;B&nbsp;(92x) |
| [`distillation_color_d5_Z`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_color_d5_Z.stim) | 3 | 14.5&nbsp;M | 8.38&nbsp;M | 8.95&nbsp;B&nbsp;(617x) | 1.36&nbsp;B&nbsp;(94x) |
| [`distillation_steane_d3_X`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_steane_d3_X.stim) | 4 | 27.1&nbsp;M | 17.4&nbsp;M | 16.3&nbsp;B&nbsp;(602x) | 1.95&nbsp;B&nbsp;(72x) |
| [`distillation_steane_d3_Y`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_steane_d3_Y.stim) | 3 | 27.1&nbsp;M | 17.4&nbsp;M | 18&nbsp;B&nbsp;(663x) | 2.12&nbsp;B&nbsp;(78x) |
| [`distillation_steane_d3_Z`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_steane_d3_Z.stim) | 3 | 22.1&nbsp;M | 10.8&nbsp;M | 15.5&nbsp;B&nbsp;(702x) | 1.76&nbsp;B&nbsp;(80x) |
| [`distillation_unencoded_X`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_unencoded_X.stim) | 4 | 42.7&nbsp;M | 14.1&nbsp;M | 17.6&nbsp;B&nbsp;(412x) | 2.25&nbsp;B&nbsp;(53x) |
| [`distillation_unencoded_Y`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_unencoded_Y.stim) | 3 | 42.8&nbsp;M | 15.4&nbsp;M | 20.2&nbsp;B&nbsp;(472x) | 2.47&nbsp;B&nbsp;(58x) |
| [`distillation_unencoded_Z`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.01059_tsim/stim/distillation_unencoded_Z.stim) | 3 | 34.2&nbsp;M | 10.8&nbsp;M | 16.7&nbsp;B&nbsp;(489x) | 1.98&nbsp;B&nbsp;(58x) |
| **[2604.05126](https://arxiv.org/abs/2604.05126)** Liu et al. (2026), *In-Situ Simultaneous Magic State Injection on Arbitrary CSS qLDPC Codes* | | | | | |
| [`bb144_cfg328_inj5_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg328_inj5_T_p0.001.stim) | 1 | 6&nbsp;M | 6.13&nbsp;M | 923&nbsp;M&nbsp;(154x) | 406&nbsp;M&nbsp;(68x) |
| [`bb144_cfg342_inj3_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg342_inj3_T_p0.001.stim) | 1 | 6.82&nbsp;M | 6.88&nbsp;M | 892&nbsp;M&nbsp;(131x) | 408&nbsp;M&nbsp;(60x) |
| [`bb144_cfg369_inj1_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg369_inj1_T_p0.001.stim) | 1 | 7.9&nbsp;M | 7.93&nbsp;M | 925&nbsp;M&nbsp;(117x) | 414&nbsp;M&nbsp;(52x) |
| [`bb144_cfg422_inj2_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg422_inj2_T_p0.001.stim) | 1 | 7.28&nbsp;M | 7.34&nbsp;M | 912&nbsp;M&nbsp;(125x) | 408&nbsp;M&nbsp;(56x) |
| [`bb144_cfg491_inj4_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg491_inj4_T_p0.001.stim) | 1 | 6.39&nbsp;M | 6.5&nbsp;M | 924&nbsp;M&nbsp;(145x) | 407&nbsp;M&nbsp;(64x) |
| [`bb144_cfg88_inj6_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.05126_qldpc_magic_state_injection/stim/bb144_cfg88_inj6_T_p0.001.stim) | 1 | 5.71&nbsp;M | 5.83&nbsp;M | 947&nbsp;M&nbsp;(166x) | 438&nbsp;M&nbsp;(77x) |
| **[2604.27058](https://arxiv.org/abs/2604.27058)** Chase and Labib (2026), *Clifft: Fast Exact Simulation of Near-Clifford Quantum Circuits* | | | | | |
| [`coherent_d3_r1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/coherent_d3_r1.stim) | 0 | 1.27&nbsp;B | 1.27&nbsp;B | 23.4&nbsp;B&nbsp;(18x) | 5.72&nbsp;B&nbsp;(4.5x) |
| [`coherent_d3_r3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/coherent_d3_r3.stim) | 4 | 20.8&nbsp;M | 13.1&nbsp;M | 10.3&nbsp;B&nbsp;(494x) | 975&nbsp;M&nbsp;(47x) |
| [`coherent_d5_r1`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/coherent_d5_r1.stim) | 0 | 630&nbsp;M | 640&nbsp;M | 12.9&nbsp;B&nbsp;(20x) | 4.46&nbsp;B&nbsp;(7.1x) |
| [`coherent_d5_r5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/coherent_d5_r5.stim) | 11 | 1.82&nbsp;k | 1.66&nbsp;k | 2.53&nbsp;M&nbsp;(1390x) | 453&nbsp;k&nbsp;(248x) |
| [`cultivation_d3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/cultivation_d3.stim) | 4 | 29.4&nbsp;M | 15.4&nbsp;M | 13.4&nbsp;B&nbsp;(455x) | 1.49&nbsp;B&nbsp;(51x) |
| [`cultivation_d5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/cultivation_d5.stim) | 6 | 1.21&nbsp;M | 60.4&nbsp;k | 1.4&nbsp;B&nbsp;(1164x) | 170&nbsp;M&nbsp;(141x) |
| [`distillation`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/distillation.stim) | 3 | 14.5&nbsp;M | 8.47&nbsp;M | 8.93&nbsp;B&nbsp;(616x) | 1.36&nbsp;B&nbsp;(94x) |
| [`surface_d7_r7`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2604.27058_clifft/stim/surface_d7_r7.stim) | 0 | 18.5&nbsp;M | 18.5&nbsp;M | 1.27&nbsp;B&nbsp;(69x) | 785&nbsp;M&nbsp;(42x) |
| **[2607.28600](https://arxiv.org/abs/2607.28600)** Fang et al. (2026), *SymFT: Universal Fault-Tolerant Quantum Circuit Simulation via Symbolic Clifford–Pauli Frames and Stabilizer Coordinates* | | | | | |
| [`MSC_circuit_d7_p0.0005`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/MSC_circuit_d7_p0.0005.stim) | 8 | 35.4&nbsp;k | 4.96&nbsp;k | 240&nbsp;M&nbsp;(6789x) | 32.6&nbsp;M&nbsp;(919x) |
| [`coherent_surface_d3_r1_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/coherent_surface_d3_r1_p1e-3_rz0p02.stim) | 0 | 1.28&nbsp;B | 1.27&nbsp;B | 25.1&nbsp;B&nbsp;(20x) | 5.7&nbsp;B&nbsp;(4.5x) |
| [`coherent_surface_d3_r3_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/coherent_surface_d3_r3_p1e-3_rz0p02.stim) | 4 | 20.9&nbsp;M | 13.4&nbsp;M | 9.84&nbsp;B&nbsp;(472x) | 974&nbsp;M&nbsp;(47x) |
| [`coherent_surface_d5_r1_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/coherent_surface_d5_r1_p1e-3_rz0p02.stim) | 0 | 627&nbsp;M | 638&nbsp;M | 13.1&nbsp;B&nbsp;(21x) | 4.45&nbsp;B&nbsp;(7.1x) |
| [`coherent_surface_d5_r5_p1e-3_rz0p02`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/coherent_surface_d5_r5_p1e-3_rz0p02.stim) | 11 | 1.82&nbsp;k | 1.66&nbsp;k | 2.53&nbsp;M&nbsp;(1390x) | 457&nbsp;k&nbsp;(251x) |
| [`distillation`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/distillation.stim) | 3 | 14.2&nbsp;M | 8.49&nbsp;M | 8.76&nbsp;B&nbsp;(616x) | 1.37&nbsp;B&nbsp;(96x) |
| [`msc_d3_inject_cultivate_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/msc_d3_inject_cultivate_p1e-3.stim) | 4 | 29.4&nbsp;M | 15.5&nbsp;M | 13.4&nbsp;B&nbsp;(455x) | 1.49&nbsp;B&nbsp;(51x) |
| [`msc_d5_inject_cultivate_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/msc_d5_inject_cultivate_p1e-3.stim) | 6 | 1.23&nbsp;M | 63.5&nbsp;k | 1.4&nbsp;B&nbsp;(1142x) | 171&nbsp;M&nbsp;(139x) |
| [`msc_proxy_d7_unverified_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/msc_proxy_d7_unverified_p1e-3.stim) | 6 | 466&nbsp;k | 37.7&nbsp;k | 1.09&nbsp;B&nbsp;(2335x) | 148&nbsp;M&nbsp;(317x) |
| [`pure_surface_d7_r7_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/pure_surface_d7_r7_p1e-3.stim) | 0 | 18.5&nbsp;M | 18.5&nbsp;M | 1.27&nbsp;B&nbsp;(68x) | 782&nbsp;M&nbsp;(42x) |
| [`pure_surface_d9_r9_p1e-3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2607.28600_symft/stim/pure_surface_d9_r9_p1e-3.stim) | 0 | 8.38&nbsp;M | 8.38&nbsp;M | 602&nbsp;M&nbsp;(72x) | 395&nbsp;M&nbsp;(47x) |
| **[2609.17706](https://arxiv.org/abs/2609.17706)** Chan et al. (2026), *Diagnosing and Restoring the Degraded Fault Distance of Magic State Cultivation* | | | | | |
| [`d3a6_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d3a6_inject_cultivate_T_p0.001.stim) | 4 | 29.4&nbsp;M | 15.5&nbsp;M | 13.7&nbsp;B&nbsp;(467x) | 1.51&nbsp;B&nbsp;(51x) |
| [`d3a6f2_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d3a6f2_inject_cultivate_T_p0.001.stim) | 4 | 27.3&nbsp;M | 13.6&nbsp;M | 13.6&nbsp;B&nbsp;(500x) | 1.49&nbsp;B&nbsp;(55x) |
| [`d5a19_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19_inject_cultivate_T_p0.001.stim) | 6 | 1.04&nbsp;M | 63.1&nbsp;k | 1.13&nbsp;B&nbsp;(1080x) | 149&nbsp;M&nbsp;(143x) |
| [`d5a19f13_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19f13_inject_cultivate_T_p0.001.stim) | 6 | 952&nbsp;k | 57.1&nbsp;k | 1.12&nbsp;B&nbsp;(1177x) | 151&nbsp;M&nbsp;(158x) |
| [`d5a19r4_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19r4_inject_cultivate_T_p0.001.stim) | 6 | 966&nbsp;k | 54.7&nbsp;k | 1.13&nbsp;B&nbsp;(1165x) | 151&nbsp;M&nbsp;(156x) |
| [`d5a19r4f13_inject_cultivate_T_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.17706_chan_color_code_cultivation/stim/d5a19r4f13_inject_cultivate_T_p0.001.stim) | 6 | 876&nbsp;k | 52.9&nbsp;k | 1.1&nbsp;B&nbsp;(1257x) | 144&nbsp;M&nbsp;(164x) |
| **[2609.18922](https://arxiv.org/abs/2609.18922)** Wan and Zapirain (2026), *Exact logical error rates for magic state cultivation* | | | | | |
| [`clifft_d3_p001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.18922_exact_ler_cultivation/stim/clifft_d3_p001.stim) | 4 | 29.5&nbsp;M | 15.5&nbsp;M | 13.5&nbsp;B&nbsp;(458x) | 1.49&nbsp;B&nbsp;(51x) |
| [`soft_cultivation_d5_p0005`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2609.18922_exact_ler_cultivation/stim/soft_cultivation_d5_p0005.stim) | 6 | 140&nbsp;k | 10.9&nbsp;k | 1.5&nbsp;B&nbsp;(10733x) | 177&nbsp;M&nbsp;(1263x) |
| **[2610.03869](https://arxiv.org/abs/2610.03869)** Lange et al. (2026), *Modular Neural Decoder for Surface Code Memory and Logic on Superconducting Processors* | | | | | |
| [`stability_d3_X_t100_alpha0.5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t100_alpha0.5_p0.001.stim) | 3 | 53.2&nbsp;k | 108 | 283&nbsp;M&nbsp;(5322x) | 13.4&nbsp;M&nbsp;(253x) |
| [`stability_d3_X_t20_alpha0.15_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t20_alpha0.15_p0.001.stim) | 3 | 1.67&nbsp;M | 47.3&nbsp;k | 1.56&nbsp;B&nbsp;(929x) | 111&nbsp;M&nbsp;(66x) |
| [`stability_d3_X_t20_alpha0.5_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t20_alpha0.5_p0.001.stim) | 3 | 373&nbsp;k | 5&nbsp;k | 1.5&nbsp;B&nbsp;(4032x) | 110&nbsp;M&nbsp;(295x) |
| [`stability_d3_X_t20_alpha1.0_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.03869_modular_neural_decoder/stim/stability_d3_X_t20_alpha1.0_p0.001.stim) | 3 | 200&nbsp;k | 2.9&nbsp;k | 974&nbsp;M&nbsp;(4880x) | 85.6&nbsp;M&nbsp;(429x) |
| **[2610.06811](https://arxiv.org/abs/2610.06811)** Cercelescu et al. (2026), *Polynomial-time simulation of non-Clifford quantum error correction (Merlin)* | | | | | |
| [`code_switching_bt27_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/code_switching_bt27_p0.001.stim) | 26 | 41&nbsp;s/shot | timeout | – | – |
| [`code_switching_bt81_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/code_switching_bt81_p0.001.stim) | 63* | – | error | – | – |
| [`cultivation_d3_t`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/cultivation_d3_t.stim) | 4 | 29.4&nbsp;M | 15.5&nbsp;M | 13.4&nbsp;B&nbsp;(458x) | 1.5&nbsp;B&nbsp;(51x) |
| [`cultivation_d5_t`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/cultivation_d5_t.stim) | 6 | 1.23&nbsp;M | 63.6&nbsp;k | 1.4&nbsp;B&nbsp;(1140x) | 171&nbsp;M&nbsp;(140x) |
| [`distillation_15to1_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_15to1_p0.001.stim) | 4 | 117&nbsp;M | 151&nbsp;M | 25.9&nbsp;B&nbsp;(222x) | 3.74&nbsp;B&nbsp;(32x) |
| [`distillation_bh10_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh10_p0.001.stim) | 4 | 111&nbsp;M | 79.9&nbsp;M | 10.4&nbsp;B&nbsp;(94x) | 1.17&nbsp;B&nbsp;(11x) |
| [`distillation_bh12_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh12_p0.001.stim) | 4 | 71.7&nbsp;M | 36.2&nbsp;M | 6.09&nbsp;B&nbsp;(85x) | 734&nbsp;M&nbsp;(10x) |
| [`distillation_bh14_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh14_p0.001.stim) | 4 | 108&nbsp;M | 67.6&nbsp;M | 7.52&nbsp;B&nbsp;(70x) | 802&nbsp;M&nbsp;(7.4x) |
| [`distillation_bh16_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh16_p0.001.stim) | 4 | 71.3&nbsp;M | 30.4&nbsp;M | 5.09&nbsp;B&nbsp;(71x) | 577&nbsp;M&nbsp;(8.1x) |
| [`distillation_bh18_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh18_p0.001.stim) | 4 | 105&nbsp;M | 58.9&nbsp;M | 6.58&nbsp;B&nbsp;(62x) | 645&nbsp;M&nbsp;(6.1x) |
| [`distillation_bh2_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh2_p0.001.stim) | 4 | 117&nbsp;M | 149&nbsp;M | 25.8&nbsp;B&nbsp;(221x) | 3.72&nbsp;B&nbsp;(32x) |
| [`distillation_bh4_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh4_p0.001.stim) | 4 | 74.9&nbsp;M | 59.8&nbsp;M | 13.9&nbsp;B&nbsp;(186x) | 1.64&nbsp;B&nbsp;(22x) |
| [`distillation_bh6_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh6_p0.001.stim) | 4 | 114&nbsp;M | 107&nbsp;M | 13.1&nbsp;B&nbsp;(115x) | 1.9&nbsp;B&nbsp;(17x) |
| [`distillation_bh8_p0.001`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06811_merlin/stim/distillation_bh8_p0.001.stim) | 4 | 74.2&nbsp;M | 46.5&nbsp;M | 9.23&nbsp;B&nbsp;(124x) | 1.01&nbsp;B&nbsp;(14x) |
| **[2610.06828](https://arxiv.org/abs/2610.06828)** Mehta et al. (2026), *The practical cost of magic state cultivation* | | | | | |
| [`color_code_cultivation_f3_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06828_practical_cost_cultivation/stim/color_code_cultivation_f3_T.stim) | 4 | 1.39&nbsp;M | 1.2&nbsp;M | 199&nbsp;M&nbsp;(143x) | 115&nbsp;M&nbsp;(83x) |
| [`color_code_cultivation_f5_T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.06828_practical_cost_cultivation/stim/color_code_cultivation_f5_T.stim) | 6 | 540&nbsp;k | 47.4&nbsp;k | 154&nbsp;M&nbsp;(286x) | 68.6&nbsp;M&nbsp;(127x) |
| **[2610.22315](https://arxiv.org/abs/2610.22315)** Wang and Gu (2026), *Magna: simulating magic state factories as cheaply as Clifford circuits* | | | | | |
| [`bh10-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh10-S.stim) | 0 | 1.22&nbsp;B | 1.22&nbsp;B | 48.3&nbsp;B&nbsp;(40x) | 6.65&nbsp;B&nbsp;(5.4x) |
| [`bh10-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh10-T.stim) | 3 | 30.1&nbsp;M | 15.2&nbsp;M | 17.5&nbsp;B&nbsp;(583x) | 2.41&nbsp;B&nbsp;(80x) |
| [`bh100-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh100-S.stim) | 0 | 292&nbsp;M | 292&nbsp;M | 47.8&nbsp;B&nbsp;(164x) | 6.62&nbsp;B&nbsp;(23x) |
| [`bh100-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh100-T.stim) | 3 | 310&nbsp;k | 3.22&nbsp;k | 1.66&nbsp;B&nbsp;(5376x) | 337&nbsp;M&nbsp;(1088x) |
| [`bh2-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh2-S.stim) | 0 | 1.77&nbsp;B | 1.77&nbsp;B | 47.8&nbsp;B&nbsp;(27x) | 6.66&nbsp;B&nbsp;(3.8x) |
| [`bh2-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh2-T.stim) | 3 | 80.5&nbsp;M | 52&nbsp;M | 29.5&nbsp;B&nbsp;(366x) | 4.04&nbsp;B&nbsp;(50x) |
| [`bh20-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh20-S.stim) | 0 | 884&nbsp;M | 884&nbsp;M | 47.9&nbsp;B&nbsp;(54x) | 6.68&nbsp;B&nbsp;(7.6x) |
| [`bh20-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh20-T.stim) | 3 | 1.54&nbsp;M | 46.9&nbsp;k | 11.1&nbsp;B&nbsp;(7178x) | 1.42&nbsp;B&nbsp;(919x) |
| [`bh4-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh4-S.stim) | 0 | 1.6&nbsp;B | 1.59&nbsp;B | 47.7&nbsp;B&nbsp;(30x) | 6.77&nbsp;B&nbsp;(4.2x) |
| [`bh4-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh4-T.stim) | 3 | 60.8&nbsp;M | 23&nbsp;M | 26.1&nbsp;B&nbsp;(430x) | 3.53&nbsp;B&nbsp;(58x) |
| [`bh40-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh40-S.stim) | 0 | 576&nbsp;M | 575&nbsp;M | 47.8&nbsp;B&nbsp;(83x) | 6.65&nbsp;B&nbsp;(12x) |
| [`bh40-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh40-T.stim) | 3 | 805&nbsp;k | 10.9&nbsp;k | 5.94&nbsp;B&nbsp;(7373x) | 809&nbsp;M&nbsp;(1005x) |
| [`bh6-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh6-S.stim) | 0 | 1.44&nbsp;B | 1.44&nbsp;B | 47.7&nbsp;B&nbsp;(33x) | 6.75&nbsp;B&nbsp;(4.7x) |
| [`bh6-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh6-T.stim) | 3 | 48.6&nbsp;M | 17.8&nbsp;M | 23&nbsp;B&nbsp;(474x) | 3.02&nbsp;B&nbsp;(62x) |
| [`bh60-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh60-S.stim) | 0 | 431&nbsp;M | 430&nbsp;M | 47.6&nbsp;B&nbsp;(111x) | 6.64&nbsp;B&nbsp;(15x) |
| [`bh60-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh60-T.stim) | 3 | 548&nbsp;k | 6.66&nbsp;k | 3.66&nbsp;B&nbsp;(6676x) | 539&nbsp;M&nbsp;(984x) |
| [`bh80-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh80-S.stim) | 0 | 346&nbsp;M | 346&nbsp;M | 47.5&nbsp;B&nbsp;(137x) | 6.65&nbsp;B&nbsp;(19x) |
| [`bh80-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/bh80-T.stim) | 3 | 384&nbsp;k | 4.57&nbsp;k | 2.85&nbsp;B&nbsp;(7432x) | 417&nbsp;M&nbsp;(1087x) |
| [`color3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/color3.stim) | 4 | 33.3&nbsp;M | 18.7&nbsp;M | 16&nbsp;B&nbsp;(480x) | 1.87&nbsp;B&nbsp;(56x) |
| [`color5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/color5.stim) | 6 | 271&nbsp;k | 24.5&nbsp;k | 1.72&nbsp;B&nbsp;(6368x) | 212&nbsp;M&nbsp;(784x) |
| [`dk`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/dk.stim) | 4 | 41.6&nbsp;M | 31.3&nbsp;M | 16.9&nbsp;B&nbsp;(406x) | 2.45&nbsp;B&nbsp;(59x) |
| [`rp2-d3-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/rp2-d3-S.stim) | 0 | 36.9&nbsp;M | 52&nbsp;M | 8.04&nbsp;B&nbsp;(218x) | 3.25&nbsp;B&nbsp;(88x) |
| [`rp2-d3`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/rp2-d3.stim) | 4 | 14.7&nbsp;M | 3.89&nbsp;M | 8.41&nbsp;B&nbsp;(572x) | 1.08&nbsp;B&nbsp;(74x) |
| [`rp2-d5-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/rp2-d5-S.stim) | 0 | 15.6&nbsp;M | 17.4&nbsp;M | 2.99&nbsp;B&nbsp;(192x) | 1.48&nbsp;B&nbsp;(95x) |
| [`rp2-d5`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/rp2-d5.stim) | 9 | 69.2&nbsp;k | 20.5&nbsp;k | 126&nbsp;M&nbsp;(1825x) | 19.1&nbsp;M&nbsp;(276x) |
| [`wg-S`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/wg-S.stim) | 0 | 79.3&nbsp;M | 78.9&nbsp;M | 4.23&nbsp;B&nbsp;(53x) | 3.69&nbsp;B&nbsp;(47x) |
| [`wg-T`](https://github.com/rafaelha/tsim-bench/blob/master/papers/2610.22315_magna/stim/wg-T.stim) | 4 | 8.28&nbsp;M | 781&nbsp;k | 4.21&nbsp;B&nbsp;(509x) | 1.15&nbsp;B&nbsp;(139x) |
<!-- benchmark-table:end -->

## How the numbers were measured

- **k_max** is the largest number of qubits Tsim holds in a dense state vector: one shot costs about 2^k_max amplitudes. It comes from
  compiling the circuit with Tsim 1.0.0's default strategy; nothing is sampled.
- **Shots per second** are for the detector sampler, returning every shot with its observables, bit-packed. Compilation and the first
  (warm-up) call don't count; each rate is the best of three calls of at least 1 s (CPU) or 0.5 s (GPU).
- **CPU (single-core):** Tsim 1.0.0 on one core of a Ryzen 9 9900X, one circuit at a time. Running many single-core jobs side by side halves Tsim's
  rate because they share memory bandwidth, so all CPU numbers are from serial runs.
- **RTX 5090:** the CUDA draft, [PR #219](https://github.com/QuEraComputing/tsim/pull/219) (`a2af975f`).
- **M4 Pro:** the Metal prototype (branch `metal-statevector-executor`, `8b4700d4`), on a 20-core GPU with 48 GB of memory. It
  reuses freed output buffers for the next call, which avoids page faults on fresh multi-GB outputs.
- **Which circuits run where:** the GPUs only run circuits with k_max up to 11, the most their executors support. The CPU column goes
  up to 15, and up to 26 for the tricycle factories (2510.07269) and Merlin's code switching. At k_max = 26 one shot takes 35–41 s on
  one core. Skipped cells show –.

Everything is produced by [`tools/benchmark.py`](tools/benchmark.py) (`uv run python tools/benchmark.py all`), and the raw numbers are
in [`results/benchmark.json`](results/benchmark.json).

## Notes on the table

- **The GPU numbers are mostly limited by copying shots back to the host.** At about 54 GB/s, a circuit with 440 bytes per shot can't
  go much above 120 M shots/s, however fast the kernels are. With postselection, only kept shots are copied: the same d=15 hook-injection
  circuit then runs at 1.5–2.3 B shots/s on the RTX 5090, instead of 124 M.
- **"unsupported"** means the GPU executor refuses the circuit because its rows are too wide for the noise kernel's on-chip memory. This
  happens for the large distillation circuits (CUDA). Metal (`8b4700d4`) writes such rows to device memory and runs them all.
- **OOM** means compiling ran out of memory (capped at 40 GB). Tsim 1.0.0 needs a matrix of detectors × error locations during
  compilation, 121 GiB for the d=25 distillation circuit. [PR #270](https://github.com/QuEraComputing/tsim/pull/270) stores that matrix
  sparsely, and with it these circuits compile in under 5 GB.
- **‡** marks numbers measured with PR #270 instead of 1.0.0, used only where 1.0.0 runs out of memory. The PR doesn't change sampling:
  seeded samples are bit-for-bit identical. The GPU builds don't have the fix yet.
- **\*** marks circuits Tsim refuses to compile: the number is how many active qubits it would need, above its limit of 30.
- **The d=15 hook-injection circuits** only run on the RTX 5090 because the benchmark lets one kernel of the CUDA draft use more on-chip
  memory than it requests by default. Without that the draft fails to launch them; with it its samples match the CPU.

## Tsim compared with Clifft

[`SUMMARY.md`](SUMMARY.md) also has Clifft 0.13.0, run with its active-width scheduler (`ActiveWidthSchedulePass`) at default settings
on one core.
- **Speed:** Tsim is faster on 161 of the 164 circuits both can run (median 6.8x). Clifft is faster on its coherent-noise surface-code
  memory circuit, which appears in both the Clifft and SymFT folders (about 5x), and narrowly on one d=5 cultivation circuit.
- **Active width:** across the 180 circuits both can compile, Tsim's k_max is smaller on 60, the same on 110 and larger on 10.
  - Tsim is much smaller on Bravyi–Haah distillation with T teleportation (Magna): 3 at every size, while Clifft grows to 42 and then
    overflows. Also fold-transversal cultivation d=5 (8 vs 22), gauging d=7 (8 vs 19) and RP² cultivation d=5 (10 vs 18).
  - The 10 where Tsim is larger are Merlin's distillation circuits (4 vs 0). With Merlin's noise model and output check, the whole
    circuit happens to be Clifford, and Clifft spots that and removes every T gate. With other noise or without the check, Clifft needs
    at least 1 ([details](papers/2610.06811_merlin/README.md)).
- **Neither can run:** circuits that need more than 30 active qubits in Tsim (Merlin bt81, the 3D toric tricycle factories), and the
  largest distillation circuits in Clifft, whose compile takes over 30 minutes (Tsim with PR #270 compiles them in 1–4 minutes).

## What's in the repository

    papers/<arxiv-id>_<name>/   one folder per paper
        README.md               where the circuits came from, what was changed, k_max table
        tex/                    the arXiv source (no figures)
        stim_src/               the authors' circuits or generator code, with commit or DOI
        make_circuits.py        writes stim/, converting to real non-Clifford gates and checking the result in Tsim
        stim/                   the circuits that were benchmarked
    tools/                      benchmark, validation and helper scripts
    results/benchmark.json      all measurements
    _search/                    how the papers were found

Run `uv sync` once, then `uv run python papers/<folder>/make_circuits.py` to rebuild a paper's circuits. A few generators need the
authors' own environment; their README says so.

<details>
<summary>Papers that were looked at but not included</summary>

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

</details>

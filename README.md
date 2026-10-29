# Active width of published non-Clifford Stim circuits

Survey of papers that release Stim circuits containing non-Clifford gates (or Clifford
proxies that convert easily to T / CCZ / CS), and the peak active width `k_max` that
Tsim and Clifft achieve on them.

- Tsim: `QuEraComputing/tsim` main at 883d787, `compile_detector_sampler()` with the default
  `active_statevector` strategy; k = largest statevector component width (compile only, no sampling).
- Clifft 0.12.0: `default_hir_pass_manager()` + `ActiveWidthSchedulePass()` (default settings);
  k = `peak_active_width`.

Measure: `uv run python tools/measure_k.py path/to/*.stim`

Each paper gets one folder `papers/<arxiv-id>_<short-name>/` with the arXiv `.tex` source, a
`stim_src/` folder with the original circuit files or code, a `make_circuits.py` that writes the
non-Clifford `.stim` files, and a `README.md`.

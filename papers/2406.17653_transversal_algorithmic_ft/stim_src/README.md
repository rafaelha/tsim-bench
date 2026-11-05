# Transversal Algorithmic Fault Tolerance

Circuits and data for the ["Low-Overhead Transversal Fault Tolerance for Universal Quantum Computation"](https://arxiv.org/abs/2406.17653) paper.

# Installation

This is a [Julia](https://julialang.org/) repository. Make sure you have Julia installed. You can install the dependencies in the `Project.toml` file by running:
```bash
julia --project=. -e 'using Pkg; Pkg.instantiate(); using CondaPkg; CondaPkg.resolve();'
```

To run the scripts, you can use the following commands:
```bash
julia --project=. scripts/figure_3_plot.jl
julia --project=. scripts/figure_4_plot.jl
```

# Contents
- [`circuits/`](circuits/): Stim circuits for the transversal algorithmic fault tolerance paper.
- [`results/`](results/): Decoded statistics for the transversal algorithmic fault tolerance paper.
- [`scripts/`](scripts/): Scripts to generate the plots.
- [`figs/`](figs/): Figures generated from the scripts.

## Circuits
- `circuits/repeated_bell/d={d},p={p}.stim`: Stim circuits for the repeated Bell measurement with distance `d` and physical error rate `p`.
- `circuits/ghz/figure_3_{method}_{d}.stim`: Stim circuits for the GHZ state preparation with method `method` and distance `d`. Available methods are `lattice_surgery` and `transversal`.
- `circuits/s_injection/d={d},p={p},p_injected={p_injected}.stim`: Stim circuits for the S-injection with final distance `d`, physical error rate `p`, and injected S-states error rate `p_injected`.
- `circuits/s_factory/d={d},p={p},p_injected={p_injected}.stim`: Stim circuits for the S factory with distance `d`, physical error rate `p`, and injected S-states error rate `p_injected`.
- `circuits/two_level_s_factory/d={d},p={p},p_injected={p_injected}.stim`: Stim circuits for the two-level S factory with distance `d`, physical error rate `p`, and injected S-states error rate `p_injected`.

> Remarks: since Stim does not support to define a non-deterministic logical observable using `OBSERVABLE_INCLUDE`. But the circuits above include non-deterministic logical observables, so we use `DETECTOR` to define those. When decoding, we generate the detector-error model first using `stim.Circuit.detector_error_model(allow_gauge_detectors=True)`, and focus on the regular detectors to predict those gauge detectors (non-deterministic logical observables).

## Results
- `results/repeated_bell/decoder={decoder}.json`: Decoded statistics for the repeated Bell measurement with the specified decoder.
- `results/s_injection/decoder={decoder}.json`: Decoded statistics for the S-injection with the specified decoder.
- `results/s_factory/decoder={decoder}.json`: Decoded statistics for the S factory with the specified decoder.
- `results/two_level_s_factory/decoder={decoder}.json`: Decoded statistics for the two-level S factory with the specified decoder.
- Available decoders:
  - `mle`: most-likely error decoder.
  - `bhuf`: belief hypergraph union-find decoder.
- Result arguments:
  - `d`: (final) distance of the surface code patch.
  - `p`: physical error rate.
  - `p_injected`: injected S-states error rate (only for S-injection and S factory).
  - `num_samples`: total number of samples used for decoding.
  - `num_ps`: total number of post-selected samples.
  - `num_les`: total number of logical errors (either observable errors or heraled failures).
  - `num_oes`: total number of observable errors (those from `OBSERVABLE_INCLUDES`).
  - `num_hfs`: total number of heraled failures (a list with the length of the total decoding steps).
  - `num_dgs`: total number of shots with disagreements at different steps of decoding (most of the disagreements should be fixed by frame flipping)
  - `psr`: post-selection rate
  - `ler`: logical error rate
  - `oer`: observable error rate
  - `hfr`: heralded failure rate
  - `dgr`: disagreement rate
 
# Licenses
- The code in the directory [`scripts/`](scripts/) of this repository is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
- The data in the directories [`circuits/`](circuits/) and [`results/`](results/) of this repository is licensed under the [Community Data License Agreement Permissive 2.0](https://cdla.dev/permissive-2-0/).

# Benchmark manifests

Every paper folder has a `circuits.toml` that says, for each circuit, which paper it comes from and
how that paper postselects. Simulators read it through the `tsim_bench` package (standard library
only; put this checkout on `sys.path`):

    python -m tsim_bench list  [--suite quick] [--max-width 11 --width-of tsim]
    python -m tsim_bench check [--max-width 20]   # needs Tsim
    python -m tsim_bench run   [--suite quick] [--no-postselect]

Tsim's `tsim-dev bench` uses the same package at a pinned commit of this repo.

## `papers/<folder>/circuits.toml`

```toml
arxiv = "2409.17595"            # the paper of this folder

[circuits."inject_cultivate_d3_p0.001"]   # file stem; the file is stim/<stem>.stim
# file = "stim/other_name.stim"           # only if the path differs
sampler = "detector"            # "detector" (default) or "measurement"
num_detectors = 20
postselect = "all"              # "all", "none", "only" or "all_except"
# detectors = "0-12, 20"        # inclusive index ranges, for "only" and "all_except"
reason = "Injection and cultivation discard every shot in which a check fails (Sec. 2)."
# random_detectors = "12-13"    # masked detectors that are random without noise by design
# detector_reference = true     # sample with use_detector_reference_sample=True
# observable_reference = true   # sample with use_observable_reference_sample=True
# arxiv = "..."                 # only if this circuit comes from another paper
```

- `postselect` follows the protocol of the paper, not convenience: a stage that the paper decodes
  (for example most of the escape stage of end-to-end cultivation, which goes to a gap
  decoder) is not masked; where the authors' code also discards on some of its detectors,
  those are masked too. `reason` says where the
  paper or its code defines the postselected detectors (section, figure, coordinate convention,
  tag), and how the ranges were derived.
- `"none"` is a decision too: say why (a memory experiment, a decoded protocol, ...).
- Tsim reports raw detector values, not flips against a noiseless reference as Stim does. Set
  `detector_reference = true` only if some masked detector is deterministically 1 without noise.
- Some protocols postselect on detectors that are random even without noise, for example
  to select the injected rotation angle (STAR). List them in `random_detectors`; they are
  still masked, and `check` requires them to be random rather than fixed.
- Active widths come from `k_max.json` (`tsim_k`, `clifft_k`, ...), so `--max-width` filters on
  the width recorded for one backend.
- `check` samples each noiseless circuit of Tsim width at most `--max-width` and fails if a
  masked detector ever fires.

## `suites.toml`

Named lists of circuit ids (`<folder>/<file stem>`):

```toml
[quick]
circuits = ["2409.17595_magic_state_cultivation/inject_cultivate_d5_p0.001", ...]
```

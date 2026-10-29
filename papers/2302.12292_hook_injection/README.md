# Cleaner magic states with hook injection

Craig Gidney (2023), [arXiv:2302.12292](https://arxiv.org/abs/2302.12292).

## Where the circuits are

The data is on Zenodo [10.5281/zenodo.7575030](https://zenodo.org/records/7575030) (`circuits.zip`, `code.zip`, `stats.csv`). The code is on GitHub at
[Strilanc/hook-injection](https://github.com/Strilanc/hook-injection), which I used at commit `cdbdcae`. The circuits inject a Y-basis state
|+i⟩ = S|+⟩ (a Clifford stand-in) with four schemes:
- **hook injection:** the injection is a single S = Z^0.5 "hook" rotation on a measurement ancilla, `make_hook_injection_round(exponent=...)`;
- **pregrown hook injection:** the same, starting from the full-size patch;
- **Li injection:** the data qubit is reset with `RY`;
- **ZZ (CPHASE) injection:** a `SQRT_ZZ` gate.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/hook-injection/`: the generator (`src/hookinj`, without tests), `tools/`, `step1_generate_circuits.sh`, README and requirements.
  I did not copy the 7 MB Zenodo `circuits.zip`; it holds the same Y/X-basis circuits at many noise strengths.
- `make_circuits.py` builds the Y-basis "magic verify" variant of each scheme. It uses d=15, d memory rounds, 2 postselected rounds and
  postselected diameters 5 and 7, as in `step1_generate_circuits.sh`, with uniform depolarizing p=0.001. It checks that each circuit contains
  exactly one injection gate and replaces it:
  - S → T (Z^0.25)
  - RY → RX + T
  - SQRT_ZZ → R_ZZ(0.25)
- Noise model: the paper uses SI1000. I used uniform depolarizing without the SI1000 CZ conversion (which `tools/gen_circuits` applies only
  for SI1000), so the injection gate is not fused into neighbouring layers.
- Checks: each circuit is sampled noiselessly in Tsim (1024 shots). No detector is random, every detector value equals the Y-proxy value,
  and the final logical-Y readout gives P(1) ≈ 0.14 as expected for a T state. For ZZ injection, the proxy with `SQRT_ZZ` written as
  `R_ZZ(0.5)` reproduces the proxy exactly, which confirms the half-turn angle convention.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `hook_inject_T_d15_pd5_p0.001.stim` | 1 T | 1 | 1 | 1 |
| `hook_inject_T_d15_pd7_p0.001.stim` | 1 T | 1 | 1 | 1 |
| `li_inject_T_d15_pd5_p0.001.stim` | 1 T | 1 | 1 | 1 |
| `li_inject_T_d15_pd7_p0.001.stim` | 1 T | 1 | 1 | 1 |
| `pregrown_hook_inject_T_d15_pd5_p0.001.stim` | 1 T | 1 | 1 | 1 |
| `pregrown_hook_inject_T_d15_pd7_p0.001.stim` | 1 T | 1 | 1 | 1 |
| `zz_inject_T_d15_pd5_p0.001.stim` | 1 R_ZZ | 1 | 1 | 1 |
| `zz_inject_T_d15_pd7_p0.001.stim` | 1 R_ZZ | 1 | 1 | 1 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

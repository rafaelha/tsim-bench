# Exact logical error rates for magic state cultivation

Kwok Ho Wan, Ainhoa Zapirain (2026), [arXiv:2609.18922](https://arxiv.org/abs/2609.18922).

## Where the circuits are

The companion code and data are at [kh428/exact_ler_for_msc](https://github.com/kh428/exact_ler_for_msc), which I used at commit `332bc04`.
- **Original inputs** (`data/inputs/`): two native-T Stim circuits.
  - `clifft_d3_p001.stim` is d=3 inject+cultivate, taken from Clifft's docs (`circuit_d3_t_gate_p0.001.stim`).
  - `soft_cultivation_d5_p0005.stim` is SOFT's d=5 circuit at p=0.005 with a provenance header. The paper fixes it by SHA-256
    `859d925c…`, and `pauli_semiwebs/circuits/d5_native_t.stim` is the same file.
- **Alternative circuits** (`data/alternatives/inputs/`): RP², fold-transversal and Chan et al. These are stored as the authors' internal
  event-list models (`model.json`), several with different schemas, next to the supplied S-proxy sources. I did not export these models to
  Stim. Their source papers have their own folders: RP² is in [`../2503.18657_rp2_cultivation`](../2503.18657_rp2_cultivation),
  fold-transversal is 2509.05212 and Chan et al. is 2609.17706.

## What I did

- `tex/`: arXiv source. I removed the figures but kept the large TikZ semiweb and detector-web diagrams.
- `stim_src/exact_ler_for_msc/`: README, LICENSE, manifest, docs, `pauli_semiwebs/circuits/`, and `inputs_and_alternative_inputs/` (the
  merged contents of `data/inputs/` and `data/alternatives/inputs/`).
- `stim/`: verbatim copies of the two native-T inputs. No conversion is needed.
- Check: both circuits are sampled noiselessly in Tsim (4096 shots). All detectors are deterministic and the observable is always 0.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `clifft_d3_p001.stim` | 15 T_DAG, 14 T | 4 | 4 | 4 |
| `soft_cultivation_d5_p0005.stim` | 33 T_DAG, 39 T | 6 | 10 | 10 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

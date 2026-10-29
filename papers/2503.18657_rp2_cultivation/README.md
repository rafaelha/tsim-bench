# Efficient Magic State Cultivation on RP²

Zi-Han Chen, Ming-Cheng Chen, Chao-Yang Lu, Jian-Wei Pan (2025), [arXiv:2503.18657](https://arxiv.org/abs/2503.18657).

## Where the circuits are

The paper links to [Zihan-Chen-PhMA/Cultiv_T_RP2](https://github.com/Zihan-Chen-PhMA/Cultiv_T_RP2), which I used at commit `77ad9b3`. Its
`circuit_garage/` holds four Stim circuits at p=0.001:
- MSC-3 cultivation
- MSC-5 cultivation
- MSC-3 end-to-end into a d=7 surface code
- MSC-5 end-to-end into a d=11 surface code

The paper says that it simulates the Clifford variant: "we replace all T (T†) gates in our protocols with S (S†) gates".

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/`: the repo's `circuit_garage/` (the original S-proxy circuits), the generator (`t_gadget.py`, `RP_surface_codes.py`), the
  sampling scripts, README and LICENSE.
- `make_circuits.py` reverses the authors' substitution: every `S` becomes `T` and every `S_DAG` becomes `T_DAG`. It writes the result to
  `stim/`.
- Check: each circuit is sampled noiselessly in Tsim (1024 shots). No detector is random, and every detector value equals the value
  in the S-proxy circuit.

  The final logical-Y observable reads 1 with probability ≈ 0.146 = (1 − 1/√2)/2, as expected for a T state. For d=5 this is 0.1446
  over 20k shots; the table from `make_circuits.py` shows 0.125 because it uses only 1024 shots.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `rp_3_rp_5_sc_11_end2end_6_full_rds.stim` | 51 T, 50 T_DAG | 9 | 18 | 18 |
| `rp_3_rp_5_T_cult.stim` | 51 T, 50 T_DAG | 10 | 18 | 18 |
| `rp_3_sc_7_end2end_4_full_rds.stim` | 16 T, 15 T_DAG | 4 | 8 | 8 |
| `rp_3_T_cult.stim` | 16 T, 15 T_DAG | 4 | 8 | 8 |

Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

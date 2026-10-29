# Transversal architecture for megaquop-scale quantum simulation with neutral atoms (transversal STAR)

Refaat Ismail, I-Chi Chen, Chen Zhao, Ronen Weiss, Fangli Liu, Hengyun Zhou, Sheng-Tao Wang, Andrew Sornborger, Milan Kornjača (2025),
[arXiv:2509.18294](https://arxiv.org/abs/2509.18294).

## Where the circuits are

The paper itself links no circuits. QuEra published STAR circuits for Tsim in the YQuantum 2026 challenge,
[YQuantum-2026/QuEra-Challenge](https://github.com/YQuantum-2026/QuEra-Challenge), which I used at commit `8976b49`. They are
`assets/star_circuits/star_d={3,...,15}.stim`, which the challenge describes as the "transversal STAR architecture" circuits, with a default
logical angle of 0.01π. Each circuit:
1. prepares a logical |+⟩ in a distance-d surface code;
2. applies d physical rotations R_Z(θ_phys);
3. runs two postselected stabilizer rounds, then d further rounds;
4. undoes the rotation with a simulated perfect logical R_Z(−0.01);
5. reads out the logical X.

These circuits come from the challenge rather than from a paper repository, so I can't confirm they are the exact circuits behind the paper's
figures.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/QuEra-Challenge/`: the challenge README, `challenge.md` (which includes the `physical_angle` helper) and the circuits.
- `make_circuits.py` copies the circuits. It drops target-less noise lines and strips the annotation tags `CX[FEED_FORWARD]` and
  `TICK[DISABLE_ERROR]`, both of which Clifft rejects.
- Check: the circuits are sampled noiselessly in Tsim. The d−1 detectors after the rotations are random, because the rotations put the
  patch into a superposition of syndromes and the protocol postselects on them. After postselection the logical observable is always 0.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) | Clifft k (default passes) |
|---|---|---|---|---|
| `star_d=11.stim` | 12 R_Z | 2 | 2 | 11 |
| `star_d=13.stim` | 14 R_Z | 2 | 2 | 13 |
| `star_d=15.stim` | 16 R_Z | 2 | 2 | 15 |
| `star_d=3.stim` | 4 R_Z | 2 | 2 | 3 |
| `star_d=5.stim` | 6 R_Z | 2 | 2 | 5 |
| `star_d=7.stim` | 8 R_Z | 2 | 2 | 7 |
| `star_d=9.stim` | 10 R_Z | 2 | 2 | 9 |

`ActiveWidthSchedulePass` reduces Clifft's width from d to 2.
Tsim: main@883d787, default `active_statevector` strategy, largest statevector component width.
Clifft 0.12.0: default HIR passes + `ActiveWidthSchedulePass()`, `peak_active_width`.

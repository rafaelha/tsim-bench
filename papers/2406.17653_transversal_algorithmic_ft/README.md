# Low-Overhead Transversal Fault Tolerance for Universal Quantum Computation

Hengyun Zhou, Chen Zhao, Madelyn Cain, Dolev Bluvstein, Nishad Maskara, Casey Duckering, Hong-Ye Hu, Sheng-Tao Wang, Aleksander Kubica,
Mikhail D. Lukin (2024), [arXiv:2406.17653](https://arxiv.org/abs/2406.17653).

## Where the circuits are

Zenodo record [16552626](https://zenodo.org/records/16552626) ("Data for Low-Overhead Transversal Fault Tolerance…") contains:
- `circuits/`: Stim circuits for repeated Bell measurements, GHZ preparation, S injection, an S factory and a two-level S factory;
- `results/`: the decoded statistics (MLE and belief-hypergraph union-find decoders);
- `scripts/`: the Julia plotting scripts.

The non-deterministic logical observables are written as `DETECTOR`s ("gauge detectors"), as the Zenodo README explains.

## What I did

- `tex/`: arXiv source. I removed the figures.
- `stim_src/`: the Zenodo README, `scripts/`, the S-injection circuits at p_injected = 0.1 (d = 3, 5, 7, 9), and
  `results/s_injection/`.
  - Each circuit injects noisy |Y⟩ states (`RY` + `Z_ERROR(p_injected)`) into surface-code patches and consumes them with transversal
    gates and feedforward.
  - The circuits for other p_injected values differ only in that one error rate.
- `make_circuits.py`:
  - **Conversion:** each `RY q` becomes `RX q` + `T q` (T|+⟩ is the T state). The `Z_ERROR` after it is kept as the injection noise, and
    target-less lines are dropped for Clifft.
  - **Check:** each circuit is sampled noiselessly in Tsim (512 shots). All detectors stay deterministic and equal the |Y⟩ proxy's, and
    the logical observable becomes random (P(1) ≈ 0.75), as expected for a T state read out in a Pauli basis.
- Not converted: the `s_factory` and `two_level_s_factory` circuits distil |Y⟩ (S) states. With T in place of the |Y⟩ inputs, the same
  detectors are random as in the proxy (16 gauge detectors at d=3), but every output becomes random (≈ 0.36). That protocol has no T
  analogue, so the result would not be a T factory.

## Active width k_max

| circuit | non-Clifford gates | Tsim k | Clifft k (ActiveWidthSchedulePass) |
|---|---|---|---|
| `s_injection_T_d3_p0.001_pinj0.1.stim` | 2 T | 1 | 2 |
| `s_injection_T_d5_p0.001_pinj0.1.stim` | 2 T | 1 | 2 |
| `s_injection_T_d7_p0.001_pinj0.1.stim` | 2 T | 1 | 2 |
| `s_injection_T_d9_p0.001_pinj0.1.stim` | 2 T | 1 | 2 |

Tsim 1.0.0, default `active_statevector` strategy, largest statevector component width. Clifft 0.13.0: default HIR passes +
`ActiveWidthSchedulePass()` (default settings), `peak_active_width`. Compile only, from `results/benchmark.json`
(`tools/benchmark.py`). Each simulator ran in its own process, capped at 40 GB of memory and 30 min.

# Which central simulation figures can be reproduced with real T gates and no decoder?

This survey covers the 27 papers in `papers/`. For each paper I read the figure captions and the simulation sections in `tex/`. I then checked
whether each central figure's numbers come only from **postselection on detectors plus a noiseless final check or tomography** (decoder-free), or
whether they need a decoder (MWPM, BP-OSD, complementary gap, soft output, neural, ...).

For every decoder-free figure I estimated the cost of regenerating it with Tsim, using the real non-Clifford gates.

## How the runtimes are estimated

- **Rates:** from `results/benchmark.json`, i.e. Tsim 1.0.0 on one pinned core of a Ryzen 9 9900X, and Tsim GPU draft #219 on an RTX 5090.
  - **12-core column:** taken as 6× the single-core rate. The README records that 8–10 parallel jobs halve each job's rate.
  - **GPU rates in the tables are conservative.** With on-device postselection (`sample(..., postselection_mask=...)`) I measured
    2.5–2.6e9 shots/s on d=5 cultivation (benchmark: 1.4–1.7e9) and 3.6e9 shots/s on STAR d=7 (benchmark: 8.2e8).
  - **Host-side filtering caps the GPU.** Filtering on the host in numpy limits the GPU to about 4e7 shots/s, so long runs must postselect on
    the device.
- **Shot budgets:**
  - Where the paper reports its budget, I use it.
  - Otherwise each point gets 100 accepted logical errors (1000 for cheap injection-level points), with shots = errors / (LER × acceptance).
- **LER and acceptance inputs:** measured here where possible (short Tsim runs at p=1e-3, below), otherwise taken from the paper.
- **Scaling to other p:** LER is scaled as p³ and acceptance as acc(1e-3)^(p/1e-3). I assume Tsim's rate is roughly independent of p.
- **Precision:** these are order-of-magnitude estimates (±3×). The dominant term is always the lowest-p / highest-distance point.

### Spot checks (real T gates, Tsim, p = 1e-3, all detectors postselected)

| circuit | acceptance (paper) | LER of kept shots | shots |
|---|---|---|---|
| 2409.17595 `inject_cultivate_d3` | 0.687 | 1.0e-6 (140 errors) | 2e8 (3.5 s, GPU) |
| 2409.17595 `inject_cultivate_d5` | 0.144 (0.144) | ~7e-9 (2 errors) | 2e9 |
| 2512.23037 SOFT `circuit_d5` | 0.144 (0.144) | **3.5e-9 (51 errors)**; SOFT: 4.59e-9 (49), Clifft: 2.67e-9 | 1e11 (**3.5 min** on the RTX 5090) |
| 2509.08658 `d3_cultivation_T` | 0.647 | 1.1e-6 | 2e8 |
| 2509.18294 STAR d=3 / 5 / 7 | 0.577 / 0.115 / 0.0074 | 3.0e-5 / 1.5e-5 / 1.54e-5 | up to 2e10 (5.6 s, GPU) |
| 2503.18657 MSC-3 / MSC-5 | 0.514 (0.514) / 0.0945 (0.095) | (Y readout random, see below) | |
| 2502.01743 unrotated H d1=3 | 0.548 | (observable random, see below) | |
| 2509.05212 fold-d3 | 0.750 | (no observable) | |

The SOFT row reproduces SOFT's p = 1e-3 point (74 billion shots on 16 H800s) with real T gates: 1e11 shots in 3.5 minutes of wall time on one RTX 5090.
The effective rate of 4.8e8 shots/s includes copying the 14% kept rows to the host.

## Summary

| # | paper | decoder-free central figure? | what can be reproduced | est. shots | 1 core | 12 cores | RTX 5090 |
|---|---|---|---|---|---|---|---|
| 1 | 2302.12292 hook injection | **No** | Frontier (Fig. 5) and noise sweep (Fig. 6) idle a d=15 patch for 15 rounds and use correlated MWPM; the T circuits end in a random Y readout | – | – | – | – |
| 2 | 2406.17653 transversal algorithmic FT | **No** | Fig. 3 (Clifford) and Fig. 4 (S factory) are MLE/BHUF-decoded; the S factory has no T analogue | – | – | – | – |
| 3 | 2409.07707 color-code MSD | **No** | Growing with a logical-gap cut; the MSD cost ansatz is built from decoded memory runs | – | – | – | – |
| 4 | 2409.17595 Gidney cultivation | **Yes (pre-escape)** | Fig. 13 `t-vs-s` (d=3, T curve) | 1.6e9 | 54 s | 9 s | <1 s |
| | | | Fig. 21 `inject-only-sampled` (9 d=3 + 3 d=5 circuits) | 2.0e12 | 18 d | 3 d | 24 min |
| | | No | End-to-end (Fig. 11), idling, gap calibration: complementary gap | | | | |
| 5 | 2502.01743 Vaknin surface-code cultivation | **Yes (one SI figure)** | Fig. 26 `full_vector_simulation`: unrotated H, d1=3, no expansion, 4 p, 100 errors each. The authors spent **1e6 CPU-hours** for 1e7 shots/point; the same 1e7 shots/point take 3 min on one core here | 7e8 | 1 h | 10 min | 7 s |
| | | No | All expansion figures (complementary gap) | | | | |
| 6 | 2503.18657 RP² cultivation | **Partly (table)** | Table 1 "ungrown" MSC-3 + MSC-5 (T LER ~2e-9 assumed for MSC-5), plus the per-round survival figure | 5.3e11 | 1.1 yr | 65 d | 3.3 h |
| | | No | Main Fig. 3 (end-to-end, soft-output decoder) | | | | |
| 7 | 2504.02935 erasure injection | **Yes (ungrown)** | Figs. 2 + 4, ungrown hook / Lao-Criger d1=3 injection | 4.4e8 | 5 s | <1 s | <1 s |
| | | | Fig. 5, inject + cultivate d=3, Pauli p=1e-4. LER depends only on the Pauli rate, so one run serves all erasure settings | 1.1e11 | 53 min | 9 min | 6 s |
| | | No | Fig. 3 expansion to d=15 (decoder) | | | | |
| 8 | 2505.13587 correlated decoding | **No** | Decoding is the subject; Fig. 4 distillation is MWPM-decoded with committed stages | – | – | – | – |
| 9 | 2507.12511 unfolded distillation | **No** | All figures decode the noisy X-stabilizer rounds with BP-OSD | – | – | – | – |
| 10 | 2509.05212 fold-transversal cultivation | **Yes (SI)** | Fig. `app_hxy`(b): Y vs H_XY cultivation, fd3, escape excluded, 5 p | 1.5e9 | 1.5 min | 15 s | 1 s |
| | | No | Main Fig. 1 (LER/STO) and the PM-noise and staircase figures (complementary gap) | | | | |
| 11 | 2509.08658 few Clifford terms | **Yes (all)** | Figs. 15–17, 19: d=3 T-cultivation LER and discard vs p (2^26 and 2^29–2^32 shots/point, 10 p) | 4.4e10 | 24 min | 4 min | 4 s |
| 12 | 2509.18294 transversal STAR | **Yes (injection)** | Figs. 6, 13, 14 (PS variants), 15: k=3 full-PS TMR, d=3/5/7, sweeps over p and θ, 12 points/d, 1000 errors | 1.1e11 | 3.4 h | 34 min | 2.2 min |
| | | | Same, at the authors' budget (Fig. 15: 4e10–6e10 shots/point) | 8.4e11 | 14 h | 2.3 h | 8 min |
| | | No | Figs. 3, 4, 7, 8, 10, 12: decoded Clifford gadgets; Fig. 7 combines both | | | | |
| 13 | 2510.07269 transversal dimension jump | **No** | Fig. 2 (MWPM/BP-OSD). The postselection-only magic-state Table II is a table, needs Tsim k=26 (beyond the CPU and GPU limits) and has random CCZ observables | – | – | – | – |
| 14 | 2510.24615 lattice-surgery cultivation | **No** | PyMatching + complementary gap everywhere | – | – | – | – |
| 15 | 2512.13908 Google cultivation experiment | **Yes (all sim curves)** | Figs. 2–4 and SI (tomography vs θ, kickback tomography, p sweep, memory N sweep). Postselect all + logical tomography; SI1000 noise must be added | ~6e9 | 3 min | 34 s | <1 s |
| | | ? | SI coherent-detuning simulations (R_Z on every qubit in every layer). The active width will grow; not estimated | | | | |
| 16 | 2512.23037 SOFT | **Yes** | Fig. 2 / Table 3: d=5 inject + cultivate with T, p = 2e-3 / 1e-3 / 5e-4, using the authors' 2.37e11 shots (**16 H800 × 20 days** in the paper) | 2.4e11 | 10 d ² | 1.7 d | 2.3 min |
| 17 | 2603.05429 gauging cultivation | **Yes** | Fig. 4a–c + Table 1: d=3 (6 p), d=5 (2 p), d=7 at p=5e-4 (the authors' 2e11 postselected samples at 1.5% success) | 1.9e13 | 31 yr | 5 yr | **2.9 d** |
| | | | (d=7 alone) | 1.3e13 | 30 yr | 5 yr | 2.8 d |
| 18 | 2604.01059 Tsim | **Yes (trivially)** | Throughput benchmark and validation figures | – | min | – | min |
| 19 | 2604.05126 qLDPC injection | **No** (LER) | Injection error needs decoding of the r2 rounds; only the discard-rate panels are decoder-free, and they match the Clifford proxy | – | – | – | – |
| 20 | 2604.27058 Clifft | **Yes (inject + cultivate)** | Fig. 6, T vs S for d=3 (6 p) and d=5 (3 p, brute force, no importance sampling; Clifft used 9.6e10 importance-sampled shots and 12 machine-hours) | 2.4e11 | 2.3 d | 9 h | 3 min |
| | | No | Fig. 7 end-to-end (complementary-gap MWPM) | | | | |
| 21 | 2607.28600 SymFT | **Yes (trivially)** | Benchmark tables only | – | min | – | min |
| 22 | 2609.17706 Chan (degraded fault distance) | **Yes** | Pre-escape LER: d=3 S/T ± flags; d=5 original vs Z-flagged, 5 p down to 5e-4, 30 errors/point | 8e12 | 96 d | 16 d | 2 h |
| 23 | 2609.18922 exact LER | **Analytic** | The curves are an exact series; the Monte Carlo reference points are SOFT's run (#16) | (= #16) | | | |
| 24 | 2610.03869 modular neural decoder | **No** | Decoder benchmark | – | – | – | – |
| 25 | 2610.06811 Merlin | **Benchmark only** | Fig. `bh` and Table 2 (1000 shots each). The BH, 15-to-1 and cultivation rows take seconds in Tsim; the code-switching rows (bt27 needs k=26, bt81) are infeasible | – | s | – | s |
| 26 | 2610.06828 practical cost of cultivation | **No** | Escape-stage complementary gap / Caliper | – | – | – | – |
| 27 | 2610.22315 Magna | **Yes** | Fig. 8a: Bravyi–Haah k=2, 6, 10 output infidelity vs p (8 p down to 1e-4) | 3e10 | 11 min | 2 min | 1 s |
| | | | Fig. 9: color-code and RP² cultivation, d=3 and d=5, acceptance and infidelity (5 p each; RP² d=5 dominates) | 1.4e12 | 184 d | 31 d | 2.3 h |
| | | No | Fig. 10: logical 15-to-1 (decoder-controlled feedforward) | | | | |

² With the SOFT circuit (2.7e5 shots/s on one core). Gidney's equivalent d=5 circuit runs at 1.26e6 shots/s, which gives about 2.2 days on one core.

**Score:**
- 13 papers have at least one decoder-free central simulation figure (#4, 5, 6, 7, 10, 11, 12, 15, 16, 17, 20, 22, 27).
- 4 are benchmark-only or analytic (#18, 21, 23, 25).
- 10 need a decoder (#1, 2, 3, 8, 9, 13, 14, 19, 24, 26).

## What has to change in the circuits before the figure can be made

The decoder-free figures all measure the *T state*, so the final check must be deterministic. Several of our converted circuits still end in a
Pauli readout, which is random on a T state.

| circuits | issue | fix |
|---|---|---|
| 2409.17595, 2512.23037, 2509.08658, 2604.27058, 2609.17706, 2610.22315 | none: the final readout is already wrapped in T…T† | run as is |
| 2503.18657 `rp_*_T_cult`, 2504.02935 both circuits, 2603.05429 `gauging_*` | final logical-Y readout, random (P(1) ≈ 0.146) | noiseless T†-basis wrap (decode the patch noiselessly, apply T†, measure X), as in Clifft's converter |
| 2502.01743 `unrotated_H_injection*` | observable random (P = 0.5) | add the noiseless magic-basis (H) measurement that the paper's Fig. 26 uses |
| 2509.05212 `fold-d3` | no `OBSERVABLE_INCLUDE` | add the noiseless logical H_XY check |
| 2512.13908 | released circuits are noiseless | add SI1000 noise (the paper used p = 2.3e-3 and 3.0e-3) |
| 2509.18294 STAR | its detectors after the rotations are random by design | postselect on the raw parities; do **not** use `use_detector_reference_sample` (it cuts acceptance tenfold) |
| 2504.02935 erasure | erasures are heralded | discard heralded shots: the kept-shot LER needs only the Pauli part, and acceptance gets the analytic survival factor |
| all p sweeps | our circuits are at p = 1e-3 only | regenerate at the other noise strengths |

## Takeaways

- **Cheap:** most decoder-free figures are pre-escape cultivation or injection at d=3, or STAR/Google-type injection. Each needs ≤1e11 shots: minutes
  to hours on one core, seconds on the GPU. Examples are the Vaknin figure that cost 1e6 CPU-hours and Wan's 2^32-shot points.
- **d=5 cultivation (SOFT, Gidney Fig. 21, Clifft Fig. 6, Chan, Magna color d=5):** 2e11–2e12 shots per figure. This takes days to weeks
  on a 12-core CPU but **minutes to hours on one RTX 5090**. SOFT's 237-billion-shot table (16 H800 × 20 days) takes about 2–3 minutes of
  GPU kernel time.
- **Width-limited:** RP² MSC-5 (k=10) and Magna RP² d=5 (k=9) run 30–50× slower per shot than color-code d=5, so they need hours of GPU
  time. Gauging d=7 at p=5e-4 (k=8, 1.3e13 shots) is the most expensive figure in the set: about 3 GPU-days, and infeasible on CPU.
- **Fault distance:** T-state d=5 cultivation has fault distance 3, not 5 (2609.17706, 2609.18922). Its pre-escape LER at p=1e-3 is therefore
  2.7–4.6e-9, not the S-proxy's 2×3.5e-10. Our 1e11-shot run gives 3.5e-9.

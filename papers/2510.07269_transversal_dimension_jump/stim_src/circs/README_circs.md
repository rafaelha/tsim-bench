# circs

Benchmark circuits for non-Clifford simulators.

## tricycle_factories

CCZ magic-state factories built from three blocks of a tricycle code, following the CCZ
error-detection experiment of Li, Preskill and Xu, *Transversal Dimension Jump for Product
qLDPC Codes* ([arXiv:2510.07269](https://arxiv.org/abs/2510.07269)), with the CCZ simulated as a real gate
rather than as Pauli noise.

The circuits use [tsim](https://github.com/QuEraComputing/tsim) syntax: `CCZ` is not a stim gate, so load
them with `tsim.Circuit(...)` (clifft also parses them).

Each circuit:

1. prepares three code blocks with data in |+>, then runs one round of Z-syndrome extraction;
2. applies a feed-forward X correction computed from the Z syndrome (`CX rec[...] q`), and adds the
   redundant Z checks as meta-check detectors. A real CCZ needs this correction: without it the CCZ
   acts on X^e|+̄⟩ instead of |+̄⟩;
3. applies the depth-2 transversal CCZ (each data qubit is in two physical CCZs). It implements logical CCZ on the 6 triples (a, b, c) of
   logical qubits from the three blocks with a, b, c distinct;
4. applies the paper's CCZ noise (weight-5 Z per data qubit), then a transversal MX;
5. reads out the X-check detectors and the 9 logical-X observables. The observables are random
   (P = 3/8 each, noiselessly) because the output is a CCZ-type magic state.

Noise everywhere is the paper's d3_blp model at p = 1e-3: `DEPOLARIZE1` on Z-ancillas after reset and
before `MR`, `DEPOLARIZE2` after each CX, `E(0.001)` weight-5 Z after the CCZ, and `DEPOLARIZE1` on data before `MX`.

### Circuits and active width k_max

k_max is the peak active width of the state-vector simulation: one shot holds 2^k_max amplitudes.

| file | code per block | qubits (3 blocks) | physical CCZs | tsim k_max | clifft default | clifft beam 8 | clifft beam 128 |
|---|---|---|---|---|---|---|---|
| `tricycle_6_3_2.stim` | [[6,3,2]] | 36 | 12 | 9 | 12 | 9 | 9 |
| `tricycle_9_3_2.stim` | [[9,3,2]] | 54 | 18 | 11 | 15 | 12 | 12 |
| `tricycle_12_3_2.stim` | [[12,3,2]] | 72 | 24 | 16 | 17 | 15 | 14 |
| `tricycle_15_3_2.stim` | [[15,3,2]] | 90 | 30 | 16 | 20 | 16 | 15 |
| `tricycle_18_3_2.stim` | [[18,3,2]] | 108 | 36 | 20 | 23 | 19 | 18 |
| `tricycle_21_3_3.stim` | [[21,3,3]] | 126 | 42 | 23 | 25 | 21 | 20 |
| `tricycle_24_3_2.stim` | [[24,3,2]] | 144 | 48 | 20 | 29 | 19 | 18 |
| `tricycle_27_3_3.stim` | [[27,3,3]] | 162 | 54 | 24 | 33 | 26 | 24 |
| `blp_27_3_3.stim` | [[27,3,3]] (paper's d3_blp) | 162 | 54 | 26 | 31 | 26 | 26 |
| `toric_81_3_3.stim` | [[81,3,3]] 3D toric | 486 | 162 | 63* | 79 | 54 | 58 |
| `toric_375_3_5.stim` | [[375,3,5]] 3D toric | 2250 | 750 | 186* | pending | pending | pending |

- tsim: `strategy="active_statevector"` (the default) at commit 6589011. *Above 30, tsim refuses to
  compile, and the value comes from its "needs N active qubits" error.
- clifft 0.12.0: `default_hir_pass_manager()` (default), then the same with
  `ActiveWidthSchedulePass(beam_width=8 or 128, search_budget=1e9)` appended.
- Verification: the clifft values are the peak of `active_width_trace` and match
  `compile(...).peak_active_width` for every circuit except the two toric codes; both runs gave the same numbers.
  Noiseless tsim sampling of the four circuits with k_max ≤ 16 gives deterministic detectors, and
  logical-X observables at 3/8, the exact value for the target 9-qubit state.
- Timing at k_max = 26 (`blp_27_3_3.stim`, Ryzen 9 9900X): clifft 3.1 s/shot on one core, tsim 67 s/shot on one thread.

### Codes

- `blp_27_3_3.stim` is the paper's [[27,3,3]] bivariate tricycle code (G = Z3 x Z3,
  A = x + x^2 y, B = x^2 y + x^2 y^2, C = 1 + x y^2). Its Z-syndrome round and CCZ triples are the authors'
  (identical to the saved circuit in notebook 3 of
  [tinghui2012/transversal-dimension-jump](https://github.com/tinghui2012/transversal-dimension-jump));
  steps 2–5 were added here.
- The other files are tricycle codes on 3-torus quotients R^3/L (qubits on edges, X checks on vertices,
  Z checks on faces, CCZ from the cubical cup product), written by `generate.py`. The `toric_*` files are
  the 3D toric codes of the paper (L = 3Z^3, 5Z^3). `tricycle_21_3_3` uses the lattice
  x + 2y + 3z ≡ 0 (mod 7), the smallest index with distance 3. For every code with n ≤ 81, the
  generator checks that the transversal CCZ preserves the code space and acts as the logical gate
  above. The small lattices give degenerate cell complexes (some cells are glued to themselves); the
  algebraic checks still pass.

Regenerate with `python tricycle_factories/generate.py` (needs numpy).

# Active width of published non-Clifford Stim circuits

A literature survey of papers that release Stim circuits with non-Clifford gates, or Clifford proxies that convert to real T/CCZ/CS
gates. For each one I measured the peak active width `k_max` that Tsim and Clifft reach on its circuits.

- **Tsim:** `QuEraComputing/tsim` main at `883d787`. `compile_detector_sampler()` with the default `active_statevector` strategy;
  k = largest statevector component width (compile only, no sampling).
- **Clifft 0.12.0:** `default_hir_pass_manager()` + `ActiveWidthSchedulePass()` with default settings; k = `peak_active_width`. The width
  without the scheduler is also recorded.

Results: [`SUMMARY.md`](SUMMARY.md), with a per-paper overview and a per-circuit table. Regenerate it with `uv run python tools/summary.py`.

## Layout

    papers/<arxiv-id>_<name>/
        README.md          where the circuits are, what was done, k_max table
        tex/               arXiv source (.tex/.bib/.bbl/.cls; figures and other binaries removed)
        stim_src/          the authors' released circuits and/or generator code (subset, with commit/DOI)
        make_circuits.py   writes stim/ (conversion to real non-Clifford gates + noiseless Tsim checks)
        stim/              the non-Clifford circuits that were measured
        k_max.json         raw measurements (tools/measure_k.py)
    tools/
        measure_k.py       k_max in Tsim and Clifft (each in a child process with a timeout)
        validate.py        noiseless Tsim checks (deterministic detectors, agreement with the Clifford proxy)
        gates.py           CS, CS_DAG, CH, CSWAP, controlled-(S X) decompositions into T/CX/H/CCX, verified against unitaries
        stimtext.py        clean-ups for Clifft (target-less lines, tags)
        remote_zip.py      extract single files from remote zips with HTTP range requests (multi-GB Zenodo archives)
        fetch_arxiv.sh     download and unpack an arXiv source, list code/data links
        arxiv_meta.py      title/authors/year from the arXiv API
        ktable.py, summary.py
    _search/               brief, the 20 GPT-6.1 Terra scout reports, merged candidate list

Run `uv sync` once. Then `uv run python papers/<folder>/make_circuits.py` and `uv run python tools/measure_k.py papers/<folder>/stim/*.stim`.
A few generators need the authors' own environment; the folder README says when.

## How the candidates were found

Twenty GPT-6.1 Terra scouts each searched one area (`_search/BRIEF.md`, `_search/scout_*.json`):
- cultivation
- distillation
- code switching
- injection
- fold-transversal gates
- coherent errors
- simulator benchmarks
- CCZ/CS
- experiments
- gauging and lattice surgery
- small codes
- STAR and rotations
- qLDPC
- neutral atoms
- Zenodo
- GitHub
- zero-level distillation and layouts
- logical algorithms and compilers
- colour codes
- recent cost studies

The merged, deduplicated list has 50 entries (`_search/candidates.json`). I found Chan et al. (2609.17706) separately, through the exact-LER
repository.

## Papers not processed

| arXiv | paper | reason |
|---|---|---|
| 2510.07269 | Transversal dimension jump for product qLDPC codes | CCZ is modelled by a weight-5 Pauli surrogate; regenerating needs bposd/ldpc and notebook-generated code matrices |
| 2505.23567 | Scalable decoding for fast transversal logic (Turner et al.) | Zenodo "T gate proxy" circuits are logical-level proxies with \|0⟩ inputs, no S feedforward and no H layers; real T gates need encoded \|T⟩ preparation and logical S corrections |
| 2608.23819 | CircLS (Zhang) | Lattice-surgery compilations with every magic state replaced by a logical \|+⟩ patch; real T gates need encoded \|T⟩ preparation and conditional logical S |
| 2412.14256 | Scaling and logic in the colour code (Google) | The Zenodo data has only X/Z memory circuits, no injection circuits |
| 2412.15187 | Measurement-free universal QC (Veroni et al.) | Stim files are Clifford concatenation cycles; the CCZ/universality part is Julia (SparseStates.jl) |
| 2412.15165 | Logical magic state distillation experiment (QuEra) | No released circuits; covered through the Tsim paper's reproduction in `papers/2604.01059_tsim` |
| 2404.07482 | Colour code decoder (Lee et al.) | Clifford memory circuits; the package's cultivation circuits are covered in `papers/2409.07707_color_code_msd` |
| 2412.01446 | Magic state injection on IBM processors | Code Ocean capsule with Qiskit code; no Stim circuit |
| 2506.20661 | Architectural mechanisms of a universal FTQC (Harvard/QuEra) | Coherent-error experiments are hardware schedules; no Stim circuits |
| 2403.13732 | Experimental fault-tolerant code switching | Qiskit circuits; would need a manual translation, including feedforward |
| 2601.10964 | Code-generic universal FTQC | The T protocol is in Cirq; Stim is used only for Clifford parts |
| 2604.02033, 2610.06730 | Non-Pauli codes / CSS codes with universal transversal gates | No Stim generator; reconstruction from the paper only |
| 2309.08663, 2608.09727, 2605.21867, 2403.03991 | [[8,3,2]] CCZ; binary-extension-field MSD; zero-level CCZ; zero-level distillation | No Stim circuits; reconstruction from figures or notebooks |
| 1905.06903 | Magic state distillation: not as costly as you think | Resource-count code only |
| 2303.04672, 2303.17380, 2509.23642 | Coherent errors (FLO); arbitrary-rotation preparation; multi-level injection | Fermionic-linear-optics or Julia simulations; no Stim circuits |
| 2412.01391 | Transversal Clifford gates on rotated surface codes | Logical S-gate memory benchmarks; not a magic-state circuit |
| 2402.17761, 2508.14200, 2408.11894 | FT state-preparation synthesis | Stabilizer-state preparation only |
| 2405.00146 | Burst errors in magic state factories | Clifford lattice-surgery memory |
| tqec | tqec package | Clifford block-graph compiler; no non-Clifford resource |

## Simulator observations

- **Tsim tag bug:** at 883d787, Tsim mis-parses any instruction tag that contains the token ` T`, e.g. `TICK[Encode T]` or
  `H[my T tag] 0` ("Targets must be separated by spacing"). main@4b951f3 ("stop rewriting tags", #218) fixes it; I checked.
- **Tsim correlated-error chains:** Tsim compiles a `CORRELATED_ERROR`/`ELSE_CORRELATED_ERROR` chain of length k into a 2^k table, so a
  63-term chain (exact 3-qubit depolarizing noise) fails with "Maximum allowed dimension exceeded". See
  `papers/2509.05212_fold_transversal_cultivation`.
- **Clifft parser strictness:** Clifft rejects target-less instructions such as `DEPOLARIZE1(0.001)` and `R`, and any tag outside
  `LEVEL_TRANSITION`, so several published files needed `tools/stimtext.py`.
- **Width comparison:** across the 164 circuits measured by both simulators, Tsim's k is smaller on 57, equal on 97, and larger on 10.
  - Tsim much smaller: Bravyi–Haah distillation with T teleportation (Magna) stays at k=3 for every size, while Clifft grows to 42 and
    overflows from bh60 on. Fold-transversal d=5 gives 8 vs 22, gauging d=7 8 vs 19, and RP² d=5 10 vs 18.
  - Tsim larger: the 10 circuits are Merlin's "clean" distillation workloads (Tsim 4, Clifft 0). The intermediate states are non-stabilizer,
    but the only noise is Z after the T_DAG gates and the ideal output is undone before readout. By triorthogonality the whole circuit is then
    Clifford as an operator, and Clifft's `PhasePolynomialPass` cancels every T gate. Switching off either ingredient brings Clifft back to
    k ≥ 1 (variant table in `papers/2610.06811_merlin/README.md`).
  - Not measured by both: Clifft overflows on Magna bh60/80/100 (Tsim 3), and Tsim's `active_statevector` refuses Merlin's bt81, which
    would need 63 active qubits against a limit of 30 (Clifft 52).
  - `ActiveWidthSchedulePass` matters most on the STAR circuits, where it brings Clifft from k=d down to 2.

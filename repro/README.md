# Decoder-free reproductions on the GPU

This directory re-runs every central simulation figure of the papers in `../papers` that can be made **without a decoder**
(all detectors postselected, plus a noiseless final check or logical tomography) on the Tsim CUDA executor. Each one is run
twice where possible:

- the paper's **Clifford proxy** ($S$ in place of $T$, or $|Y\rangle$), to check that the GPU kernel reproduces the published
  numbers;
- the **real non-Clifford circuit** ($T$ gates, small-angle rotations, CCZ, ...).

The survey that selected these figures is in [`../DECODER_FREE_FIGURES.md`](../DECODER_FREE_FIGURES.md). The output is
[`report/report.pdf`](report/report.pdf): one section per paper, and every figure states its own compute budget (GPU sampling
time, compile time, shots, GPU model and Tsim commit).

## Running

```bash
repro/setup.sh                                  # environments: .venv, .venvs/tsim-gpu, .venvs/vaknin
uv run python -m repro.run_all --tier 1         # cheap points (all studies)
uv run python -m repro.run_all                  # everything (tiers 1-3, ~24 GPU-hours)
uv run python -m repro.make_report              # figures + report.pdf from whatever has been sampled
```

- `run_all` generates every circuit (cached in `circuits/`, git-ignored, regenerated with `--regenerate`), then samples the points
  one at a time, cheapest tier first. Each point runs in a fresh process inside a memory-capped systemd scope.
- **Resuming:** results accumulate in `results/<study>/<point>.json`. Re-running continues every unfinished point until its
  stopping rule (target errors, max shots, max GPU seconds) is met, so raising a budget in a study file only samples the
  difference.
- **Restarts:** if a circuit or the Tsim build changes, the point starts over; the old file is kept as `*.stale-*.json`.
  `--fresh` forces a restart.
- **Partial progress:** `make_report` works at any point. Missing points are absent from the plots, and a study whose figure
  code fails prints the traceback in the PDF.
- **Other options:** `--only <study ...>`, `--points <substring ...>`, `--variant clifford|t`, `--max-hours H`, `--scale 0.01`
  (smoke test), `--no-report`.

To re-run everything after a GPU kernel change:

```bash
TSIM_GPU_SPEC='bloqade-tsim[gpu] @ git+https://github.com/QuEraComputing/tsim@<commit>' repro/setup.sh
uv run python -m repro.run_all
```

## Layout

| file | role |
|---|---|
| `common.py` | `Point`/`Figure` records, circuit helpers (noise stripping, S/T swaps, noiseless checks), statistics, budget lines |
| `gpu_worker.py` | samples one point in `.venvs/tsim-gpu` (device-side postselection, host counts of kept shots, errors, observable ones) |
| `run_all.py` | the single entry point: circuits, sampling queue, report |
| `make_report.py` | figures and `report/report.tex` / `report.pdf` |
| `magic_check.py` | turns a Pauli readout that is random for a magic state into a deterministic noiseless magic-basis check |
| `plotting.py` | shared matplotlib helpers |
| `studies/*.py` | one module per paper: generator calls, points with budgets, figures with published overlays |
| `external/vaknin_generate.py` | Vaknin et al.'s generator, run in their pinned environment |
| `results/` | sampled counts (committed) and `run_log.jsonl` |
| `data/` | downloaded published data (Zenodo `stats.csv`) |

## How points are measured

- **Postselection:** Tsim postselects on the device (`sample(..., postselection_mask=...)`) and copies only the kept rows. The
  worker counts kept shots, logical errors (any observable differing from its noiseless reference) and, for tomography, the ones
  per observable.
- **Time budget:** the `seconds` budget is the wall time of the sampling loop (sampling plus host-side counting); compile time is
  recorded separately.
- **Reference sample:** detector reference samples are XOR-ed in only where every postselected detector is deterministic. Where
  some are random by design (STAR, the Google experiment away from the $T$ angle), the raw parity must be 0.

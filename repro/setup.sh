#!/usr/bin/env bash
# Build the environments used by repro/ (run from the repository root).
#
#   .venv               project environment (uv sync): circuit generation, plots, report
#   .venvs/tsim-gpu     Tsim with the CUDA statevector executor: all sampling
#   .venvs/vaknin       Vaknin et al.'s pinned environment (qutip, pennylane, ...): their generator
#   .venvs/clifft       Clifft 0.13.0: independent CPU cross-check of selected non-Clifford points (repro/clifft_check.py)
#
# TSIM_GPU_SPEC selects the Tsim build to sample with. Results record the installed commit, and a
# point whose Tsim build changed is re-sampled from scratch, so after changing the kernel:
#   TSIM_GPU_SPEC='bloqade-tsim[gpu] @ git+https://github.com/QuEraComputing/tsim@<commit>' repro/setup.sh
#   uv run python -m repro.run_all
set -euo pipefail
TSIM_GPU_SPEC=${TSIM_GPU_SPEC:-"bloqade-tsim[gpu] @ git+https://github.com/QuEraComputing/tsim@a2af975f"}

uv sync
uv venv -q --allow-existing -p 3.12 .venvs/tsim-gpu
uv pip install -q -p .venvs/tsim-gpu --reinstall-package bloqade-tsim "$TSIM_GPU_SPEC"
uv venv -q --allow-existing -p 3.12 .venvs/vaknin
uv pip install -q -p .venvs/vaknin -r papers/2502.01743_surface_code_cultivation/stim_src/repo_ec28f6b/requirements.txt
uv venv -q --allow-existing -p 3.12 .venvs/clifft
uv pip install -q -p .venvs/clifft clifft==0.13.0 numpy
.venvs/tsim-gpu/bin/python -c "import tsim, cupy; print('tsim', tsim.__file__, 'GPUs', cupy.cuda.runtime.getDeviceCount())"
command -v tectonic >/dev/null || command -v latexmk >/dev/null || command -v pdflatex >/dev/null || \
  echo "note: no LaTeX engine (tectonic/latexmk/pdflatex) on PATH; make_report will only write report.tex"

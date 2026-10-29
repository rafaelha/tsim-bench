"""Reproduce the target-scoring / noise-model variant table in README.md.

Builds 15-to-1 and Bravyi-Haah (k=6) distillation with the authors' ``build_distillation_case`` for
each combination of noise model (Z after T_DAG vs. depolarizing on all gates) and target scoring,
and prints k for Clifft (default passes + ActiveWidthSchedulePass), Clifft without HIR passes, and
Tsim. Usage: uv run python variants.py
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE / "stim_src" / "merlin-sim"))

import clifft  # noqa: E402
import tsim  # noqa: E402
from benchmarks.protocols import build_distillation_case  # noqa: E402


def clifft_k(text, passes):
    pm = clifft.default_hir_pass_manager()
    pm.add(clifft.ActiveWidthSchedulePass())
    return clifft.compile(text, hir_passes=pm if passes else None).peak_active_width


def tsim_k(text):
    program = tsim.Circuit(text).compile_detector_sampler()._program
    return max((c.width for c in program.components if hasattr(c, "width")), default=0)


VARIANTS = [
    ("Z noise + target scoring (benchmark default)", {}),
    ("Z noise, no target scoring", dict(target_scoring=False)),
    ("depolarizing noise + target scoring", dict(noisy_clifford=True)),
    ("depolarizing noise, no target scoring", dict(noisy_clifford=True, target_scoring=False)),
]

if __name__ == "__main__":
    for label, kwargs in VARIANTS:
        for protocol, k in [("15to1", 1), ("bh", 6)]:
            text = build_distillation_case(protocol, k=k, p_phys=0.001, **kwargs).circuit
            print(f"{label:46s} {protocol + (str(k) if protocol == 'bh' else ''):6s} "
                  f"clifft={clifft_k(text, True)} clifft_no_passes={clifft_k(text, False)} tsim={tsim_k(text)}")

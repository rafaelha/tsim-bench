"""Benchmark corpus: circuits from published papers, with how to postselect each one.

Only the standard library is imported here, so the package also works inside the Python
environment of the simulator under test (add the checkout root to ``sys.path``).
"""

from .manifest import ROOT, Case, cases, load, mask_indices, parse_ranges, suites

__all__ = ["ROOT", "Case", "cases", "load", "mask_indices", "parse_ranges", "suites"]

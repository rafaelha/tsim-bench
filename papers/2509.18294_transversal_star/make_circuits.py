"""Copy the transversal STAR circuits (Ismail et al., arXiv:2509.18294) into stim/.

The circuits (stim_src/QuEra-Challenge/star_circuits, YQuantum-2026/QuEra-Challenge at 8976b49) are
native Tsim circuits with R_Z rotations: a logical |+> in a distance-d surface code, d physical
rotations R_Z(theta_phys) on a logical-Z support, two rounds of stabilizers (postselected), d more
rounds, and a simulated perfect logical un-rotation R_Z(-0.01) before an MPP logical X readout
(default logical angle 0.01*pi). Two text changes make them acceptable to Clifft: target-less noise
lines such as ``DEPOLARIZE1(0.001)`` (no-ops in Stim) are dropped, and the annotation tags
``CX[FEED_FORWARD]`` and ``TICK[DISABLE_ERROR]`` are removed.

Check: without noise, the d-1 detectors of the first round after the rotations are random (the
rotations create a superposition of syndromes; the protocol postselects on them), every other
detector is deterministic, and after postselecting on all detectors the logical observable is 0.

Usage: uv run python make_circuits.py
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import numpy as np  # noqa: E402
import tsim  # noqa: E402

import stimtext  # noqa: E402
import validate  # noqa: E402


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for path in sorted((HERE / "stim_src" / "QuEra-Challenge" / "star_circuits").glob("*.stim")):
        text = stimtext.strip_tags(stimtext.drop_targetless(path.read_text()))
        sampler = tsim.Circuit(validate.strip_noise(text)).compile_detector_sampler(seed=0)
        det, obs = sampler.sample(4096, separate_observables=True)
        keep = ~det.any(axis=1)
        assert keep.any() and not obs[keep].any(), path.name
        (out / path.name).write_text(text)
        print(f"wrote stim/{path.name}: postselection keeps {keep.mean():.3f} noiselessly, observable 0 on kept shots")


if __name__ == "__main__":
    main()

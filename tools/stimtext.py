"""Small text clean-ups that make Stim-dialect files acceptable to both Tsim and Clifft."""

import re

_KEEP = ("TICK", "DETECTOR", "OBSERVABLE_INCLUDE", "SHIFT_COORDS")


def drop_targetless(text):
    """Drop gate/noise lines without targets, e.g. ``DEPOLARIZE1(0.001)``.

    Stim treats them as no-ops; Clifft's parser rejects them. Annotations are kept.
    """
    return re.sub(rf"^\s*(?!{'|'.join(_KEEP)})[A-Z_0-9]+(\([^)]*\))?\s*$\n?", "", text, flags=re.M)


def strip_tags(text):
    """Remove instruction tags such as ``I[echo]``; Clifft only accepts them on LEVEL_TRANSITION."""
    return re.sub(r"^(\s*[A-Z_0-9]+)\[[^\]]*\]", r"\1", text, flags=re.M)

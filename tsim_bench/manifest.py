"""Read ``papers/*/circuits.toml`` and ``suites.toml``.

Each paper folder has a ``circuits.toml`` (format in ``BENCHMARKS.md``). Every circuit records
the arXiv paper it comes from and how that paper postselects. Active widths come from the
folder's ``k_max.json``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10, for the worker in an older Tsim's environment
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None

ROOT = Path(__file__).resolve().parent.parent


def _toml(path: Path) -> dict:
    if tomllib is None:
        raise RuntimeError("reading tsim-bench manifests needs Python 3.11+, or tomli installed")
    return tomllib.loads(path.read_text())
POSTSELECT_KINDS = ("all", "none", "only", "all_except")


@dataclass(frozen=True)
class Case:
    """One benchmark circuit."""

    id: str  # "<paper folder>/<file stem>"
    path: Path
    arxiv: str
    sampler: str  # "detector" or "measurement"
    postselect: str  # one of POSTSELECT_KINDS
    detectors: str  # index ranges for "only" and "all_except", else ""
    num_detectors: int
    reason: str
    random_detectors: str = ""  # masked detectors that are random without noise by design
    detector_reference: bool = False
    observable_reference: bool = False
    widths: dict = field(default_factory=dict, compare=False)  # backend -> active width or None

    def width(self, backend: str = "tsim") -> int | None:
        return self.widths.get(backend)


def parse_ranges(text: str) -> list[int]:
    """Parse ``"0-3, 7, 10-11"`` into ``[0, 1, 2, 3, 7, 10, 11]`` (inclusive ranges)."""
    out: list[int] = []
    for part in text.replace(" ", "").split(","):
        if not part:
            continue
        lo, _, hi = part.partition("-")
        out.extend(range(int(lo), int(hi or lo) + 1))
    return out


def mask_indices(case: Case) -> list[int]:
    """Return the detector indices to postselect on (a shot is kept if none fires)."""
    n = case.num_detectors
    if case.postselect == "none":
        return []
    if case.postselect == "all":
        return list(range(n))
    listed = parse_ranges(case.detectors)
    if any(i < 0 or i >= n for i in listed) or len(set(listed)) != len(listed):
        raise ValueError(f"{case.id}: detector ranges out of bounds or repeated")
    if case.postselect == "only":
        return sorted(listed)
    excluded = set(listed)
    return [i for i in range(n) if i not in excluded]


def _widths(folder: Path) -> dict[str, dict]:
    record = folder / "k_max.json"
    if not record.exists():
        return {}
    widths = {}
    prefix = f"papers/{folder.name}/"
    for entry in json.loads(record.read_text()):
        # Most records give the file relative to the folder, some relative to the repo.
        file = entry["file"].removeprefix(prefix)
        widths[file] = {
            key[: -len("_k")]: entry[key] if isinstance(entry[key], int) else None
            for key in entry
            if key.endswith("_k")
        }
    return widths


def load(root: Path = ROOT) -> dict[str, Case]:
    """Return every circuit of the corpus by id. Raise on an incomplete manifest entry."""
    out: dict[str, Case] = {}
    for manifest in sorted(root.glob("papers/*/circuits.toml")):
        folder = manifest.parent
        table = _toml(manifest)
        arxiv = table["arxiv"]
        widths = _widths(folder)
        for name, entry in table.get("circuits", {}).items():
            file = entry.get("file", f"stim/{name}.stim")
            kind = entry["postselect"]
            if kind not in POSTSELECT_KINDS:
                raise ValueError(f"{folder.name}/{name}: unknown postselect {kind!r}")
            if not entry.get("reason"):
                raise ValueError(f"{folder.name}/{name}: postselect needs a reason")
            case = Case(
                id=f"{folder.name}/{Path(file).stem}",
                path=folder / file,
                arxiv=entry.get("arxiv", arxiv),
                sampler=entry.get("sampler", "detector"),
                postselect=kind,
                detectors=entry.get("detectors", ""),
                num_detectors=int(entry["num_detectors"]),
                reason=entry["reason"],
                random_detectors=entry.get("random_detectors", ""),
                detector_reference=bool(entry.get("detector_reference", False)),
                observable_reference=bool(entry.get("observable_reference", False)),
                widths=widths.get(file, {}),
            )
            mask_indices(case)  # validates the ranges
            if case.id in out:
                raise ValueError(f"{case.id}: listed twice")
            out[case.id] = case
    return out


def suites(root: Path = ROOT) -> dict[str, list[str]]:
    """Return the named suites of ``suites.toml``: suite name -> circuit ids."""
    table = _toml(root / "suites.toml")
    return {name: list(entry["circuits"]) for name, entry in table.items()}


def cases(
    suite: str | None = None,
    *,
    max_width: int | None = None,
    width_of: str = "tsim",
    only: str | None = None,
    root: Path = ROOT,
) -> list[Case]:
    """Select circuits: a suite (default: the whole corpus), filtered by recorded width.

    A circuit without a recorded width for ``width_of`` is dropped when ``max_width`` is set.
    """
    corpus = load(root)
    if suite in (None, "corpus"):
        selected = list(corpus.values())
    else:
        named = suites(root)
        if suite not in named:
            raise KeyError(f"unknown suite {suite!r}: {', '.join(['corpus', *named])}")
        missing = [i for i in named[suite] if i not in corpus]
        if missing:
            raise KeyError(f"suite {suite!r} names unknown circuits: {missing}")
        selected = [corpus[i] for i in named[suite]]
    if max_width is not None:
        selected = [
            c for c in selected if c.width(width_of) is not None and c.width(width_of) <= max_width
        ]
    if only:
        selected = [c for c in selected if only in c.id]
    return selected

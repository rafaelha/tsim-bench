r"""Published data used by the figures and checks: pinned URLs, sha256, and how to turn them into ``repro/data/*``.

Every study reads published numbers through ``data_file(name)``, which downloads (and, for pickles,
converts) the file on first use, so ``repro/data`` can be deleted and is rebuilt by ``run_all`` /
``make_report``:

    uv run python -m repro.data_sources        # fetch everything now

Downloads are checked against the pinned sha256 before use; a mismatch raises.
"""

import hashlib
import json
import pathlib
import urllib.request

from repro import common

DATA = common.REPRO / "data"

SOURCES = {
    # Gidney, Shutty, Jones, arXiv:2409.17595: released sinter stats (Zenodo 13777072).
    "zenodo_13777072_stats.csv": dict(
        url="https://zenodo.org/records/13777072/files/stats.csv?download=1",
        sha256="5f680dd2c0a2738ddb20877c8c1f1bf85b1f4bd5f76a7851daba197303ad98a1"),
    # Chase, Labib, arXiv:2604.27058: published inject+cultivate results (clifft-paper at db7dc9f).
    "clifft_paper_inject_cultivate_analysis.json": dict(
        url="https://raw.githubusercontent.com/unitaryfoundation/clifft-paper/db7dc9f/magic_state_cultivation/results/inject_cultivate/analysis.json",
        sha256="01b45991a1e25124742c1b30bbc023bf0c1869f500b55b2e75013b1272a4ab7a"),
    # Jacoby et al., arXiv:2504.02935: released data of Fig. 2 (injection-with-erasure-qubits at 407a678).
    "erasure_compare_injections_5e6runs_2erasures.csv": dict(
        url="https://raw.githubusercontent.com/shohamjac/injection-with-erasure-qubits/407a678aafd693b0380246c843c28a67d1fcfc99/out/2024-12-24-compare_injections_5e6runs_2erasures",
        sha256="ce6c37be02fd8e46545da8396f351b87e00aeb7ed7ff487d0806d7c8ac9c6e2a"),
    # Hetényi, Brown, Williamson, arXiv:2603.05429: yield-comparison pickles of Fig. 4(b) (IBM/gauging_clifford_measurement
    # at ce90c09), converted to JSON. The pickles are trusted at this pinned hash (unpickling executes code).
    "GaugingClifford_high_dist_yield_nopipeline.json": dict(
        url="https://raw.githubusercontent.com/IBM/gauging_clifford_measurement/ce90c09/yield_comparison/GaugingClifford_high_dist_yield_nopipeline.pkl",
        sha256="812407503d2ce690422be8f40dcc239e90d3a0f54de09cb1c4d27b1a78a088cf", convert="pickle_to_json"),
    "Gidney_cultivation_high_dist_yield.json": dict(
        url="https://raw.githubusercontent.com/IBM/gauging_clifford_measurement/ce90c09/yield_comparison/Gidney_cultivation_high_dist_yield.pkl",
        sha256="b2a3f0e3d1c9c7d023cfc8a66e05f5c1d045bef2b94fcb4e048700431e2000ab", convert="pickle_to_json"),
}


def _download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "tsim-repro"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _pickle_to_json(raw):
    import io
    import pickle

    d = pickle.load(io.BytesIO(raw))

    def conv(x):
        return x.tolist() if hasattr(x, "tolist") else x

    return json.dumps({str(k): ({str(kk): conv(vv) for kk, vv in v.items()} if isinstance(v, dict) else conv(v)) for k, v in d.items()}).encode()


def data_file(name):
    """Path of a published input file, downloading and verifying it if needed."""
    path = DATA / name
    if path.exists():
        return path
    src = SOURCES[name]
    raw = _download(src["url"])
    digest = hashlib.sha256(raw).hexdigest()
    if digest != src["sha256"]:
        raise RuntimeError(f"{name}: sha256 {digest} != pinned {src['sha256']} ({src['url']})")
    if src.get("convert") == "pickle_to_json":
        raw = _pickle_to_json(raw)
    DATA.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


def main():
    for name in SOURCES:
        print(name, data_file(name))


if __name__ == "__main__":
    main()

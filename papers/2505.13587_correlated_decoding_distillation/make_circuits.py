"""Write T-gate 15-to-1 distillation circuits from "Fast correlated decoding of transversal logical
algorithms" (Cain, Bluvstein, Zhao, Gu, Maskara, Kalinowski, Geim, Kubica, Lukin, Zhou, arXiv:2505.13587).

The authors' Zenodo record (doi:10.5281/zenodo.15702016, ``distillation.zip``) has the Stim circuits
of their magic state distillation benchmark (Fig. 4): the 15-to-1 circuit with transversal CNOTs
between 16 rotated surface-code patches of distance d = 5, 9, 13, 17, 21, 25, with SD6 noise at
p = 0.001. Stim cannot hold |T>, so each of the 15 input magic states is prepared as ``RX`` followed
by a transversal-in-time ``S`` on one patch qubit before the patch is grown (a |Y> = S|+> proxy), and
the output is checked against a reference patch prepared the same way (a second ``S`` line). The
logical Z/X readouts are written as DETECTORs (the authors' "gauge detectors"; no
OBSERVABLE_INCLUDE).

Conversion: every ``S`` line becomes ``T`` (T|+> is the |T> state the paper's Fig. 4 distils). Checks
(d = 5 and 9; the larger files are skipped because noiseless sampling takes long): sampled noiselessly
in Tsim, every detector that is deterministic in the S proxy is deterministic with the same value, and
the random detectors are exactly the proxy's random ones (the 32 logical readouts).

Usage: uv run python make_circuits.py   (downloads distillation.zip, 8.8 MB, into stim_src/_download/)
"""

import pathlib
import re
import sys
import urllib.request
import zipfile

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))

import stimtext  # noqa: E402
import validate  # noqa: E402

URL = "https://zenodo.org/records/15702016/files/distillation.zip?download=1"
DOWNLOAD = HERE / "stim_src" / "_download" / "distillation.zip"
DISTANCES = [5, 9, 13, 17, 21, 25]
VALIDATE = {5, 9}


def proxy_text(d):
    if not DOWNLOAD.exists():
        DOWNLOAD.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL, DOWNLOAD)
    with zipfile.ZipFile(DOWNLOAD) as z:
        return z.read(f"distillation/distillation_{d}").decode()


def s_to_t(text):
    assert len(re.findall(r"^S ", text, flags=re.M)) == 2
    return re.sub(r"^S ", "T ", text, flags=re.M)


def main():
    out = HERE / "stim"
    out.mkdir(exist_ok=True)
    for d in DISTANCES:
        proxy = proxy_text(d)
        text = stimtext.drop_targetless(s_to_t(proxy))
        if d in VALIDATE:
            ref = validate.check(proxy, shots=256)
            result = validate.check(text, proxy=proxy, shots=256)
            assert result["matches_proxy"] and result["random_in_proxy_only"] == 0, result
            assert result["random_detectors"] == ref["random_detectors"], (result, ref)
            note = f"{result['random_detectors']} random detectors (same as the S proxy)"
        else:
            note = "not sampled"
        (out / f"distillation_15to1_T_d{d}_p0.001.stim").write_text(text)
        print(f"wrote stim/distillation_15to1_T_d{d}_p0.001.stim: {note}", flush=True)


if __name__ == "__main__":
    main()

from typing import Counter

from .code import BBCode


def test_decompose_mono_to_interactions():
    code = BBCode.from_n(n=144)
    rst = code.decompose_mono_to_native_auts()
    cnts = Counter(rst.values())
    print(cnts)

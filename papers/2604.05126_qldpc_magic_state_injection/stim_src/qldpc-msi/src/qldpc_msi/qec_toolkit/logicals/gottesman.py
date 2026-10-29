import numpy as np
import qldpc
from numpy.typing import NDArray


def get_css_logicals_gottesman(
    Hx: NDArray[np.int_], Hz: NDArray[np.int_]
) -> tuple[list[NDArray[np.int_]], list[NDArray[np.int_]]]:
    """Use qldpc package to get logical operators."""
    css_code = qldpc.codes.CSSCode(Hx, Hz)
    logX = css_code.get_logical_ops(qldpc.objects.Pauli.X)
    logX = np.array(logX)
    print(f"{logX.shape=}")
    new_logX = [one_X for one_X in logX]

    logZ = css_code.get_logical_ops(qldpc.objects.Pauli.Z)
    logZ = np.array(logZ)
    new_logZ = [one_Z for one_Z in logZ]
    return new_logX, new_logZ

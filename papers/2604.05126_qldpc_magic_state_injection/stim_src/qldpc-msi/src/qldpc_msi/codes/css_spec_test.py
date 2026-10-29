from .css_circ_layout import CSSCircLayout
from ..tour_bb.code import BBCode
from ..xu_hgp.code import XuHgpCode


def test_bb_canonical_css_layout() -> None:
    code = BBCode.from_n(144)
    layout = code.get_circ_layout()

    assert isinstance(layout, CSSCircLayout)
    layout.validate_for(code)
    assert layout.col_id_to_dat_uid[:3] == (0, 1, 2)
    assert layout.Hx_row_id_to_x_check_uid[0] == code.num_dat_qubits
    assert layout.Hz_row_id_to_z_check_uid[0] == code.num_dat_qubits + code.num_x_checks
    assert len(layout.all_uids) == code.num_dat_qubits + code.num_checks


def test_xu_hgp_canonical_css_layout_and_derived_sizes() -> None:
    code = XuHgpCode(225)
    layout = code.get_circ_layout()

    layout.validate_for(code)
    assert code.num_dat_qubits == code.Hx.shape[1] == code.Hz.shape[1]
    assert code.num_checks == code.num_x_checks + code.num_z_checks
    assert code.num_logicals == len(code.get_logical_ops_stim()[0])
    assert layout.Hx_row_id_to_x_check_uid[0] == code.num_dat_qubits

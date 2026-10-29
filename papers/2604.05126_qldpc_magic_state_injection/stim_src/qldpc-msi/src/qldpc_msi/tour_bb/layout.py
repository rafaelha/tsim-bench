"""Stable BB layout helpers exposed through the `tour_bb` facade."""

from .code import BBCode


def get_cell_layout(code: BBCode) -> dict[int, tuple[int, int]]:
    """Get the cell-like layout of the code.
    L, X, Z, R. If they have the same monomial, they are in the same cell.
    The layout is a 2l x 2m grid. For gross code, l = 12, m = 6.
    Cell pattern, same as IBM's BB code paper, Figure 3(A), top left corner.
    Row 1:   X  |  R
    Row 0:   L  |  Z
           Col0 | Col 1

    This layout is for visualization and debugging purposes.
    """
    total_cell_layout: dict[int, tuple[int, int]] = {}
    for qtype in ["L", "X", "Z", "R"]:
        cell_layout = _get_cell_layout_of_one_type(code, qtype)
        total_cell_layout.update(cell_layout)
    assert len(total_cell_layout) == 2 * code.n
    return total_cell_layout


def _get_cell_layout_of_one_type(code: BBCode, qtype: str) -> dict[int, tuple[int, int]]:
    """Get the cell-like layout of the code for one type of qubits."""
    match qtype:
        case "L":
            shift_col, shift_row = 0, 0
            shift_uid = 0
        case "R":
            shift_col, shift_row = +1, +1
            shift_uid = code.lm
        case "X":
            shift_col, shift_row = 0, +1
            shift_uid = code.dlm
        case "Z":
            shift_col, shift_row = +1, 0
            shift_uid = code.dlm + code.lm
        case _:
            raise ValueError(f"Invalid qtype: {qtype}")
    cell_layout = {}
    for qid in range(code.lm):
        cell_coord = (qid // code.m, qid % code.m)
        coord = (cell_coord[0] * 2 + shift_col, cell_coord[1] * 2 + shift_row)
        cell_layout[qid + shift_uid] = coord
    assert len(cell_layout) == code.lm
    return cell_layout

import numpy as np
from numpy.typing import NDArray


class SubmatrixFinderByDFS:
    """There is a m x n matrix on F2. Find k rows and k cols
    s.t. the submatrix selected by these rows and cols has only one "1" in each row and each columns.

    Algorithm: Use DFS.
    In each iteration, choose a row in `cand_rows`, and sweep the `cand_cols`,
    choose a col where there is a "1".
    Then, remove all the cols in `cand_cols` that have "1" in the chosen row.
    Then, remove all the rows in `cand_rows` that have "1" in the chosen col.
    Then, go to the next iteration of DFS.
    After returning from the inner DFS, restore the removed rows and cols,
    and choose the next row in `cand_rows`.

    Prune:
    - Not enough rows and cols to reach k
    - Visited in the previous iteration
    """

    def __init__(self, matrix: NDArray[np.int_], k: int, max_n_sols=10):
        assert k <= matrix.shape[0] and k <= matrix.shape[1], f"No enough rows and cols to reach k."
        self.matrix = matrix
        self.k = k
        self.max_n_sols = max_n_sols

        # solutions, list of (row_indices, col_indices)
        self.sols: list[tuple[list[int], list[int]]] = []
        self.cnt_reach_level_k: int = 0

    def _dfs(self, cur_k: int, cand_rows: set[int], cand_cols: set[int], cur_rows: list[int], cur_cols: list[int]):
        if len(self.sols) >= self.max_n_sols:
            return
        cand_rows = cand_rows.copy()
        cand_cols = cand_cols.copy()
        if self.k > min(len(cand_rows), len(cand_cols)) + cur_k:
            # prune, not enough rows and cols to reach k
            # print(f"{cur_k=}, {len(cand_rows)=}, {len(cand_cols)=} prune, not enough rows and cols to reach k")
            return

        if cur_k == self.k:
            # Sort and convert to tuples for hashability ! TODO: better way
            # sorted_rows = tuple(sorted(cur_rows))
            # sorted_cols = tuple(sorted(cur_cols))
            self.sols.append((cur_rows.copy(), cur_cols.copy()))
            self.cnt_reach_level_k += 1
            # print(f"{self.cnt_reach_level_k=}")
            return

        min_row_id = cur_rows[-1] if cur_rows else -1
        for i in cand_rows:
            if i <= min_row_id:
                # prune, visited in the previous iteration
                continue
            # if it is a valid row
            row = self.matrix[i, :]
            nonzero_cols = np.nonzero(row)[0]
            nonzero_cand_cols = cand_cols & set(nonzero_cols)
            if len(nonzero_cand_cols) == 0:  # this is an impossible row
                continue

            cand_rows.remove(i)
            # remove all the cols that commute with the row i (including j)
            cand_cols -= nonzero_cand_cols
            for j in nonzero_cand_cols:
                # choose i-th row and j-th col, i.e., find a logical operator (i, j)
                # remove all the rows that commute with the col j
                conflict_rows = cand_rows & set(np.nonzero(self.matrix[:, j])[0])
                cand_rows -= conflict_rows
                self._dfs(cur_k + 1, cand_rows, cand_cols, cur_rows + [i], cur_cols + [j])
                # restore the removed rows
                cand_rows |= conflict_rows
            cand_cols |= nonzero_cand_cols
            cand_rows.add(i)

    def find(self) -> list[tuple[list[int], list[int]]]:
        """
        Return: list of (row_indices, col_indices)
        """
        cand_rows = set(range(self.matrix.shape[0]))
        cand_cols = set(range(self.matrix.shape[1]))
        self._dfs(0, cand_rows, cand_cols, [], [])
        return self.sols

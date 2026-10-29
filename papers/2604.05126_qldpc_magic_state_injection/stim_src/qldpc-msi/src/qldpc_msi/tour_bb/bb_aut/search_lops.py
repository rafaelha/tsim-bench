from functools import partial
from multiprocessing import Pool, cpu_count
from typing import Sequence

import numpy as np
import stim
from tqdm import tqdm

from .base_bb_aut import BBLogicalQubit, LogicalOp
from .submatrix_finder import SubmatrixFinderByDFS


def get_anticommuting_lxs_and_lzs(
    cand_lxs: list[BBLogicalQubit],
    cand_lzs: list[BBLogicalQubit],
    n_require: int,
    max_n_sols: int,
) -> list[tuple[list[int], list[int]]]:
    """Find n_require anticommuting lxs and lzs from cand_lxs and cand_lzs.

    Returns:
        list[tuple[list[int], list[int]]]: list of (lx indices, lz indices)
    """
    anticommuting_mat = np.zeros((len(cand_lxs), len(cand_lzs)), dtype=np.int_)
    for i, lx in enumerate(cand_lxs):
        for j, lz in enumerate(cand_lzs):
            if not lx.commutes_with(lz):
                anticommuting_mat[i, j] = 1

    submatrix_finder = SubmatrixFinderByDFS(anticommuting_mat, k=n_require, max_n_sols=max_n_sols)
    solutions = submatrix_finder.find()
    return solutions


def get_anticommuting_mat(lxs: Sequence[LogicalOp], lzs: Sequence[LogicalOp]) -> np.ndarray:
    """Get the anticommuting matrix of lxs and lzs."""
    anticommuting_mat = np.zeros((len(lxs), len(lzs)), dtype=np.int_)
    for i, lx in enumerate(lxs):
        for j, lz in enumerate(lzs):
            if not lx.commutes_with(lz):
                anticommuting_mat[i, j] = 1
    return anticommuting_mat


def get_overlap_mat(lxs: list[BBLogicalQubit], lzs: list[BBLogicalQubit]) -> np.ndarray:
    """Get the number of overlapping support matrix of lxs and lzs.
    Rows are lxs, columns are lzs.
    """
    overlap_mat = np.zeros((len(lxs), len(lzs)), dtype=np.int_)
    for i, lx in enumerate(lxs):
        for j, lz in enumerate(lzs):
            l_qubit_overlap, r_qubit_overlap = lx.get_support_overlap(lz)
            overlap_mat[i, j] = len(l_qubit_overlap) + len(r_qubit_overlap)
    return overlap_mat


class ConjPathSearcher:
    """Reproduce Andrew's conjugation results.
    http://arxiv.org/abs/2407.18393, Section 4.3.
    """

    def __init__(self, native_pss: list[stim.PauliString]):
        self.native_pss = native_pss
        self.n_qubits = len(native_pss[0])
        self.ps_to_path: dict[str, list[stim.PauliString]] = {self._ps_to_key(ps): [ps] for ps in native_pss}

    def _ps_to_key(self, ps: stim.PauliString) -> str:
        """Remove phase since it will not affect conjugation and anti-commutation."""
        return str(ps)[-self.n_qubits :]

    def grow_one_step(self) -> int:
        newly_found: dict[str, list[stim.PauliString]] = {}
        for i, (key_i, path_i) in tqdm(enumerate(self.ps_to_path.items()), total=len(self.ps_to_path)):
            ps_i = stim.PauliString(key_i)
            for j, (key_j, path_j) in enumerate(self.ps_to_path.items()):
                if i == j:
                    continue

                ps_j = stim.PauliString(key_j)
                if ps_i.commutes(ps_j):
                    continue

                # ps_i anti-commutes with ps_j
                # try to find a conjugation path from ps_j to ps_i
                new_ps = ps_i * ps_j
                new_key = self._ps_to_key(new_ps)
                if new_key not in self.ps_to_path:
                    newly_found[new_key] = path_i + path_j
                else:
                    # already found a path, check if the new path is shorter
                    if len(self.ps_to_path[new_key]) > len(path_i) + len(path_j):
                        newly_found[new_key] = path_i + path_j

        # update the path dict
        for key, path in newly_found.items():
            self.ps_to_path[key] = path

        return len(newly_found)

    def grow_one_step_parallel(self) -> int:
        # snapshot current items and build worker args
        items = list(self.ps_to_path.items())
        worker_fn = partial(
            _worker_step,
            items=items,
            n_qubits=self.n_qubits,
        )
        args = [(key, path) for key, path in items]

        # spin up a pool and map
        with Pool(processes=cpu_count()) as pool:
            # tqdm here just to see overall progress
            results = list(tqdm(pool.starmap(worker_fn, args), total=len(args), desc="parallel grow step"))

        # merge all worker‐found dicts, picking the shortest path for each key
        newly_found: dict[str, list[stim.PauliString]] = {}
        for worker_dict in results:
            for k, p in worker_dict.items():
                # if we've never seen k, or this path is shorter
                if k not in self.ps_to_path or len(self.ps_to_path[k]) > len(p):
                    # also check among other newly_found
                    if k not in newly_found or len(newly_found[k]) > len(p):
                        newly_found[k] = p

        # update our master map
        self.ps_to_path.update(newly_found)
        return len(newly_found)

    def grow_until_full(self, max_ps_cnt: int | None = None) -> None:
        if max_ps_cnt is None:
            max_ps_cnt = 4**self.n_qubits

        assert isinstance(max_ps_cnt, int)
        while len(self.ps_to_path) < max_ps_cnt:
            newly_found_cnt = self.grow_one_step_parallel()

        return


def _worker_step(
    key_i: str, path_i: list[stim.PauliString], items: list[tuple[str, list[stim.PauliString]]], n_qubits: int
) -> dict[str, list[stim.PauliString]]:
    """
    Worker function: given one basis element (key_i, path_i) and
    the full snapshot of items, return any newly-found conjugation paths.
    """
    newly = {}
    ps_i = stim.PauliString(key_i)
    for key_j, path_j in items:
        if key_j == key_i:
            continue
        ps_j = stim.PauliString(key_j)
        if ps_i.commutes(ps_j):
            continue
        new_ps = ps_i * ps_j
        new_key = str(new_ps)[-n_qubits:]
        new_path = path_i + path_j
        # first time seen, or strictly shorter path
        if new_key not in newly or len(newly[new_key]) > len(new_path):
            newly[new_key] = new_path
    return newly

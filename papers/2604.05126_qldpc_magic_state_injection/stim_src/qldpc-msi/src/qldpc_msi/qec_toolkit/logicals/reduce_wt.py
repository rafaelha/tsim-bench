# reduce_wt.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple, Dict, Any
import numpy as np


# =============================================================================
# 0) Small GF(2) linear-algebra utilities
# =============================================================================

def _as_gf2_matrix(A: Any) -> np.ndarray:
    """
    Convert input to a uint8 numpy array with entries in {0,1}.
    Accepts numpy arrays, scipy sparse (via .toarray()), lists, etc.
    """
    if hasattr(A, "toarray"):
        A = A.toarray()
    A = np.asarray(A)
    # Force 0/1
    A = (A.astype(np.uint8) & 1)
    return A


def gf2_rref(A: np.ndarray) -> tuple[np.ndarray, list[int]]:
    """
    Reduced row echelon form over GF(2).
    Returns:
        R : rref(A) (new matrix)
        pivots : list of pivot column indices

    Notes:
      - This is a standard Gauss-Jordan elimination but in GF(2),
        so "subtraction" is XOR.
      - Complexity is fine for n~225, m~O(100-1000).
    """
    A = _as_gf2_matrix(A).copy()
    m, n = A.shape
    pivots: list[int] = []
    r = 0

    for c in range(n):
        # Find a row >= r with a 1 in column c
        pivot_rows = np.flatnonzero(A[r:, c])
        if pivot_rows.size == 0:
            continue
        piv = int(pivot_rows[0] + r)

        # Swap pivot row into position r
        if piv != r:
            A[[r, piv]] = A[[piv, r]]

        # Eliminate all other 1's in column c
        # (including above and below) to get RREF
        for rr in range(m):
            if rr != r and A[rr, c]:
                A[rr, :] ^= A[r, :]

        pivots.append(c)
        r += 1
        if r == m:
            break

    return A, pivots


def gf2_rank(A: np.ndarray) -> int:
    """Rank over GF(2)."""
    R, _ = gf2_rref(A)
    # Nonzero rows in RREF correspond to rank
    return int(np.count_nonzero(np.any(R != 0, axis=1)))


def gf2_rowspace_basis(A: np.ndarray) -> np.ndarray:
    """
    Return an independent row basis for rowspace(A) over GF(2).
    Implementation: compute RREF of A, then keep the nonzero rows.
    """
    R, _ = gf2_rref(A)
    nz = np.any(R != 0, axis=1)
    return R[nz].copy()


def gf2_nullspace_basis(A: np.ndarray) -> np.ndarray:
    """
    Return a basis for ker(A) = {x : A x = 0} over GF(2).

    Output:
        N : (#free_vars, n) matrix whose rows form a basis.

    Construction:
      - Compute RREF and pivot columns.
      - Choose each free variable as 1 one-at-a-time, solve pivot vars.
    """
    A = _as_gf2_matrix(A)
    m, n = A.shape
    R, pivots = gf2_rref(A)

    pivot_set = set(pivots)
    free_cols = [c for c in range(n) if c not in pivot_set]

    if len(free_cols) == 0:
        # Only solution is x=0
        return np.zeros((0, n), dtype=np.uint8)

    # Map pivot col -> pivot row index in RREF
    # In RREF, pivot i is in row i (in the elimination order).
    # But if some rows are all-zero, pivots length gives number of pivot rows.
    num_piv = len(pivots)

    N = np.zeros((len(free_cols), n), dtype=np.uint8)

    for i_free, fcol in enumerate(free_cols):
        x = np.zeros(n, dtype=np.uint8)
        x[fcol] = 1

        # Solve pivot vars from RREF equations:
        # For each pivot row r:
        #   x[pivot_col] = sum_{j != pivot_col} R[r,j] * x[j] (mod2)
        # since R has pivot 1 at pivot_col.
        for r in range(num_piv - 1, -1, -1):
            pcol = pivots[r]
            # dot product over GF(2): parity of overlap
            rhs = int(np.dot(R[r, :], x) & 1)  # includes pivot itself
            # Because pivot is 1 and included in dot, we have:
            #   rhs = x[pcol] + sum_{j!=pcol} R[r,j] x[j]
            # so x[pcol] = rhs (since x[pcol] currently 0)
            # But easier: compute sum_{j!=pcol} and set pivot to that.
            # We'll do explicit:
            s = int(np.dot(R[r, :], x) & 1)
            # s = x[pcol] + other_terms, but x[pcol]=0 right now.
            x[pcol] = s

        N[i_free, :] = x

    return N


def gf2_inv(A: np.ndarray) -> np.ndarray:
    """
    Inverse of a k×k matrix over GF(2). Raises if not invertible.
    """
    A = _as_gf2_matrix(A)
    k, k2 = A.shape
    if k != k2:
        raise ValueError(f"gf2_inv requires square matrix; got {A.shape}")

    I = np.eye(k, dtype=np.uint8)
    aug = np.concatenate([A.copy(), I], axis=1)  # k×(2k)

    r = 0
    for c in range(k):
        piv_rows = np.flatnonzero(aug[r:, c])
        if piv_rows.size == 0:
            raise ValueError("Matrix not invertible over GF(2)")
        piv = int(piv_rows[0] + r)

        if piv != r:
            aug[[r, piv]] = aug[[piv, r]]

        for rr in range(k):
            if rr != r and aug[rr, c]:
                aug[rr, :] ^= aug[r, :]
        r += 1

    inv = aug[:, k:]
    return inv


def gf2_matmul(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Matrix product over GF(2): (A @ B) mod 2.
    """
    return (A @ B) & 1


def gf2_vecmul(A: np.ndarray, x: np.ndarray) -> np.ndarray:
    """
    Matrix-vector product over GF(2): (A @ x) mod 2.
    """
    return (A @ x) & 1


def wt(x: np.ndarray) -> int:
    """Hamming weight of a binary vector."""
    return int(np.count_nonzero(x))


# =============================================================================
# 1) Weight reduction core
# =============================================================================

@dataclass(frozen=True)
class ReduceReport:
    """
    Summary of a reduction run.

    - wt_before / wt_after: per-row weights
    - comm_matrix_before/after: Lx Lz^T (mod2), should remain identical
    """
    wt_before_x: tuple[int, ...]
    wt_after_x: tuple[int, ...]
    wt_before_z: tuple[int, ...]
    wt_after_z: tuple[int, ...]
    comm_before: np.ndarray
    comm_after: np.ndarray


def _greedy_local_reduce(
    v: np.ndarray,
    stab_basis: np.ndarray,
    *,
    passes: int = 6,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    Greedy hill-climb in the coset v + span(stab_basis).

    We repeatedly scan stabilizer generators s:
      if wt(v ⊕ s) < wt(v): accept the move.

    This never increases weight, but can get stuck in local minima.
    """
    v = _as_gf2_matrix(v).reshape(-1).copy()
    stab_basis = _as_gf2_matrix(stab_basis)
    if stab_basis.size == 0:
        return v

    rng = rng or np.random.default_rng()
    best = v
    best_w = wt(best)

    for _ in range(passes):
        order = np.arange(stab_basis.shape[0])
        rng.shuffle(order)
        improved = False
        for idx in order:
            s = stab_basis[idx]
            cand = best ^ s
            cw = wt(cand)
            if cw < best_w:
                best, best_w = cand, cw
                improved = True
        if not improved:
            break
    return best


def _iterated_local_search_reduce(
    v: np.ndarray,
    stab_basis: np.ndarray,
    *,
    restarts: int = 50,
    shake: int = 4,
    greedy_passes: int = 6,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    Iterated local search for lower weight in coset v + span(stab_basis).

    Repeat:
      - "shake": apply XOR of a small random subset of stabilizers
      - then greedy reduce
      - keep best seen

    This is cheap and usually beats plain greedy.
    """
    v = _as_gf2_matrix(v).reshape(-1)
    stab_basis = _as_gf2_matrix(stab_basis)
    if stab_basis.size == 0:
        return v.copy()

    rng = rng or np.random.default_rng()

    # Start from greedy-reduced original
    best = _greedy_local_reduce(v, stab_basis, passes=greedy_passes, rng=rng)
    best_w = wt(best)

    m = stab_basis.shape[0]
    shake = max(0, min(shake, m))

    for _ in range(restarts):
        cand = best.copy()

        # --- random "shake" move ------------------------------------------------
        if shake > 0:
            pick = rng.choice(m, size=shake, replace=False)
            for j in pick:
                cand ^= stab_basis[j]

        # --- greedy descent back into a local minimum ---------------------------
        cand = _greedy_local_reduce(cand, stab_basis, passes=greedy_passes, rng=rng)
        cw = wt(cand)
        if cw < best_w:
            best, best_w = cand, cw

    return best


# =============================================================================
# 2) Public entry point
# =============================================================================

def reduce_wt(
    lxs: Any,
    lzs: Any,
    Hx: Any,
    Hz: Any,
    *,
    # heuristic knobs
    method: str = "ils",          # "greedy" or "ils"
    restarts: int = 80,
    shake: int = 4,
    greedy_passes: int = 6,
    seed: int | None = 0,
    # validation knobs
    require_paired_identity: bool = True,
) -> tuple[np.ndarray, np.ndarray, ReduceReport]:
    """
    Entry function requested.

    Inputs:
      - lxs, lzs: (k, n) paired logical operators (binary vectors).
        You say lxs[i] and lzs[i] are paired logicals, i.e. Lx Lz^T = I (mod2).
      - Hx, Hz: CSS check matrices / stabilizer generators
        * X-stabilizers: rowspace(Hx)
        * Z-stabilizers: rowspace(Hz)

    Output:
      - lxs_red, lzs_red: weight-reduced logical basis
      - report: before/after weights and commutation matrix check

    --------------------------------------------------------------------------
    Why this is safe:
      - For X-logical row x: replacing x <- x ⊕ s with s in rowspace(Hx)
        multiplies by an X-stabilizer, so it stays the same logical class.
      - It also preserves commutation with every Z-logical, because any
        z in ker(Hx) commutes with every s in rowspace(Hx).
      - Same for Z-logicals using rowspace(Hz).
    --------------------------------------------------------------------------
    """
    rng = np.random.default_rng(seed)

    Lx = _as_gf2_matrix(lxs)
    Lz = _as_gf2_matrix(lzs)
    Hx = _as_gf2_matrix(Hx)
    Hz = _as_gf2_matrix(Hz)

    if Lx.shape != Lz.shape:
        raise ValueError(f"Shape mismatch: lxs {Lx.shape} vs lzs {Lz.shape}")
    k, n = Lx.shape
    if Hx.shape[1] != n or Hz.shape[1] != n:
        raise ValueError(
            f"Hx/Hz must have n columns={n}. Got Hx{Hx.shape}, Hz{Hz.shape}"
        )

    # --- basic validity checks -------------------------------------------------
    # X logical must commute with Z checks: Hz @ x = 0
    syn_x = gf2_matmul(Hz, Lx.T)  # (mZ, k)
    if np.any(syn_x):
        raise ValueError("Invalid Lx: some rows have non-trivial syndrome under Hz.")

    # Z logical must commute with X checks: Hx @ z = 0
    syn_z = gf2_matmul(Hx, Lz.T)  # (mX, k)
    if np.any(syn_z):
        raise ValueError("Invalid Lz: some rows have non-trivial syndrome under Hx.")

    comm_before = gf2_matmul(Lx, Lz.T)  # k×k
    if require_paired_identity:
        if not np.array_equal(comm_before, np.eye(k, dtype=np.uint8)):
            raise ValueError(
                "Input logicals are not paired as identity (Lx Lz^T != I). "
                "If you want auto-pairing, do it before calling reduce_wt."
            )

    # --- choose stabilizer bases (independent generators) ----------------------
    Sx = gf2_rowspace_basis(Hx)   # basis for X-stabilizer rowspace
    Sz = gf2_rowspace_basis(Hz)   # basis for Z-stabilizer rowspace

    # --- pick reducer ----------------------------------------------------------
    def reduce_vec(v: np.ndarray, basis: np.ndarray) -> np.ndarray:
        if method == "greedy":
            return _greedy_local_reduce(v, basis, passes=greedy_passes, rng=rng)
        if method == "ils":
            return _iterated_local_search_reduce(
                v, basis,
                restarts=restarts,
                shake=shake,
                greedy_passes=greedy_passes,
                rng=rng,
            )
        raise ValueError(f"Unknown method={method!r}. Use 'greedy' or 'ils'.")

    wt_before_x = tuple(wt(Lx[i]) for i in range(k))
    wt_before_z = tuple(wt(Lz[i]) for i in range(k))

    # --- reduce every logical row independently --------------------------------
    Lx_red = np.zeros_like(Lx)
    Lz_red = np.zeros_like(Lz)

    for i in range(k):
        Lx_red[i] = reduce_vec(Lx[i], Sx)
        Lz_red[i] = reduce_vec(Lz[i], Sz)

    # --- re-validate invariants ------------------------------------------------
    # Syndrome constraints remain satisfied (should, by CSS properties)
    syn_x2 = gf2_matmul(Hz, Lx_red.T)
    syn_z2 = gf2_matmul(Hx, Lz_red.T)
    if np.any(syn_x2):
        raise RuntimeError("Bug: reduction broke Hz-syndrome for some X-logical.")
    if np.any(syn_z2):
        raise RuntimeError("Bug: reduction broke Hx-syndrome for some Z-logical.")

    comm_after = gf2_matmul(Lx_red, Lz_red.T)
    if not np.array_equal(comm_after, comm_before):
        raise RuntimeError("Bug: reduction changed logical commutation matrix.")

    wt_after_x = tuple(wt(Lx_red[i]) for i in range(k))
    wt_after_z = tuple(wt(Lz_red[i]) for i in range(k))

    report = ReduceReport(
        wt_before_x=wt_before_x,
        wt_after_x=wt_after_x,
        wt_before_z=wt_before_z,
        wt_after_z=wt_after_z,
        comm_before=comm_before,
        comm_after=comm_after,
    )
    return Lx_red, Lz_red, report
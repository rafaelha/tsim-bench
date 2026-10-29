# reduce_wt_test.py
from __future__ import annotations

from pathlib import Path

import numpy as np

# Relative import (same directory)
from .reduce_wt import (
    _as_gf2_matrix,
    gf2_inv,
    gf2_matmul,
    gf2_nullspace_basis,
    gf2_rank,
    gf2_rowspace_basis,
    reduce_wt,
)

# =============================================================================
# 1) Build HGP(CSS) checks from the SEED matrix H
# =============================================================================


def build_hgp_css_checks(H_seed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Given a seed parity-check matrix H_seed of shape (nC, nV),
    build the HGP CSS check matrices (Hx, Hz) for the code hgp(H_seed, H_seed).

    Conventions used here (standard Tillich–Zémor / bposd.hgp style):
      - data-qubit vector length: n = nV^2 + nC^2
      - Hx is (nC*nV, n)  (X-checks)
      - Hz is (nC*nV, n)  (Z-checks)

    Block structure:
      Hx = [ H ⊗ I_{nV}   |   I_{nC} ⊗ H^T ]
      Hz = [ I_{nV} ⊗ H   |   H^T ⊗ I_{nC} ]

    Everything is over GF(2).
    """
    H = _as_gf2_matrix(H_seed)
    nC, nV = H.shape
    I_v = np.eye(nV, dtype=np.uint8)
    I_c = np.eye(nC, dtype=np.uint8)

    left_Hx = np.kron(H, I_v)  # (nC*nV, nV*nV)
    right_Hx = np.kron(I_c, H.T)  # (nC*nV, nC*nC)
    Hx = np.concatenate([left_Hx, right_Hx], axis=1)

    left_Hz = np.kron(I_v, H)  # (nV*nC, nV*nV) == (nC*nV, nV^2)
    right_Hz = np.kron(H.T, I_c)  # (nV*nC, nC*nC) == (nC*nV, nC^2)
    Hz = np.concatenate([left_Hz, right_Hz], axis=1)

    # sanity: shapes
    assert Hx.shape[0] == nC * nV
    assert Hz.shape[0] == nC * nV
    assert Hx.shape[1] == nV * nV + nC * nC
    assert Hz.shape[1] == nV * nV + nC * nC

    # CSS orthogonality: Hx Hz^T = 0
    prod = gf2_matmul(Hx, Hz.T)
    assert np.all(prod == 0), "CSS condition violated: Hx Hz^T != 0"

    return Hx, Hz


# =============================================================================
# 2) Derive a valid paired logical basis (Lx, Lz) from Hx, Hz
# =============================================================================


def derive_css_logicals(Hx: np.ndarray, Hz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Derive some valid paired logical basis for a CSS code (Hx, Hz) over GF(2).

    We use the quotient characterization:

      X-logical space  ~  ker(Hz) / rowspace(Hx)
      Z-logical space  ~  ker(Hx) / rowspace(Hz)

    Steps:
      (1) Compute basis for rowspace(Hx) and ker(Hz).
      (2) Pick k vectors from ker(Hz) that are independent modulo rowspace(Hx).
          Those are the Lx rows.
      (3) Similarly pick Lz rows from ker(Hx) modulo rowspace(Hz).
      (4) Symplectically pair: enforce Lx Lz^T = I by row-combining Lz.
    """
    Hx = _as_gf2_matrix(Hx)
    Hz = _as_gf2_matrix(Hz)

    n = Hx.shape[1]
    assert Hz.shape[1] == n

    # -----------------------------
    # Compute spaces we need
    # -----------------------------
    Sx = gf2_rowspace_basis(Hx)
    Sz = gf2_rowspace_basis(Hz)

    ker_Hz = gf2_nullspace_basis(Hz)  # rows are basis vectors for ker(Hz)
    ker_Hx = gf2_nullspace_basis(Hx)  # rows are basis vectors for ker(Hx)

    # Dimensions:
    dim_ker_Hz = ker_Hz.shape[0]
    dim_ker_Hx = ker_Hx.shape[0]
    rSx = Sx.shape[0]
    rSz = Sz.shape[0]

    # For CSS codes, Sx ⊆ ker(Hz) and Sz ⊆ ker(Hx), so:
    kx = dim_ker_Hz - rSx
    kz = dim_ker_Hx - rSz

    if kx != kz:
        raise RuntimeError(f"Expected kx==kz for CSS code; got {kx} vs {kz}")

    k = kx

    # -----------------------------
    # Pick k representatives for Lx
    # -----------------------------
    # We want vectors in ker(Hz) that add new directions beyond Sx.
    # We'll do a rank-growth test on [Sx; chosen_so_far].
    basis_stack = Sx.copy()
    chosen: list[np.ndarray] = []

    cur_rank = gf2_rank(basis_stack)  # should equal rSx

    for v in ker_Hz:
        trial = np.vstack([basis_stack, v])
        tr = gf2_rank(trial)
        if tr > cur_rank:
            chosen.append(v.copy())
            basis_stack = trial
            cur_rank = tr
            if len(chosen) == k:
                break

    if len(chosen) != k:
        raise RuntimeError(f"Failed to extract k={k} X-logicals from ker(Hz)/Sx.")

    Lx = np.vstack(chosen)

    # -----------------------------
    # Pick k representatives for Lz
    # -----------------------------
    basis_stack = Sz.copy()
    chosen = []
    cur_rank = gf2_rank(basis_stack)

    for v in ker_Hx:
        trial = np.vstack([basis_stack, v])
        tr = gf2_rank(trial)
        if tr > cur_rank:
            chosen.append(v.copy())
            basis_stack = trial
            cur_rank = tr
            if len(chosen) == k:
                break

    if len(chosen) != k:
        raise RuntimeError(f"Failed to extract k={k} Z-logicals from ker(Hx)/Sz.")

    Lz = np.vstack(chosen)

    # -----------------------------
    # Symplectic pairing: make Lx Lz^T = I
    # -----------------------------
    M = gf2_matmul(Lx, Lz.T)
    Minv = gf2_inv(M)  # must be invertible if both spans are correct
    # Row-combine Lz so that commutation becomes identity:
    # We want Lx (Lz')^T = I, choose Lz' = (Minv^T) Lz
    Lz = gf2_matmul(Minv.T, Lz)

    # Final checks
    assert np.all(gf2_matmul(Hz, Lx.T) == 0), "Lx not in ker(Hz)"
    assert np.all(gf2_matmul(Hx, Lz.T) == 0), "Lz not in ker(Hx)"
    assert np.array_equal(gf2_matmul(Lx, Lz.T), np.eye(k, dtype=np.uint8)), "Not paired"

    return Lx, Lz


# =============================================================================
# 3) The requested test: Xu's HGP(3,4), n=225, k=9
# =============================================================================


def test_xu_hgp() -> None:
    """
    Load the provided seed matrix 'hgp_34_n225_d4_h.txt',
    derive a valid paired logical basis,
    then weight-reduce it with reduce_wt().

    Requirements:
      - This file must live next to reduce_wt_test.py (same directory).
    """
    here = Path(__file__).resolve().parent
    h_path = "./data/codes/hgp/hgp_34_n225_d4_h.txt"
    if not Path(h_path).exists():
        raise FileNotFoundError(f"Missing {h_path}. Put hgp_34_n225_d4_h.txt in the same directory.")

    # -----------------------------
    # Load seed check matrix H
    # -----------------------------
    H_seed = np.loadtxt(h_path, dtype=float)
    H_seed = H_seed.astype(np.uint8) & 1

    # Expect (nC, nV) = (9, 12) for "34" construction
    nC, nV = H_seed.shape
    assert (nC, nV) == (9, 12), f"Unexpected H shape {H_seed.shape}; expected (9,12)."

    # -----------------------------
    # Build HGP CSS checks
    # -----------------------------
    Hx, Hz = build_hgp_css_checks(H_seed)
    n = Hx.shape[1]
    assert n == 225, f"Unexpected n={n}; expected 225."

    # k = n - rank(Hx) - rank(Hz)
    k = n - gf2_rank(Hx) - gf2_rank(Hz)
    assert k == 9, f"Unexpected k={k}; expected 9."

    # -----------------------------
    # Derive a VALID paired logical basis
    # -----------------------------
    Lx, Lz = derive_css_logicals(Hx, Hz)
    assert Lx.shape == (k, n)
    assert Lz.shape == (k, n)

    w_before = [(int(np.count_nonzero(Lx[i])), int(np.count_nonzero(Lz[i]))) for i in range(k)]

    # -----------------------------
    # Weight-reduce the basis
    # -----------------------------
    Lx_red, Lz_red, report = reduce_wt(
        Lx,
        Lz,
        Hx,
        Hz,
        method="ils",  # iterated local search + greedy
        restarts=120,
        shake=5,
        greedy_passes=8,
        seed=0,
        require_paired_identity=True,
    )

    w_after = [(int(np.count_nonzero(Lx_red[i])), int(np.count_nonzero(Lz_red[i]))) for i in range(k)]

    # -----------------------------
    # Assertions: correctness + improvement
    # -----------------------------
    # Pairing preserved
    assert np.array_equal(report.comm_after, report.comm_before)
    assert np.array_equal(report.comm_after, np.eye(k, dtype=np.uint8))

    # Syndrome constraints preserved
    assert np.all(gf2_matmul(Hz, Lx_red.T) == 0)
    assert np.all(gf2_matmul(Hx, Lz_red.T) == 0)

    # Weight should not increase row-wise (our reducer is monotone in the best-so-far sense)
    for i in range(k):
        assert w_after[i][0] <= w_before[i][0]
        assert w_after[i][1] <= w_before[i][1]

    # -----------------------------
    # Pretty print (pytest will capture, but useful when run manually)
    # -----------------------------
    print("\n" + "-" * 78)
    print("Xu HGP(3,4) n=225 k=9 logical basis weight reduction summary")
    print("-" * 78)
    for i in range(k):
        print(
            f"q{i:02d}:  X {w_before[i][0]:3d} -> {w_after[i][0]:3d}   |   "
            f"Z {w_before[i][1]:3d} -> {w_after[i][1]:3d}"
        )
    print("-" * 78)

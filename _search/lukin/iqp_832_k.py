"""Compile-only k_max estimate for [[8,3,2]] hypercube IQP circuits (Bluvstein et al. 2312.03982,
Hangleiter et al. 2404.19005, Xiao et al. 2610.03605).

Toy reconstruction, not the authors' circuits: N blocks of the [[8,3,2]] cube code, each prepared in
logical |+++> (CSS encoder), then L layers of [transversal CCZ in every block (T on even cube
vertices, T_DAG on odd ones) followed by transversal CNOTs between the blocks that differ in hypercube
dimension (layer mod log2 N), alternating control and target], then MX on
every qubit. Detectors: the X^{(8)} stabilizer of every block at the end (deterministic). No noise.
Reports Tsim 1.0.0 and Clifft 0.13.0 (ActiveWidthSchedulePass) k_max.

Usage: .venvs/tsim-cpu/bin/python _search/lukin/iqp_832_k.py
"""

import itertools
import numpy as np

VERTS = list(itertools.product([0, 1], repeat=3))  # qubit i <-> cube vertex VERTS[i]
PARITY = [sum(v) % 2 for v in VERTS]


def encoder(offset):
    # X-type generators of |+++>_L: X^8 and the three logical X's (faces x_j = 0).
    gens = [[1] * 8] + [[int(v[j] == 0) for v in VERTS] for j in range(3)]
    m = np.array(gens) % 2
    pivots, row = [], 0
    for col in range(8):  # row-reduce to find pivot qubits
        hit = [r for r in range(row, len(m)) if m[r, col]]
        if not hit:
            continue
        m[[row, hit[0]]] = m[[hit[0], row]]
        for r in range(len(m)):
            if r != row and m[r, col]:
                m[r] ^= m[row]
        pivots.append(col)
        row += 1
    lines = [f"R {' '.join(str(offset + q) for q in range(8))}",
             f"H {' '.join(str(offset + p) for p in pivots)}"]
    for r, p in enumerate(pivots):
        for q in range(8):
            if q != p and m[r, q]:
                lines.append(f"CX {offset + p} {offset + q}")
    return lines


def circuit(n_blocks, layers):
    lines = []
    for b in range(n_blocks):
        lines += encoder(8 * b)
    for layer in range(layers):
        even = [8 * b + q for b in range(n_blocks) for q in range(8) if PARITY[q] == 0]
        odd = [8 * b + q for b in range(n_blocks) for q in range(8) if PARITY[q] == 1]
        lines += [f"T {' '.join(map(str, even))}", f"T_DAG {' '.join(map(str, odd))}", "TICK"]
        dim = n_blocks.bit_length() - 1
        bit = 1 << (layer % dim) if dim else 0
        pairs = [(a, a ^ bit) for a in range(n_blocks) if bit and not a & bit]
        if layer % 2:
            pairs = [(b, a) for a, b in pairs]
        for a, b in pairs:
            perm = list(range(8))  # transversal CNOT (identity permutation keeps the code space)
            lines.append("CX " + " ".join(f"{8 * a + q} {8 * b + perm[q]}" for q in range(8)))
        lines.append("TICK")
    lines.append(f"MX {' '.join(str(q) for q in range(8 * n_blocks))}")
    m = 8 * n_blocks
    for b in range(n_blocks):
        lines.append("DETECTOR " + " ".join(f"rec[{-m + 8 * b + q}]" for q in range(8)))
    return "\n".join(lines) + "\n"


def main():
    import clifft
    import tsim

    for n_blocks in [2, 4, 8, 16]:
        for layers in [1, 2, 3, 4, 5, 6]:
            text = circuit(n_blocks, layers)
            try:
                s = tsim.Circuit(text).compile_detector_sampler()
                tk = max((c.width for c in s._program.components if hasattr(c, "width")), default=0)
            except Exception as e:  # noqa: BLE001
                tk = f"{type(e).__name__}: {str(e)[:60]}"
            try:
                pm = clifft.default_hir_pass_manager()
                pm.add(clifft.ActiveWidthSchedulePass())
                ck = clifft.compile(text, hir_passes=pm).peak_active_width
            except Exception as e:  # noqa: BLE001
                ck = f"{type(e).__name__}: {str(e)[:60]}"
            print(f"blocks={n_blocks:2d} logicals={3 * n_blocks:2d} layers={layers}: tsim k={tk}  clifft k={ck}",
                  flush=True)


if __name__ == "__main__":
    main()

"""Generate tsim CCZ-factory circuits for tricycle codes on 3-torus quotients R^3/L.

Each code has qubits on the edges of the cubulation Z^3/L, X checks on vertices,
Z checks on faces, and the transversal CCZ is the cubical cup product (each data
qubit sits in exactly two physical CCZs). The circuit follows the structure of
the CCZ error-detection experiment of arXiv:2510.07269:

  1. three blocks, data in |+>, one round of Z-syndrome extraction
  2. feed-forward X correction from the Z syndrome (needed for a real CCZ), with the
     redundant Z checks as meta-check detectors
  3. depth-2 transversal CCZ (real CCZ gates, tsim syntax)
  4. paper's CCZ noise (weight-5 Z per data qubit), then transversal MX
  5. X-check detectors and the 9 logical-X observables

Usage: python generate.py  (writes the .stim files next to this script)
"""

import itertools
import os

import numpy as np

P = 1e-3

LATTICES = {  # name -> rows generating the lattice L
    "toric_81_3_3": [[3, 0, 0], [0, 3, 0], [0, 0, 3]],
    "toric_375_3_5": [[5, 0, 0], [0, 5, 0], [0, 0, 5]],
    "tricycle_6_3_2": [[2, 0, 0], [1, 1, 0], [1, 0, 1]],
    "tricycle_9_3_2": [[3, 0, 0], [1, 1, 0], [1, 0, 1]],
    "tricycle_12_3_2": [[2, 0, 0], [0, 2, 0], [1, 1, 1]],
    "tricycle_15_3_2": [[5, 0, 0], [2, 1, 0], [3, 0, 1]],
    "tricycle_18_3_2": [[3, 0, 0], [0, 2, 0], [1, 1, 1]],
    "tricycle_21_3_3": [[7, 0, 0], [2, 1, 0], [3, 0, 1]],
    "tricycle_24_3_2": [[4, 0, 0], [0, 2, 0], [1, 1, 1]],
    "tricycle_27_3_3": [[3, 0, 0], [0, 3, 0], [1, 1, 1]],
}


# 3D toric code of size L: Z strings have length L, X membranes area L^2.
KNOWN_DISTANCE = {"toric_81_3_3": (3, 9), "toric_375_3_5": (5, 25)}


def gf2_rank(m):
    m = m.copy() % 2
    r = 0
    for c in range(m.shape[1]):
        rows = np.flatnonzero(m[r:, c])
        if not len(rows):
            continue
        p = r + rows[0]
        m[[r, p]] = m[[p, r]]
        for i in np.flatnonzero(m[:, c]):
            if i != r:
                m[i] ^= m[r]
        r += 1
        if r == m.shape[0]:
            break
    return r


def gf2_nullspace(m):
    m = m.copy() % 2
    n = m.shape[1]
    piv, r = [], 0
    for c in range(n):
        rows = np.flatnonzero(m[r:, c])
        if not len(rows):
            continue
        p = r + rows[0]
        m[[r, p]] = m[[p, r]]
        for i in np.flatnonzero(m[:, c]):
            if i != r:
                m[i] ^= m[r]
        piv.append(c)
        r += 1
        if r == m.shape[0]:
            break
    basis = []
    for f in (c for c in range(n) if c not in piv):
        v = np.zeros(n, np.uint8)
        v[f] = 1
        for i, c in enumerate(piv):
            v[c] = m[i, f]
        basis.append(v)
    return np.array(basis)


def gf2_right_inverse(h):
    """Independent rows I of h and R with h[I] R = 1 (mod 2)."""
    rows, independent = [], []
    for r in range(h.shape[0]):
        stacked = np.vstack(rows + [h[r]])
        if gf2_rank(stacked) > len(rows):
            rows.append(h[r])
            independent.append(r)
    hi = np.array(rows)
    k, n = hi.shape
    aug = np.concatenate([hi, np.eye(k, dtype=np.uint8)], 1)
    piv, r = [], 0
    for c in range(n):
        cand = np.flatnonzero(aug[r:, c])
        if not len(cand):
            continue
        p = r + cand[0]
        aug[[r, p]] = aug[[p, r]]
        for i in np.flatnonzero(aug[:, c]):
            if i != r:
                aug[i] ^= aug[r]
        piv.append(c)
        r += 1
        if r == k:
            break
    inv = np.zeros((n, k), np.uint8)
    for i, c in enumerate(piv):
        inv[c] = aug[i, n:]
    assert ((hi.astype(int) @ inv) % 2 == np.eye(k)).all()
    return independent, inv


def torus_code(lattice):
    lat = np.array(lattice, dtype=np.int64)
    inv = np.linalg.inv(lat.astype(float))
    num_v = round(abs(np.linalg.det(lat)))

    def canon(v):
        f = np.array(v, float) @ inv
        f -= np.floor(f + 1e-9)
        return tuple(np.round(f @ lat).astype(np.int64))

    verts = {}
    span = int(np.abs(lat).sum()) + 1
    for v in itertools.product(range(-span, span + 1), repeat=3):
        verts.setdefault(canon(v), len(verts))
    assert len(verts) == num_v
    e = np.eye(3, dtype=np.int64)
    vid = lambda v: verts[canon(v)]
    edge = lambda v, d: 3 * vid(v) + d
    n = 3 * num_v
    hx = np.zeros((num_v, n), np.uint8)
    for v in verts:
        for d in range(3):
            hx[vid(v), edge(v, d)] ^= 1
            hx[vid(v), edge(np.subtract(v, e[d]), d)] ^= 1
    hz = []
    for v in verts:
        for a, b in [(0, 1), (0, 2), (1, 2)]:
            row = np.zeros(n, np.uint8)
            for q in (edge(v, a), edge(np.add(v, e[a]), b), edge(np.add(v, e[b]), a), edge(v, b)):
                row[q] ^= 1
            if row.any():
                hz.append(row)
    hz = np.array(hz)
    triples = set()
    for v in verts:
        for s in itertools.permutations(range(3)):
            p1 = np.add(v, e[s[0]])
            p2 = np.add(p1, e[s[1]])
            triples.add((edge(v, s[0]), edge(p1, s[1]), edge(p2, s[2])))
    hx = hx[hx.any(1)]
    return n, hx, hz, sorted(triples)


def logical_x(hx, hz):
    lx, base = [], hx.copy()
    for v in gf2_nullspace(hz):
        if gf2_rank(np.vstack([base, v])) > gf2_rank(base):
            lx.append(v)
            base = np.vstack([base, v])
    return np.array(lx)


def check_ccz(n, hx, hz, lx, triples):
    """Transversal CCZ preserves the code and acts as CCZ on the 6 triples a,b,c distinct."""
    tensor = np.zeros((n, n, n), np.uint8)
    for t in triples:
        tensor[t] = 1
    f = lambda a, b, c: int(np.einsum("ijk,i,j,k->", tensor, a, b, c) % 2)
    ker = gf2_nullspace(hz)
    assert not (hx.astype(int) @ hz.T % 2).any()
    for g in hx:
        for b in ker:
            for c in ker:
                assert f(g, b, c) == f(b, g, c) == f(b, c, g) == 0
    logical = {(a, b, c) for a in range(3) for b in range(3) for c in range(3) if f(lx[a], lx[b], lx[c])}
    assert logical == set(itertools.permutations(range(3))), logical


def cx_layers(hz):
    """Bipartite edge colouring of the (data, Z-check) graph: one CX layer per colour."""
    deg = max(hz.sum(0).max(), hz.sum(1).max())
    colour = {}
    at_q, at_c = {}, {}
    for c, q in zip(*np.nonzero(hz.T)):  # edges (data q, check c)
        q, c = int(c), int(q)
        free_q = next(x for x in range(deg) if (q, x) not in at_q)
        free_c = next(x for x in range(deg) if (c, x) not in at_c)
        if free_q != free_c:
            # flip the free_q/free_c alternating path that starts at check c
            a, b = free_q, free_c
            path, node, side, col = [], c, "c", a
            while True:
                nxt = (at_c if side == "c" else at_q).get((node, col))
                if nxt is None:
                    break
                path.append(nxt)
                node = nxt[0] if side == "c" else nxt[1]
                side = "q" if side == "c" else "c"
                col = b if col == a else a
            for edge_ in path:
                old = colour.pop(edge_)
                del at_q[(edge_[0], old)], at_c[(edge_[1], old)]
            for i, edge_ in enumerate(path):
                new = b if i % 2 == 0 else a
                colour[edge_] = new
                at_q[(edge_[0], new)] = edge_
                at_c[(edge_[1], new)] = edge_
        colour[(q, c)] = free_q
        at_q[(q, free_q)] = (q, c)
        at_c[(c, free_q)] = (q, c)
    assert len(colour) == int(hz.sum())
    layers = [[] for _ in range(deg)]
    for (q, c), x in colour.items():
        layers[x].append((q, c))
    for layer in layers:
        assert len({q for q, _ in layer}) == len(layer) == len({c for _, c in layer})
    return [sorted(layer) for layer in layers if layer]


def ccz_layers(triples):
    layers = []
    for t in triples:
        for layer in layers:
            if not set(t) & layer["q"]:
                layer["g"].append(t)
                layer["q"] |= set(t)
                break
        else:
            layers.append({"g": [t], "q": set(t)})
    return [layer["g"] for layer in layers]


def factory_circuit(name, n, hx, hz, lx, triples, header):
    nz = len(hz)
    stride = n + nz
    data = lambda b, q: stride * b + q
    anc = lambda b, c: stride * b + n + c
    all_data = [data(b, q) for b in range(3) for q in range(n)]
    all_anc = [anc(b, c) for b in range(3) for c in range(nz)]
    out = [f"# {line}" if line else "#" for line in header]
    out.append("RX " + " ".join(map(str, all_data)))
    out.append("R " + " ".join(map(str, all_anc)))
    out.append(f"DEPOLARIZE1({P}) " + " ".join(map(str, all_anc)))
    out.append("TICK")
    for layer in cx_layers(hz):
        pairs = " ".join(f"{data(b, q)} {anc(b, c)}" for b in range(3) for q, c in layer)
        out += [f"CX {pairs}", f"DEPOLARIZE2({P}) {pairs}", "TICK"]
    out.append(f"DEPOLARIZE1({P}) " + " ".join(map(str, all_anc)))
    out.append("MR " + " ".join(map(str, all_anc)))
    num_meas = len(all_anc)
    rec_anc = lambda b, c: f"rec[{b * nz + c - num_meas}]"
    independent, inv = gf2_right_inverse(hz)
    for b in range(3):
        for r in range(nz):
            if r in independent:
                continue
            coeffs = (hz[r].astype(int) @ inv) % 2
            recs = [anc(b, r)] + [anc(b, independent[i]) for i in np.flatnonzero(coeffs)]
            out.append("DETECTOR " + " ".join(rec_anc(b, a - stride * b - n) for a in recs))
        for i, r in enumerate(independent):
            for q in np.flatnonzero(inv[:, i]):
                out.append(f"CX {rec_anc(b, r)} {data(b, q)}")
    out.append("TICK")
    phys = [tuple(data(b, t[b]) for b in range(3)) for t in triples]
    for layer in ccz_layers(phys):
        out += ["CCZ " + " ".join(str(q) for t in layer for q in t), "TICK"]
    for b in range(3):
        for q in range(n):
            partners = sorted({x for t in phys if t[b] == data(b, q) for x in t if x != data(b, q)})
            out.append(f"E({P}) " + " ".join(f"Z{x}" for x in [data(b, q), *partners]))
    out.append("TICK")
    out.append(f"DEPOLARIZE1({P}) " + " ".join(map(str, all_data)))
    out.append("MX " + " ".join(map(str, all_data)))
    rec_data = lambda b, q: f"rec[{b * n + q - 3 * n}]"
    for b in range(3):
        for row in hx:
            out.append("DETECTOR " + " ".join(rec_data(b, q) for q in np.flatnonzero(row)))
    for b in range(3):
        for i, row in enumerate(lx):
            out.append(f"OBSERVABLE_INCLUDE({3 * b + i}) " + " ".join(rec_data(b, q) for q in np.flatnonzero(row)))
    return "\n".join(out) + "\n"


def distance(h, g):
    """Minimum weight of ker(h) outside rowspace(g), by brute force (small codes only)."""
    ker = gf2_nullspace(h)
    if len(ker) > 22:
        return None
    rank_g, best = gf2_rank(g), None
    for bits in itertools.product([0, 1], repeat=len(ker)):
        if not any(bits):
            continue
        v = (np.array(bits) @ ker) % 2
        if gf2_rank(np.vstack([g, v])) == rank_g:
            continue
        best = int(v.sum()) if best is None else min(best, int(v.sum()))
    return best


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for name, lattice in LATTICES.items():
        n, hx, hz, triples = torus_code(lattice)
        lx = logical_x(hx, hz)
        k = n - gf2_rank(hx) - gf2_rank(hz)
        assert k == 3
        if n <= 81:
            check_ccz(n, hx, hz, lx, triples)
        dz, dx = KNOWN_DISTANCE.get(name) or (distance(hx, hz), distance(hz, hx))
        header = [
            f"{name}: tricycle code on the 3-torus R^3/L, lattice L rows = {lattice}",
            f"[[{n},{k},{'?' if dz is None else min(dz, dx)}]] per block (d_Z={dz}, d_X={dx}), three blocks, "
            f"{len(triples)} physical CCZs",
            "Real transversal CCZ (tsim syntax: CCZ is not a stim gate). Generated by generate.py.",
            f"Noise: DEPOLARIZE1({P}) on Z-ancillas after reset and before MR, DEPOLARIZE2({P}) after each CX,",
            f"E({P}) weight-5 Z per data qubit after the CCZ, DEPOLARIZE1({P}) on data before MX.",
        ]
        text = factory_circuit(name, n, hx, hz, lx, triples, header)
        with open(os.path.join(here, f"{name}.stim"), "w") as f:
            f.write(text)
        print(name, f"n={n} d_Z={dz} d_X={dx} nCCZ={len(triples)}")


if __name__ == "__main__":
    main()

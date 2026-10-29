import itertools

import numpy as np
import pulp
import stim
import tqdm


def decompose_pauli_str(target_pauli_str: stim.PauliString | np.ndarray, native_paulis_mat: np.ndarray) -> list[int]:
    """Synthesize the target pauli string using the native paulis."""
    if isinstance(target_pauli_str, stim.PauliString):
        xs, zs = target_pauli_str.to_numpy()
        symp_vec = np.hstack((xs, zs), dtype=np.int_)
    elif isinstance(target_pauli_str, np.ndarray):
        symp_vec = target_pauli_str
    else:
        raise ValueError(f"Invalid target pauli string: {target_pauli_str}")
    coeff = solve_GF2_linear_eq(native_paulis_mat, symp_vec)
    return coeff


def get_distribution_of_decomposing_arbitrary_pauli_str(
    native_paulis_mat: np.ndarray,
    n_samples: int,
) -> dict[int, int]:
    """Get the distribution of decomposing arbitrary pauli string into basis paulis."""
    n_qubits = native_paulis_mat.shape[1] // 2

    # there are native_cnts[i] many pauli strings using i many native paulis
    native_cnts: dict[int, int] = {}
    # for pauli_str in tqdm.tqdm(stim.PauliString.iter_all(n_qubits), total=4**n_qubits):
    for pauli_str in tqdm.tqdm([stim.PauliString.random(n_qubits) for _ in range(n_samples)]):
        xs, zs = pauli_str.to_numpy()
        symp_vec = np.hstack((xs, zs), dtype=np.int_)
        # coeff = np.linalg.solve(native_paulis_mat.T, GF2(symp_vec))
        coeff = solve_GF2_linear_eq(np.array(native_paulis_mat, dtype=np.int_), symp_vec)
        coeff = np.array(coeff, dtype=np.int_)
        assert np.all((np.array(native_paulis_mat, dtype=np.int_).T @ np.array(coeff, dtype=np.int_)) % 2 == symp_vec)
        # print(f"{pauli_str=}")
        # print(f"{coeff=}")
        n_used_native_paulis = np.count_nonzero(coeff)
        # print(f"{n_used_native_paulis=}")
        native_cnts[n_used_native_paulis] = native_cnts.get(n_used_native_paulis, 0) + 1

        ps_lst = []
        for ps_idx in np.nonzero(coeff)[0]:
            vec = np.array(native_paulis_mat[ps_idx, :], dtype=np.bool_)
            # print(f"{vec=}, {vec[:n_qubits]=}, {vec[n_qubits:]=}")
            ps = stim.PauliString.from_numpy(xs=vec[:n_qubits], zs=vec[n_qubits:])
            ps_lst.append(ps)

        # anti_commuting_seqs = find_anti_comm_ps_seqs(ps_lst)
        # if len(anti_commuting_seqs) > 0:
        #     print(f"{len(anti_commuting_seqs)=}")
        #     # for seq in anti_commuting_seqs:
        #     #     print(f"{seq=}")
        # else:
        #     print(f"no anti-commuting sequence for {pauli_str=}")

    return native_cnts


def solve_GF2_linear_eq(G_bits: np.ndarray, p_bits: np.ndarray) -> list[int]:
    """Solve the linear equation over GF(2)."""
    # G_bits: shape (m, n) numpy array of 0/1
    # p_bits: length-n numpy array of 0/1

    m, n = G_bits.shape
    prob = pulp.LpProblem("minimize_weight", pulp.LpMinimize)

    # binary decision vars
    c = pulp.LpVariable.dicts("c", range(m), cat="Binary")
    # integer slack for each equation
    z = pulp.LpVariable.dicts("z", range(n), lowBound=0, cat="Integer")

    # parity‐check constraints
    for j in range(n):
        prob += pulp.lpSum(G_bits[i, j] * c[i] for i in range(m)) - 2 * z[j] == p_bits[j]

    # objective = minimize Hamming weight of c
    prob += pulp.lpSum(c[i] for i in range(m))

    # prob.solve()
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    c_opt = [int(c[i].value()) for i in range(m)]
    return c_opt


def find_anti_comm_ps_seqs(
    pauli_strs: list[stim.PauliString],
) -> list[list[stim.PauliString]]:
    """Find the anti-commuting sequences of pauli strs.
    Requirement: Define R_j = Q_1 * Q_2 * ... * Q_j.
    Find all the sequences of Q_i's s.t. { R_j, Q_{j+1} } = 0 for all j.
    """
    n_ps = len(pauli_strs)

    valid_seqs = []
    for seq in itertools.permutations(pauli_strs):
        cur_vec = seq[0]
        is_invalid = False
        cur_seq = [cur_vec]  # R_j
        for i in range(1, n_ps):
            if cur_vec.commutes(seq[i]):
                is_invalid = True
                break
            cur_vec = cur_vec * seq[i]
            cur_seq.append(cur_vec)

        if not is_invalid:
            valid_seqs.append(cur_seq)

    return valid_seqs

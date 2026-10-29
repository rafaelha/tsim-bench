"""Find maximum injectable sets (denoted as I) and corresponding injection qubits,
and grouping of overlaps.

Constraints:
(1) T_i \\notin overlap(X_i, Z_j) for all i, j in inj_lids
(2) Overlaps are pair-closed.
"""

import itertools
from dataclasses import dataclass

import networkx as nx
import numpy as np


@dataclass
class InjCfg:
    inj_lids: list[int]
    inj_uids: list[int]
    groups: list[list[int]]

    def inj_map_key(self) -> tuple[tuple[int, int], ...]:
        """Canonical, hashable key: sorted (inj_lid, inj_uid) pairs.

        This is the user's notion of uniqueness for an injection configuration.
        """
        return tuple(sorted(zip(self.inj_lids, self.inj_uids)))


def _canonicalize_inj_cfg(cfg: InjCfg) -> InjCfg:
    """Make ordering deterministic (helpful for reproducible outputs).

    - sort inj_lids and reorder inj_uids accordingly
    - sort each group and sort the list of groups lexicographically
    """
    lid_to_uid = {lid: uid for lid, uid in zip(cfg.inj_lids, cfg.inj_uids)}
    inj_lids_sorted = sorted(cfg.inj_lids)
    inj_uids_sorted = [lid_to_uid[lid] for lid in inj_lids_sorted]

    groups_sorted: list[list[int]] = []
    for g in cfg.groups:
        gg = sorted(g)
        if gg:
            groups_sorted.append(gg)
    groups_sorted.sort()

    return InjCfg(inj_lids_sorted, inj_uids_sorted, groups_sorted)


def dedup_inj_cfgs_by_inj_map(cfgs: list[InjCfg]) -> list[InjCfg]:
    """Deduplicate configurations using only the injection map as the key.

    If multiple configs share the same inj_map, we keep a deterministic
    representative (lexicographically smallest after canonicalization).
    """
    unique: dict[tuple[tuple[int, int], ...], InjCfg] = {}
    for cfg in cfgs:
        cfg_can = _canonicalize_inj_cfg(cfg)
        key = cfg_can.inj_map_key()

        # Keep a deterministic representative if duplicates exist.
        if key not in unique:
            unique[key] = cfg_can
        else:
            cur = unique[key]
            if (cfg_can.inj_lids, cfg_can.inj_uids, cfg_can.groups) < (cur.inj_lids, cur.inj_uids, cur.groups):
                assert False, f"They should have the same triplet; turn this off for partial key deduplication."
                unique[key] = cfg_can

    # Return in deterministic order by inj_map.
    return [unique[k] for k in sorted(unique.keys())]


# ----------  the top-level function ----------
def find_all_valid_inj_cfgs(lx_supps: list[list[int]], lz_supps: list[list[int]]) -> list[InjCfg]:
    """Find all valid injection logical qubit ids settings.

    Returns:
        list[InjCfg]: List of injectable logical qubit ids settings.
    """
    assert len(lx_supps) == len(lz_supps)
    k = len(lx_supps)
    xz_pair_to_overlaps: dict[tuple[int, int], list[int]] = {}
    overlap_to_xz_pairs: dict[int, list[tuple[int, int]]] = {}

    # -------- 1. derive the overlap(X_i, Z_j) and its reverse map --------
    n_overlaps = np.zeros((k, k), dtype=np.int_)
    for (i, lx_supp), (j, lz_supp) in itertools.product(enumerate(lx_supps), enumerate(lz_supps)):
        # print(f"{lx_supp=}, {lz_supp=}")
        lx_supp = set(lx_supp)
        lz_supp = set(lz_supp)
        overlap = [uid for uid in lx_supp & lz_supp]
        xz_pair_to_overlaps[(i, j)] = list(sorted(overlap))
        n_overlaps[i, j] = len(overlap)
    # print(f"\n{n_overlaps}")

    for xz_pair, overlap in xz_pair_to_overlaps.items():
        for uid in overlap:
            if uid in overlap_to_xz_pairs:
                overlap_to_xz_pairs[uid].append(xz_pair)
            else:
                overlap_to_xz_pairs[uid] = [xz_pair]
    # for uid, xz_pairs in overlap_to_xz_pairs.items():
    #     print(f"{uid=}, {len(xz_pairs)=}")

    # -------- 2. brute-force all the possible injection uids for all k logicals --------
    cand_inj_uids_lst = get_cand_inj_uids_for_all_k_logicals(lx_supps, lz_supps)
    # print(f"{len(cand_inj_uids_lst)=}")
    # print(f"{cand_inj_uids_lst[0]=}")

    # -------- 3. for each injection uids, find the maximum injectable logical ids subsets --------
    valid_inj_cfgs: list[InjCfg] = []
    for inj_uids_of_k in cand_inj_uids_lst:
        inj_cfgs = get_maximum_injectable_subsets_given_k_inj_uids(
            inj_uids_of_k, overlap_to_xz_pairs, xz_pair_to_overlaps
        )

        # --------- 4. each subset and its corresponding injection uids form a valid injection configuration. ---------
        valid_inj_cfgs.extend(inj_cfgs)
    # Deduplicate by the user's notion of uniqueness: inj_map := {inj_lid: inj_uid}.
    return dedup_inj_cfgs_by_inj_map(valid_inj_cfgs)


def get_maximum_injectable_subsets_given_k_inj_uids(
    inj_uids_of_k: list[int],
    overlap_to_xz_pairs: dict[int, list[tuple[int, int]]],
    xz_pair_to_overlaps: dict[tuple[int, int], list[int]],
) -> list[InjCfg]:
    """Given k injection uids, find the maximum injectable logical ids subsets of [0, k-1].

    Once injection uids are fixed, we will know some logicals cannot be injected together.
    We then find the maximum injectable logical ids subsets.
    There might be more than one maximum injectable logical ids subsets, sharing the same number of logicals.
    Any subset of any subset is also injectable.

    Returns:
        list[list[int]]: All maximum injectable logical ids subsets.
    """
    k = len(inj_uids_of_k)

    # ------ 1. T_i \notin overlap(X_i, Z_j) for all i, j in inj_lids ------
    conflict_mat = np.zeros((k, k), dtype=np.int_)
    for lid, inj_uid in enumerate(inj_uids_of_k):
        for xz_pair in overlap_to_xz_pairs[inj_uid]:
            if xz_pair[0] == xz_pair[1]:
                continue
            the_other_lid = xz_pair[0] if xz_pair[0] != lid else xz_pair[1]
            conflict_mat[lid, the_other_lid] = 1

    # the MISs are the candidates for the maximum injectable logical ids subsets.
    MISs, max_k = get_all_MISs(conflict_mat)

    # ------- 2. for each MIS/candidate set, find subset of MIS that is pair-closed ------
    valid_inj_cfgs: list[InjCfg] = []
    for MIS in MISs:
        inj_cfgs = comp_maximum_subsets_of_cand_lids(
            MIS,
            np.array(inj_uids_of_k)[MIS].tolist(),
            xz_pair_to_overlaps,
        )

        valid_inj_cfgs.extend(inj_cfgs)
    return valid_inj_cfgs


def comp_maximum_subsets_of_cand_lids(
    cand_lids: list[int],
    inj_uids: list[int],
    xz_to_overlap: dict[tuple[int, int], list[int]],
) -> list[InjCfg]:
    """Compute the valid maximum injection logical-id subsets from the candidate logical ids.

    This version enforces the GHZ-2 (Bell-pair) pair-closure condition by explicitly
    constructing a pairing (or concluding none exists).

    Returns:
        list[tuple[list[int], list[tuple[int, int]]]]:
        - subset of logical ids
        - groups of uids (empty list if no groups required)
    """
    assert len(cand_lids) == len(inj_uids)
    lid_to_inj_uid = {lid: uid for lid, uid in zip(cand_lids, inj_uids)}
    n = len(cand_lids)

    all_maximum: list[InjCfg] = []

    # brute-force: search by decreasing subset size
    for r in range(n, 0, -1):
        for comb in itertools.combinations(cand_lids, r):
            S = list(comb)
            groups = compute_pair_closed_groups_for_injection_subset(S, lid_to_inj_uid, xz_to_overlap)
            if groups is not None:
                all_maximum.append(InjCfg(S, [lid_to_inj_uid[lid] for lid in S], groups))

        # if all_maximum:  # early exit
        #     break

    return all_maximum


# ------------- pair-closed pairing -----------


def compute_pair_closed_groups(
    constraint_sets: list[set[int]],
) -> list[list[int]] | None:
    """Construct a GHZ-2 (Bell-pair) grouping that is pair-closed w.r.t. all constraint sets.

    Pair-closed means: for every constraint set S and every pair {u,v} in the pairing,
    u in S iff v in S. Equivalently, every constraint set is a union of whole pairs.

    Args:
        constraint_sets: list of qubit-sets whose parities must be simultaneously satisfied.

    Returns:
        A list of disjoint groups covering U := union(constraint_sets) if feasible;
        otherwise None.
    """
    if not constraint_sets:
        return []

    U: set[int] = set().union(*constraint_sets)

    # Group qubits by their membership "signature" across all constraint sets.
    groups: dict[int, list[int]] = {}
    for q in U:
        mask = 0
        # mask is the signature: \sigma(q) = (1[q\in S_1], 1[q\in S_2], ..., 1[q\in S_k])
        # S_i: constraint set
        # The qubit p, q may be paired iff \sigma(p) = \sigma(q)
        for t, S in enumerate(constraint_sets):
            if q in S:
                mask |= 1 << t
        groups.setdefault(mask, []).append(q)

    # Feasible iff every signature class has even size.
    for qs in groups.values():
        if len(qs) % 2 == 1:
            return None

    return list(groups.values())


def groups_to_pairs(groups: list[list[int]]) -> list[tuple[int, int]]:
    """Convert a dictionary of groups to a list of pairs.
    Pair adjacent elements in each group."""
    pairs: list[tuple[int, int]] = []
    for qs in groups:
        qs.sort()
        for idx in range(0, len(qs), 2):
            pairs.append((qs[idx], qs[idx + 1]))
    return pairs


def compute_pair_closed_groups_for_injection_subset(
    subset_lids: list[int],
    lid_to_inj_uid: dict[int, int],
    xz_to_overlap: dict[tuple[int, int], list[int]],
    return_pairs: bool = False,
) -> list[list[int]] | None:
    """Compute an explicit GHZ-2 pairing for a chosen injection subset.

    Constraint sets included:
      (1) self-core: overlap(X_i,Z_i) \\ {Q_i}  for each i in subset_lids
      (2) cross overlap: overlap(X_i,Z_j) for each ordered i != j in subset_lids

    Returns:
        pairing as list[(u,v)] if feasible under pair-closure; else None.
    """
    constraint_sets: list[set[int]] = []

    # (1) self-core sets
    for i in subset_lids:
        Di = set(xz_to_overlap[(i, i)]) - {lid_to_inj_uid[i]}
        assert len(Di) % 2 == 0, f"{i=}, {len(Di)=}"
        if Di:
            constraint_sets.append(Di)

    # (2) cross overlap sets (ordered)
    for i, j in itertools.permutations(subset_lids, 2):
        if i == j:
            continue
        if (i, j) not in xz_to_overlap:
            continue
        Cij = set(xz_to_overlap[(i, j)])
        assert len(Cij) % 2 == 0, f"{i=}, {j=}, {len(Cij)=}"
        if Cij:
            constraint_sets.append(Cij)

    groups = compute_pair_closed_groups(constraint_sets)
    if groups is None:
        return None

    if return_pairs:
        return list(map(list, groups_to_pairs(groups)))
    else:
        return groups


# ----------  the helper functions ----------


def get_cand_inj_uids_for_all_k_logicals(
    lx_supps: list[list[int]],
    lz_supps: list[list[int]],
) -> list[list[int]]:
    """overlap(X_i, Z_i) might have multiple qubits.
    We brute-force all the possible injection qubit ids.
    Returns:
        list[list[int]]: All valid injection physical uids
    """
    assert len(lx_supps) == len(lz_supps)
    inj_uid_cands_lst: list[list[int]] = []

    for i, (lx_supp, lz_supp) in enumerate(zip(lx_supps, lz_supps)):
        overlap = sorted(list(set(lx_supp) & set(lz_supp)))
        inj_uid_cands_lst.append(overlap)

    inj_uids_lst = list(itertools.product(*inj_uid_cands_lst))
    inj_uids_lst = [list(lst) for lst in inj_uids_lst]
    return inj_uids_lst


def get_all_MISs(
    incidence_mat: np.ndarray,
) -> tuple[list[list[int]], int]:
    """Get all maximal independent sets of the graph."""
    n = incidence_mat.shape[0]
    G = nx.from_numpy_array(incidence_mat)  # original graph
    C = nx.complement(G)  # complement graph

    # enumerate all maximal cliques of the complement
    cliques = list(nx.find_cliques(C))
    if not cliques:
        return [list(range(n))], n  # edgeless graph case

    max_k = max(len(c) for c in cliques)
    # cliques of max size in complement = maximum independent sets in original
    MIS = sorted({tuple(sorted(c)) for c in cliques if len(c) == max_k})
    return [list(s) for s in MIS], max_k


def make_xz_pair_to_overlap(
    lx_supps: list[list[int]],
    lz_supps: list[list[int]],
) -> dict[tuple[int, int], list[int]]:
    """Make the mapping from xz pair to overlap.
    If overlap is empty, the key is not in the dictionary.

    Returns:
        dict[tuple[int, int], list[int]]: The mapping from xz pair to overlap.
        E.g., (0, 1): [2, 3, 4] means overlap(X0, Z1) = [2, 3, 4].
        If overlap is empty, the key is not in the dictionary.
    """
    assert len(lx_supps) == len(lz_supps)
    xz_pair_to_overlap: dict[tuple[int, int], list[int]] = {}
    for i, j in itertools.product(range(len(lx_supps)), range(len(lz_supps))):
        overlap = sorted(list(set(lx_supps[i]) & set(lz_supps[j])))
        xz_pair_to_overlap[(i, j)] = overlap
    return xz_pair_to_overlap

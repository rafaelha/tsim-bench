from .code import XuHgpCode


def test_logical_basis_weight():
    code = XuHgpCode(225)
    lxs_stim, lzs_stim = code.get_logical_ops_stim()
    lxs = [lx.to_numpy()[0] for lx in lxs_stim]
    lzs = [lz.to_numpy()[1] for lz in lzs_stim]
    lxs_supp = [lx.nonzero()[0].tolist() for lx in lxs]
    lzs_supp = [lz.nonzero()[0].tolist() for lz in lzs]
    for lx_supp, lz_supp in zip(lxs_supp, lzs_supp):
        print(f"{len(lx_supp)=}, {len(lz_supp)=}, overlap={len(set(lx_supp) & set(lz_supp))}")

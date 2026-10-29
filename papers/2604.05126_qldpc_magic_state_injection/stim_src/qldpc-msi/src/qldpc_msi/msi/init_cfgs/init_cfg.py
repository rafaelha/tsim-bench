import itertools
from dataclasses import dataclass


@dataclass
class InitCfg:
    inj_lids: list[int]
    inj_uids: list[int]
    ghz_uids_lst: list[list[int]]
    fixed_stab_uids: list[int]
    fixed_x_stab_ids: list[int]
    fixed_z_stab_ids: list[int]
    dat_uids_init_in_x: list[int]
    dat_uids_init_in_z: list[int]

    @property
    def n_fixed_stabs(self) -> int:
        return len(self.fixed_x_stab_ids) + len(self.fixed_z_stab_ids)

    def verify(self) -> None:
        """Verify the init config.

        Assume ghz_uids_lst, dat_uids_init_in_x, dat_uids_init_in_z, are all distinct
        (though ghz preparation might reset in X or Z, we still distinguish them).
        """
        _ghz_uids_set = set(itertools.chain(*self.ghz_uids_lst))
        assert set(_ghz_uids_set) & set(self.dat_uids_init_in_x) == set()
        assert set(_ghz_uids_set) & set(self.dat_uids_init_in_z) == set()
        assert set(_ghz_uids_set) & set(self.inj_uids) == set()
        assert set(self.dat_uids_init_in_x) & set(self.dat_uids_init_in_z) == set()

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, InitCfg)
        return (
            self.inj_lids == other.inj_lids
            and self.inj_uids == other.inj_uids
            and self.ghz_uids_lst == other.ghz_uids_lst
            and self.fixed_stab_uids == other.fixed_stab_uids
            and self.fixed_x_stab_ids == other.fixed_x_stab_ids
            and self.fixed_z_stab_ids == other.fixed_z_stab_ids
            and self.dat_uids_init_in_x == other.dat_uids_init_in_x
            and self.dat_uids_init_in_z == other.dat_uids_init_in_z
        )

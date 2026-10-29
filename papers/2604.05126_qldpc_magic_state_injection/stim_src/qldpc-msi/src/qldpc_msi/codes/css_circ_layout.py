from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base_code import CSSSpec


@dataclass(frozen=True)
class CSSCircLayout:
    Hx_row_id_to_x_check_uid: tuple[int, ...]
    Hz_row_id_to_z_check_uid: tuple[int, ...]
    col_id_to_dat_uid: tuple[int, ...]

    @classmethod
    def canonical_for(cls, code: CSSSpec) -> "CSSCircLayout":
        n = code.num_dat_qubits
        nx = code.num_x_checks
        nz = code.num_z_checks
        layout = cls(
            Hx_row_id_to_x_check_uid=tuple(range(n, n + nx)),
            Hz_row_id_to_z_check_uid=tuple(range(n + nx, n + nx + nz)),
            col_id_to_dat_uid=tuple(range(n)),
        )
        layout.validate_for(code)
        return layout

    @property
    def x_check_uids(self) -> tuple[int, ...]:
        return self.Hx_row_id_to_x_check_uid

    @property
    def z_check_uids(self) -> tuple[int, ...]:
        return self.Hz_row_id_to_z_check_uid

    @property
    def check_uids(self) -> tuple[int, ...]:
        return self.Hx_row_id_to_x_check_uid + self.Hz_row_id_to_z_check_uid

    @property
    def all_uids(self) -> tuple[int, ...]:
        return self.col_id_to_dat_uid + self.check_uids

    def validate_for(self, code: CSSSpec) -> None:
        if len(self.col_id_to_dat_uid) != code.num_dat_qubits:
            raise ValueError(f"Column-to-data UID map length mismatch: {len(self.col_id_to_dat_uid)} vs {code.num_dat_qubits}")
        if len(self.Hx_row_id_to_x_check_uid) != code.num_x_checks:
            raise ValueError(
                f"Hx-row-to-X-check UID map length mismatch: {len(self.Hx_row_id_to_x_check_uid)} vs {code.num_x_checks}"
            )
        if len(self.Hz_row_id_to_z_check_uid) != code.num_z_checks:
            raise ValueError(
                f"Hz-row-to-Z-check UID map length mismatch: {len(self.Hz_row_id_to_z_check_uid)} vs {code.num_z_checks}"
            )

        data_uid_set = set(self.col_id_to_dat_uid)
        check_uid_set = set(self.check_uids)
        if len(data_uid_set) != len(self.col_id_to_dat_uid):
            raise ValueError("Data UIDs must be unique.")
        if len(check_uid_set) != len(self.check_uids):
            raise ValueError("Check UIDs must be unique.")
        if data_uid_set & check_uid_set:
            raise ValueError("Data UIDs and check UIDs must be disjoint.")

from __future__ import annotations

import glob
import pickle
from pathlib import Path
from typing import Any, ClassVar, TypedDict, override

import numpy as np
import pandas as pd
from numpy.typing import NDArray


class BaseDataMgr:
    """
    Runtime behavior:
      - load/save/is_data_exist accept flexible *args/**kwargs (for backwards compatibility).
      - Subclasses can provide Pylance keyword completion by adding TYPE_CHECKING-only
        method redeclarations with `Unpack[TypedDict]`.

    Important typing principle:
      - Class-level configuration is stored in ClassVars (file_type, data_subdir, *_param).
      - Instance-level resolved path is stored in `self.data_dir`.
        Do NOT assign to ClassVars via `self`.
    """

    file_type: ClassVar[str] = ""
    data_subdir: ClassVar[Path] = Path("")  # relative to repo root (two levels above this file)
    load_param: ClassVar[dict[str, Any]] = {}
    save_param: ClassVar[dict[str, Any]] = {}

    def __init__(self) -> None:
        cur_file_dir = Path(__file__).parent
        path_to_repo_root = cur_file_dir.parent.parent
        self.data_dir: Path = path_to_repo_root / self.data_subdir

    def load(self, *args: Any, **kwargs: Any) -> Any:
        filepath = self.get_filepath(*args, **kwargs)

        if self.file_type == "pkl":
            with open(filepath, "rb") as f:
                return pickle.load(f, **self.load_param)

        if self.file_type == "csv":
            return pd.read_csv(filepath, **self.load_param)

        raise ValueError(f"Unknown file type {self.file_type}")

    def save(self, data: Any, *args: Any, **kwargs: Any) -> None:
        filepath = self.get_filepath(*args, **kwargs)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if self.file_type == "pkl":
            with open(filepath, "wb") as f:
                pickle.dump(data, f, **self.save_param)
            return

        if self.file_type == "csv":
            if not hasattr(data, "to_csv"):
                raise TypeError("CSV save expects a pandas.DataFrame (or similar with .to_csv).")
            data.to_csv(filepath, index=False, **self.save_param)
            return

        if self.file_type == "txt":
            with open(filepath, "w") as f:
                for item in data:
                    f.write(str(item) + "\n")
            return

        raise ValueError(f"Unknown file type {self.file_type}")

    def is_data_exist(self, *args: Any, **kwargs: Any) -> bool:
        return self.get_filepath(*args, **kwargs).exists()

    def get_signature(self, *args: Any, **kwargs: Any) -> str:
        """
        Default signature builder.

        Note: This preserves the caller's keyword ordering (dict insertion order),
        matching your original behavior to avoid breaking existing filenames.
        """
        sign = ""
        for k, v in kwargs.items():
            if isinstance(v, list):
                v = ",".join(map(str, v))
            sign += f"{k}={v}-"
        return sign[:-1] if sign else sign

    def get_filepath(self, *args: Any, **kwargs: Any) -> Path:
        sign = self.get_signature(*args, **kwargs)
        return self.data_dir / f"{sign}.{self.file_type}"


class MsiDataKwargs(TypedDict):
    code_id: str
    ps: list[float]
    inj_method: str
    noise_model: str
    cfg_id: int
    n_psel_cycles: int
    n_se_cycles: int
    n_shots: int
    idm: bool
    nodet: bool


class MsiDataMgr(BaseDataMgr):
    data_subdir: ClassVar[Path] = Path("data/msi")
    file_type: ClassVar[str] = "pkl"

    @override
    def get_signature(
        self,
        code_id: str,
        ps: list[float],
        inj_method: str,
        noise_model: str,
        cfg_id: int,
        n_psel_cycles: int,
        n_se_cycles: int,
        n_shots: int,
        idm: bool,
        nodet: bool,
    ) -> str:
        ps_str = ",".join(map(str, ps))
        return (
            f"{code_id}/"
            f"{inj_method}-{noise_model}/"
            f"{ps_str}/"
            f"{cfg_id}-pc={n_psel_cycles}-sc={n_se_cycles}-s={n_shots}-idm={idm}-nodet={nodet}"
        )


class InitCfgV2Kwargs(TypedDict):
    code_id: str
    noise_model: str
    init_method: str
    _id: int


class InitCfgMgrV2(BaseDataMgr):
    data_subdir: ClassVar[Path] = Path("data/init_cfgs_v2")
    file_type: ClassVar[str] = "pkl"

    @override
    def get_signature(
        self, code_id: str, noise_model: str, init_method: str, remove_dummy_cnots: bool, _id: int
    ) -> str:
        if remove_dummy_cnots:
            return f"{code_id}/{noise_model}-{init_method}-remove_dummy_cnots/{_id}"
        else:
            return f"{code_id}/{noise_model}-{init_method}/{_id}"

    def count(self, code_id: str, noise_model: str, init_method: str, remove_dummy_cnots: bool) -> int:
        if remove_dummy_cnots:
            dir_part = self.data_dir / f"{code_id}/{noise_model}-{init_method}-remove_dummy_cnots"
        else:
            dir_part = self.data_dir / f"{code_id}/{noise_model}-{init_method}"
        # Escape path so literal brackets in code_id (e.g. [[144,12,12]]) are not treated as glob character class
        pattern = glob.escape(str(dir_part)) + "/*.pkl"

        matching_files = glob.glob(pattern)
        return len(matching_files)


class HGPCodeDataMgr(BaseDataMgr):
    data_subdir = Path("data/codes/hgp")
    file_type = "pkl"

    @override
    def load(self, n: int) -> NDArray[np.int_]:
        text_file_pattern = self.data_dir / f"hgp_34_n{n}_d*_h.txt"
        matching_files = glob.glob(str(text_file_pattern))
        if not matching_files:
            raise FileNotFoundError(f"No files found matching pattern: {text_file_pattern}")
        if len(matching_files) > 1:
            raise ValueError(f"Multiple files found matching pattern: {text_file_pattern}")

        text_file = matching_files[0]
        with open(text_file, "r") as f:
            lines = f.readlines()
        H = []
        for line in lines:
            H.append(list(map(float, line.split())))
        return np.array(H, dtype=np.int_)

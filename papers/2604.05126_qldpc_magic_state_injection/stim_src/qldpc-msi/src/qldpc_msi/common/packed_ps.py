import numpy as np
import stim


class PackedPS:
    def __init__(self, xs: int, zs: int):
        self.xs = xs
        self.zs = zs

    def commutes(self, other: "PackedPS") -> bool:
        return (bin(self.xs & other.zs).count("1") + bin(self.zs & other.xs).count("1")) % 2 == 0

    def to_tuple(self) -> tuple[int, int]:
        return self.xs, self.zs

    @staticmethod
    def from_tuple(xs: int, zs: int) -> "PackedPS":
        return PackedPS(xs, zs)

    @staticmethod
    def from_numpy(xs: np.ndarray, zs: np.ndarray) -> "PackedPS":
        return PackedPS(int("".join(str(int(x)) for x in xs), 2), int("".join(str(int(z)) for z in zs), 2))

    def __mul__(self, other: "PackedPS") -> "PackedPS":
        return PackedPS(self.xs ^ other.xs, self.zs ^ other.zs)

    @staticmethod
    def from_pauli_string(ps: stim.PauliString) -> "PackedPS":
        xs, zs = ps.to_numpy()
        xs_str = "".join(str(int(x)) for x in xs)
        zs_str = "".join(str(int(z)) for z in zs)
        return PackedPS(int(xs_str, 2), int(zs_str, 2))

    def to_pauli_string(self, n_qubits: int) -> stim.PauliString:
        xs = np.array([int(x) for x in bin(self.xs)[2:].zfill(n_qubits)], dtype=np.bool_)
        zs = np.array([int(z) for z in bin(self.zs)[2:].zfill(n_qubits)], dtype=np.bool_)
        return stim.PauliString.from_numpy(xs=xs, zs=zs)

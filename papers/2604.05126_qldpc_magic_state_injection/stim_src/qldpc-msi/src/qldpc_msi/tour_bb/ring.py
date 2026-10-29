from __future__ import annotations

import galois


class GF2CyclicPolyRing2D:
    """F_2[x,y] / (x^l - 1, y^m - 1)"""

    __slots__ = ("l", "m", "_all_monomials")

    def __init__(self, l: int, m: int) -> None:
        if l < 1 or m < 1:
            raise ValueError("Moduli must be positive integers")
        self.l = l
        self.m = m
        self._all_monomials = [self.monomial(xexp, yexp) for xexp in range(self.l) for yexp in range(self.m)]

    def __repr__(self) -> str:
        return f"<FM2 mod({self.l},{self.m})>"

    def monomial(self, xexp: int = 0, yexp: int = 0) -> Monomial:
        """
        Create a new Monomial x^xexp y^yexp in this field (automatically reduced).
        """
        return Monomial(xexp % self.l, yexp % self.m, self)

    def get_all_monomials(self) -> list[Monomial]:
        """
        Get all monomials in this ring.
        """
        return self._all_monomials

    def get_monomials_from_vec(self, vec: galois.GF2) -> list[Monomial]:
        return [self._all_monomials[i] for i in vec.nonzero()[0]]


class Monomial:
    __slots__ = ("xexp", "yexp", "ring")

    def __init__(self, xexp: int, yexp: int, ring: GF2CyclicPolyRing2D) -> None:
        self.xexp = xexp % ring.l
        self.yexp = yexp % ring.m
        self.ring = ring

    def __hash__(self) -> int:
        return int(self.xexp * self.ring.m + self.yexp)

    def __pow__(self, power: int) -> Monomial:
        return Monomial(self.xexp * power, self.yexp * power, self.ring)

    def __mul__(self, other: Monomial) -> Monomial:
        if self.ring is not other.ring:
            raise ValueError(f"Cannot multiply monomials from different rings, {self.ring} and {other.ring}")
        return Monomial(self.xexp + other.xexp, self.yexp + other.yexp, self.ring)

    def __truediv__(self, other: Monomial) -> Monomial:
        if self.ring is not other.ring:
            raise ValueError("Cannot divide monomials from different rings")
        return Monomial(self.xexp - other.xexp, self.yexp - other.yexp, self.ring)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Monomial)
            and self.ring is other.ring
            and self.xexp == other.xexp
            and self.yexp == other.yexp
        )

    def __str__(self) -> str:
        return f"exp=({self.xexp},{self.yexp})"

    def __repr__(self) -> str:
        return f"Mono({self.xexp}, {self.yexp})"

    def T(self) -> Monomial:
        # "Twist" map: (l - x, m - y) mod (l, m)
        return Monomial(self.ring.l - self.xexp, self.ring.m - self.yexp, self.ring)

    def as_tuple(self) -> tuple[int, int]:
        return (self.xexp, self.yexp)


class Polynomial:
    __slots__ = ("monomials",)

    def __init__(self, monomials: list[Monomial]) -> None:
        self.monomials = list(monomials)

    def __str__(self) -> str:
        return f"Polynomial({self.monomials})"

    def __mul__(self, other: Polynomial) -> Polynomial:
        rst: list[Monomial] = []
        for mono in self.monomials:
            for o in other.monomials:
                rst.append(mono * o)
        return Polynomial(rst)

    def T(self) -> Polynomial:
        rst = [mono.T() for mono in self.monomials]
        return Polynomial(rst)

    def as_tuples(self) -> list[tuple[int, int]]:
        return [mono.as_tuple() for mono in self.monomials]

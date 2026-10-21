"""Szenario: eine n x n-Kostenmatrix für beide Fragen (Zuordnung und Rundreise).

Die Diagonale trägt FORBIDDEN: kein Fahrzeug fährt zu sich selbst, keine Rundreise bleibt am Ort. Die Kartenvariante ist symmetrisch (Entfernungen,
auf ganze Zahlen gerundet), die Zufallsmatrix nicht."""

import math
from dataclasses import dataclass

import numpy as np

import zrt_constants as C


@dataclass(frozen=True)
class Instance:
    kind: str                                              # "euclid" oder "random"
    matrix: tuple[tuple[int, ...], ...]                    # matrix[i][j]: Kosten von i nach j, Diagonale = FORBIDDEN
    points: tuple[tuple[float, float], ...] | None = None  # Orte der Karte (nur "euclid")

    @property
    def n(self) -> int:
        return len(self.matrix)


def label(i: int) -> str:
    """Anzeigename von Ort i (0-basiert im Kern, 1-basiert für Leserinnen und Leser)."""
    return f"O{i + 1}"


def from_matrix(rows, kind: str = "random") -> Instance:
    """Instanz aus einer Liste von Zeilen (Diagonale wird auf FORBIDDEN gesetzt); für Handrechnungen und Tests."""
    n = len(rows)
    matrix = tuple(tuple(C.FORBIDDEN if i == j else int(rows[i][j]) for j in range(n)) for i in range(n))
    return Instance(kind, matrix)


def make_instance(n: int, kind: str, seed: int) -> Instance:
    """Deterministisch aus (n, kind, seed): gleiche Eingabe, gleiche Instanz."""
    rng = np.random.default_rng(seed)
    if kind == "euclid":
        pts = [(float(x), float(y)) for x, y in rng.uniform(0, C.COORD_MAX, size=(n, 2))]
        matrix = tuple(
            tuple(C.FORBIDDEN if i == j else int(round(math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]))) for j in range(n)) for i in range(n)
        )
        return Instance(kind, matrix, tuple(pts))
    if kind == "random":
        raw = rng.integers(C.COST_LOW, C.COST_HIGH + 1, size=(n, n))
        matrix = tuple(tuple(C.FORBIDDEN if i == j else int(raw[i][j]) for j in range(n)) for i in range(n))
        return Instance(kind, matrix)
    raise ValueError(f"unbekannte Matrixart: {kind}")

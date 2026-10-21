"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zrt_scenario import Instance, from_matrix  # noqa: E402


@pytest.fixture
def mini() -> Instance:
    """4 Orte. Kosten 1 zwischen 0 und 1 sowie zwischen 2 und 3 (beide Richtungen), alle anderen Wege 10, Diagonale gesperrt.

    Handrechnung: die billigste Zuordnung ist 0->1, 1->0, 2->3, 3->2 mit 1+1+1+1 = 4 und zerfällt in die zwei Teilkreise (0 1) und (2 3).
    Jede Rundreise nutzt höchstens zwei der Kosten-1-Wege und zwei Wege zu 10: die beste kostet 1+10+1+10 = 22 (z. B. 0-1-2-3-0). Lücke (22-4)/22 = 81,8 %."""
    return from_matrix([[0, 1, 10, 10], [1, 0, 10, 10], [10, 10, 0, 1], [10, 10, 1, 0]])

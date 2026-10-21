"""Orakel-Test: Zuordnung und Rundreise gegen unabhängige Rechenwege (DEMO-PLAYBOOK §12, ORACLE-PLAYBOOK).

- Zuordnung: Ungarische Methode == Aufzählen == `scipy.optimize.linear_sum_assignment` (Bibliothek, anderer Algorithmus).
- Rundreise: Held–Karp == Aufzählen == CP-SAT mit `AddCircuit` (Solver-Modell, anderer Rechenweg).
- Relaxation: billigste Zuordnung <= billigste Rundreise, Gleichheit bei einem einzigen Kreis.
Im Repo laufen kleine, schnelle Fassungen (unter 10 s); der große Lauf mit mehr als 300 Instanzen lief im Scratch-Ordner (siehe README, „Tests“).
Das Orakel selbst ist an der Mini-Instanz von Hand geprüft (conftest: 4 und 22)."""

import numpy as np
import pytest

import zrt_algorithm as A
import zrt_constants as C
from zrt_scenario import from_matrix, make_instance


def _scipy_assignment_cost(inst):
    linear_sum_assignment = pytest.importorskip("scipy.optimize").linear_sum_assignment
    cost = np.array(inst.matrix, dtype=float)
    rows, cols = linear_sum_assignment(cost)
    return int(round(cost[rows, cols].sum()))


def _cpsat_tour_cost(inst):
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")
    n = inst.n
    model = cp_model.CpModel()
    literals, arcs = {}, []
    for i in range(n):
        for j in range(n):
            if i != j:
                literals[i, j] = model.NewBoolVar(f"a{i}_{j}")
                arcs.append((i, j, literals[i, j]))
    model.AddCircuit(arcs)
    model.Minimize(sum(inst.matrix[i][j] * lit for (i, j), lit in literals.items()))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 20
    status = solver.Solve(model)
    assert status == cp_model.OPTIMAL
    return int(round(solver.ObjectiveValue()))


def test_oracle_on_the_mini_instance_by_hand(mini):
    assert _scipy_assignment_cost(mini) == 4
    assert _cpsat_tour_cost(mini) == 22


def test_hungarian_matches_scipy_and_enumeration():
    for seed in range(120):
        for kind in ("euclid", "random"):
            n = 2 + seed % 7                                            # 2 bis 8
            inst = make_instance(n, kind, seed)
            h = A.hungarian(inst)
            assert A.check_feasible_assignment(inst, h.plan), (kind, seed)
            assert A.assignment_cost(inst, h.plan) == h.cost, (kind, seed)
            assert h.cost == _scipy_assignment_cost(inst), (kind, seed)
            if n <= 7:
                assert h.cost == A.enumerate_assignments(inst).cost, (kind, seed)


def test_hungarian_matches_scipy_on_larger_sizes():
    for seed in range(15):
        for n in (20, 50):
            inst = make_instance(n, "random" if seed % 2 else "euclid", seed)
            assert A.hungarian(inst).cost == _scipy_assignment_cost(inst), (n, seed)


def test_held_karp_matches_enumeration():
    for seed in range(80):
        n = 2 + seed % 7                                                # 2 bis 8
        for kind in ("euclid", "random"):
            inst = make_instance(n, kind, seed)
            k = A.held_karp(inst)
            assert A.check_feasible_tour(inst, k.plan), (kind, seed)
            assert A.tour_cost(inst, k.plan) == k.cost, (kind, seed)
            assert k.cost == A.enumerate_tours(inst).cost, (kind, seed)


def test_held_karp_matches_cp_sat():
    for seed in range(12):
        n = 6 + seed % 5                                                # 6 bis 10
        inst = make_instance(n, "random" if seed % 2 else "euclid", seed)
        assert A.held_karp(inst).cost == _cpsat_tour_cost(inst), (n, seed)


def test_ties_do_not_change_the_cost():
    """Alle Einträge gleich: jede Lösung kostet n mal den Wert; das Orakel und die Verfahren stimmen in den Kosten überein."""
    for n in (3, 4, 6):
        inst = from_matrix([[7] * n for _ in range(n)])
        assert A.hungarian(inst).cost == A.enumerate_assignments(inst).cost == _scipy_assignment_cost(inst) == 7 * n
        assert A.held_karp(inst).cost == A.enumerate_tours(inst).cost == 7 * n


def test_assignment_is_a_lower_bound_of_the_tour():
    for seed in range(60):
        n = 3 + seed % 6
        for kind in ("euclid", "random"):
            inst = make_instance(n, kind, seed)
            assert _scipy_assignment_cost(inst) <= A.held_karp(inst).cost, (kind, seed)
    assert C.FORBIDDEN > 100 * 16 * 2        # die Diagonalsperre ist teurer als jede erlaubte Lösung

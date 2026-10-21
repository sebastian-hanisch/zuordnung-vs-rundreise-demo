"""Kern gegen Handrechnung an der Mini-Instanz (conftest) und gegen Aufzählen: jede Einheit einzeln (DEMO-PLAYBOOK §1b)."""

import math

import pytest

import zrt_algorithm as A
import zrt_constants as C
from zrt_scenario import from_matrix, make_instance

# --- Kosten, Prüfer, Teilkreise ------------------------------------------------------------------------------------------------------------------


def test_assignment_cost_by_hand(mini):
    assert A.assignment_cost(mini, (1, 0, 3, 2)) == 4      # 1 + 1 + 1 + 1
    assert A.assignment_cost(mini, (2, 3, 1, 0)) == 40     # 10 + 10 + 10 + 10


def test_tour_cost_by_hand(mini):
    assert A.tour_cost(mini, (0, 1, 2, 3)) == 22           # 0-1 (1) + 1-2 (10) + 2-3 (1) + 3-0 (10)
    assert A.tour_cost(mini, (0, 2, 1, 3)) == 40           # 10 + 10 + 10 + 10


def test_cycles_of_assignment_by_hand():
    assert A.cycles_of_assignment((1, 0, 3, 2)) == [(0, 1), (2, 3)]
    assert A.cycles_of_assignment((1, 2, 3, 0)) == [(0, 1, 2, 3)]
    assert A.cycles_of_assignment((1, 2, 0, 4, 3)) == [(0, 1, 2), (3, 4)]


def test_checkers_accept_valid_and_reject_broken(mini):
    assert A.check_feasible_assignment(mini, (1, 0, 3, 2))
    assert not A.check_feasible_assignment(mini, (0, 1, 2, 3))        # Fixpunkte
    assert not A.check_feasible_assignment(mini, (1, 1, 3, 2))        # kein Permutation
    assert not A.check_feasible_assignment(mini, (1, 0, 3))           # zu kurz
    assert A.check_feasible_tour(mini, (0, 2, 1, 3))
    assert not A.check_feasible_tour(mini, (1, 0, 2, 3))              # Start nicht bei Ort 0
    assert not A.check_feasible_tour(mini, (0, 1, 1, 3))              # Ort doppelt


# --- Zuordnung -----------------------------------------------------------------------------------------------------------------------------------


def test_hungarian_on_the_mini_instance(mini):
    r = A.hungarian(mini)
    assert r.cost == 4 and r.exact and A.check_feasible_assignment(mini, r.plan)
    assert A.cycles_of_assignment(r.plan) == [(0, 1), (2, 3)]
    assert A.assignment_cost(mini, r.plan) == r.cost


def test_enumerate_assignments_on_the_mini_instance(mini):
    r = A.enumerate_assignments(mini)
    assert r.cost == 4 and r.finished and r.accesses == 4 * math.factorial(4)      # 96
    assert A.check_feasible_assignment(mini, r.plan)


def test_hungarian_counts_accesses_below_the_bound(mini):
    assert 0 < A.hungarian(mini).accesses <= A.accesses_hungarian_bound(4)


# --- Rundreise -----------------------------------------------------------------------------------------------------------------------------------


def test_held_karp_on_the_mini_instance(mini):
    r = A.held_karp(mini)
    assert r.cost == 22 and r.exact and A.check_feasible_tour(mini, r.plan)
    assert A.tour_cost(mini, r.plan) == 22
    assert r.accesses == 18                                 # 3 * 2 * 2 Übergänge + 3 Start- + 3 Rückkanten


def test_enumerate_tours_on_the_mini_instance(mini):
    r = A.enumerate_tours(mini)
    assert r.cost == 22 and r.finished and r.accesses == 24      # 3! Reihenfolgen, je 4 Zugriffe
    assert A.check_feasible_tour(mini, r.plan) and A.tour_cost(mini, r.plan) == 22


# --- Beziehung der beiden Fragen -----------------------------------------------------------------------------------------------------------------


def test_assignment_never_costs_more_than_the_tour(mini):
    assert A.hungarian(mini).cost <= A.held_karp(mini).cost
    for seed in range(40):
        for kind in ("euclid", "random"):
            inst = make_instance(7, kind, seed)
            assert A.hungarian(inst).cost <= A.held_karp(inst).cost, (kind, seed)


def test_equality_holds_when_the_cheapest_assignment_is_one_cycle():
    """Ist die billigste Zuordnung ein einziger Kreis, ist sie selbst eine Rundreise: dann sind beide Kosten gleich."""
    hits = 0
    for seed in range(60):
        inst = make_instance(6, "random", seed)
        r = A.hungarian(inst)
        if len(A.cycles_of_assignment(r.plan)) == 1:
            hits += 1
            assert A.held_karp(inst).cost == r.cost, seed
    assert hits > 0, "kein Fall mit einem einzigen Kreis: der Test prüft nichts"


# --- Budget --------------------------------------------------------------------------------------------------------------------------------------


def test_enumeration_stops_at_the_budget_and_never_exceeds_it():
    inst = make_instance(8, "euclid", 1)
    r = A.enumerate_assignments(inst, 1000)
    assert not r.finished and r.accesses <= 1000 and r.accesses > 1000 - inst.n
    t = A.enumerate_tours(inst, 1000)
    assert not t.finished and t.accesses <= 1000 and t.accesses > 1000 - inst.n


def test_held_karp_stops_at_the_budget_and_never_exceeds_it():
    inst = make_instance(10, "random", 2)
    for budget in (0, 5, 100, 3000, 9000):
        r = A.held_karp(inst, budget)
        assert r.accesses <= budget
        assert not r.finished and r.cost is None and r.plan is None


def test_budget_equal_to_the_formula_is_enough():
    inst = make_instance(7, "euclid", 3)
    assert A.held_karp(inst, A.accesses_held_karp(7)).finished
    assert not A.held_karp(inst, A.accesses_held_karp(7) - 1).finished
    assert A.enumerate_tours(inst, A.accesses_enumerate_tour(7)).finished
    assert not A.enumerate_tours(inst, A.accesses_enumerate_tour(7) - 1).finished
    assert A.enumerate_assignments(inst, A.accesses_enumerate_assignment(7)).finished
    assert not A.enumerate_assignments(inst, A.accesses_enumerate_assignment(7) - 1).finished


def test_aborted_enumeration_keeps_only_feasible_best_so_far():
    inst = make_instance(8, "euclid", 4)
    r = A.enumerate_assignments(inst, 20000)
    if r.cost is not None:
        assert r.cost < C.FORBIDDEN and A.check_feasible_assignment(inst, r.plan)
    t = A.enumerate_tours(inst, 20000)
    assert t.cost is not None and A.check_feasible_tour(inst, t.plan) and A.tour_cost(inst, t.plan) == t.cost


# --- Komposition ---------------------------------------------------------------------------------------------------------------------------------


def test_solve_dispatches_by_method(mini):
    assert A.solve_assignment(mini, "hungarian").method == "hungarian"
    assert A.solve_assignment(mini, "enumerate").method == "enumerate"
    assert A.solve_tour(mini, "held_karp").method == "held_karp"
    assert A.solve_tour(mini, "enumerate").method == "enumerate"
    with pytest.raises(ValueError):
        A.solve_assignment(mini, "held_karp")
    with pytest.raises(ValueError):
        A.solve_tour(mini, "hungarian")


def test_worst_case_at_the_slider_maximum_finishes():
    """Kein Zeittest (DEMO-PLAYBOOK §1c): fängt nur Hänger und Aufblähen am Regler-Maximum (n = 16)."""
    inst = make_instance(C.N_MAX, "random", 5)
    h = A.hungarian(inst)
    assert h.exact and h.accesses <= A.accesses_hungarian_bound(C.N_MAX)
    k = A.held_karp(inst, C.BUDGETS[-1])
    assert k.exact and k.accesses == A.accesses_held_karp(C.N_MAX)
    assert h.cost <= k.cost


def test_from_matrix_sets_the_diagonal():
    inst = from_matrix([[5, 2], [3, 7]])
    assert inst.matrix[0][0] == inst.matrix[1][1] == C.FORBIDDEN and inst.matrix[0][1] == 2 and inst.matrix[1][0] == 3

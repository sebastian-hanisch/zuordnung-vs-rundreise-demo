"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1, 2, 3, Gleichstände, Budgetgrenzen inklusive."""

import pytest

import zrt_algorithm as A
from zrt_scenario import from_matrix


def test_exactly_two_places():
    """n = 2: die einzige Zuordnung ist der Tausch, die einzige Rundreise hin und zurück."""
    inst = from_matrix([[0, 3], [5, 0]])
    h = A.hungarian(inst)
    assert h.cost == 8 and h.plan == (1, 0) and A.cycles_of_assignment(h.plan) == [(0, 1)]
    assert A.enumerate_assignments(inst).cost == 8
    k = A.held_karp(inst)
    assert k.cost == 8 and k.plan == (0, 1) and k.accesses == 2
    assert A.enumerate_tours(inst).cost == 8 and A.enumerate_tours(inst).accesses == 2


def test_single_place():
    """n = 1: keine Zuordnung ohne Fixpunkt, die Rundreise ist leer (Kosten 0, kein Zugriff)."""
    inst = from_matrix([[0]])
    h = A.hungarian(inst)
    assert h.cost is None and h.plan is None and not h.exact
    e = A.enumerate_assignments(inst)
    assert e.cost is None and e.plan is None and e.finished
    for r in (A.held_karp(inst), A.enumerate_tours(inst)):
        assert r.cost == 0 and r.plan == (0,) and r.accesses == 0 and r.exact


def test_three_places_two_directions_differ():
    """n = 3: zwei Rundreisen (0-1-2 und 0-2-1) mit verschiedenen Kosten; die Zuordnung ist ein Dreikreis oder eine Zerlegung ohne Fixpunkt (nur Dreikreise)."""
    inst = from_matrix([[0, 1, 9], [9, 0, 1], [1, 9, 0]])
    assert A.held_karp(inst).cost == 3 and A.held_karp(inst).plan == (0, 1, 2)
    assert A.enumerate_tours(inst).cost == 3
    assert A.hungarian(inst).cost == 3 and A.enumerate_assignments(inst).cost == 3


def test_empty_instance_is_defined():
    inst = from_matrix([])
    assert inst.n == 0
    assert A.tour_cost(inst, ()) == 0 and A.cycles_of_assignment(()) == []
    assert A.enumerate_tours(inst).cost == 0 and A.held_karp(inst).cost == 0


def test_zero_costs():
    inst = from_matrix([[0] * 5 for _ in range(5)])
    assert A.hungarian(inst).cost == 0 and A.held_karp(inst).cost == 0
    assert A.enumerate_assignments(inst).cost == 0 and A.enumerate_tours(inst).cost == 0


def test_budget_zero_and_budget_exactly_one_item():
    inst = from_matrix([[0, 1, 2], [3, 0, 4], [5, 6, 0]])
    r = A.enumerate_assignments(inst, 0)
    assert not r.finished and r.accesses == 0 and r.cost is None
    r = A.enumerate_tours(inst, 3)                       # genau eine Reihenfolge (n = 3 Zugriffe) passt
    assert not r.finished and r.accesses == 3 and r.cost is not None
    r = A.enumerate_tours(inst, 6)                       # beide Reihenfolgen passen genau
    assert r.finished and r.accesses == 6


@pytest.mark.parametrize("method", ["enumerate", "held_karp"])
def test_tour_methods_agree_on_symmetric_instance_with_ties(method):
    inst = from_matrix([[0, 2, 2, 2], [2, 0, 2, 2], [2, 2, 0, 2], [2, 2, 2, 0]])
    assert A.solve_tour(inst, method).cost == 8


# --- Lücken aus der Mutationsprüfung ----------------------------------------------------------------------------------------------------------------


def test_feasibility_checker_looks_at_the_last_position_too():
    """Ein Fixpunkt nur am letzten Ort muss auffallen (Mutation: Schleife bis n - 1)."""
    inst = from_matrix([[0, 1, 2], [3, 0, 4], [5, 6, 0]])
    assert not A.check_feasible_assignment(inst, (1, 0, 2))
    assert A.check_feasible_assignment(inst, (1, 2, 0))


def test_tour_checker_on_empty_and_single_instance():
    """n = 0 und n = 1: der Prüfer darf nicht auf order[0] zugreifen, wo es nichts gibt (Mutation der Konstante im Nullwächter)."""
    assert A.check_feasible_tour(from_matrix([]), ())
    assert A.check_feasible_tour(from_matrix([[0]]), (0,))
    assert not A.check_feasible_tour(from_matrix([[0]]), ())


def test_cycles_include_a_fixed_point_at_the_last_position():
    """Ein einzelner Ort am Ende ist ein Kreis der Länge 1 (Mutation: Schleife bis n - 1)."""
    assert A.cycles_of_assignment((1, 0, 2)) == [(0, 1), (2,)]
    assert A.cycles_of_assignment((0,)) == [(0,)]


def test_tie_rule_is_the_first_in_lexicographic_order():
    """Bei gleichen Kosten bleibt die zuerst gesehene Lösung (Mutation: `<` gegen `<=`): erste zulässige Permutation (1, 0, 3, 2), erste Reihenfolge (0, 1, 2, 3)."""
    inst = from_matrix([[5] * 4 for _ in range(4)])
    assert A.enumerate_assignments(inst).plan == (1, 0, 3, 2)
    assert A.enumerate_tours(inst).plan == (0, 1, 2, 3)


def test_formulas_at_the_smallest_sizes():
    """n = 1: eine Rundreise ohne Kante braucht keinen Zugriff (Mutation der Grenze n >= 2); n = 0 ebenso."""
    assert A.accesses_enumerate_tour(1) == 0 and A.accesses_enumerate_tour(0) == 0
    assert A.accesses_enumerate_assignment(1) == 1


def test_held_karp_stops_exactly_at_the_budget_boundary(mini):
    """Der Lauf gibt höchstens das Budget aus und hört genau dort auf, wo der nächste Schritt es überschritte (Mutationen `>` gegen `>=` und die Zahl der Übergänge je Menge).
    Mini-Instanz: 3 Startkanten, dann drei Mengen mit je 2 Übergängen (Stand 9), eine Menge mit 6 Übergängen (Stand 15), 3 Rückkanten (Stand 18)."""
    expected = {3: 3, 4: 3, 5: 5, 8: 7, 9: 9, 10: 9, 14: 9, 15: 15, 17: 15, 18: 18}
    for budget, accesses in expected.items():
        r = A.held_karp(mini, budget)
        assert r.accesses == accesses, budget
        assert r.finished == (budget >= 18), budget


def test_held_karp_with_budget_equal_to_the_start_edges():
    """Budget genau n - 1: die Startkanten sind bezahlt, mehr nicht (Mutation `k > budget` gegen `k >= budget`)."""
    inst = from_matrix([[0, 1, 2, 3, 4], [1, 0, 5, 6, 7], [2, 5, 0, 8, 9], [3, 6, 8, 0, 1], [4, 7, 9, 1, 0]])
    r = A.held_karp(inst, 4)
    assert r.accesses == 4 and not r.finished and r.cost is None
    assert A.held_karp(inst, 3).accesses == 0


def test_held_karp_tie_rule_prefers_the_smaller_index():
    """Bei gleichen Kosten gewinnt der kleinere Vorgänger und der kleinere letzte Ort; die Reihenfolge wird rückwärts gebaut (Mutationen `<` gegen `<=`)."""
    assert A.held_karp(from_matrix([[5] * 4 for _ in range(4)])).plan == (0, 3, 2, 1)
    assert A.held_karp(from_matrix([[5] * 5 for _ in range(5)])).plan == (0, 4, 3, 2, 1)

"""Zweig-Tests (Nullspalten-Lehre, DEMO-PLAYBOOK §0): jedes Verfahren weicht auf mindestens einer Instanz vom Nachbarverfahren ab, und jeder Fall wird ausgeführt."""

import zrt_algorithm as A
from zrt_scenario import make_instance


def test_methods_differ_in_accesses_but_not_in_cost():
    inst = make_instance(7, "euclid", 11)
    h, e = A.hungarian(inst), A.enumerate_assignments(inst)
    assert h.cost == e.cost and h.accesses != e.accesses and h.accesses < e.accesses
    k, t = A.held_karp(inst), A.enumerate_tours(inst)
    assert k.cost == t.cost and k.accesses != t.accesses and k.accesses < t.accesses


def test_some_instance_has_a_multi_cycle_assignment_and_a_strictly_dearer_tour():
    """Der Teilkreis-Fall wird tatsächlich ausgeführt (sonst wäre die Lücke eine tote Spalte)."""
    multi, strict = 0, 0
    for seed in range(40):
        for kind in ("euclid", "random"):
            inst = make_instance(8, kind, seed)
            h, k = A.hungarian(inst), A.held_karp(inst)
            if len(A.cycles_of_assignment(h.plan)) >= 2:
                multi += 1
            if k.cost > h.cost:
                strict += 1
    assert multi > 0 and strict > 0


def test_some_instance_has_a_single_cycle_assignment():
    assert any(len(A.cycles_of_assignment(A.hungarian(make_instance(6, "random", s)).plan)) == 1 for s in range(60))


def test_budget_branch_both_outcomes_occur():
    inst = make_instance(9, "euclid", 5)
    assert A.enumerate_tours(inst, 10 ** 7).finished
    assert not A.enumerate_tours(inst, 1000).finished
    assert A.held_karp(inst, 10 ** 7).finished
    assert not A.held_karp(inst, 1000).finished


def test_euclid_is_symmetric_and_random_is_not():
    e = make_instance(8, "euclid", 3)
    assert all(e.matrix[i][j] == e.matrix[j][i] for i in range(8) for j in range(8))
    r = make_instance(8, "random", 3)
    assert any(r.matrix[i][j] != r.matrix[j][i] for i in range(8) for j in range(8))

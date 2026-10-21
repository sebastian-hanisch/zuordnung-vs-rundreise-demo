"""Die geschlossenen Zählformeln gegen gezählte Läufe, und das größte n im Budget gegen Handrechnung."""

import math

import pytest

import zrt_algorithm as A
from zrt_scenario import make_instance


@pytest.mark.parametrize("n", range(1, 9))
def test_enumerate_assignment_formula_matches_the_count(n):
    if n == 1:
        assert A.enumerate_assignments(make_instance(1, "random", 1)).accesses == 1 == A.accesses_enumerate_assignment(1)
        return
    inst = make_instance(n, "random", n)
    assert A.enumerate_assignments(inst).accesses == A.accesses_enumerate_assignment(n) == n * math.factorial(n)


@pytest.mark.parametrize("n", range(2, 9))
def test_enumerate_tour_formula_matches_the_count(n):
    inst = make_instance(n, "euclid", n)
    assert A.enumerate_tours(inst).accesses == A.accesses_enumerate_tour(n) == n * math.factorial(n - 1)


@pytest.mark.parametrize("n", range(2, 13))
def test_held_karp_formula_matches_the_count(n):
    inst = make_instance(n, "euclid", n)
    assert A.held_karp(inst).accesses == A.accesses_held_karp(n)


def test_held_karp_formula_by_hand():
    """Von Hand: n = 4 hat 3 * 2 * 2 = 12 Übergänge, dazu 3 Start- und 3 Rückkanten."""
    assert A.accesses_held_karp(4) == 18
    assert A.accesses_held_karp(3) == 6 and A.accesses_held_karp(2) == 2 and A.accesses_held_karp(1) == 0
    assert A.accesses_held_karp(12) == 11 * 10 * 512 + 22      # 56 342


def test_hungarian_stays_below_the_bound_on_many_instances():
    for seed in range(50):
        for n in (2, 3, 5, 9, 14):
            for kind in ("euclid", "random"):
                inst = make_instance(n, kind, seed)
                assert A.hungarian(inst).accesses <= A.accesses_hungarian_bound(n), (n, kind, seed)


def test_budget_frontier_by_hand():
    # n * n! <= 10^6: 8 * 8! = 322 560 passt, 9 * 9! = 3 265 920 nicht
    assert A.budget_frontier(A.accesses_enumerate_assignment, 10 ** 6) == 8
    # n * (n-1)! <= 10^6: 9 * 8! = 362 880 passt, 10 * 9! = 3 628 800 nicht
    assert A.budget_frontier(A.accesses_enumerate_tour, 10 ** 6) == 9
    # Held–Karp: n = 15 braucht 14 * 13 * 4096 + 28 = 745 500, n = 16 braucht 15 * 14 * 8192 + 30 = 1 720 350
    assert A.accesses_held_karp(15) == 745500 and A.accesses_held_karp(16) == 1720350
    assert A.budget_frontier(A.accesses_held_karp, 10 ** 6) == 15
    assert A.budget_frontier(A.accesses_hungarian_bound, 10 ** 6) == 100
    assert A.budget_frontier(A.accesses_hungarian_bound, 10 ** 9) == 1000


def test_budget_frontier_with_thousand_times_the_budget():
    assert A.budget_frontier(A.accesses_enumerate_assignment, 10 ** 9) == 11      # 11 * 11! = 439 084 800
    assert A.budget_frontier(A.accesses_enumerate_tour, 10 ** 9) == 12            # 12 * 11! = 479 001 600
    assert A.accesses_held_karp(23) == 22 * 21 * 2 ** 20 + 44
    assert A.budget_frontier(A.accesses_held_karp, 10 ** 9) == 23
    assert A.budget_frontier(A.accesses_hungarian_bound, 10 ** 9) == 1000


def test_budget_frontier_edges():
    assert A.budget_frontier(A.accesses_enumerate_assignment, 0) == 0
    assert A.budget_frontier(A.accesses_hungarian_bound, 1) == 1
    assert A.budget_frontier(A.accesses_hungarian_bound, 8) == 2
    assert A.budget_frontier(A.accesses_hungarian_bound, 7) == 1
    assert A.budget_frontier(A.accesses_hungarian_bound, 10 ** 12, n_cap=500) == 500    # Deckel

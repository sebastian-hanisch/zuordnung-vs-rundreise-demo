"""Szenario: deterministisch, Diagonale gesperrt, Werte im dokumentierten Bereich."""

import math

import pytest

import zrt_constants as C
from zrt_scenario import from_matrix, label, make_instance


@pytest.mark.parametrize("kind", ["euclid", "random"])
def test_same_input_same_instance_and_other_seed_differs(kind):
    assert make_instance(8, kind, 5) == make_instance(8, kind, 5)
    assert make_instance(8, kind, 5) != make_instance(8, kind, 6)


@pytest.mark.parametrize("kind", ["euclid", "random"])
def test_diagonal_is_forbidden_and_the_rest_is_allowed(kind):
    inst = make_instance(9, kind, 1)
    assert inst.n == 9
    for i in range(9):
        for j in range(9):
            assert (inst.matrix[i][j] == C.FORBIDDEN) == (i == j)


def test_random_costs_stay_in_the_documented_range():
    inst = make_instance(12, "random", 2)
    values = [inst.matrix[i][j] for i in range(12) for j in range(12) if i != j]
    assert C.COST_LOW <= min(values) and max(values) <= C.COST_HIGH
    assert inst.points is None


def test_euclid_entries_are_rounded_distances_of_the_points():
    inst = make_instance(8, "euclid", 3)
    assert inst.points is not None and len(inst.points) == 8
    for i in range(8):
        assert 0 <= inst.points[i][0] <= C.COORD_MAX and 0 <= inst.points[i][1] <= C.COORD_MAX
        for j in range(8):
            if i != j:
                assert inst.matrix[i][j] == round(math.hypot(inst.points[i][0] - inst.points[j][0], inst.points[i][1] - inst.points[j][1]))


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError):
        make_instance(5, "grid", 1)


def test_labels_are_one_based():
    assert label(0) == "O1" and label(15) == "O16"


def test_from_matrix_keeps_off_diagonal_values():
    inst = from_matrix([[9, 2, 3], [4, 9, 6], [7, 8, 9]])
    assert inst.matrix[0][1:] == (2, 3) and inst.matrix[2][:2] == (7, 8) and inst.matrix[1][1] == C.FORBIDDEN

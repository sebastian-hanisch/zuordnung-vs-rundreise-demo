"""Kennzahlen, Messreihen und Prüfung vor der Anzeige."""

import math

import pytest

import zrt_algorithm as A
import zrt_constants as C
import zrt_evaluation as ev
from zrt_scenario import from_matrix, make_instance


def test_number_formats():
    assert ev.fmt_int(0) == "0" and ev.fmt_int(999) == "999" and ev.fmt_int(1000) == "1.000" and ev.fmt_int(1720350) == "1.720.350"
    assert ev.fmt_num(22.66) == "22,7" and ev.fmt_num(5.0, 0) == "5" and ev.fmt_num(2.4432, 2) == "2,44"


def test_relaxation_gap_by_hand():
    assert ev.relaxation_gap(4, 22) == pytest.approx(81.8181818, rel=1e-6)
    assert ev.relaxation_gap(22, 22) == 0.0
    assert ev.relaxation_gap(0, 0) == 0.0          # Nenner 0: keine Lücke statt Division durch null
    assert ev.relaxation_gap(5, 10) == 50.0


def test_default_analysis_is_exact_and_consistent():
    a = ev.analyse(ev.Settings())
    assert a.assignment.exact and a.tour.exact and a.gap is not None and a.gap >= 0
    assert a.cycles is not None and sum(len(c) for c in a.cycles) == a.inst.n
    assert ev.validation_errors(a) == []


def test_analysis_with_exhausted_budget_has_no_gap_and_no_cycles():
    a = ev.analyse(ev.Settings(n=11, assign="enumerate", tour="enumerate", budget=10_000))
    assert not a.assignment.exact and not a.tour.exact and a.gap is None and a.cycles is None
    assert ev.validation_errors(a) == []                       # auch Teillösungen sind zulässig


def test_settings_are_keyword_only():
    with pytest.raises(TypeError):
        ev.Settings(8, "euclid", 35)                          # nie positional (Memory feedback_settings_dataclass_keyword_args)


def test_validation_catches_broken_results():
    inst = from_matrix([[0, 1, 10, 10], [1, 0, 10, 10], [10, 10, 0, 1], [10, 10, 1, 0]])
    s = ev.Settings(n=4)
    good_a = A.Result("hungarian", 4, (1, 0, 3, 2), 5, True)
    good_t = A.Result("held_karp", 22, (0, 1, 2, 3), 18, True)
    assert ev.validation_errors(ev.Analysis(s, inst, good_a, good_t, ((0, 1), (2, 3)), 81.0)) == []
    fixpoint = A.Result("hungarian", 4, (0, 1, 2, 3), 5, True)
    assert "Fixpunkt" in ev.validation_errors(ev.Analysis(s, inst, fixpoint, good_t, None, None))[0]
    wrong_cost = A.Result("hungarian", 5, (1, 0, 3, 2), 5, True)
    assert "Neuberechnung" in ev.validation_errors(ev.Analysis(s, inst, wrong_cost, good_t, None, None))[0]
    bad_tour = A.Result("held_karp", 22, (1, 0, 2, 3), 18, True)
    assert "genau einmal" in ev.validation_errors(ev.Analysis(s, inst, good_a, bad_tour, None, None))[0]
    wrong_tour = A.Result("held_karp", 23, (0, 1, 2, 3), 18, True)
    assert "Neuberechnung" in ev.validation_errors(ev.Analysis(s, inst, good_a, wrong_tour, None, None))[0]
    assert "teurer" in ev.validation_errors(ev.Analysis(s, inst, good_a, good_t, None, -1.0))[0]


def test_sweep_gap_structure_and_bounds():
    rows = ev.sweep_gap("euclid", sizes=(4, 6), seeds=C.SWEEP_SEEDS[:6])
    assert [r["n"] for r in rows] == [4, 6]
    for r in rows:
        assert r["count"] == 6 and 0 <= r["gap_median"] <= r["gap_max"] <= 100 and 1 <= r["cycles_median"] <= r["n"] // 2 + 1
        assert 0 <= r["one_cycle"] <= r["count"]


def test_sweep_gap_uses_the_fixed_instances():
    assert ev.sweep_gap("random", sizes=(5,), seeds=C.SWEEP_SEEDS[:5]) == ev.sweep_gap("random", sizes=(5,), seeds=C.SWEEP_SEEDS[:5])
    assert len(C.SWEEP_SEEDS) == 20 and len(set(C.SWEEP_SEEDS)) == 20


def test_sweep_gap_matches_a_hand_recomputation():
    rows = ev.sweep_gap("random", sizes=(6,), seeds=(1, 2, 3))
    gaps, cycles = [], []
    for seed in (1, 2, 3):
        inst = make_instance(6, "random", seed)
        h, k = A.hungarian(inst), A.held_karp(inst)
        gaps.append(100.0 * (k.cost - h.cost) / k.cost)
        cycles.append(len(A.cycles_of_assignment(h.plan)))
    assert rows[0]["gap_median"] == pytest.approx(sorted(gaps)[1]) and rows[0]["gap_max"] == pytest.approx(max(gaps))
    assert rows[0]["cycles_median"] == sorted(cycles)[1] and rows[0]["one_cycle"] == sum(1 for c in cycles if c == 1)


def test_loglog_slope_of_exact_powers():
    assert ev.loglog_slope([{"n": n, "accesses": n ** 2} for n in (10, 20, 40, 80)]) == pytest.approx(2.0)
    assert ev.loglog_slope([{"n": n, "accesses": 7 * n ** 3} for n in (10, 100)]) == pytest.approx(3.0)


def test_hungarian_scaling_is_below_the_bound_and_growing():
    rows = ev.hungarian_scaling("random", sizes=(10, 20, 40), seeds=C.GROWTH_SEEDS)
    assert [r["n"] for r in rows] == [10, 20, 40]
    assert all(0 < r["accesses"] <= r["bound"] for r in rows)
    assert rows[0]["accesses"] < rows[1]["accesses"] < rows[2]["accesses"]
    assert 1.5 < ev.loglog_slope(rows) < 3.0


def test_growth_rows_follow_the_formulas():
    rows = ev.growth_rows(sizes=(4, 8), seeds=C.GROWTH_SEEDS[:2])
    assert rows[0]["enum_assignment"] == 96 and rows[0]["enum_tour"] == 24 and rows[0]["held_karp"] == 18 and rows[0]["hungarian_bound"] == 64
    assert rows[1]["enum_assignment"] == 8 * math.factorial(8) and rows[1]["enum_tour"] == 8 * math.factorial(7)
    assert rows[1]["held_karp"] == 7 * 6 * 32 + 14 and rows[1]["hungarian_bound"] == 512
    assert all(0 < r["hungarian_measured"] <= r["hungarian_bound"] for r in rows)


def test_frontier_rows_match_hand_values():
    rows = ev.frontier_rows()
    first = rows[0]
    assert first["budget"] == 10 ** 6
    assert first["n"] == {"enum_assignment": 8, "enum_tour": 9, "held_karp": 15, "hungarian": 100}
    assert first["n_fast"] == {"enum_assignment": 11, "enum_tour": 12, "held_karp": 23, "hungarian": 1000}
    assert [r["budget"] for r in rows] == list(C.FRONTIER_BUDGETS)
    for r in rows:                                              # mehr Budget, mindestens gleiches n
        assert all(r["n_fast"][m] >= r["n"][m] for m in r["n"])


def test_step_factor_by_hand():
    assert ev.step_factor("held_karp", 4) == 3.0                   # 18 / 6
    assert ev.step_factor("enum_tour", 5) == 5.0                   # 5 * 4! / (4 * 3!) = 120 / 24
    assert ev.step_factor("hungarian", 4) == pytest.approx(64 / 27)

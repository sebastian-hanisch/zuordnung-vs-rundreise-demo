"""Jede Zahl der README steht hier und wird über dieselben Auswertungsfunktionen wie in der App nachgerechnet (DEMO-PLAYBOOK §4).

Ganzzahlige Zähler und Handwerte sind exakt, Zufallsdurchschnitte (Median über die festen Instanzen SWEEP_SEEDS) als Bänder: die Karten-Entfernungen werden gerundet
(`round(hypot)`), und eine Plattform mit abweichender libm könnte in seltenen Randfällen eine Entfernung um eins verschieben."""

import pytest

import zrt_algorithm as A
import zrt_constants as C
import zrt_evaluation as ev
from zrt_scenario import make_instance

BAND = 0.3     # Prozentpunkte: Toleranz für Medianwerte der Lücke


# --- Befund 1: Zählformeln und das größte n im Budget ---------------------------------------------------------------------------------------------


def test_claim_counting_formulas_at_n_12():
    """README, Wachstumstabelle: bei n = 12 sind es 5.748.019.200 (Zuordnung aufzählen), 479.001.600 (Rundreise aufzählen), 56.342 (Held–Karp), Schranke 1.728."""
    row = ev.growth_rows(sizes=(12,))[0]
    assert row["enum_assignment"] == 5_748_019_200
    assert row["enum_tour"] == 479_001_600
    assert row["held_karp"] == 56_342
    assert row["hungarian_bound"] == 1_728
    assert round(row["enum_tour"] / row["held_karp"]) == 8_502


def test_claim_step_factors():
    """README: ein zusätzlicher Ort verteuert Held–Karp um den Faktor 2,44 (n = 11 → 12) und 2,31 (n = 15 → 16), das Aufzählen der Rundreise um den Faktor n."""
    assert ev.step_factor("held_karp", 12) == pytest.approx(2.443, abs=0.001)
    assert ev.step_factor("held_karp", 16) == pytest.approx(2.308, abs=0.001)
    assert ev.step_factor("enum_tour", 12) == 12 and ev.step_factor("enum_tour", 16) == 16


def test_claim_budget_frontier():
    """README, Tabelle „Größtes n im Budget“: Aufzählen Zuordnung / Aufzählen Rundreise / Held–Karp / Ungarisch (Schranke n³), je Budget und mit tausendfachem Budget."""
    rows = {r["budget"]: r for r in ev.frontier_rows()}
    keys = ("enum_assignment", "enum_tour", "held_karp", "hungarian")
    assert [rows[10 ** 6]["n"][k] for k in keys] == [8, 9, 15, 100]
    assert [rows[10 ** 6]["n_fast"][k] for k in keys] == [11, 12, 23, 1000]
    assert [rows[10 ** 8]["n"][k] for k in keys] == [10, 11, 21, 464]
    assert [rows[10 ** 8]["n_fast"][k] for k in keys] == [13, 14, 29, 4641]
    assert [rows[10 ** 9]["n"][k] for k in keys] == [11, 12, 23, 1000]
    assert [rows[10 ** 9]["n_fast"][k] for k in keys] == [13, 14, 32, 10000]


def test_claim_thousand_times_hardware_is_additive_for_exponential_methods_and_multiplicative_for_the_polynomial_one():
    """README: bei 10^6 Zugriffen gewinnt das Aufzählen der Rundreise 3 Orte, Held–Karp 8 Orte, die Ungarische Methode (Schranke) wächst auf das Zehnfache."""
    r = ev.frontier_rows()[0]
    assert r["n_fast"]["enum_tour"] - r["n"]["enum_tour"] == 3
    assert r["n_fast"]["held_karp"] - r["n"]["held_karp"] == 8
    assert r["n_fast"]["hungarian"] == 10 * r["n"]["hungarian"]


# --- Befund 2: Zuordnung als Relaxation der Rundreise ---------------------------------------------------------------------------------------------


EUCLID = {4: (12.5, 2, 0), 6: (16.8, 3, 0), 8: (18.1, 4, 0), 10: (22.0, 4, 0), 12: (24.9, 5, 0)}      # n: (Median der Lücke %, Median der Teilkreise, schon Rundreise von 20)
RANDOM = {4: (0.0, 1, 16), 6: (5.3, 2, 4), 8: (6.7, 2, 4), 10: (3.7, 2, 4), 12: (7.1, 2, 2)}


@pytest.mark.parametrize("kind,expected", [("euclid", EUCLID), ("random", RANDOM)])
def test_claim_gap_between_assignment_and_tour(kind, expected):
    """README, Lückentabelle: Median der Lücke, Median der Teilkreise und Zahl der Instanzen (von 20), bei denen die billigste Zuordnung schon eine Rundreise ist."""
    rows = {r["n"]: r for r in ev.sweep_gap(kind)}
    assert set(rows) == set(expected) == set(C.N_GAP)
    for n, (gap, cycles, single) in expected.items():
        r = rows[n]
        assert r["count"] == 20
        assert r["gap_median"] == pytest.approx(gap, abs=BAND), (kind, n)
        assert r["cycles_median"] == cycles, (kind, n)
        assert r["one_cycle"] == single, (kind, n)


def test_claim_euclid_gap_grows_and_random_gap_stays_small():
    """README: bei den 20 festen Karten je Größe steigen die Mediane der Lücke von n = 4 bis n = 12 von rund 12 % auf rund 25 % (mit anderen Karten flacht der Anstieg ab n = 8 ab), auf Zufallsmatrizen bleibt er unter 8 %; kein einziges Kartenbeispiel von 100 ist schon eine Rundreise."""
    euclid = ev.sweep_gap("euclid")
    random = ev.sweep_gap("random")
    medians = [r["gap_median"] for r in euclid]
    assert medians == sorted(medians) and medians[0] < 13 and medians[-1] > 24
    assert max(r["gap_median"] for r in random) < 8
    assert sum(r["one_cycle"] for r in euclid) == 0 and sum(r["count"] for r in euclid) == 100


def test_claim_maximum_gap_reaches_half_on_maps():
    """README: im Einzelfall liegt die Zuordnung auf Karten bis zu 53 % unter der Rundreise (Maximum über 20 Karten, n = 4 bis 12)."""
    assert max(r["gap_max"] for r in ev.sweep_gap("euclid")) == pytest.approx(53.1, abs=BAND)


# --- Befund 3: Wachstum der Ungarischen Methode ---------------------------------------------------------------------------------------------------


def test_claim_hungarian_grows_slower_than_its_bound_on_random_matrices():
    """README: auf Zufallsmatrizen wächst die Ungarische Methode etwa wie n^2,4 (Ausgleichsgerade n = 10 bis 160; hier 2,44), bei n = 160 im Median 181.650 Zugriffe gegen die Schranke 4.096.000."""
    rows = ev.hungarian_scaling("random")
    assert 2.3 < ev.loglog_slope(rows) < 2.6
    last = rows[-1]
    assert last["n"] == 160 and last["bound"] == 4_096_000
    assert last["accesses"] == pytest.approx(181_650, rel=0.01)
    assert all(r["accesses"] / r["bound"] < 0.2 for r in rows)


def test_claim_hungarian_on_maps_grows_even_slower():
    """README: auf Karten liegt der gemessene Exponent bei etwa 2,2 und bei n = 160 im Median 78.726 Zugriffe."""
    rows = ev.hungarian_scaling("euclid")
    assert 2.1 < ev.loglog_slope(rows) < 2.4
    assert rows[-1]["accesses"] == pytest.approx(78_726, rel=0.02)


def test_claim_hungarian_measured_at_n_12():
    """README: bei n = 12 im Median 238 Zugriffe (Zufallsmatrizen, fünf feste Instanzen) gegen die Schranke 1.728."""
    row = ev.growth_rows(sizes=(12,))[0]
    assert row["hungarian_measured"] == pytest.approx(238, rel=0.02)


# --- Einzelinstanzen (Presets) und Handrechnung ---------------------------------------------------------------------------------------------------


def test_claim_mini_instance_by_hand():
    """README, Lehrbeispiel: vier Orte, zwei Paare mit Kosten 1: billigste Zuordnung 4 in zwei Teilkreisen, beste Rundreise 22, Lücke (22 − 4) / 22 = 81,8 %."""
    from zrt_scenario import from_matrix
    inst = from_matrix([[0, 1, 10, 10], [1, 0, 10, 10], [10, 10, 0, 1], [10, 10, 1, 0]])
    h, k = A.hungarian(inst), A.held_karp(inst)
    assert (h.cost, k.cost) == (4, 22) and len(A.cycles_of_assignment(h.plan)) == 2
    assert ev.relaxation_gap(h.cost, k.cost) == pytest.approx(81.818, abs=0.001)


def test_claim_default_preset_instance():
    """README: das Standard-Preset (n = 8, Karte, Zufalls-Seed 35) ist eine EINZELNE Instanz: Zuordnung 190 (71 Zugriffe, 4 Teilkreise), Rundreise 316 (1.358 Zugriffe), Lücke 39,9 %."""
    a = ev.analyse(ev.Settings())
    assert (a.assignment.cost, a.assignment.accesses, len(a.cycles)) == (190, 71, 4)
    assert (a.tour.cost, a.tour.accesses) == (316, 1_358)
    assert a.gap == pytest.approx(39.87, abs=0.05)


def test_claim_enumeration_preset_aborts_at_the_budget():
    """README: das Preset „Aufzählen stößt an die Grenze“ (n = 11, Budget 1.000.000) bricht beide Läufe ab; die Zuordnung hat bis dahin noch keine zulässige Permutation gesehen."""
    a = ev.analyse(ev.Settings(**C.PRESETS["Aufzählen stößt an die Grenze"]))
    assert not a.assignment.finished and a.assignment.cost is None and a.assignment.accesses == 999_999
    assert not a.tour.finished and a.tour.cost is not None and a.tour.accesses == 999_999
    assert A.accesses_enumerate_tour(11) == 39_916_800 > 1_000_000      # 11 * 10!


def test_claim_held_karp_at_the_slider_maximum():
    """README: bei n = 16 braucht Held–Karp 1.720.350 Zugriffe (3 Mio. Budget), die Ungarische Methode höchstens 4.096."""
    assert A.accesses_held_karp(16) == 1_720_350
    a = ev.analyse(ev.Settings(**C.PRESETS["Held–Karp am Rand"]))
    assert a.tour.exact and a.tour.accesses == 1_720_350
    assert a.assignment.exact and a.assignment.accesses <= A.accesses_hungarian_bound(16) == 4_096


def test_claim_unit_is_matrix_accesses_and_verdicts_state_the_unit():
    """README: die Einheit ist der Zugriff auf die Kostenmatrix; der abgebrochene Lauf nennt die Zugriffe, nicht Sekunden."""
    a = ev.analyse(ev.Settings(n=11, assign="enumerate", tour="enumerate", budget=10_000))
    text = ev.verdict_main(a)[1]
    assert "Zugriffen" in text and "Sekunden" not in text
    assert make_instance(5, "euclid", 1).n == 5

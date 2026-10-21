"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import zrt_algorithm as A
import zrt_evaluation as ev
from zrt_scenario import from_matrix


def _analysis(assignment_result, tour_result, cycles, gap, **settings):
    inst = from_matrix([[0, 1, 10, 10], [1, 0, 10, 10], [10, 10, 0, 1], [10, 10, 1, 0]])
    return ev.Analysis(ev.Settings(**settings), inst, assignment_result, tour_result, cycles, gap)


def _exact(cost, accesses=10, method="hungarian"):
    return A.Result(method, cost, (0,), accesses, True)


def test_main_verdict_one_cycle_is_a_success():
    kind, text = ev.verdict_main(_analysis(_exact(22), _exact(22, method="held_karp"), ((0, 1, 2, 3),), 0.0))
    assert kind == "success" and "ein einziger Kreis" in text and "beide kosten 22." in text


def test_main_verdict_tie_with_several_cycles_is_an_info():
    kind, text = ev.verdict_main(_analysis(_exact(22), _exact(22, method="held_karp"), ((0, 1), (2, 3)), 0.0))
    assert kind == "info" and "beide 22" in text and "in 2 Teilkreisen" in text and "Gleichstand" in text


def test_main_verdict_names_costs_gap_and_cycles():
    kind, text = ev.verdict_main(_analysis(_exact(4), _exact(22, method="held_karp"), ((0, 1), (2, 3)), ev.relaxation_gap(4, 22)))
    assert kind == "info"
    assert "kostet 4" in text and "Rundreise 22" in text and "**81,8 %** billiger" in text and "in 2 Teilkreisen" in text


def test_main_verdict_aborted_assignment_only_names_the_assignment():
    aborted = A.Result("enumerate", None, None, 999999, False)
    kind, text = ev.verdict_main(_analysis(aborted, _exact(22, method="held_karp"), None, None, assign="enumerate", budget=1_000_000))
    assert kind == "warning"
    assert "Budget von 1.000.000 Zugriffen reicht nicht" in text
    assert "Die Zuordnung brach nach 999.999 Zugriffen ab (Verfahren: Aufzählen aller Zuordnungen)" in text
    assert "Rundreise" not in text.split("Erhöhen")[0]


def test_main_verdict_both_aborted_names_both_with_their_own_method_label():
    a = A.Result("enumerate", 9, (0,), 5000, False)       # Teillösung zählt nicht als exakt
    kind, text = ev.verdict_main(_analysis(a, a, None, None, assign="enumerate", tour="enumerate", budget=5000))
    assert kind == "warning"
    assert "Die Zuordnung brach nach 5.000 Zugriffen ab (Verfahren: Aufzählen aller Zuordnungen)" in text
    assert "; die Rundreise brach nach 5.000 Zugriffen ab (Verfahren: Aufzählen aller Rundreisen)" in text


def test_frontier_verdict_names_additive_and_multiplicative_growth():
    rows = [{"budget": 1_000_000,
             "n": {"enum_assignment": 8, "enum_tour": 9, "held_karp": 15, "hungarian": 100},
             "n_fast": {"enum_assignment": 11, "enum_tour": 12, "held_karp": 23, "hungarian": 1000}}]
    kind, text = ev.verdict_frontier(rows)
    assert kind == "info"
    assert "1.000.000 Zugriffen" in text and "bis n = 9" in text and "Held–Karp bis n = 15" in text and "bis n = 100" in text
    assert "beim Aufzählen um 3" in text and "bei Held–Karp um 8" in text and "von 100 auf 1.000" in text and "10-Fache" in text


def test_gap_verdict_uses_the_largest_size_of_both_kinds():
    euclid = [{"n": 10, "gap_median": 5.0, "cycles_median": 2, "one_cycle": 0, "count": 20}, {"n": 12, "gap_median": 24.9, "cycles_median": 5, "one_cycle": 1, "count": 20}]
    random = [{"n": 10, "gap_median": 1.0, "cycles_median": 1, "one_cycle": 9, "count": 20}, {"n": 12, "gap_median": 7.1, "cycles_median": 2, "one_cycle": 2, "count": 20}]
    kind, text = ev.verdict_gap({"euclid": euclid, "random": random})
    assert kind == "info"
    assert "Bei n = 12" in text and "**24,9 %**" in text and "(Zufallsmatrix: 7,1 %)" in text
    assert "im Median 5 Teilkreise (Zufallsmatrix: 2)" in text and "nur in 1 von 20 Karten (Zufallsmatrix: 2 von 20)" in text


def test_methods_verdict_with_hand_values():
    row = {"n": 6, "enum_assignment": 4320, "enum_tour": 720, "held_karp": 150, "hungarian_bound": 216, "hungarian_measured": 40.4}   # handgesetzt: 720 / 150 = 4,8
    kind, text = ev.verdict_methods(row)
    assert kind == "info"
    assert "Bei n = 6" in text and "4.320 Matrixeinträge" in text and "höchstens 216" in text and "gemessen im Median 40)" in text
    assert "720 beim Aufzählen und 150 bei Held–Karp" in text and "5-mal weniger" in text
    assert "von n = 5 auf n = 6" in text


def test_methods_verdict_small_ratio_is_not_called_many_times_fewer():
    row = {"n": 4, "enum_assignment": 96, "enum_tour": 24, "held_karp": 18, "hungarian_bound": 64, "hungarian_measured": 20}
    assert "kaum weniger" in ev.verdict_methods(row)[1]


def test_scaling_verdict_names_exponent_and_bound():
    rows = [{"n": 10, "accesses": 100, "bound": 1000}, {"n": 100, "accesses": 10000, "bound": 1_000_000}]
    kind, text = ev.verdict_scaling(rows)
    assert kind == "info"
    assert "etwa wie n^2,00" in text and "n = 10 bis 100" in text and "im Median 10.000 Zugriffe" in text and "liegt bei 1.000.000" in text

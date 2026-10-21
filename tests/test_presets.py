"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink-Begrenzung."""

import zrt_constants as C
import zrt_evaluation as ev
import zrt_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_valid_choices():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX
        assert preset["kind"] in C.KINDS and preset["assign"] in C.ASSIGN_METHODS and preset["tour"] in C.TOUR_METHODS and preset["budget"] in C.BUDGETS


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    assert next(iter(C.PRESETS)) == "Standardfall (Voreinstellung)"


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_choice_specs_list_their_options_with_first_and_last_as_bounds():
    for key in ("kind_radio", "assign_select", "tour_select", "budget_select"):
        spec = P.SETTING_SPECS[key]
        assert spec.options and spec.lo == spec.options[0] and spec.hi == spec.options[-1], key


def test_coerce_limits_numbers_and_rejects_unknown_choices():
    n = P.SETTING_SPECS["n_slider"]
    assert P._coerce(n, "3") == C.N_MIN and P._coerce(n, "99") == C.N_MAX and P._coerce(n, "9") == 9 and P._coerce(n, "x") is None
    assert P._coerce(n, ["12"]) == 12 and P._coerce(n, []) is None
    kind = P.SETTING_SPECS["kind_radio"]
    assert P._coerce(kind, "random") == "random" and P._coerce(kind, "nonsense") is None
    budget = P.SETTING_SPECS["budget_select"]
    assert P._coerce(budget, "100000") == 100000 and P._coerce(budget, "123") is None


def test_presets_cover_the_documented_situations():
    """Die Presets zeigen, was ihre Hilfe verspricht: Standard exakt, Zufallsmatrix exakt, Aufzählen bricht ab, Held–Karp am Rand läuft zu Ende."""
    results = {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}
    assert results["Standardfall (Voreinstellung)"].assignment.exact and results["Standardfall (Voreinstellung)"].tour.exact
    assert results["Standardfall (Voreinstellung)"].cycles is not None and len(results["Standardfall (Voreinstellung)"].cycles) >= 2
    assert results["Zufallsmatrix statt Karte"].gap is not None and results["Zufallsmatrix statt Karte"].inst.points is None
    grenze = results["Aufzählen stößt an die Grenze"]
    assert not grenze.assignment.finished and not grenze.tour.finished
    rand = results["Held–Karp am Rand"]
    assert rand.tour.exact and rand.inst.n == C.N_MAX and rand.tour.accesses == 1720350

# Preset-Abstimmung (2026-10-21)

Jedes Preset wurde mit `zrt_evaluation.analyse` gerechnet; die Spalten sind dieselben Zahlen, die die App zeigt (Einzelinstanzen, Zufalls-Seed 35). Gegen die Hilfetexte in `zrt_constants.PRESET_HELP` geprüft; `tests/test_presets.py` (`test_presets_cover_the_documented_situations`) hält die Aussagen fest.

| Preset | n | Matrix | Zuordnung (Verfahren: Kosten, Zugriffe, Lauf zu Ende) | Rundreise (Verfahren: Kosten, Zugriffe, Lauf zu Ende) | Teilkreise | Lücke |
|---|---|---|---|---|---|---|
| Standardfall (Voreinstellung) | 8 | Karte | Ungarisch: 190, 71, ja | Held–Karp: 316, 1.358, ja | 4 | 39,9 % |
| Zufallsmatrix statt Karte | 10 | Zufall | Ungarisch: 133, 186, ja | Held–Karp: 146, 9.234, ja | 2 | 8,9 % |
| Aufzählen stößt an die Grenze | 11 | Karte | Aufzählen: keine zulässige Zuordnung gesehen, 999.999, nein | Aufzählen: 399 (bisher beste), 999.999, nein | – | – |
| Held–Karp am Rand | 16 | Karte | Ungarisch: 292, 751, ja | Held–Karp: 376, 1.720.350, ja | 7 | 22,3 % |

Hinweise: Die Lücke des Standardfalls (39,9 %) liegt deutlich über dem Median der Messreihe (18,1 % bei n = 8); sie ist eine Einzelinstanz und steht in der README so, nicht als Median. Das Preset „Aufzählen stößt an die Grenze“ bricht bei 999.999 statt 1.000.000 Zugriffen ab, weil der nächste Schritt (11 Zugriffe) das Budget überschritte.

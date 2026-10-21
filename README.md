# Zuordnung gegen Rundreise: dieselbe Matrix, zwei Klassen – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-zuordnung-vs-rundreise-demo.streamlit.app/)** -->

Erstes Stück der **Komplexitätsklassen-Reihe** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, **Wurzel** der Reihe. Anders als die Fall-Demos (ein Anwendungsfall, mehrere Verfahren im Vergleich) zeigt sie **einen Begriff**, „Komplexitätsklasse“, an einem wachsenden Beispiel: **einer Kostenmatrix, zwei Fragen**. Die Kante in der Reihe: Folgestücke ordnen die Rundreise über Reduktionen ein (Stück 3) und fragen, wie schwer typische Instanzen wirklich sind (Stück 4); dieses Stück legt die Messgröße und die Grundaussage fest.

## Warum dieses Problem

Welches Fahrzeug fährt zu welchem Auftrag (**Zuordnung**), und in welcher Reihenfolge besucht ein Fahrzeug alle Orte (**Rundreise**)? Beide suchen eine Anordnung von n Dingen, beide haben n! Möglichkeiten, und beide lassen sich durch Aufzählen lösen. Trotzdem gilt die Zuordnung als **leicht** (Klasse P: die Ungarische Methode kommt mit höchstens n³ Schritten aus), die Rundreise als **schwer** (NP-schwer: ein polynomiales Verfahren ist nicht bekannt, und ein solches Verfahren würde P = NP beweisen). Die Kernfrage der Demo: **Woran liegt der Unterschied, und wie sieht man ihn?** Die Antwort in zwei Teilen: Die Klasse gehört zum *Problem*, nicht zum Verfahren (das Aufzählen kostet bei beiden gleich viel, das Verfahren trennt sie); und die billigste Zuordnung ist eine **Relaxation** der Rundreise: sie darf in mehrere Teilkreise zerfallen, die Rundreise nicht.

## Modell

- **Matrix.** n × n-Kosten, Diagonale gesperrt (kein Fahrzeug fährt zu sich selbst, keine Rundreise bleibt am Ort). Zwei Arten: **Karte** (Entfernungen zwischen zufälligen Orten in [0, 100]², auf ganze Zahlen gerundet, symmetrisch) und **Zufallsmatrix** (ganze Zahlen 1 bis 100, in jede Richtung anders). Beide sind **Instanzfamilien**, keine Naturgesetze.
- **Zuordnung.** Permutation σ ohne Fixpunkt, minimiere Σ c(i, σ(i)): das Ziel zählt je Position, der Nachbar spielt keine Rolle.
- **Rundreise.** Zyklische Reihenfolge ab Ort 1, minimiere die Summe über aufeinanderfolgende Paare: das Ziel hängt vom Nachbarn ab.
- **Beziehung.** Jede Rundreise ist eine Zuordnung mit **einem einzigen Kreis**. Daher OPT(Zuordnung) ≤ OPT(Rundreise), mit Gleichheit, wenn die billigste Zuordnung selbst ein einziger Kreis ist.
- **Aufwand.** Gezählt wird der **Zugriff auf die Kostenmatrix**, nicht die Laufzeit. Jedes Verfahren hat ein Budget und bricht ab, bevor es mehr Zugriffe ausgibt; die App zeigt dann „bisher beste“ Werte, nie „optimal“.
- Mathematik und Annahmentabelle: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Verfahren | Problem | Zugriffe | Anmerkung |
|---|---|---|---|
| Aufzählen aller Zuordnungen | Zuordnung | n · n! | exakt, behält die billigste Permutation ohne Fixpunkt |
| Ungarische Methode | Zuordnung | gezählt, Schranke n³ | Potenziale und kürzeste Verbesserungswege; exakt |
| Aufzählen aller Rundreisen | Rundreise | n · (n−1)! | Reihenfolgen ab Ort 1; exakt |
| Held–Karp | Rundreise | (n−1)(n−2) · 2^(n−3) + 2(n−1) | Teilmengen-DP, exakt; Zählformel im Test gegen gezählte Läufe geprüft |

Experimente in der App: **Wie weit kommt man mit einem Budget?** (größtes n im Budget, tausendfache Hardware), **Wie weit ist die Zuordnung von der Rundreise?** (Lücke und Teilkreise über n, Karte gegen Zufallsmatrix), **Das Verfahren ist nicht das Problem** (dasselbe Problem, zwei Verfahren; gemessenes Wachstum der Ungarischen Methode gegen die Schranke).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Medianwerte sind über 20 feste Instanzen je Größe (`SWEEP_SEEDS`) gebildet, das Wachstum der Ungarischen Methode über fünf feste Zufallsmatrizen (`GROWTH_SEEDS`); die Zahlen aus den Presets sind Einzelinstanzen und als solche ausgewiesen.

| Frage | Befund |
|---|---|
| **Wie viel liest das Aufzählen, wie viel das beste Verfahren? (n = 12)** | Aufzählen aller Zuordnungen 5.748.019.200 Zugriffe, Ungarisch höchstens 1.728 (Schranke n³, gemessen im Median 238); Aufzählen aller Rundreisen 479.001.600, Held–Karp 56.342, also rund 8.502-mal weniger (`test_claim_counting_formulas_at_n_12`). |
| **Wie wächst Held–Karp?** | Jeder zusätzliche Ort verteuert Held–Karp um den Faktor 2,44 (n = 11 → 12) bzw. 2,31 (n = 15 → 16), das Aufzählen der Rundreise um den Faktor n: exponentiell bleibt beides (`test_claim_step_factors`). |
| **Wie weit kommt man in 10⁶ Zugriffen?** | Aufzählen aller Zuordnungen bis n = 8, aller Rundreisen bis n = 9, Held–Karp bis n = 15, Ungarisch (nach der Schranke n³) bis n = 100 (`test_claim_budget_frontier`). |
| **Was bringt tausendfache Hardware?** | Bei 10⁶ Zugriffen gewinnt das Aufzählen der Rundreisen 3 Orte (9 → 12), Held–Karp 8 Orte (15 → 23): **additiv**; die Ungarische Methode wächst nach der Schranke auf das Zehnfache (100 → 1.000): **multiplikativ**. Bei 10⁸ und 10⁹ Zugriffen dieselbe Struktur (Tabelle in der App, `test_claim_thousand_times_hardware_…`). |
| **Wie weit liegt die billigste Zuordnung unter der Rundreise? (Karte)** | Median der Lücke 12,5 / 16,8 / 18,1 / 22,0 / 24,9 % bei n = 4 / 6 / 8 / 10 / 12, Median der Teilkreise 2 / 3 / 4 / 4 / 5; in **0 von 100** Karten (5 Größen × 20) ist die billigste Zuordnung schon eine Rundreise; Maximum der Lücke 53,1 % (`test_claim_gap_…`). |
| **Und bei Zufallsmatrizen?** | Median der Lücke 0,0 / 5,3 / 6,7 / 3,7 / 7,1 %, Median der Teilkreise 1 / 2 / 2 / 2 / 2; die Zuordnung ist bei n = 4 in 16, bei n = 6, 8, 10 in je 4 und bei n = 12 in 2 von 20 Fällen schon eine Rundreise. Die Lücke ist hier klein, aber nicht monoton (`test_claim_gap_…`). |
| **Erreicht die Ungarische Methode ihre Schranke n³?** | **Nein, nicht auf diesen Matrizen.** Gemessen wächst sie auf Zufallsmatrizen etwa wie n^2,4 (Ausgleichsgerade über n = 10 bis 160; bei n = 160 im Median 181.650 Zugriffe gegen 4.096.000), auf Karten etwa wie n^2,2 (78.726 bei n = 160). Die Schranke gilt für den schlimmsten Fall, der hier nicht gebaut wurde (`test_claim_hungarian_…`). |
| **Lehrbeispiel von Hand (4 Orte)** | Billigste Zuordnung 4 in zwei Teilkreisen, beste Rundreise 22, Lücke 81,8 % (`test_claim_mini_instance_by_hand`). |
| **Standard-Preset (Einzelinstanz: n = 8, Karte, Zufalls-Seed 35)** | Zuordnung 190 (71 Zugriffe, 4 Teilkreise), Rundreise 316 (1.358 Zugriffe), Lücke 39,9 %; ausdrücklich eine Einzelinstanz und deutlich über dem Median 18,1 % (`test_claim_default_preset_instance`). |

## Ehrliche Grenzen

- **Zugriffe sind keine Laufzeit.** Speicher, Python-Aufwand und Cache fehlen; die Zählung vergleicht Verfahren, nicht Rechner. Die Zählformeln gelten für **diese** Implementierungen.
- **„NP-schwer“ ist eine Aussage unter P ≠ NP**, die unbewiesen ist; „kein polynomiales Verfahren bekannt“ heißt nicht „unmöglich“. Dass n! und 2ⁿ die Rundreise kennzeichnen, sagt die Demo nur über Aufzählen und Held–Karp.
- **Der schlimmste Fall der Ungarischen Methode wird nicht gezeigt.** Die Messung belegt, dass die Schranke n³ auf Zufallsmatrizen und Karten weit unterschritten wird, nicht, dass sie nie erreicht wird.
- **Zwei Matrixarten.** Die Lücke zwischen Zuordnung und Rundreise ist eine Aussage über diese Familien. Die Karten-Medianwerte hängen an 20 festen Instanzen je Größe (an einzelnen Größen gemessen: n = 4 bis 12), die Zufallswerte schwanken nicht monoton mit n.
- **Karten sind gerundet.** Entfernungen werden auf ganze Zahlen gerundet; Gleichstände zwischen verschiedenen Reihenfolgen sind dadurch häufiger als bei reellen Zahlen.
- **Nur exakte Verfahren für die Rundreise.** Heuristiken (2-opt, Lin–Kernighan) sind Gegenstand der Trajektorien-Metaheuristiken-Linie, nicht dieses Stücks.
- **In P heißt nicht schnell.** Dazu gibt es Gegenbeispiele in der Lineare-Programmierung-Reihe (`klee-minty-demo`, `ellipsoid-demo`).

## Befunde und Korrekturen gegenüber dem Plan

- **Hypothese widerlegt:** Der Plan erwartete für die Ungarische Methode ein Wachstum wie n³. Die Vormessung und die Messreihe zeigen auf Zufallsmatrizen etwa n^2,4 und auf Karten etwa n^2,2. n³ bleibt die Schranke, aber keine Messung; die App zeigt beides getrennt.
- **Einheit gewechselt:** Die Vormessung zählte Schleifenschritte, der Bau zählt **Zugriffe auf die Kostenmatrix** für alle Verfahren (sonst sind Aufzählen und Ungarisch nicht vergleichbar). Dadurch ändern sich einzelne Zahlen (z. B. Aufzählen aller Rundreisen kommt in 10⁶ Zugriffen bis n = 9 statt bis n = 10); die Aussagen blieben gleich.
- **Reglerzuschnitt:** Statt eines Reglers „Verfahren“ gibt es zwei (je einen für Zuordnung und Rundreise), weil die Ungarische Methode nur für die Zuordnung und Held–Karp nur für die Rundreise gilt. Den im Plan genannten Regler „Anzeige“ gibt es nicht: beide Fragen stehen immer nebeneinander, also kein totes oder bedingtes Bedienelement.
- **Lücke größer als vermutet:** Der Plan nannte die Lücke Zuordnung → Rundreise „klein“; auf Karten ist sie es nicht (Median 12,5 bis 24,9 %), nur auf Zufallsmatrizen (0 bis 7,1 %).
- **Entscheidungsfrage nicht ausgespielt:** Die Frage „Kosten höchstens K?“ wird im Expander der App erklärt, nicht als Ja/Nein-Anzeige umgesetzt; das gehört zum Folgestück über Zertifikate und Reduktionen.
- **Unerklärte Konsolenmeldung:** Beim ersten Zeichnen meldet der Browser fünfmal `<text> attribute y: Expected length, "-Infinity"`. Sie war weder an einzelnen Abbildungen noch in einer zweispaltigen Testseite reproduzierbar, und alle Diagramme zeigen danach endliche Positionen; ursächlich nicht geklärt, ohne sichtbare Wirkung.

## Verifikation

- **Kern:** jede Einheit gegen Handrechnung an der Mini-Instanz (`tests/conftest.py`: 4 und 22); Zählformeln gegen gezählte Läufe (`tests/test_formulas.py`), Budgetgrenzen inklusive, Randfälle n = 0, 1, 2, 3 (`tests/test_edge_cases.py`); jeder Zweig wird ausgeführt (`tests/test_branches.py`: Teilkreis-Fall, Einkreis-Fall, Budget in beiden Ausgängen).
- **Orakel** (`tests/test_oracle_zuordnung_vs_rundreise.py`): Ungarisch gegen `scipy.optimize.linear_sum_assignment` und Aufzählen, Held–Karp gegen Aufzählen und gegen CP-SAT (`AddCircuit`), Relaxation (Zuordnung ≤ Rundreise, Gleichheit bei einem Kreis). Im Repo laufen kleine Fassungen; der **große Lauf im Scratch-Ordner** (je 400 / 300 / 400 / 60 / 400 Instanzen: Ungarisch gegen scipy und Aufzählen; Ungarisch gegen scipy bei Gleichständen und n bis 44; Held–Karp gegen Aufzählen; Held–Karp gegen CP-SAT bei n bis 12; Relaxation und Einkreis-Gleichheit) fand **0 Abweichungen**.
- **Prüfung vor der Anzeige:** `validation_errors` prüft jedes Ergebnis mit dem unabhängigen Zulässigkeitsprüfer und neu berechneten Kosten (`tests/test_evaluation.py`).
- **Verdikte** als reine Funktionen, jede Zahl im Text und jede Schwelle an handgesetzten Werten (`tests/test_verdicts.py`).
- **Claims:** jede Zahl dieser README (`tests/test_claims.py`).
- **Presets:** vollständig, gültige Werte, das erste Preset ist die Standardeinstellung, jedes Preset zeigt, was seine Hilfe verspricht (`tests/test_presets.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum, alle Regler zugleich am Minimum bzw. Maximum, Permalink mit Begrenzung und unbekannten Werten, abgebrochene Läufe), Layout (Schnellstart oben, fester Kopf, aktives Preset hervorgehoben) und Footer.
- **Browser:** Presets, Held–Karp bei n = 16, abgebrochenes Aufzählen, PDF-Erzeugung durchgespielt; die Konsolenmeldung steht oben unter den Korrekturen.
- **Mutationsprüfung (Vollauf über `zrt_algorithm.py`, alle 211 Stellen):** 205 gesichert (gefangen, als äquivalent festgehalten oder durch wortgleiche Zeilen aus Nachbar-Demos gesichert), 6 Mutationen laufen in eine Endlosschleife (Zeitüberschreitung, zählt nicht als gefangen). Der erste Lauf fand echte Lücken, die jetzt Tests haben: Fixpunkt am letzten Ort, Prüfer bei n = 0 und n = 1, Teilkreis am letzten Ort, Gleichstandsregeln (zuerst gesehene Lösung bzw. kleinerer Vorgänger), die Grenze n ≥ 2 der Aufzählformel und die Budgetgrenze von Held–Karp auf den Zugriff genau. Als äquivalent festgehalten sind elf Stellen (Größe von Hilfsfeldern, `n ≥ 3` gegen `n ≥ 2` in der Zählformel mit demselben Wert 2, Gleichstand beim Ungarischen Verfahren, das nur den Plan, nicht die Kosten ändert); der Zustand steht in `tests/mutation_state.json`.

## Einordnung und Quellen (anhand der Quellen geprüft)

Ungarische Methode: Kuhn, *The Hungarian method for the assignment problem*, Naval Research Logistics Quarterly 2 (1955), S. 83 bis 97; Munkres, *Algorithms for the assignment and transportation problems*, Journal of the Society for Industrial and Applied Mathematics 5 (1957). Held–Karp-Verfahren: Bellman, *Dynamic programming treatment of the travelling salesman problem*, Journal of the ACM 9 (1962), S. 61 bis 63; Held und Karp, *A dynamic programming approach to sequencing problems* (1962). NP-Vollständigkeit des Hamiltonkreises und damit die Härte der Rundreise-Entscheidung: Karp, *Reducibility among combinatorial problems*, in: Miller und Thatcher (Hrsg.), Complexity of Computer Computations, Plenum 1972, S. 85 bis 103 (Reduktionen sind Gegenstand eines Folgestücks). Der Satz von Birkhoff und von Neumann (das Zuordnungs-LP hat ganzzahlige Ecken) ist hier nur genannt, nicht nachgeschlagen.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: beide Fragen nebeneinander, vier Experimente, Annahmentabelle, Formeln |
| `requirements-dev.txt` | Laufzeit plus pytest, scipy und OR-Tools (nur für die Gegenproben) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `zrt_algorithm.py` | Kern: Kosten, Prüfer, Teilkreise, Aufzählen, Ungarische Methode, Held–Karp, Zählformeln, größtes n im Budget |
| `zrt_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `zrt_evaluation.py` | Kennzahlen, Messreihen (Lücke, Wachstum, Budgetgrenzen), Prüfung vor der Anzeige, Verdikte |
| `zrt_layout.py` | Fester Kopf (Stylesheet) |
| `zrt_pdf_export.py` | PDF-Bericht (fpdf2) |
| `zrt_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `zrt_scenario.py` | Kostenmatrix (Karte oder Zufall), Ortsbeschriftung |
| `zrt_visualization.py` | Plotly-Abbildungen: Karte mit gerichteten Pfeilen, Wachstum, Lücke (Achsen gesperrt) |
| `tests/` | Mini-Instanz, Orakel, Formeln, Randfälle, Zweige, Verdikte, Claims, Presets, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Heuristiken für die Rundreise** (Nächster Nachbar, 2-opt, Lin–Kernighan): eigene Linie, hier steht die Klasse im Mittelpunkt.
- **Beweis der Härte** (Reduktionen, NP-Vollständigkeit): Folgestück; hier nur die Aussage und ihre Voraussetzung.
- **Ein gezielt gebauter schlimmster Fall der Ungarischen Methode:** die Messung zeigt nur, dass die Schranke auf Zufallsmatrizen und Karten nicht erreicht wird.
- **Die Entscheidungsversion „Kosten höchstens K?“ als Ja/Nein-Anzeige:** im Expander erklärt, nicht ausgespielt.
- **Branch-and-Cut und LP-Relaxationen für die Rundreise:** gehören in die Exakte-Suche-Linien.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).

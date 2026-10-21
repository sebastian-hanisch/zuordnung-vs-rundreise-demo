"""Zuordnung gegen Rundreise: dieselbe Matrix, zwei Klassen - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Wurzel der Komplexitätsklassen-Reihe: dieselbe Kostenmatrix, zwei Fragen (Zuordnung und Rundreise), Aufwand in Zugriffen auf die Matrix.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import zrt_algorithm as A
import zrt_constants as C
from zrt_evaluation import (
    METHOD_LABELS,
    Settings,
    analyse,
    fmt_int,
    fmt_num,
    frontier_rows,
    growth_rows,
    hungarian_scaling,
    sweep_gap,
    validation_errors,
    verdict_frontier,
    verdict_gap,
    verdict_main,
    verdict_methods,
    verdict_scaling,
)
from zrt_layout import dunkles_design, kopf_css
from zrt_pdf_export import build_pdf
from zrt_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from zrt_scenario import label
from zrt_visualization import assignment_edges, build_gap, build_growth, build_map, build_scaling, edge_colors, tour_edges

st.set_page_config(page_title="Zuordnung gegen Rundreise – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _gap_rows():
    return {kind: sweep_gap(kind) for kind in C.KINDS}


@st.cache_data(show_spinner=False)
def _growth():
    return growth_rows()


@st.cache_data(show_spinner=False)
def _scaling():
    return hungarian_scaling("random")


@st.cache_data(show_spinner=False)
def _pdf(settings):
    return build_pdf(analyse(settings))


def _md_table(header, rows):
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in zrt_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 Zuordnung gegen Rundreise: dieselbe Matrix, zwei Klassen")
st.markdown(
    """
Zwei Fragen an **dieselbe Kostenmatrix**: Welches Fahrzeug fährt zu welchem Auftrag (**Zuordnung**), und in welcher Reihenfolge besucht ein Fahrzeug alle Orte (**Rundreise**)?
Beide suchen eine Anordnung von n Dingen, und beide lassen sich durch Aufzählen aller Anordnungen lösen. Trotzdem gilt die Zuordnung als **leicht** (Klasse P, Ungarische Methode),
die Rundreise als **schwer** (NP-schwer; ein Verfahren mit polynomialem Aufwand ist nicht bekannt). Die Demo zählt dazu **Zugriffe auf die Kostenmatrix** statt Sekunden und zeigt:
**Die Klasse gehört zum Problem, nicht zum Verfahren.** Erstes Stück der Reihe Komplexitätsklassen (Wurzel); die Fall-Demos behandeln einzelne Anwendungen, hier steht ein Begriff im Mittelpunkt.

Weiter unten: die Experimente **🔬 Wie weit kommt man mit einem Budget?**, **🔬 Wie weit ist die Zuordnung von der Rundreise?** und **🔬 Das Verfahren ist nicht das Problem**,
dann **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So lesen wir „Klasse“", expanded=True):
    st.markdown(
        """
1. **Entscheidungsfrage.** Klassen werden an Ja/Nein-Fragen definiert: „Gibt es eine Zuordnung mit Kosten höchstens K?“ bzw. „Gibt es eine Rundreise mit Kosten höchstens K?“. Die Optimierung ist die Suche nach dem kleinsten K.
2. **Aufwand als Funktion der Größe.** Wie viele Schritte braucht das beste bekannte Verfahren bei n Orten? Hier ein Schritt = ein Lesezugriff auf die Kostenmatrix. **Polynomial** heißt: wie n², n³ (Klasse P). **Exponentiell** heißt: wie 2ⁿ oder n!.
3. **Das Verfahren ist nicht das Problem.** Alle Zuordnungen aufzuzählen kostet n · n! Zugriffe, genauso wie alle Rundreisen aufzuzählen (n · (n−1)!). Die Ungarische Methode umgeht den Baum und kommt für die Zuordnung mit höchstens n³ aus. Für die Rundreise ist kein solches Verfahren bekannt; das beste exakte (Held–Karp) braucht rund 2ⁿ · n² und bleibt exponentiell.
4. **Vorsicht.** „NP-schwer“ ist eine Aussage unter der Annahme P ≠ NP, die bis heute unbewiesen ist. „Kein polynomiales Verfahren bekannt“ ist keine Aussage, dass es unmöglich ist.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Matrix**")
    n = st.slider("Zahl der Orte n", *bounds("n_slider"), key="n_slider", help="Orte bzw. Fahrzeuge und Aufträge. Bei Aufzählen reicht das Budget schon ab n = 9 bis 11 nicht mehr.")
    kind = st.radio("Art der Kosten", list(C.KINDS), format_func=C.KINDS.get, key="kind_radio",
                    help="Karte: Entfernungen zwischen zufälligen Orten (symmetrisch). Zufallsmatrix: ganze Zahlen von 1 bis 100, in jede Richtung anders.")
    seed = st.number_input("Zufalls-Seed der Matrix", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Matrix generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Verfahren und Budget**")
    assign = st.selectbox("Verfahren für die Zuordnung", list(C.ASSIGN_METHODS), format_func=C.ASSIGN_METHODS.get, key="assign_select",
                          help="Ungarische Methode: höchstens n³ Zugriffe. Aufzählen: n · n! Zugriffe.")
    tour = st.selectbox("Verfahren für die Rundreise", list(C.TOUR_METHODS), format_func=C.TOUR_METHODS.get, key="tour_select",
                        help="Held–Karp: (n−1)(n−2) · 2^(n−3) Übergänge plus 2(n−1). Aufzählen: n · (n−1)! Zugriffe.")
    budget = st.select_slider("Budget (Zugriffe je Verfahren)", options=list(C.BUDGETS), format_func=fmt_int, key="budget_select",
                              help="Ein Verfahren bricht ab, bevor es mehr Zugriffe auf die Kostenmatrix ausgibt.")

sync_query_params({"n_slider": int(n), "kind_radio": kind, "seed_input": int(seed), "assign_select": assign, "tour_select": tour, "budget_select": int(budget)})

settings = Settings(n=int(n), kind=kind, seed=int(seed), assign=assign, tour=tour, budget=int(budget))
a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Dieselbe Matrix, zwei Fragen")
for message in validation_errors(a):
    st.error(message)

left, right = st.columns(2)
with left:
    st.markdown(f"### Zuordnung: {C.ASSIGN_METHODS[assign]}")
    r = a.assignment
    m1, m2, m3 = st.columns(3)
    m1.metric("Kosten" if r.exact else "Kosten (bisher beste)", "–" if r.cost is None else fmt_int(r.cost),
              help="Summe der Kosten Fahrzeug i → Auftrag. Bei abgebrochenem Aufzählen: beste bisher gesehene Zuordnung, nicht bewiesen optimal.")
    m2.metric("Zugriffe", fmt_int(r.accesses))
    m3.metric("Teilkreise", "–" if a.cycles is None else str(len(a.cycles)), help="Die Zuordnung zerfällt in Kreise; eine Rundreise wäre ein einziger Kreis.")
    if r.plan is not None:
        st.plotly_chart(build_map(a.inst, assignment_edges(r.plan), edge_colors(assignment_edges(r.plan), a.cycles if a.cycles else [tuple(range(a.inst.n))])), width="stretch", key="map_assignment")
        st.caption("Jeder Pfeil: Fahrzeug an diesem Ort → Auftrag am Zielort. Farbe = Teilkreis." if a.cycles else "Bisher beste Zuordnung des abgebrochenen Laufs (Farben nur bei zu Ende gegangenem Lauf).")
    else:
        st.info("Noch keine zulässige Zuordnung gesehen: das Aufzählen ist abgebrochen, bevor es eine Permutation ohne Fixpunkt fand.")
with right:
    st.markdown(f"### Rundreise: {C.TOUR_METHODS[tour]}")
    t = a.tour
    m1, m2, m3 = st.columns(3)
    m1.metric("Kosten" if t.exact else "Kosten (bisher beste)", "–" if t.cost is None else fmt_int(t.cost),
              help="Summe der Kosten entlang der geschlossenen Reise. Bei abgebrochenem Aufzählen: beste bisher gesehene Reihenfolge, nicht bewiesen optimal.")
    m2.metric("Zugriffe", fmt_int(t.accesses))
    m3.metric("Lücke zur Zuordnung", "–" if a.gap is None else f"{fmt_num(a.gap)} %", help="Wie viel billiger die Zuordnung ist als die Rundreise (in Prozent der Rundreisekosten).")
    if t.plan is not None:
        st.plotly_chart(build_map(a.inst, tour_edges(t.plan), edge_colors(tour_edges(t.plan))), width="stretch", key="map_tour")
        st.caption("Rundreise ab O1: jeder Ort genau einmal, zurück zum Start." if t.exact else "Bisher beste Reihenfolge des abgebrochenen Laufs.")
    else:
        st.info("Held–Karp ist abgebrochen, bevor es eine Rundreise fertig hatte: es liefert erst am Ende ein Ergebnis.")

if a.inst.points is None:
    st.caption("Orte der Zufallsmatrix sind nur zur Übersicht auf einem Kreis angeordnet; die Entfernungen stehen in der Matrix, nicht im Bild.")

with st.expander("Kostenmatrix anzeigen"):
    header = [""] + [label(j) for j in range(a.inst.n)]
    rows = [[label(i)] + ["–" if i == j else str(a.inst.matrix[i][j]) for j in range(a.inst.n)] for i in range(a.inst.n)]
    st.markdown(_md_table(header, rows))

if st.button("📄 PDF erstellen"):
    st.session_state["pdf_for"] = settings
if st.session_state.get("pdf_for") == settings:
    st.download_button("⬇️ PDF herunterladen", data=_pdf(settings), file_name="zuordnung-gegen-rundreise.pdf", mime="application/pdf")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie weit ist die billigste Zuordnung von einer Rundreise entfernt?")
vkind, vtext = verdict_main(a)
getattr(st, vkind)(vtext)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie weit kommt man mit einem Budget?")
growth = _growth()
st.caption("Zugriffe auf die Kostenmatrix über n (logarithmische Achse). Aufzählen und Held–Karp aus den Zählformeln (im Test gegen gezählte Läufe geprüft), "
           "Ungarisch als Schranke n³ und als gemessener Median über fünf feste Zufallsmatrizen. Die gestrichelte graue Linie ist das Budget aus der Seitenleiste.")
st.plotly_chart(build_growth(growth, settings.budget), width="stretch", key="growth_chart")
frontier = frontier_rows()
st.markdown("**Größtes n, das in das Budget passt**, rein aus den Zählformeln; „×1000“ ist tausendfach schnellere Hardware:")
header = ["Budget (Zugriffe)"] + [METHOD_LABELS[m] for m in frontier[0]["n"]]
table_rows = []
for fr in frontier:
    table_rows.append([fmt_int(fr["budget"])] + [fmt_int(fr["n"][m]) for m in fr["n"]])
    table_rows.append([f"{fmt_int(fr['budget'])} × {fmt_int(C.HARDWARE_FACTOR)}"] + [fmt_int(fr["n_fast"][m]) for m in fr["n"]])
st.markdown(_md_table(header, table_rows))
vkind, vtext = verdict_frontier(frontier)
getattr(st, vkind)(vtext)

st.markdown("---")

st.subheader("🔬 Experiment: Wie weit ist die Zuordnung von der Rundreise?")
with st.spinner("Rechne die Messreihe (20 feste Matrizen je Größe, beide Matrixarten) …"):
    gap_rows = _gap_rows()
st.caption("Median und Maximum über 20 feste Matrizen (SWEEP_SEEDS) je Größe; beide Probleme exakt gelöst (Ungarisch und Held–Karp). Die Lücke ist die Zuordnung als Anteil der Rundreisekosten unterhalb.")
st.plotly_chart(build_gap(gap_rows), width="stretch", key="gap_chart")
gap_header = ["n", "Karte: Lücke (Median)", "Karte: Teilkreise (Median)", "Karte: schon eine Rundreise", "Zufall: Lücke (Median)", "Zufall: Teilkreise (Median)", "Zufall: schon eine Rundreise"]
gap_table = []
for e, z in zip(gap_rows["euclid"], gap_rows["random"]):
    gap_table.append([e["n"], f"{fmt_num(e['gap_median'])} %", fmt_num(e["cycles_median"], 0), f"{e['one_cycle']} von {e['count']}",
                      f"{fmt_num(z['gap_median'])} %", fmt_num(z["cycles_median"], 0), f"{z['one_cycle']} von {z['count']}"])
st.markdown(_md_table(gap_header, gap_table))
vkind, vtext = verdict_gap(gap_rows)
getattr(st, vkind)(vtext)

st.markdown("---")

st.subheader("🔬 Experiment: Das Verfahren ist nicht das Problem")
st.caption("Dasselbe Problem, zwei Verfahren. Bei der Zuordnung ändert der Wechsel die Wachstumsart (exponentiell → polynomial), bei der Rundreise nur den Exponentialfaktor (n! → 2ⁿ).")
size = st.select_slider("Zahl der Orte für den Vergleich", options=list(C.N_GROWTH), value=12, key="compare_n")
row = next(r for r in growth if r["n"] == size)
st.markdown(_md_table(
    ["Problem", "Aufzählen", "bestes Verfahren", "Faktor"],
    [
        ["Zuordnung", fmt_int(row["enum_assignment"]), f"Ungarisch: Schranke {fmt_int(row['hungarian_bound'])}, gemessen {fmt_int(round(row['hungarian_measured']))}", f"{fmt_int(round(row['enum_assignment'] / row['hungarian_bound']))}-fach (gegen Schranke)"],
        ["Rundreise", fmt_int(row["enum_tour"]), f"Held–Karp: {fmt_int(row['held_karp'])}", f"{fmt_int(round(row['enum_tour'] / row['held_karp']))}-fach"],
    ],
))
vkind, vtext = verdict_methods(row)
getattr(st, vkind)(vtext)
scaling = _scaling()
st.markdown("**Gemessenes Wachstum der Ungarischen Methode** (Zufallsmatrizen, Median über fünf feste Matrizen) gegen die Schranke n³:")
st.plotly_chart(build_scaling(scaling), width="stretch", key="scaling_chart")
vkind, vtext = verdict_scaling(scaling)
getattr(st, vkind)(vtext)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Zugriffe auf die Matrix sind der Aufwand** | Zugriffe sind keine Laufzeit: Speicher, Python-Overhead und Cache-Verhalten fehlen. Die Zählung vergleicht Verfahren, nicht Rechner. | – |
| **n! und 2ⁿ sind Eigenschaften der Verfahren** | Dass die Rundreise „n! oder 2ⁿ“ braucht, sagt die Demo nur über Aufzählen und Held–Karp. Dass **kein** schnelleres Verfahren existiert, ist unbewiesen. | Stück 3 (Reduktionen) ordnet die Rundreise über NP-Vollständigkeit ein |
| **NP-schwer heißt: unter P ≠ NP nicht polynomial lösbar** | Die Aussage hängt an einer unbewiesenen Annahme und gilt für den schlimmsten Fall, nicht für jede Instanz. | Stück 4 (SAT-Phasenübergang) und die Härte-und-Struktur-Reihe |
| **In P heißt schnell** | Polynomial ist nicht gleich praktisch schnell: die Schranke n³ der Ungarischen Methode ist ein schlimmster Fall, gemessen wächst sie hier deutlich langsamer, und andere polynomiale Verfahren (Ellipsoid-Methode) sind in der Praxis langsam. | `ellipsoid-demo`, `klee-minty-demo` (Lineare-Programmierung-Reihe) |
| **Zwei Matrixarten stehen für „typisch“** | Karte und Zufallsmatrix sind Instanzfamilien. Die Lücke zwischen Zuordnung und Rundreise ist eine Aussage über diese Familien, kein Naturgesetz. | – |
| **Ein schlimmster Fall der Ungarischen Methode wird nicht gezeigt** | Die Schranke n³ wird auf diesen Matrizen nicht erreicht; eine gezielt gebaute Familie wird nicht vorgeführt. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ist eine Kostenmatrix $c_{ij}$ für $i, j \in \{1, \dots, n\}$; die Diagonale ist gesperrt ($c_{ii} = \infty$, in der Demo $10^6$).

**Zuordnung.** Gesucht ist eine Permutation $\sigma$ ohne Fixpunkt mit minimalen Kosten:
"""
    )
    st.latex(r"\min_{\sigma} \sum_{i=1}^{n} c_{i\,\sigma(i)}")
    st.markdown(
        r"""
Als lineares Programm mit $x_{ij} \ge 0$, Zeilensummen $=1$ und Spaltensummen $=1$ liegen die Ecken des zulässigen Bereichs bei ganzen Zahlen (Satz von Birkhoff und von Neumann): das Zuordnungsproblem ist ein LP, also gilt $\text{OPT}_{\text{Zuordnung}}$ polynomial berechenbar, die Ungarische Methode mit höchstens $O(n^3)$ Schritten.

**Rundreise.** Gesucht ist eine zyklische Reihenfolge $\pi$ aller Orte mit minimalen Kosten:
"""
    )
    st.latex(r"\min_{\pi} \sum_{i=1}^{n} c_{\pi(i)\,\pi(i+1)} \quad (\pi(n+1) = \pi(1))")
    st.markdown(
        r"""
Jede Rundreise ist eine Zuordnung mit **einem einzigen Kreis**. Verlangt man nur „jeder Ort hat einen Nachfolger und einen Vorgänger“, bleibt die Zuordnung, die mehrere Kreise haben darf. Daraus folgt
"""
    )
    st.latex(r"\text{OPT}_{\text{Zuordnung}} \;\le\; \text{OPT}_{\text{Rundreise}}")
    st.markdown(
        r"""
mit Gleichheit, wenn die billigste Zuordnung selbst ein einziger Kreis ist.

**Held–Karp.** Sei $D(S, j)$ der billigste Weg von Ort 1 über alle Orte der Menge $S \subseteq \{2, \dots, n\}$, der in $j \in S$ endet:
"""
    )
    st.latex(r"D(\{j\}, j) = c_{1j}, \qquad D(S, j) = \min_{k \in S \setminus \{j\}} \big( D(S \setminus \{j\}, k) + c_{kj} \big)")
    st.latex(r"\text{OPT}_{\text{Rundreise}} = \min_{j} \big( D(\{2, \dots, n\}, j) + c_{j1} \big)")
    st.markdown(
        r"""
**Zugriffe.** Die Demo zählt jeden Lesezugriff auf $c_{ij}$:
"""
    )
    st.latex(r"\text{Aufzählen (Zuordnung)}: n \cdot n! \qquad \text{Aufzählen (Rundreise)}: n \cdot (n-1)! \qquad \text{Held–Karp}: (n-1)(n-2)\,2^{\,n-3} + 2(n-1)")

    st.markdown(
        """
| Annahme | Bedeutung | Wer setzt an |
|---|---|---|
| Diagonale gesperrt | kein Fahrzeug fährt zu sich selbst, keine Rundreise bleibt am Ort | – |
| Start bei Ort 1 | jede Rundreise lässt sich zyklisch so drehen; das spart den Faktor n | – |
| Ganzzahlige Kosten | exakter Vergleich der Kosten; Karten-Entfernungen sind auf ganze Zahlen gerundet | – |
| Rundreise exakt | nur exakte Verfahren; Heuristiken sind nicht Gegenstand dieses Stücks | `lin-kernighan-demo` und die Trajektorien-Metaheuristiken |

**Folgestücke.** Stück 3 der Reihe (Reduktionen, mit Zertifikaten) ordnet die Rundreise über NP-Vollständigkeit ein: sie zeigt, wie sich Probleme aufeinander zurückführen lassen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)

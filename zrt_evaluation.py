"""Kennzahlen, Verdikt-Logik und Sweeps (alle Verdikte sind reine Funktionen (Art, Text), DEMO-PLAYBOOK §12)."""

from dataclasses import dataclass
from statistics import median

import numpy as np

import zrt_algorithm as A
import zrt_constants as C
from zrt_scenario import Instance, make_instance


@dataclass(frozen=True, kw_only=True)
class Settings:
    n: int = C.DEFAULT_N
    kind: str = C.DEFAULT_KIND
    seed: int = C.DEFAULT_SEED
    assign: str = C.DEFAULT_ASSIGN
    tour: str = C.DEFAULT_TOUR
    budget: int = C.DEFAULT_BUDGET


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    inst: Instance
    assignment: A.Result
    tour: A.Result
    cycles: tuple[tuple[int, ...], ...] | None   # Teilkreise der Zuordnung (nur bei vollständigem Lauf)
    gap: float | None                            # Prozent der Rundreisekosten; nur wenn beide Läufe zu Ende gingen


# Zählformeln je Verfahren; die Schlüssel stehen in Tabellen und Diagrammen
METHOD_ACCESSES = {
    "enum_assignment": A.accesses_enumerate_assignment,
    "enum_tour": A.accesses_enumerate_tour,
    "held_karp": A.accesses_held_karp,
    "hungarian": A.accesses_hungarian_bound,
}
METHOD_LABELS = {
    "enum_assignment": "Zuordnung: Aufzählen",
    "enum_tour": "Rundreise: Aufzählen",
    "held_karp": "Rundreise: Held–Karp",
    "hungarian": "Zuordnung: Ungarisch (Schranke n³)",
}


# --- Zahlen im deutschen Format ------------------------------------------------------------------------------------------------------------------


def fmt_int(n: int) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner (1.720.350)."""
    return f"{n:,}".replace(",", ".")


def fmt_num(x: float, digits: int = 1) -> str:
    """Dezimalzahl mit Komma (22,7)."""
    return f"{x:.{digits}f}".replace(".", ",")


# --- Einzelanalyse -------------------------------------------------------------------------------------------------------------------------------


def relaxation_gap(assignment_cost: int, tour_cost: int) -> float:
    """Wie viel billiger die Zuordnung ist als die Rundreise, in Prozent der Rundreisekosten (Basis ist die teurere). Ohne Kosten (Nenner 0) gibt es keine Lücke."""
    return 0.0 if tour_cost <= 0 else 100.0 * (tour_cost - assignment_cost) / tour_cost


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.n, settings.kind, settings.seed)
    assignment = A.solve_assignment(inst, settings.assign, settings.budget)
    tour = A.solve_tour(inst, settings.tour, settings.budget)
    cycles = tuple(A.cycles_of_assignment(assignment.plan)) if assignment.exact else None
    gap = relaxation_gap(assignment.cost, tour.cost) if assignment.exact and tour.exact else None
    return Analysis(settings, inst, assignment, tour, cycles, gap)


def validation_errors(a: Analysis) -> list[str]:
    """Ergebnis vor der Anzeige prüfen (DEMO-PLAYBOOK §1d): unabhängiger Prüfer und neu berechnete Kosten."""
    errors = []
    r = a.assignment
    if r.plan is not None:
        if not A.check_feasible_assignment(a.inst, r.plan):
            errors.append("Die Zuordnung ist keine Permutation ohne Fixpunkt.")
        elif A.assignment_cost(a.inst, r.plan) != r.cost:
            errors.append("Die Kosten der Zuordnung stimmen nicht mit der Neuberechnung überein.")
    t = a.tour
    if t.plan is not None:
        if not A.check_feasible_tour(a.inst, t.plan):
            errors.append("Die Rundreise besucht nicht jeden Ort genau einmal ab Ort 1.")
        elif A.tour_cost(a.inst, t.plan) != t.cost:
            errors.append("Die Kosten der Rundreise stimmen nicht mit der Neuberechnung überein.")
    if a.gap is not None and a.gap < 0:
        errors.append("Die Zuordnung ist teurer als die Rundreise: das darf nicht sein.")
    return errors


# --- Messreihen ----------------------------------------------------------------------------------------------------------------------------------


def sweep_gap(kind: str, sizes=C.N_GAP, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Lücke Zuordnung -> Rundreise und Teilkreise über die Größe: Median über die festen Instanzen SWEEP_SEEDS (nie ein einzelner Seed)."""
    rows = []
    for n in sizes:
        gaps, cycle_counts = [], []
        for seed in seeds:
            inst = make_instance(n, kind, seed)
            h = A.hungarian(inst)
            k = A.held_karp(inst)
            gaps.append(relaxation_gap(h.cost, k.cost))
            cycle_counts.append(len(A.cycles_of_assignment(h.plan)))
        rows.append({
            "n": n, "kind": kind, "count": len(seeds),
            "gap_median": median(gaps), "gap_max": max(gaps),
            "cycles_median": median(cycle_counts),
            "one_cycle": sum(1 for c in cycle_counts if c == 1),
        })
    return rows


def hungarian_scaling(kind: str = "random", sizes=C.N_HUNGARIAN, seeds=C.GROWTH_SEEDS) -> list[dict]:
    """Gemessene Zugriffe der Ungarischen Methode über n (Median über feste Instanzen) neben der Schranke n^3."""
    rows = []
    for n in sizes:
        values = [A.hungarian(make_instance(n, kind, seed)).accesses for seed in seeds]
        rows.append({"n": n, "accesses": median(values), "bound": A.accesses_hungarian_bound(n)})
    return rows


def loglog_slope(rows: list[dict]) -> float:
    """Steigung der Ausgleichsgeraden im doppelt-logarithmischen Diagramm (Zugriffe gegen n): das gemessene „Exponent-Gefühl“."""
    xs = np.log([r["n"] for r in rows])
    ys = np.log([r["accesses"] for r in rows])
    return float(np.polyfit(xs, ys, 1)[0])


def growth_rows(sizes=C.N_GROWTH, kind: str = "random", seeds=C.GROWTH_SEEDS) -> list[dict]:
    """Zugriffe je Verfahren über n: Formeln für Aufzählen und Held–Karp, Schranke n^3 und gemessener Median für die Ungarische Methode."""
    rows = []
    for n in sizes:
        measured = median(A.hungarian(make_instance(n, kind, seed)).accesses for seed in seeds)
        rows.append({
            "n": n,
            "enum_assignment": A.accesses_enumerate_assignment(n),
            "enum_tour": A.accesses_enumerate_tour(n),
            "held_karp": A.accesses_held_karp(n),
            "hungarian_bound": A.accesses_hungarian_bound(n),
            "hungarian_measured": measured,
        })
    return rows


def frontier_rows(budgets=C.FRONTIER_BUDGETS, factor: int = C.HARDWARE_FACTOR) -> list[dict]:
    """Größtes n im Budget B und im `factor`-fachen Budget (tausendfach schnellere Hardware), rein aus den Zählformeln."""
    rows = []
    for budget in budgets:
        rows.append({
            "budget": budget,
            "n": {m: A.budget_frontier(fn, budget) for m, fn in METHOD_ACCESSES.items()},
            "n_fast": {m: A.budget_frontier(fn, budget * factor) for m, fn in METHOD_ACCESSES.items()},
        })
    return rows


def step_factor(method: str, n: int) -> float:
    """Faktor, um den der Aufwand wächst, wenn ein Ort hinzukommt: Aufzählen ~ n, Held–Karp -> 2, Schranke n^3 -> (1 + 1/n)^3."""
    fn = METHOD_ACCESSES[method]
    return fn(n) / fn(n - 1)


# --- Verdikte (rein) -----------------------------------------------------------------------------------------------------------------------------


def verdict_main(a: Analysis) -> tuple[str, str]:
    """Kernergebnis: Lücke und Teilkreise, oder Abbruch durch das Budget."""
    s = a.settings
    parts = []
    for name, r, label in (("Zuordnung", a.assignment, C.ASSIGN_METHODS[s.assign]), ("Rundreise", a.tour, C.TOUR_METHODS[s.tour])):
        if not r.exact:
            parts.append(f"die {name} brach nach {fmt_int(r.accesses)} Zugriffen ab (Verfahren: {label})")
    if parts:
        parts[0] = parts[0][0].upper() + parts[0][1:]
        return "warning", (f"Das Budget von {fmt_int(s.budget)} Zugriffen reicht nicht. " + "; ".join(parts) + ". "
                           "Erhöhen Sie das Budget oder wechseln Sie zu einem Verfahren, das den Baum umgeht.")
    k = len(a.cycles)
    ac, tc = a.assignment.cost, a.tour.cost
    if k == 1 and a.gap == 0:
        return "success", f"Die billigste Zuordnung ist hier zugleich eine Rundreise (ein einziger Kreis): beide kosten {fmt_int(ac)}."
    if a.gap == 0:
        return "info", (f"Zuordnung und Rundreise kosten beide {fmt_int(ac)}, obwohl die Zuordnung in {k} Teilkreisen läuft: "
                        "eine gleich billige Rundreise existiert (Gleichstand).")
    return "info", (f"Die billigste Zuordnung kostet {fmt_int(ac)}, die beste Rundreise {fmt_int(tc)}: die Zuordnung ist **{fmt_num(a.gap)} %** billiger, "
                    f"weil sie in {k} Teilkreisen läuft statt in einem einzigen Kreis.")


def verdict_frontier(rows: list[dict]) -> tuple[str, str]:
    """Wirkung tausendfacher Hardware auf das größte lösbare n (erste Zeile = kleinstes Budget)."""
    r = rows[0]
    n, f = r["n"], r["n_fast"]
    return "info", (
        f"Mit {fmt_int(r['budget'])} Zugriffen kommt das Aufzählen der Rundreisen bis n = {n['enum_tour']}, Held–Karp bis n = {n['held_karp']}, "
        f"die Ungarische Methode (nach der Schranke n³) bis n = {n['hungarian']}. Mit tausendfachem Budget wächst n beim Aufzählen um {f['enum_tour'] - n['enum_tour']} "
        f"und bei Held–Karp um {f['held_karp'] - n['held_karp']} (**additiv**); bei der Ungarischen Methode steigt es von {fmt_int(n['hungarian'])} auf {fmt_int(f['hungarian'])}, "
        f"also auf das {fmt_num(f['hungarian'] / n['hungarian'], 0)}-Fache (**multiplikativ**)."
    )


def verdict_gap(rows_by_kind: dict[str, list[dict]]) -> tuple[str, str]:
    """Wie weit die Zuordnung unter der Rundreise liegt: größte gemessene Größe, Karte gegen Zufallsmatrix."""
    e, r = rows_by_kind["euclid"][-1], rows_by_kind["random"][-1]
    return "info", (
        f"Bei n = {e['n']} liegt die billigste Zuordnung auf der Karte im Median **{fmt_num(e['gap_median'])} %** unter der besten Rundreise "
        f"(Zufallsmatrix: {fmt_num(r['gap_median'])} %). Sie hat dabei im Median {fmt_num(e['cycles_median'], 0)} Teilkreise (Zufallsmatrix: {fmt_num(r['cycles_median'], 0)}); "
        f"nur in {e['one_cycle']} von {e['count']} Karten (Zufallsmatrix: {r['one_cycle']} von {r['count']}) ist sie schon eine Rundreise."
    )


def verdict_methods(row: dict) -> tuple[str, str]:
    """Dasselbe Problem, zwei Verfahren: Zugriffe bei einer Größe n."""
    n = row["n"]
    ratio = row["enum_tour"] / row["held_karp"]
    fewer = "kaum weniger" if ratio < 2 else f"{fmt_int(round(ratio))}-mal weniger"
    return "info", (
        f"Bei n = {n} liest das Aufzählen aller Zuordnungen {fmt_int(row['enum_assignment'])} Matrixeinträge, die Ungarische Methode höchstens {fmt_int(row['hungarian_bound'])} "
        f"(gemessen im Median {fmt_int(round(row['hungarian_measured']))}). Für die Rundreise sind es {fmt_int(row['enum_tour'])} beim Aufzählen und {fmt_int(row['held_karp'])} bei Held–Karp, "
        f"also {fewer}, aber jeder zusätzliche Ort verteuert Held–Karp weiter etwa auf das Doppelte "
        f"(von n = {n - 1} auf n = {n}: Faktor {fmt_num(step_factor('held_karp', n), 2)}), die Ungarische Methode nur nach der Schranke auf das {fmt_num(step_factor('hungarian', n), 2)}-Fache."
    )


def verdict_scaling(rows: list[dict]) -> tuple[str, str]:
    """Gemessener Exponent der Ungarischen Methode gegen die Schranke n^3."""
    slope = loglog_slope(rows)
    last = rows[-1]
    return "info", (
        f"Auf Zufallsmatrizen wächst die Zahl der Zugriffe der Ungarischen Methode etwa wie n^{fmt_num(slope, 2)} (Ausgleichsgerade über n = {rows[0]['n']} bis {last['n']}); "
        f"bei n = {last['n']} sind es im Median {fmt_int(round(last['accesses']))} Zugriffe, die Schranke n³ liegt bei {fmt_int(last['bound'])}. "
        "Die Schranke gilt für den schlimmsten Fall und wird auf diesen Matrizen weit unterschritten."
    )

"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets.

Komplexität am Regler-Maximum (DEMO-PLAYBOOK §1c): n = 16 bedeutet für Held–Karp rund 1,7 Mio. Zugriffe (15 · 14 · 2^13 + 30), für das Aufzählen aller
Rundreisen 16 · 15! (weit über jedem Budget, die App bricht beim Budget ab), für die Ungarische Methode höchstens 16^3 = 4096 Zugriffe."""

N_MIN, N_MAX, DEFAULT_N = 4, 16, 8
SEED_MAX, DEFAULT_SEED = 999999, 35
FORBIDDEN = 10 ** 6                        # Kosten der Diagonale: kein Fahrzeug fährt zu sich selbst, keine Rundreise bleibt am Ort
COORD_MAX = 100                            # Orte der Karte liegen in [0, 100] x [0, 100]
COST_LOW, COST_HIGH = 1, 100               # Zufallsmatrix: ganzzahlige Kosten, gleichverteilt

KINDS = {"euclid": "Karte (Entfernungen)", "random": "Zufallsmatrix (1 bis 100)"}
DEFAULT_KIND = "euclid"
ASSIGN_METHODS = {"hungarian": "Ungarische Methode", "enumerate": "Aufzählen aller Zuordnungen"}
DEFAULT_ASSIGN = "hungarian"
TOUR_METHODS = {"held_karp": "Held–Karp (Teilmengen-DP)", "enumerate": "Aufzählen aller Rundreisen"}
DEFAULT_TOUR = "held_karp"
BUDGETS = (10_000, 100_000, 1_000_000, 3_000_000)   # Zugriffe auf die Kostenmatrix, die ein Verfahren höchstens ausgeben darf
DEFAULT_BUDGET = 1_000_000

SWEEP_SEEDS = tuple(range(100000, 100020))  # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund
GROWTH_SEEDS = SWEEP_SEEDS[:5]              # Wachstum der Ungarischen Methode (große n): fünf feste Instanzen genügen
N_GAP = (4, 6, 8, 10, 12)                   # Größen der Lücken-Messreihe (Held–Karp bei n = 12: rund 56 000 Zugriffe je Instanz)
N_GROWTH = (4, 6, 8, 10, 12, 14, 16)        # Größen der Wachstumstabelle (Formeln)
N_HUNGARIAN = (10, 20, 40, 80, 160)         # Größen für das gemessene Wachstum der Ungarischen Methode
FRONTIER_BUDGETS = (10 ** 6, 10 ** 8, 10 ** 9)
HARDWARE_FACTOR = 1000                      # „tausendfach schnellere Hardware“ = tausendfaches Budget

COLOR_TOUR = "#C0392B"
COLOR_CYCLES = ("#2F6B65", "#4C78A8", "#B8860B", "#8E44AD", "#D35400", "#16A085", "#7F8C8D", "#C0392B")
COLOR_LINE = "#4c78a8"
COLOR_NODE = "#34495E"

PRESETS = {
    "Standardfall (Voreinstellung)": {"n": DEFAULT_N, "kind": "euclid", "seed": DEFAULT_SEED, "assign": "hungarian", "tour": "held_karp", "budget": DEFAULT_BUDGET},
    "Zufallsmatrix statt Karte": {"n": 10, "kind": "random", "seed": DEFAULT_SEED, "assign": "hungarian", "tour": "held_karp", "budget": DEFAULT_BUDGET},
    "Aufzählen stößt an die Grenze": {"n": 11, "kind": "euclid", "seed": DEFAULT_SEED, "assign": "enumerate", "tour": "enumerate", "budget": DEFAULT_BUDGET},
    "Held–Karp am Rand": {"n": N_MAX, "kind": "euclid", "seed": DEFAULT_SEED, "assign": "hungarian", "tour": "held_karp", "budget": 3_000_000},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "8 Orte auf einer Karte: Ungarische Methode für die Zuordnung, Held–Karp für die Rundreise. Die billigste Zuordnung zerfällt meist in mehrere Teilkreise.",
    "Zufallsmatrix statt Karte": "10 Orte mit zufälligen Kosten statt Entfernungen: die Lücke zwischen Zuordnung und Rundreise ist hier meist kleiner.",
    "Aufzählen stößt an die Grenze": "11 Orte, beide Probleme durch Aufzählen: schon n = 11 braucht mehr Zugriffe als das Budget erlaubt, beide Läufe brechen ab.",
    "Held–Karp am Rand": "16 Orte, größte Größe: Held–Karp braucht rund 1,7 Mio. Zugriffe, die Ungarische Methode höchstens 4096; das Budget ist auf 3 Mio. gestellt.",
}

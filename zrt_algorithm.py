"""Kern der Demo (reines Python): Zuordnung und Rundreise auf derselben Kostenmatrix, gezählt in Zugriffen auf die Matrix.

Einheit des Aufwands ist ein **Zugriff auf die Kostenmatrix** (`matrix[i][j]` gelesen), nicht die Laufzeit. Jede Regel ist eine eigene Funktion mit expliziten
Ein- und Ausgaben (DEMO-PLAYBOOK §1b); `solve_assignment` und `solve_tour` rufen nur der Reihe nach auf.

Verfahren und Zugriffe:
- Zuordnung, Aufzählen: n! Permutationen, je n Zugriffe, also n · n!.
- Zuordnung, Ungarische Methode: Zugriff je Kandidatenprüfung; gezählt, Schranke n^3.
- Rundreise, Aufzählen: (n-1)! Reihenfolgen ab Ort 0, je n Zugriffe, also n · (n-1)!.
- Rundreise, Held–Karp: ein Zugriff je Übergang, insgesamt (n-1)(n-2) 2^(n-3) + 2(n-1)."""

import itertools
import math
from dataclasses import dataclass

import zrt_constants as C
from zrt_scenario import Instance


@dataclass(frozen=True)
class Result:
    method: str
    cost: int | None           # None: keine zulässige Lösung gefunden (Budget erreicht oder gar nicht lösbar)
    plan: tuple[int, ...] | None  # Zuordnung: plan[i] = Auftrag von Fahrzeug i; Rundreise: Reihenfolge der Orte ab Ort 0
    accesses: int              # Zugriffe auf die Kostenmatrix
    finished: bool             # False: Budget erreicht, cost/plan sind höchstens die beste bisher gesehene Lösung

    @property
    def exact(self) -> bool:
        """Optimal bewiesen: der Lauf ist zu Ende gegangen und hat eine Lösung gefunden."""
        return self.finished and self.cost is not None


# --- Kosten und Prüfer ---------------------------------------------------------------------------------------------------------------------------


def assignment_cost(inst: Instance, sigma) -> int:
    """Summe der Kosten Fahrzeug i -> Auftrag sigma[i] (jedes Ziel zählt für sich, der Nachbar spielt keine Rolle)."""
    return sum(inst.matrix[i][sigma[i]] for i in range(len(sigma)))


def tour_cost(inst: Instance, order) -> int:
    """Summe der Kosten entlang der geschlossenen Rundreise (jedes Paar aufeinanderfolgender Orte zählt, zurück zum Start eingeschlossen)."""
    n = len(order)
    if n < 2:
        return 0
    return sum(inst.matrix[order[i]][order[(i + 1) % n]] for i in range(n))


def check_feasible_assignment(inst: Instance, sigma) -> bool:
    """Eine Permutation ohne Fixpunkt: jedes Fahrzeug bekommt genau einen anderen Auftrag, jeder Auftrag genau ein Fahrzeug."""
    sigma = tuple(sigma)
    return len(sigma) == inst.n and sorted(sigma) == list(range(inst.n)) and all(sigma[i] != i for i in range(inst.n))


def check_feasible_tour(inst: Instance, order) -> bool:
    """Jeder Ort genau einmal, Start bei Ort 0."""
    order = tuple(order)
    return len(order) == inst.n and sorted(order) == list(range(inst.n)) and (inst.n == 0 or order[0] == 0)


def cycles_of_assignment(sigma) -> list[tuple[int, ...]]:
    """Zerlegt die Zuordnung in Teilkreise (jeder beginnt beim kleinsten Ort, Reihenfolge nach dem kleinsten Ort)."""
    seen = [False] * len(sigma)
    cycles = []
    for start in range(len(sigma)):
        if seen[start]:
            continue
        cycle = []
        x = start
        while not seen[x]:
            seen[x] = True
            cycle.append(x)
            x = sigma[x]
        cycles.append(tuple(cycle))
    return cycles


# --- Zählformeln (geschlossen) -------------------------------------------------------------------------------------------------------------------


def accesses_enumerate_assignment(n: int) -> int:
    """n · n! Zugriffe: n! Permutationen, jede liest n Matrixeinträge."""
    return n * math.factorial(n) if n >= 1 else 0


def accesses_enumerate_tour(n: int) -> int:
    """n · (n-1)! Zugriffe: (n-1)! Reihenfolgen ab Ort 0, jede liest n Matrixeinträge (n = 1: keine Kante)."""
    return n * math.factorial(n - 1) if n >= 2 else 0


def accesses_held_karp(n: int) -> int:
    """(n-1)(n-2) 2^(n-3) Übergänge plus n-1 Startkanten plus n-1 Rückkanten (n = 2: 2, n = 1: 0)."""
    if n >= 3:
        return (n - 1) * (n - 2) * 2 ** (n - 3) + 2 * (n - 1)
    return 2 if n == 2 else 0


def accesses_hungarian_bound(n: int) -> int:
    """Obere Schranke n^3 der Ungarischen Methode (Schranke, keine Messung)."""
    return n ** 3


def budget_frontier(accesses_fn, budget: int, n_cap: int = 100000) -> int:
    """Größtes n, dessen Zugriffszahl `accesses_fn(n)` das Budget nicht übersteigt (0, wenn schon n = 1 nicht passt). Die Funktion wächst mit n."""
    n = 0
    while n < n_cap and accesses_fn(n + 1) <= budget:
        n += 1
    return n


# --- Zuordnung -----------------------------------------------------------------------------------------------------------------------------------


def enumerate_assignments(inst: Instance, budget: int | None = None) -> Result:
    """Alle n! Permutationen, je n Zugriffe; behält die billigste Permutation ohne Fixpunkt. Bricht ab, wenn das nächste n Zugriffe das Budget überschritten."""
    n = inst.n
    m = inst.matrix
    accesses = 0
    best_cost = None
    best_plan = None
    for sigma in itertools.permutations(range(n)):
        if budget is not None and accesses + n > budget:
            return Result("enumerate", best_cost, best_plan, accesses, False)
        accesses += n
        cost = sum(m[i][sigma[i]] for i in range(n))
        if cost < C.FORBIDDEN and (best_cost is None or cost < best_cost):
            best_cost, best_plan = cost, sigma
    return Result("enumerate", best_cost, best_plan, accesses, True)


def hungarian(inst: Instance) -> Result:
    """Ungarische Methode (Potenziale, kürzeste Verbesserungswege), O(n^3). Ein Zugriff je geprüftem Kandidaten (Spalte, die noch nicht im Baum ist)."""
    n = inst.n
    if n < 2:
        return Result("hungarian", None, None, 0, True)
    a = inst.matrix
    u = [0] * (n + 1)
    v = [0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)
    accesses = 0
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [math.inf] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = math.inf
            j1 = 0
            for j in range(1, n + 1):
                if not used[j]:
                    accesses += 1
                    cur = a[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    sigma = [0] * n
    for j in range(1, n + 1):
        sigma[p[j] - 1] = j - 1
    return Result("hungarian", assignment_cost(inst, sigma), tuple(sigma), accesses, True)


# --- Rundreise -----------------------------------------------------------------------------------------------------------------------------------


def enumerate_tours(inst: Instance, budget: int | None = None) -> Result:
    """Alle (n-1)! Reihenfolgen ab Ort 0, je n Zugriffe. Bricht ab, wenn die nächste Reihenfolge das Budget überschritte."""
    n = inst.n
    if n < 2:
        return Result("enumerate", 0, (0,) if n == 1 else (), 0, True)
    m = inst.matrix
    accesses = 0
    best_cost = None
    best_plan = None
    for rest in itertools.permutations(range(1, n)):
        if budget is not None and accesses + n > budget:
            return Result("enumerate", best_cost, best_plan, accesses, False)
        accesses += n
        order = (0,) + rest
        cost = sum(m[order[i]][order[(i + 1) % n]] for i in range(n))
        if best_cost is None or cost < best_cost:
            best_cost, best_plan = cost, order
    return Result("enumerate", best_cost, best_plan, accesses, True)


def held_karp(inst: Instance, budget: int | None = None) -> Result:
    """Held–Karp: billigster Weg von Ort 0 über eine Teilmenge S der Orte 1..n-1, der in j endet; ein Zugriff je Übergang. Bricht vor einem Schritt ab, der das Budget überschritte."""
    n = inst.n
    if n < 2:
        return Result("held_karp", 0, (0,) if n == 1 else (), 0, True)
    m = inst.matrix
    k = n - 1
    if budget is not None and k > budget:
        return Result("held_karp", None, None, 0, False)
    inf = math.inf
    dp: list = [None] * (1 << k)
    parent: list = [None] * (1 << k)
    accesses = 0
    for j in range(1, n):                                  # Startkanten 0 -> j
        mask = 1 << (j - 1)
        dp[mask] = [inf] * k
        dp[mask][j - 1] = m[0][j]
        parent[mask] = [0] * k
        accesses += 1
    for mask in range(1, 1 << k):
        size = bin(mask).count("1")
        if size < 2:
            continue
        if budget is not None and accesses + size * (size - 1) > budget:
            return Result("held_karp", None, None, accesses, False)
        row = [inf] * k
        par = [0] * k
        members = [j for j in range(1, n) if mask >> (j - 1) & 1]
        for j in members:
            prev_mask = mask & ~(1 << (j - 1))
            prev = dp[prev_mask]
            best = inf
            best_k = 0
            for kk in members:
                if kk == j:
                    continue
                accesses += 1
                value = prev[kk - 1] + m[kk][j]
                if value < best:
                    best, best_k = value, kk
            row[j - 1] = best
            par[j - 1] = best_k
        dp[mask] = row
        parent[mask] = par
    full = (1 << k) - 1
    if budget is not None and accesses + k > budget:
        return Result("held_karp", None, None, accesses, False)
    best = inf
    last = 1
    for j in range(1, n):                                  # Rückkanten j -> 0
        accesses += 1
        value = dp[full][j - 1] + m[j][0]
        if value < best:
            best, last = value, j
    order = []
    mask = full
    j = last
    while mask:
        order.append(j)
        prev_j = parent[mask][j - 1]
        mask &= ~(1 << (j - 1))
        j = prev_j
    order.append(0)
    order.reverse()
    return Result("held_karp", int(best), tuple(order), accesses, True)


# --- Komposition ---------------------------------------------------------------------------------------------------------------------------------


def solve_assignment(inst: Instance, method: str, budget: int | None = None) -> Result:
    if method == "hungarian":
        return hungarian(inst)
    if method == "enumerate":
        return enumerate_assignments(inst, budget)
    raise ValueError(f"unbekanntes Verfahren für die Zuordnung: {method}")


def solve_tour(inst: Instance, method: str, budget: int | None = None) -> Result:
    if method == "held_karp":
        return held_karp(inst, budget)
    if method == "enumerate":
        return enumerate_tours(inst, budget)
    raise ValueError(f"unbekanntes Verfahren für die Rundreise: {method}")

"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import zrt_constants as C
from zrt_scenario import Instance, label


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.22), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def node_positions(inst: Instance) -> list[tuple[float, float]]:
    """Orte der Karte, oder bei der Zufallsmatrix gleichmäßig auf einem Kreis (Entfernungen sind dort nicht maßstäblich; Ort 1 oben)."""
    if inst.points is not None:
        return [(x, y) for x, y in inst.points]
    n = inst.n
    return [(math.sin(2 * math.pi * i / n), math.cos(2 * math.pi * i / n)) for i in range(n)]


def edge_colors(edges, cycles=None) -> list[str]:
    """Farbe je Kante: bei der Zuordnung nach Teilkreis, sonst die Rundreisefarbe."""
    if cycles is None:
        return [C.COLOR_TOUR] * len(edges)
    cycle_of = {i: c for c, cycle in enumerate(cycles) for i in cycle}
    return [C.COLOR_CYCLES[cycle_of[i] % len(C.COLOR_CYCLES)] for i, _ in edges]


def assignment_edges(sigma) -> list[tuple[int, int]]:
    return [(i, sigma[i]) for i in range(len(sigma))]


def tour_edges(order) -> list[tuple[int, int]]:
    n = len(order)
    return [(order[i], order[(i + 1) % n]) for i in range(n)] if n >= 2 else []


def build_map(inst: Instance, edges, colors, key_hint: str = ""):
    """Orte mit gerichteten Kanten. Gegenläufige Kanten (zwei Orte tauschen) werden seitlich versetzt, damit beide Pfeile sichtbar bleiben."""
    pos = node_positions(inst)
    xs = [p[0] for p in pos]
    ys = [p[1] for p in pos]
    span = (max(xs) - min(xs)) or 1.0
    shorten = 0.045 * span                       # Pfeilspitze vor dem Ortspunkt enden lassen
    offset = 0.014 * span
    present = set(edges)
    fig = go.Figure()
    for (i, j), color in zip(edges, colors):
        (x0, y0), (x1, y1) = pos[i], pos[j]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        ux, uy = dx / length, dy / length
        px, py = -uy, ux                         # Normale zur Kante
        side = offset if (j, i) in present else 0.0
        ax, ay = x0 + ux * shorten * 0.4 + px * side, y0 + uy * shorten * 0.4 + py * side
        hx, hy = x1 - ux * shorten + px * side, y1 - uy * shorten + py * side
        fig.add_annotation(x=hx, y=hy, ax=ax, ay=ay, xref="x", yref="y", axref="x", ayref="y", showarrow=True,
                           arrowhead=3, arrowsize=1.1, arrowwidth=2.2, arrowcolor=color, text="")
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text", text=[label(i) for i in range(inst.n)], textposition="top center",
        marker=dict(size=13, color=C.COLOR_NODE, line=dict(width=1, color="white")),
        hovertemplate="%{text}<extra></extra>", showlegend=False,
    ))
    pad = 0.12 * span
    fig.update_xaxes(range=[min(xs) - pad, max(xs) + pad], visible=False)
    fig.update_yaxes(range=[min(ys) - pad, max(ys) + pad], visible=False)
    return _base(fig, 420)


def build_growth(rows, budget: int | None = None):
    """Zugriffe über n (log-Achse): Aufzählen, Held–Karp, Schranke n^3 und gemessener Median der Ungarischen Methode; optional das Budget als Linie."""
    xs = [r["n"] for r in rows]
    fig = go.Figure()
    series = (
        ("enum_assignment", "Zuordnung: Aufzählen (n · n!)", "#7F8C8D", "dot"),
        ("enum_tour", "Rundreise: Aufzählen (n · (n-1)!)", C.COLOR_TOUR, "solid"),
        ("held_karp", "Rundreise: Held–Karp", "#B8860B", "solid"),
        ("hungarian_bound", "Zuordnung: Schranke n³", C.COLOR_LINE, "dash"),
        ("hungarian_measured", "Zuordnung: Ungarisch, gemessen (Median)", C.COLOR_CYCLES[0], "solid"),
    )
    for key, name, color, dash in series:
        fig.add_trace(go.Scatter(x=xs, y=[max(r[key], 1) for r in rows], mode="lines+markers", name=name, line=dict(color=color, width=2.5, dash=dash),
                                 hovertemplate="n = %{x}: %{y:,.0f} Zugriffe<extra></extra>"))
    if budget:
        fig.add_hline(y=budget, line=dict(color="gray", width=1.5, dash="dot"), annotation_text="Budget", annotation_position="top left")
    fig.update_xaxes(title_text="Zahl der Orte n", dtick=2)
    fig.update_yaxes(title_text="Zugriffe auf die Kostenmatrix (log)", type="log")
    return _base(fig, 420)


def build_scaling(rows):
    """Gemessene Zugriffe der Ungarischen Methode gegen die Schranke n^3, beide logarithmisch."""
    xs = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["bound"] for r in rows], mode="lines+markers", name="Schranke n³", line=dict(color=C.COLOR_LINE, width=2.5, dash="dash")))
    fig.add_trace(go.Scatter(x=xs, y=[r["accesses"] for r in rows], mode="lines+markers", name="gemessen (Median)", line=dict(color=C.COLOR_CYCLES[0], width=3),
                             hovertemplate="n = %{x}: %{y:,.0f}<extra></extra>"))
    fig.update_xaxes(title_text="Zahl der Orte n (log)", type="log")
    fig.update_yaxes(title_text="Zugriffe (log)", type="log")
    return _base(fig, 340)


def build_gap(rows_by_kind):
    """Lücke Zuordnung -> Rundreise über n, Median und Maximum, Karte gegen Zufallsmatrix."""
    fig = go.Figure()
    for kind, color in (("euclid", C.COLOR_CYCLES[0]), ("random", C.COLOR_CYCLES[2])):
        rows = rows_by_kind[kind]
        xs = [r["n"] for r in rows]
        fig.add_trace(go.Scatter(x=xs, y=[r["gap_median"] for r in rows], mode="lines+markers", name=f"{C.KINDS[kind]}: Median", line=dict(color=color, width=3),
                                 hovertemplate="n = %{x}: %{y:.1f} %<extra></extra>"))
        fig.add_trace(go.Scatter(x=xs, y=[r["gap_max"] for r in rows], mode="lines", name=f"{C.KINDS[kind]}: Maximum", line=dict(color=color, width=1.5, dash="dot"),
                                 hovertemplate="n = %{x}: %{y:.1f} %<extra></extra>"))
    fig.update_xaxes(title_text="Zahl der Orte n", dtick=2)
    fig.update_yaxes(title_text="Zuordnung billiger als Rundreise (%)", rangemode="tozero")
    return _base(fig, 360)

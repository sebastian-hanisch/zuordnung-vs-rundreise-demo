"""Abbildungen: Kanten, Farben, Orte; alle Achsen gesperrt; PDF baut mit Umlauten und bei abgebrochenem Lauf."""

import math

import zrt_algorithm as A
import zrt_constants as C
import zrt_evaluation as ev
import zrt_visualization as V
from zrt_pdf_export import build_pdf
from zrt_scenario import make_instance


def test_edges_by_hand():
    assert V.assignment_edges((1, 0, 3, 2)) == [(0, 1), (1, 0), (2, 3), (3, 2)]
    assert V.tour_edges((0, 2, 1)) == [(0, 2), (2, 1), (1, 0)]
    assert V.tour_edges((0,)) == [] and V.tour_edges(()) == []


def test_edge_colors_follow_the_cycles():
    edges = V.assignment_edges((1, 0, 3, 2))
    colors = V.edge_colors(edges, [(0, 1), (2, 3)])
    assert colors[0] == colors[1] == C.COLOR_CYCLES[0] and colors[2] == colors[3] == C.COLOR_CYCLES[1]
    assert V.edge_colors(V.tour_edges((0, 1, 2)), None) == [C.COLOR_TOUR] * 3


def test_many_cycles_cycle_through_the_palette():
    cycles = [(2 * i, 2 * i + 1) for i in range(len(C.COLOR_CYCLES) + 2)]
    sigma = [0] * (2 * len(cycles))
    for a, b in cycles:
        sigma[a], sigma[b] = b, a
    colors = V.edge_colors(V.assignment_edges(sigma), cycles)
    assert len(colors) == len(sigma) and colors[0] == colors[2 * len(C.COLOR_CYCLES)]


def test_node_positions_map_and_circle():
    euclid = make_instance(6, "euclid", 1)
    assert V.node_positions(euclid) == list(euclid.points)
    rand = make_instance(6, "random", 1)
    pos = V.node_positions(rand)
    assert len(pos) == 6 and pos[0] == (0.0, 1.0)
    assert all(abs(math.hypot(x, y) - 1) < 1e-9 for x, y in pos)


def test_map_has_one_arrow_per_edge_and_locked_axes():
    inst = make_instance(8, "euclid", 2)
    r = A.hungarian(inst)
    edges = V.assignment_edges(r.plan)
    fig = V.build_map(inst, edges, V.edge_colors(edges, A.cycles_of_assignment(r.plan)))
    assert len(fig.layout.annotations) == len(edges) == 8
    assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
    assert list(fig.data[0].text) == [f"O{i + 1}" for i in range(8)]


def test_two_way_edges_are_offset_but_one_way_edges_are_not():
    inst = make_instance(4, "random", 1)
    both = V.build_map(inst, [(0, 1), (1, 0)], ["#000", "#000"])
    one = V.build_map(inst, [(0, 1), (1, 2)], ["#000", "#000"])
    a0, a1 = both.layout.annotations
    assert (a0.x, a0.y) != (a1.x, a1.y) and (a0.ax, a0.ay) != (a1.ax, a1.ay)
    # einseitige Kante liegt exakt auf der Geraden von Ort 0 zu Ort 1 (Winkel von Anfang und Ende gleich)
    o = one.layout.annotations[0]
    p0, p1 = V.node_positions(inst)[0], V.node_positions(inst)[1]
    cross = (o.x - o.ax) * (p1[1] - p0[1]) - (o.y - o.ay) * (p1[0] - p0[0])
    assert abs(cross) < 1e-9


def test_charts_lock_their_axes():
    growth = ev.growth_rows(sizes=(4, 6), seeds=C.GROWTH_SEEDS[:2])
    gap = {k: ev.sweep_gap(k, sizes=(4, 6), seeds=C.SWEEP_SEEDS[:3]) for k in C.KINDS}
    scaling = ev.hungarian_scaling("random", sizes=(10, 20), seeds=C.GROWTH_SEEDS[:2])
    for fig in (V.build_growth(growth, 1000), V.build_growth(growth), V.build_gap(gap), V.build_scaling(scaling)):
        assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
    assert V.build_growth(growth).layout.yaxis.type == "log"
    assert len(V.build_growth(growth).data) == 5 and len(V.build_gap(gap).data) == 4


def test_pdf_builds_for_complete_and_aborted_runs():
    done = ev.analyse(ev.Settings(n=6))
    pdf = build_pdf(done)
    assert pdf[:5] == b"%PDF-" and len(pdf) > 1000
    aborted = ev.analyse(ev.Settings(n=11, assign="enumerate", tour="enumerate", budget=10_000))
    assert build_pdf(aborted)[:5] == b"%PDF-"
    assert build_pdf(ev.analyse(ev.Settings(n=C.N_MAX, kind="random")))[:5] == b"%PDF-"

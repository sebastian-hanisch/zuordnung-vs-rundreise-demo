"""PDF-Export (fpdf2, Kernschriften): Einstellungen, Ergebnisse und Kostenmatrix als Tabelle. Kein Gedankenstrich und kein Euro-Zeichen (Kernschriften)."""

from fpdf import FPDF

import zrt_constants as C
import zrt_evaluation as ev
from zrt_scenario import label


def _text(value: str) -> str:
    """Zeichen, die die Kernschriften nicht kennen, ersetzen (Gedankenstrich, Pfeile, Fettdruck-Markierung)."""
    return (value.replace("–", "-").replace("—", "-").replace("→", "->").replace("**", "").replace("€", "EUR")
            .replace("·", "*").replace("³", "^3").replace("≤", "<=").replace("≥", ">="))


def _para(pdf: FPDF, height: float, text: str) -> None:
    """Absatz über die volle Breite; danach steht der Cursor wieder am linken Rand (fpdf2 setzt ihn sonst an den rechten Rand)."""
    pdf.multi_cell(0, height, _text(text), new_x="LMARGIN", new_y="NEXT")


def build_pdf(a: ev.Analysis) -> bytes:
    s = a.settings
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _text("Zuordnung gegen Rundreise: dieselbe Matrix, zwei Klassen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    _para(pdf, 5.5,
          f"Orte: {s.n}   Matrix: {C.KINDS[s.kind]}   Zufalls-Seed: {s.seed}\n"
          f"Verfahren Zuordnung: {C.ASSIGN_METHODS[s.assign]}   Verfahren Rundreise: {C.TOUR_METHODS[s.tour]}\n"
          f"Budget: {ev.fmt_int(s.budget)} Zugriffe auf die Kostenmatrix")
    pdf.ln(2)
    kind, verdict = ev.verdict_main(a)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Ergebnis", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    _para(pdf, 5.5, verdict)
    pdf.ln(1)
    for name, r in (("Zuordnung", a.assignment), ("Rundreise", a.tour)):
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, name, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        plan = "keine zulässige Lösung gefunden" if r.plan is None else " ".join(label(i) for i in r.plan)
        _para(pdf, 5.5,
              f"Kosten: {'-' if r.cost is None else ev.fmt_int(r.cost)}   Zugriffe: {ev.fmt_int(r.accesses)}   Lauf zu Ende: {'ja' if r.finished else 'nein (Budget)'}\n"
              + (f"Zuordnung Fahrzeug i -> Auftrag: {plan}" if name == "Zuordnung" else f"Reihenfolge: {plan}"))
    if a.cycles is not None:
        _para(pdf, 5.5, "Teilkreise der Zuordnung: " + "; ".join("(" + " ".join(label(i) for i in c) + ")" for c in a.cycles))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Kostenmatrix", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    cell = min(14.0, 175.0 / (a.inst.n + 1))
    pdf.cell(cell, 5, "", border=1)
    for j in range(a.inst.n):
        pdf.cell(cell, 5, label(j), border=1, align="C")
    pdf.ln()
    for i in range(a.inst.n):
        pdf.cell(cell, 5, label(i), border=1, align="C")
        for j in range(a.inst.n):
            pdf.cell(cell, 5, "-" if i == j else str(a.inst.matrix[i][j]), border=1, align="C")
        pdf.ln()
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    _para(pdf, 4.5, "Aufwand in Zugriffen auf die Kostenmatrix, nicht in Sekunden. Sebastian Hanisch - Operations Research und Machine Learning.")
    return bytes(pdf.output())

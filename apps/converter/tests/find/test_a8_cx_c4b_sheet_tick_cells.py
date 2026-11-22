"""A8 CX, ORDER C4 (sheets), part b: a tick box drawn as one small bordered cell.

A sheet draws "postaw x w wybranym polu" as an empty one-cell square with all four borders, followed on the same row
by the words of the option in a cell without borders. Two such rows one under the other are the options of one
question (RADIO or CHECKBOX later), as a drawn square beside words is on a PDF page. A bordered cell with words left
of it ("Nr rachunku | [ ]") stays a place to fill; a grid of cells that are all bordered (a ruled table) is not a row
of tick boxes.

Synthetic words only; built with openpyxl and read by our own XLSX reader.
"""
from __future__ import annotations

import io

from app.find import find
from app.readers import read_document
from find_builders import STRICT


def _book(fill) -> bytes:  # noqa: ANN001
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Formularz"
    fill(ws)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _box():  # noqa: ANN202
    from openpyxl.styles import Border, Side

    thin = Side(style="thin")
    return Border(left=thin, right=thin, top=thin, bottom=thin)


def _find(fill):  # noqa: ANN001, ANN202
    return find(read_document(_book(fill), "xlsx"), STRICT)


def test_bordered_one_cell_squares_before_words_are_one_choice():
    def fill(ws):  # noqa: ANN001
        ws["A1"] = "Wniosek o zwrot oplaty"
        ws["A3"] = "5. Sposob zwrotu oplaty (postaw x w wybranym polu)"
        ws.merge_cells("A3:J3")
        ws["C5"].border = _box()
        ws["E5"] = "Gotowka w kasie urzedu"
        ws.merge_cells("E5:J5")
        ws["C7"].border = _box()
        ws["E7"] = "Przelewem na rachunek bankowy"
        ws.merge_cells("E7:J7")
        ws["A9"] = "Nr rachunku"
        ws.merge_cells("A9:B9")
        ws["C9"].border = _box()
        ws.merge_cells("C9:J9")

    out = _find(fill)
    groups = [c for c in out.candidates if c.kind == "choice_group"]
    assert [[o.text for o in g.options] for g in groups] == [["Gotowka w kasie urzedu", "Przelewem na rachunek bankowy"]]
    labels = [c.label.text for c in out.candidates if c.kind == "cell" and c.label]
    assert "Nr rachunku" in labels, labels


def test_bordered_cell_with_words_left_of_it_stays_a_place():
    """Negative control: "Kod | [ ] | (xx-xxx)": words left of the square make it a place to fill."""
    def fill(ws):  # noqa: ANN001
        ws["A1"] = "Dane wnioskodawcy"
        ws["A3"] = "Numer domu"
        ws["B3"].border = _box()
        ws["C3"] = "(cyframi)"
        ws["A5"] = "Numer lokalu"
        ws["B5"].border = _box()
        ws["C5"] = "(jesli jest)"

    out = _find(fill)
    assert not [c for c in out.candidates if c.kind in ("box", "choice_group")], [c.kind for c in out.candidates]


def test_a_ruled_grid_is_not_a_row_of_tick_boxes():
    """Negative control: every cell bordered (a ruled table): an empty cell before a bordered text is a place."""
    def fill(ws):  # noqa: ANN001
        ws["A1"] = "Wykaz"
        for r in (3, 4):
            for col in "BC":
                ws[f"{col}{r}"].border = _box()
        ws["C3"] = "Pierwsza pozycja wykazu"
        ws["C4"] = "Druga pozycja wykazu"

    out = _find(fill)
    assert not [c for c in out.candidates if c.kind in ("box", "choice_group")], [c.kind for c in out.candidates]

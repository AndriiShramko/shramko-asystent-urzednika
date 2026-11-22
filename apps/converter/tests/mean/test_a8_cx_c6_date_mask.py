"""A8 CX, ORDER C6: a printed date mask (DD-MM-RRRR, spaced "D D - M M - R R R R", one letter per cell) makes the
place a DATEPICKER; box glyphs in front of "D D -", "M M -", "R R R R" are the mask, never options of a choice.
Synthetic papers."""
from __future__ import annotations

import io

from app.find import find
from app.mean import understand
from app.readers import read_document
from tests.find.find_builders import Native, flow, model

DOTS = "." * 30


def _fields(m) -> list[tuple[str, str, int]]:  # noqa: ANN001
    b = understand(m, find(m))
    return [(f.type, f.label, len(f.options or [])) for s in b.matter for f in s.fields]


def test_boxes_in_front_of_mask_parts_are_one_date_not_a_choice():
    page = flow("DEKLARACJA O WYSOKOSCI OPLATY", "C. OKOLICZNOSCI ZLOZENIA",
                "Pierwsza deklaracja - data zdarzenia powodujacego obowiazek:",
                "□ D D -", "□ M M -", "□ R R R R", bold=(0, 1))
    got = _fields(model(page))
    assert not any(t in ("RADIO", "CHECKBOX", "SELECT") for t, _l, _n in got), got
    assert any(t == "DATEPICKER" for t, _l, _n in got), got


def test_spaced_mask_printed_after_a_comb_makes_a_datepicker():
    n = Native()
    n.text(70, 60, "DEKLARACJA O WYSOKOSCI OPLATY", 300, bold=True)
    n.text(50, 100, "C. OKOLICZNOSCI ZLOZENIA", 200, bold=True)
    n.text(50, 130, "Zmiana danych nastapila:", 160)
    for k in range(8):
        n.rect(220 + 16 * k + (8 if k >= 2 else 0) + (8 if k >= 4 else 0), 126, 16, 18)
    n.text(220, 148, "D D - M M - R R R R", 150, size=8.0)
    got = _fields(model(n.page()))
    assert any(t == "DATEPICKER" for t, _l, _n in got), got


def test_one_letter_per_cell_mask_after_a_sheet_place_makes_a_datepicker():
    import openpyxl
    from openpyxl.styles import Border, Side

    thin = Side(style="thin")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"] = "C. OKOLICZNOSCI ZLOZENIA"
    ws["A3"] = "Zmiana danych nastapila:"
    ws["B3"].border = Border(bottom=thin)
    for col, ch in zip("CDEFGHIJKL", "DD-MM-RRRR"):
        ws[f"{col}3"] = ch
    buf = io.BytesIO()
    wb.save(buf)
    got = _fields(read_document(buf.getvalue(), "xlsx"))
    assert any(t == "DATEPICKER" and "Zmiana" in lab for t, lab, _n in got), got


def test_a_plain_place_without_a_mask_stays_text():
    """Negative control: no mask, no date word: a text field."""
    page = flow("WNIOSEK", "A. DANE", "Nazwa klubu: " + DOTS, "Dyscyplina: " + DOTS, bold=(0, 1))
    got = _fields(model(page))
    assert [t for t, _l, _n in got] == ["TEXT_FIELD", "TEXT_FIELD"], got

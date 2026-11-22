"""A8 S04: a sheet drawn as a page (thin rows, PDF-to-XLSX converters write them) puts a merged place to fill one
row above the merged words left of it. The label must be found on any row the place covers, not only its top row.

Synthetic words only; built with openpyxl and read by our own XLSX reader.
"""
from __future__ import annotations

import io

from app.find import find
from app.readers import read_document
from find_builders import STRICT, tops


def _sheet() -> bytes:
    import openpyxl
    from openpyxl.styles import Border, Side

    thin = Side(style="thin")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Formularz"
    for r in range(1, 30):
        ws.row_dimensions[r].height = 3
    ws["A1"] = "Wniosek o rezerwacje sali"
    ws.merge_cells("A1:C4")
    # words on rows 9-13, the place to fill on rows 8-11, right next to them (the offset the converters write)
    ws["A9"] = "w terminie od"
    ws.merge_cells("A9:F13")
    ws.merge_cells("G8:L11")
    for col in "GHIJKL":
        ws[f"{col}11"].border = Border(bottom=thin)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_merged_place_one_row_above_its_words_keeps_the_label():
    pm = read_document(_sheet(), "xlsx")
    out = find(pm, STRICT)
    labels = [c.label.text if c.label else None for c in tops(out)]
    assert any(lab and "terminie od" in lab for lab in labels), labels
    assert not any(w.code == "LABEL_NOT_FOUND" for w in out.warnings), [w.code for w in out.warnings]

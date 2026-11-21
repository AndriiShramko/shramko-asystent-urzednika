"""WP-F2b: XLSX, ODS and binary Word readers on synthetic files built in the test. Synthetic text only."""
from __future__ import annotations

import io
import time

import pytest

from app.readers import ReaderError, read_document
from app.readers import doc as D
from app.readers._sheet import a1, col_letters, parse_range

from sheet_doc_builders import BOLD, IN_TABLE, ROW_END, doc_bytes, ods_bytes, ods_cell, ole_bytes, symbol


def _zip_of(members: dict[str, bytes]) -> bytes:
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, body in members.items():
            z.writestr(name, body)
    return buf.getvalue()


def _runs(m):
    return [r for p in m.pages for r in p.runs]


def _cells(m, page=0):
    return {(c.r, c.c): c for t in m.pages[page].tables for c in t.cells}


# ---------------------------------------------------------------- grid helpers


def test_a1_notation_round_trip():
    assert [col_letters(c) for c in (0, 25, 26, 701, 702)] == ["A", "Z", "AA", "ZZ", "AAA"]
    assert a1(6, 1) == "B7"
    assert parse_range("$B$7:D9") == (6, 1, 8, 3)
    assert parse_range("A:A") is None


# ---------------------------------------------------------------- XLSX


def _xlsx(build) -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    build(wb)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _form(wb):
    from openpyxl.styles import Border, Font, Side
    from openpyxl.worksheet.datavalidation import DataValidation

    thin = Side(style="thin")
    ws = wb.active
    ws.title = "Arkusz1"
    ws["A1"] = "Wniosek o wydanie zaświadczenia"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A3"] = "Imię i nazwisko"
    ws.merge_cells("B3:D3")
    for col in "BCD":
        ws[f"{col}3"].border = Border(top=thin, bottom=thin, left=thin if col == "B" else None,
                                      right=thin if col == "D" else None)
    ws["A5"] = 12
    ws["A6"] = 0.5
    ws["F8"].border = Border(bottom=thin)  # an empty bordered cell: a place to fill
    ws["F9"] = "pod linią"                # its neighbour below declares nothing; the shared edge is drawn on F8
    ws.row_dimensions[2].hidden = True
    ws.row_dimensions[3].height = 30
    ws.column_dimensions["B"].width = 20
    ws["A7"] = "Czy posiada psa"
    dv = DataValidation(type="list", formula1="Lista!$A$1:$A$2")
    dv2 = DataValidation(type="list", formula1='"Pies,Suka"')
    dv3 = DataValidation(type="list", formula1="INDIRECT(A1)")
    ws.add_data_validation(dv)
    ws.add_data_validation(dv2)
    ws.add_data_validation(dv3)
    dv.add("B7")
    dv2.add("C7:C8")
    dv3.add("D7")
    lista = wb.create_sheet("Lista")
    lista["A1"], lista["A2"] = "Tak", "Nie"
    lista.sheet_state = "hidden"


def test_xlsx_grid_merges_borders_and_sizes():
    m = read_document(_xlsx(_form), "xlsx")
    assert m.source.reader == "xlsx" and len(m.pages) == 2
    p = m.pages[0]
    assert p.origin == "flow" and p.name == "Arkusz1" and not p.hidden
    title = _runs(m)[0]
    assert (title.text, title.anchor, title.bold, title.size) == ("Wniosek o wydanie zaświadczenia", "Arkusz1!A1",
                                                                  True, 14)
    cells = _cells(m)
    merged = cells[(2, 1)]
    assert (merged.rs, merged.cs, merged.borders, merged.runs, merged.anchor) == (1, 3, "trbl", [], "Arkusz1!B3")
    assert (2, 2) not in cells and (2, 3) not in cells   # one cell per merge, not one per grid square
    assert cells[(7, 5)].borders == "b" and cells[(7, 5)].runs == []
    texts = {r.anchor: r.text for r in _runs(m)}
    assert texts["Arkusz1!A5"] == "12" and texts["Arkusz1!A6"] == "0.5"
    assert p.row_heights[1] == 0 and p.row_heights[2] == 30 and p.row_heights[0] == 15
    assert p.col_widths[1] == 105 and p.col_widths[0] > 40
    assert len(p.row_heights) == 9 and len(p.col_widths) == 6   # up to the last used row and column only
    assert p.tables[0].anchor == "Arkusz1!A1:F9"


def test_xlsx_hidden_sheet_and_list_widgets():
    m = read_document(_xlsx(_form), "xlsx")
    assert m.pages[1].hidden and m.pages[1].name == "Lista"
    assert [w.page for w in m.warnings if w.code == "HIDDEN_SHEET"] == [2]
    ws = {w.anchor: w for w in m.pages[0].widgets}
    assert ws["Arkusz1!B7"].kind == "choice" and ws["Arkusz1!B7"].options == ["Tak", "Nie"]
    assert ws["Arkusz1!C7:C8"].options == ["Pies", "Suka"]
    assert ws["Arkusz1!D7"].options == []   # not resolved: no guessed list, a warning instead
    assert any(w.code == "UNREADABLE_PART" and w.anchor == "Arkusz1!D7" for w in m.warnings)


def test_xlsx_cell_budget_and_broken_files():
    with pytest.raises(ReaderError) as e:
        read_document(_xlsx(_form), "xlsx", {"max_cells": 5})
    assert e.value.code == "TOO_LARGE"
    with pytest.raises(ReaderError) as e:
        read_document(b"not a zip at all", "xlsx")
    assert e.value.code == "UNREADABLE" and "Traceback" not in e.value.reason
    zip_of = _zip_of

    with pytest.raises(ReaderError) as e:
        read_document(zip_of({"a.xml": b"<a/>"}), "xlsx")
    assert e.value.code == "UNREADABLE"


# ---------------------------------------------------------------- ODS

TRAILING = ('<table:table-row table:number-rows-repeated="1048000">'
            '<table:table-cell table:number-columns-repeated="1024"/></table:table-row>')


def _ods_form() -> bytes:
    rows = (
        '<table:table-row table:style-name="ro1">' + ods_cell("Wniosek o wynajem", "ceBold") + "</table:table-row>"
        '<table:table-row table:style-name="ro1">' + ods_cell("Imię i nazwisko")
        + ods_cell("", "ceB", 'table:number-columns-spanned="3" table:number-rows-spanned="1"')
        + '<table:covered-table-cell table:number-columns-repeated="2" table:style-name="ceB"/></table:table-row>'
        '<table:table-row>' + ods_cell("a<text:s text:c=\"2\"/>b<text:tab/>c") + ods_cell("", "ceB", 'table:content-validation-name="v1"')
        + ods_cell("", None, 'table:content-validation-name="v2"') + "</table:table-row>"
        '<table:table-row table:visibility="collapse">' + ods_cell("ukryty wiersz") + "</table:table-row>"
        + TRAILING
    )
    main = (f'<table:table table:name="Arkusz1" table:style-name="ta1">'
            f'<table:table-column table:style-name="co1" table:number-columns-repeated="1024"/>{rows}</table:table>')
    hidden = ('<table:table table:name="Lista" table:style-name="taH"><table:table-column/>'
              '<table:table-row>' + ods_cell("Tak") + '</table:table-row><table:table-row>' + ods_cell("Nie")
              + "</table:table-row></table:table>")
    validations = (
        '<table:content-validation table:name="v1" table:condition="of:cell-content-is-in-list([$Lista.$A$1:.$A$2])"/>'
        '<table:content-validation table:name="v2" table:condition="of:cell-content-is-in-list(&quot;Pies&quot;;&quot;Suka&quot;)"/>'
    )
    return ods_bytes(main + hidden, validations)


def test_ods_grid_spans_styles_and_trailing_repeats():
    t = time.perf_counter()
    m = read_document(_ods_form(), "ods")
    assert time.perf_counter() - t < 2   # the million trailing rows are never expanded
    assert m.source.reader == "ods" and len(m.pages) == 2
    p = m.pages[0]
    title = _runs(m)[0]
    assert (title.text, title.anchor, title.bold, title.size) == ("Wniosek o wynajem", "Arkusz1!A1", True, 14)
    cells = _cells(m)
    assert (cells[(1, 1)].cs, cells[(1, 1)].borders) == (3, "trbl")
    assert (1, 2) not in cells
    texts = {r.anchor: r.text for r in _runs(m)}
    assert texts["Arkusz1!A3"] == "a  b\tc"   # text:s c=2 is two spaces
    assert texts["Arkusz1!A4"] == "ukryty wiersz" and p.row_heights[3] == 0
    assert p.row_heights[0] == 20 and len(p.row_heights) == 4
    assert p.col_widths == [72.0, 72.0, 72.0, 72.0]   # 2.54 cm, up to the last used column
    ws = {w.anchor: w.options for w in p.widgets}
    assert ws == {"Arkusz1!B3": ["Tak", "Nie"], "Arkusz1!C3": ["Pies", "Suka"]}
    assert m.pages[1].hidden and [w.page for w in m.warnings if w.code == "HIDDEN_SHEET"] == [2]


def test_negative_control_ods_row_repeated_a_million_times_is_refused_before_expanding():
    row = '<table:table-row table:number-rows-repeated="1000000">' + ods_cell("x", "ceB") + "</table:table-row>"
    data = ods_bytes(f'<table:table table:name="A">{row}</table:table>')
    t = time.perf_counter()
    with pytest.raises(ReaderError) as e:
        read_document(data, "ods")
    assert e.value.code == "TOO_LARGE" and time.perf_counter() - t < 1


def test_ods_row_with_content_repeated_many_times_is_kept_and_flagged():
    row = '<table:table-row table:number-rows-repeated="150">' + ods_cell("", "ceB") + "</table:table-row>"
    m = read_document(ods_bytes(f'<table:table table:name="A">{row}</table:table>'), "ods")
    assert len(m.pages[0].tables[0].cells) == 150
    assert [w for w in m.warnings if w.code == "UNREADABLE_PART" and "repeated 150 times" in (w.detail or "")]


def test_ods_broken_files():
    for members in ({"mimetype": b"application/vnd.oasis.opendocument.text", "content.xml": b"<a/>"},
                    {"content.xml": b"<a/>"},     # no spreadsheet body
                    {"styles.xml": b"<a/>"}):     # no content.xml
        with pytest.raises(ReaderError) as e:
            read_document(_zip_of(members), "ods")
        assert e.value.code == "UNREADABLE"
    with pytest.raises(ReaderError) as e:
        read_document(_zip_of({"content.xml": b'<?xml version="1.0"?><!DOCTYPE a [<!ENTITY e "x">]><a>&e;</a>'}),
                      "ods")
    assert e.value.code == "UNREADABLE" and "entities" in e.value.reason
    empty = read_document(ods_bytes('<table:table table:name="A"/>'), "ods")
    assert empty.pages[0].runs == [] and empty.pages[0].tables == []


# ---------------------------------------------------------------- binary Word

TITLE = "Wniosek o wydanie\r"
ROWS = "Imię wnioskodawcy\x07Imię pełnomocnika\x07\x07..........\x07..........\x07\x07"
FIELD = "\x13 FORMCHECKBOX \x14\x15 zgoda\r"
PETS = "( pies ( suka\r"
TAIL = "Strona pierwsza\x0cDruga strona\r"
MAIN = TITLE + ROWS + FIELD + PETS + TAIL


def _marks(text: str, start: int, pattern: str) -> dict[int, bytes]:
    """Properties of the marks of a table text: a cell end is IN_TABLE, a row end (second \\x07) is ROW_END."""
    out, prev = {}, ""
    for i, ch in enumerate(text):
        if ch == "\x07":
            out[start + i] = ROW_END if prev == "\x07" else IN_TABLE
        prev = ch
    return out


def _doc(**kw) -> bytes:
    base = len(TITLE)
    para = _marks(ROWS, base, "")
    pets = MAIN.index(PETS)
    chars = {i: BOLD for i in range(len(TITLE) - 1)}
    chars[pets] = symbol(1, 0xF06F)
    chars[pets + 7] = symbol(1, 0xF06F)
    args = dict(txbx=["Pole w ramce\r"], para=para, chars=chars, compressed=len(TITLE))
    args.update(kw)
    return doc_bytes(MAIN, **args)


def test_doc_body_table_symbols_fields_pages_and_text_boxes():
    m = read_document(_doc(), "doc")
    assert m.source.reader == "doc.flow" and all(p.origin == "flow" for p in m.pages)
    assert len(m.pages) == 2
    runs = _runs(m)
    first = runs[0]
    assert (first.text, first.anchor, first.bold) == ("Wniosek o wydanie", "p[0]", True)
    cells = _cells(m)
    # drill 5: neighbouring names of applicant and proxy stay separate cells, each with its own run
    labels = {k: [r.text for r in runs if r.id in c.runs] for k, c in cells.items()}
    assert labels[(0, 0)] == ["Imię wnioskodawcy"] and labels[(0, 1)] == ["Imię pełnomocnika"]
    assert labels[(1, 0)] == [".........."] and labels[(1, 1)] == [".........."]
    assert cells[(1, 1)].anchor == "tbl[0]/cell[1,1]" and m.pages[0].tables[0].anchor == "tbl[0]"
    texts = [r.text for r in runs]
    assert "☐ zgoda" in texts and "□ pies □ suka" in texts and "FORMCHECKBOX" not in " ".join(texts)
    assert [(w.kind, w.anchor) for w in m.pages[0].widgets] == [("checkbox", "p[1]")]
    assert [r.text for r in m.pages[1].runs] == ["Druga strona", "Pole w ramce"]
    assert m.pages[1].runs[1].anchor == "txbx[0]/p[0]"
    details = " ".join(w.detail or "" for w in m.warnings)
    assert "flow only" in details and "1 text boxes" in details   # the honest gaps of drill 5


def test_doc_without_paragraph_properties_reads_cells_as_paragraphs_and_says_so():
    m = read_document(_doc(with_papx=False), "doc")
    assert not any(p.tables for p in m.pages)
    assert "Imię pełnomocnika" in [r.text for r in _runs(m)]
    assert any("cell and row ends are not told apart" in (w.detail or "") for w in m.warnings)


def test_doc_all_utf16_and_zero_table_stream():
    m = read_document(doc_bytes("Zażółć gęślą jaźń\r", flags=0), "doc")
    assert [r.text for r in _runs(m)] == ["Zażółć gęślą jaźń"]


@pytest.mark.parametrize("kw,code", [
    ({"flags": 0x0200 | 0x0100}, "ENCRYPTED"),
    ({"nfib": 0x0065}, "UNREADABLE"),
    ({"table_name": "0Table"}, "UNREADABLE"),   # the FIB names 1Table, the file holds 0Table
])
def test_doc_refusals(kw, code):
    with pytest.raises(ReaderError) as e:
        read_document(doc_bytes("Tekst\r", **kw), "doc")
    assert e.value.code == code


def test_doc_not_ole_or_not_word_or_empty():
    legacy_workbook = lambda: ole_bytes({"Workbook": b"x"})  # noqa: E731

    for data in (b"plain text", legacy_workbook()):
        with pytest.raises(ReaderError) as e:
            read_document(data, "doc")
        assert e.value.code == "UNREADABLE"
    with pytest.raises(ReaderError) as e:
        read_document(doc_bytes("\r\r"), "doc")
    assert "no text" in e.value.reason


def test_piece_table_and_sprm_parsers_on_bytes():
    import struct

    plc = struct.pack("<3I", 0, 4, 6) + struct.pack("<HIH", 0, 0x40000000 | 200, 0) + struct.pack("<HIH", 0, 300, 0)
    pieces = D.parse_clx(b"\x01\x02\x00ab" + b"\x02" + struct.pack("<I", len(plc)) + plc, 1000)
    assert [(p.cp0, p.cp1, p.fc, p.wide) for p in pieces] == [(0, 4, 100, False), (4, 6, 300, True)]
    with pytest.raises(ReaderError):
        D.parse_clx(b"\x02" + struct.pack("<I", len(plc)) + plc, 301)   # a piece outside the stream
    with pytest.raises(ReaderError):
        D.parse_clx(b"\x07", 1000)
    tdef = struct.pack("<H", 0xD608) + struct.pack("<H", 4) + b"abc"
    assert D.parse_sprms(IN_TABLE + tdef + ROW_END) == {0x2416: b"\x01", 0xD608: b"\x04\x00abc", 0x2417: b"\x01"}
    assert D.parse_sprms(IN_TABLE + b"\x09\x6a\x01") == {0x2416: b"\x01"}   # a cut operand is dropped

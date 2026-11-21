"""DOCX reader on synthetic documents: python-docx for ordinary ones, raw XML for text boxes, content controls,
legacy form fields and the rest (design 5.1, 6.2; WP-F2a)."""
from __future__ import annotations

import io
import zipfile

import pytest

from app.readers import ReaderError, read_document
from readers_builders import docx_bytes, p, shape, textbox

PT = 595.3


def _texts(model) -> list[str]:  # noqa: ANN001
    return [r.text for pg in model.pages for r in pg.runs]


# ---------------------------------------------------------------- flow documents (python-docx)


@pytest.fixture(scope="module")
def flow():
    import docx

    d = docx.Document()
    d.add_heading("Wniosek testowy", level=1)
    para = d.add_paragraph("Imię i nazwisko: ")
    para.add_run("pogrubione").bold = True
    t = d.add_table(rows=2, cols=3)
    t.style = "Table Grid"
    t.cell(0, 0).text = "Nazwa"
    t.cell(0, 1).merge(t.cell(0, 2)).text = "Pole scalone"
    t.cell(1, 0).text = "Adres"
    d.add_page_break()
    d.add_paragraph("Druga strona")
    buf = io.BytesIO()
    d.save(buf)
    return read_document(buf.getvalue(), "docx")


def test_flow_pages_and_anchors(flow):
    assert flow.source.reader == "docx.flow" and flow.source.format == "docx"
    assert [pg.origin for pg in flow.pages] == ["flow", "flow"]
    assert all(pg.width is None and not pg.lines and not pg.rects for pg in flow.pages)
    first = flow.pages[0].runs
    assert first[0].text == "Wniosek testowy" and first[0].anchor == "p[0]"
    assert all(r.box is None and r.anchor for pg in flow.pages for r in pg.runs)
    assert [r.text for r in flow.pages[1].runs] == ["Druga strona"]


def test_flow_bold_is_all_or_nothing(flow):
    mixed = next(r for r in flow.pages[0].runs if r.text.startswith("Imię"))
    assert mixed.text == "Imię i nazwisko: pogrubione" and not mixed.bold


def test_flow_table_grid_merge_and_borders(flow):
    (t,) = flow.pages[0].tables
    assert t.anchor == "tbl[0]"
    cells = {(c.r, c.c): c for c in t.cells}
    assert cells[(0, 1)].cs == 2 and (0, 2) not in cells
    assert cells[(0, 0)].borders == "trbl"
    run_text = {r.id: r.text for r in flow.pages[0].runs}
    assert [run_text[x] for x in cells[(0, 1)].runs] == ["Pole scalone"]
    assert cells[(1, 0)].anchor == "tbl[0]/cell[1,0]"
    assert next(r for r in flow.pages[0].runs if r.text == "Adres").anchor == "tbl[0]/cell[1,0]/p[0]"


def test_vertical_merge_and_cell_borders_from_cell():
    body = (
        '<w:tbl><w:tblPr/><w:tblGrid><w:gridCol w:w="2000"/><w:gridCol w:w="2000"/></w:tblGrid>'
        '<w:tr><w:tc><w:tcPr><w:vMerge w:val="restart"/><w:tcBorders><w:top w:val="single"/>'
        '<w:bottom w:val="single"/></w:tcBorders></w:tcPr>' + p("Scalone w pionie") + '</w:tc>'
        '<w:tc>' + p("A") + '</w:tc></w:tr>'
        '<w:tr><w:tc><w:tcPr><w:vMerge/></w:tcPr>' + p() + '</w:tc><w:tc>' + p("B") + '</w:tc></w:tr></w:tbl>'
    )
    m = read_document(docx_bytes(body), "docx")
    cells = {(c.r, c.c): c for c in m.pages[0].tables[0].cells}
    assert cells[(0, 0)].rs == 2 and (1, 0) not in cells
    assert cells[(0, 0)].borders == "tb" and cells[(0, 1)].borders == ""


# ---------------------------------------------------------------- text rules (raw XML)


def test_tabs_leaders_underlined_blanks_symbols_hidden_deleted():
    styles = ('<w:style w:type="paragraph" w:styleId="Kropki"><w:pPr><w:tabs><w:tab w:val="left" w:pos="9000" '
              'w:leader="dot"/></w:tabs></w:pPr></w:style>')
    body = (
        '<w:p><w:pPr><w:pStyle w:val="Kropki"/></w:pPr><w:r><w:t>Miejscowość</w:t><w:tab/></w:r></w:p>'
        '<w:p><w:r><w:t>Kolumna</w:t><w:tab/><w:t>druga</w:t></w:r></w:p>'
        '<w:p><w:r><w:t xml:space="preserve">Podpis </w:t></w:r><w:r><w:rPr><w:u w:val="single"/></w:rPr>'
        '<w:t xml:space="preserve">          </w:t></w:r></w:p>'
        '<w:p><w:r><w:sym w:font="Wingdings" w:char="F06F"/><w:t xml:space="preserve"> tak </w:t></w:r>'
        '<w:r><w:rPr><w:rFonts w:ascii="Wingdings" w:hAnsi="Wingdings"/></w:rPr><w:t>þ</w:t></w:r>'
        '<w:r><w:sym w:font="Wingdings" w:char="F0AB"/></w:r></w:p>'
        '<w:p><w:r><w:t>Widoczne</w:t></w:r><w:r><w:rPr><w:vanish/></w:rPr><w:t>ukryte</w:t></w:r>'
        '<w:del><w:r><w:delText>usunięte</w:delText></w:r></w:del><w:ins><w:r><w:t> dodane</w:t></w:r></w:ins></w:p>'
    )
    m = read_document(docx_bytes(body, styles=styles), "docx")
    assert _texts(m) == ["Miejscowość..........", "Kolumna\tdruga", "Podpis __________",
                         "□ tak ☑�", "Widoczne dodane"]


def test_content_controls():
    def sdt(pr: str, content: str) -> str:
        return f'<w:sdt><w:sdtPr>{pr}</w:sdtPr><w:sdtContent>{content}</w:sdtContent></w:sdt>'

    body = (
        '<w:p><w:r><w:t xml:space="preserve">Zgoda </w:t></w:r>'
        + sdt('<w:alias w:val="zgoda"/><w14:checkbox/>', '<w:r><w:t>☐</w:t></w:r>') + '</w:p>'
        '<w:p>' + sdt('<w:tag w:val="kraj"/><w:dropDownList><w:listItem w:displayText="Polska" w:value="PL"/>'
                      '<w:listItem w:displayText="Inny" w:value="X"/></w:dropDownList>',
                      '<w:r><w:t>Polska</w:t></w:r>') + '</w:p>'
        '<w:p><w:r><w:t xml:space="preserve">Data: </w:t></w:r>'
        + sdt('<w:alias w:val="data"/><w:showingPlcHdr/><w:date/>', '<w:r><w:t>Kliknij, aby wpisać datę</w:t></w:r>')
        + '</w:p>'
        + sdt('<w:alias w:val="opis"/><w:text/>', p("Opis w kontrolce blokowej"))
    )
    m = read_document(docx_bytes(body), "docx")
    w = {x.name: x for x in m.pages[0].widgets}
    assert w["zgoda"].kind == "checkbox" and w["zgoda"].anchor == "p[0]"
    assert w["kraj"].kind == "choice" and w["kraj"].options == ["Polska", "Inny"]
    assert w["data"].kind == "date"
    assert w["opis"].kind == "text"
    assert _texts(m) == ["Zgoda ☐", "Polska", "Data:", "Opis w kontrolce blokowej"]


def test_legacy_form_fields():
    def field(code: str, ff: str, result: str = "") -> str:
        res = f'<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>{result}</w:t></w:r>' if result else ""
        return (f'<w:r><w:fldChar w:fldCharType="begin"><w:ffData>{ff}</w:ffData></w:fldChar></w:r>'
                f'<w:r><w:instrText xml:space="preserve"> {code} </w:instrText></w:r>{res}'
                '<w:r><w:fldChar w:fldCharType="end"/></w:r>')

    body = (
        '<w:p><w:r><w:t xml:space="preserve">PESEL: </w:t></w:r>'
        + field("FORMTEXT", '<w:name w:val="pesel"/><w:textInput><w:maxLength w:val="11"/></w:textInput>',
                "   ") + '</w:p>'
        '<w:p>' + field("FORMCHECKBOX", '<w:name w:val="osoba"/><w:checkBox><w:size w:val="20"/>'
                        '<w:default w:val="0"/></w:checkBox>')
        + '<w:r><w:t xml:space="preserve"> osoba fizyczna</w:t></w:r></w:p>'
        '<w:p>' + field("FORMDROPDOWN", '<w:name w:val="tryb"/><w:ddList><w:listEntry w:val="pierwszy"/>'
                        '<w:listEntry w:val="drugi"/></w:ddList>') + '</w:p>'
        '<w:p><w:r><w:t xml:space="preserve">Strona </w:t></w:r>'
        + field("PAGE", "", "3") + '</w:p>'
    )
    m = read_document(docx_bytes(body), "docx")
    w = {x.name: x for x in m.pages[0].widgets}
    assert w["pesel"].kind == "text" and w["pesel"].max_len == 11 and w["pesel"].anchor == "p[0]"
    assert w["osoba"].kind == "checkbox" and w["tryb"].kind == "choice" and w["tryb"].options == ["pierwszy", "drugi"]
    assert _texts(m) == ["PESEL:", "☐ osoba fizyczna", "Strona 3"], "field codes leaked into the text"


def test_footnotes_are_numbered_and_placed():
    body = ('<w:p><w:r><w:t>Nazwisko</w:t></w:r><w:r><w:footnoteReference w:id="7"/></w:r></w:p>')
    notes = ('<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'
             '<w:footnote w:id="7"><w:p><w:r><w:footnoteRef/></w:r><w:r><w:t>) Dane nieobowiązkowe.</w:t></w:r>'
             '</w:p></w:footnote>')
    m = read_document(docx_bytes(body, footnotes=notes), "docx")
    assert [(r.text, r.anchor) for r in m.pages[0].runs] == [("Nazwisko1", "p[0]"),
                                                            ("1) Dane nieobowiązkowe.", "fn[7]/p[0]")]


def test_page_breaks_rendered_and_section():
    body = (p("Strona pierwsza") + '<w:p><w:r><w:lastRenderedPageBreak/><w:t>Strona druga</w:t></w:r></w:p>'
            + '<w:p><w:pPr><w:sectPr><w:type w:val="nextPage"/></w:sectPr></w:pPr><w:r><w:t>Koniec sekcji</w:t>'
            + '</w:r></w:p>' + p("Strona trzecia") + p("", ppr="<w:pageBreakBefore/>") + p("Nadal trzecia"))
    m = read_document(docx_bytes(body), "docx")
    assert [[r.text for r in pg.runs] for pg in m.pages] == [
        ["Strona pierwsza"], ["Strona druga", "Koniec sekcji"], ["Strona trzecia"], ["Nadal trzecia"]]


def test_text_box_in_a_flow_document_is_read_once():
    body = (p("Treść główna dokumentu, która przeważa nad polem tekstowym.")
            + p("Druga linia treści głównej, również dłuższa niż pole.")
            + '<w:p>' + textbox(100, 100, 100, 20, p("W ramce")) + '</w:p>')
    m = read_document(docx_bytes(body), "docx")
    assert m.source.reader == "docx.flow"
    assert [(r.text, r.anchor) for r in m.pages[0].runs][-1] == ("W ramce", "p[2]/txbx[0]/p[0]")
    assert _texts(m).count("W ramce") == 1


# ---------------------------------------------------------------- native documents: text boxes with geometry


def _native_doc() -> bytes:
    page1 = ('<w:p><w:pPr><w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="567" w:right="567" '
             'w:bottom="567" w:left="567"/></w:sectPr></w:pPr>'
             + textbox(200, 60, 180, 16, p("DEKLARACJA TESTOWA", rpr='<w:b/><w:sz w:val="28"/>'))
             + textbox(40, 120, 120, 12, p("Nazwisko", rpr='<w:sz w:val="16"/>'), p("Imię"))
             + shape(40, 140, 500, 0.5)                          # black bar: a horizontal line
             + shape(40, 160, 0.6, 30)                           # vertical line
             + shape(300, 160, 12, 12, fill=None, outline=True)  # a box
             + shape(300, 200, 100, 0.5, fill="FFFFFF")          # white: invisible
             + shape(300, 220, 100, 20, fill=None)               # no fill, no outline: invisible
             + '</w:p>')
    page2 = ('<w:p>' + textbox(10, 15, 50, 10, p("Druga"), rel_h="column", rel_v="paragraph")
             + textbox(10, 15, 50, 10, p("Nieznana pozycja"), rel_h="character", rel_v="paragraph") + '</w:p>'
             + p("Poza"))  # body text between the boxes: below 20 % of the text, so the document stays native
    return docx_bytes(page1 + page2)


@pytest.fixture(scope="module")
def native():
    return read_document(_native_doc(), "docx")


def test_native_pages_from_sections(native):
    assert native.source.reader == "docx.native"
    assert [pg.origin for pg in native.pages] == ["native", "native"]
    assert native.pages[0].width == pytest.approx(PT, abs=0.1) and native.pages[0].height == pytest.approx(841.9)


def test_native_runs_take_the_text_box_box(native):
    runs = native.pages[0].runs
    assert [r.text for r in runs] == ["DEKLARACJA TESTOWA", "Nazwisko", "Imię"], "fallback copy read twice?"
    title = runs[0]
    assert title.box == (200.0, 60.0, 380.0, 76.0) and title.bold and title.size == 14
    assert runs[1].box == runs[2].box == (40.0, 120.0, 160.0, 132.0) and runs[1].size == 8


def test_native_shapes(native):
    pg = native.pages[0]
    assert sorted(ln.box for ln in pg.lines) == [(40.0, 140.25, 540.0, 140.25), (40.3, 160.0, 40.3, 190.0)]
    assert [q.box for q in pg.rects] == [(300.0, 160.0, 312.0, 172.0)]


def test_native_paragraph_relative_and_unplaceable(native):
    pg = native.pages[1]
    assert [(r.text, r.box) for r in pg.runs] == [("Druga", (38.35, 43.35, 88.35, 53.35))]
    details = " | ".join(w.detail or "" for w in native.warnings)
    assert all(w.code == "UNREADABLE_PART" for w in native.warnings)
    assert "1 drawings" in details and "4 characters of body text" in details


# ---------------------------------------------------------------- broken and hostile files


def _zip(parts: dict[str, bytes], method: int = zipfile.ZIP_DEFLATED) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", method) as z:
        for k, v in parts.items():
            z.writestr(k, v)
    return buf.getvalue()


@pytest.mark.parametrize("data,code", [
    (b"zwykly tekst nazwany .docx", "UNREADABLE"),
    (b"", "UNREADABLE"),
    (_zip({"xl/workbook.xml": b"<workbook/>"}), "UNREADABLE"),
    (_zip({"word/document.xml": b"<w:document"}), "UNREADABLE"),
    (_zip({"word/document.xml": b'<?xml version="1.0"?><!DOCTYPE d [<!ENTITY x "y">]><d>&x;</d>'}), "UNREADABLE"),
    (_zip({"word/document.xml": b"<a>" + b" " * 5_000_000 + b"</a>"}), "TOO_LARGE"),
])
def test_broken_docx_is_a_reader_error(data, code):
    with pytest.raises(ReaderError) as e:
        read_document(data, "docx")
    assert e.value.code == code


def test_part_size_limit():
    data = docx_bytes(p("Treść"))
    with pytest.raises(ReaderError) as e:
        read_document(data, "docx", {"max_part_bytes": 100})
    assert e.value.code == "TOO_LARGE"


def test_empty_body_gives_one_empty_flow_page():
    m = read_document(docx_bytes(""), "docx")
    assert len(m.pages) == 1 and m.pages[0].origin == "flow" and not m.pages[0].runs

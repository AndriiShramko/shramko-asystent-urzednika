"""A8 TT: one synthetic form, three formats (PDF, DOCX, XLSX) built in code, must give the same matter fields.

The readers differ (pdf.native, docx.flow, xlsx), the meaning layer is shared: the same printed labels must come out
as the same fields with the same types and the same validators on the matter page. A drift here means one reader
loses or reshapes a label that the others keep, which the per-reader tests cannot see.
Labels are ASCII so that the standard PDF font draws them on every machine (no font file is needed).
"""
from __future__ import annotations

import io

import pytest

from app import pipeline
from app.config import Settings

SETTINGS = Settings.from_env({"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000"})
TITLE = "Wniosek o wydanie zaswiadczenia"
LABELS = ["Imie i nazwisko *", "Numer PESEL", "Data urodzenia", "Adres e-mail", "Numer telefonu", "Miejscowosc"]
CHOICE = ("Sposob odbioru", ["osobiscie", "poczta"])
LIBRARY_TABS = {"Dane", "Kontakt i zgody", "Strona końcowa"}


def pdf_form() -> bytes:
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 780, TITLE)
    c.setFont("Helvetica", 10)
    y = 730
    for lab in LABELS:
        c.drawString(72, y, lab)
        c.rect(220, y - 4, 300, 18)
        y -= 40
    c.drawString(72, y, CHOICE[0] + ":")
    x = 220
    for opt in CHOICE[1]:
        c.rect(x, y - 2, 9, 9)
        c.drawString(x + 14, y, opt)
        x += 120
    c.save()
    return buf.getvalue()


def docx_form() -> bytes:
    import docx as pydocx

    doc = pydocx.Document()
    doc.add_heading(TITLE, 1)
    table = doc.add_table(rows=len(LABELS), cols=2)
    table.style = "Table Grid"
    for i, lab in enumerate(LABELS):
        table.cell(i, 0).text = lab
    doc.add_paragraph(CHOICE[0] + ": " + "   ".join("☐ " + opt for opt in CHOICE[1]))
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def xlsx_form() -> bytes:
    import openpyxl
    from openpyxl.styles import Border, Font, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"] = TITLE
    ws["A1"].font = Font(bold=True, size=14)
    thin = Side(style="thin")
    for i, lab in enumerate(LABELS):
        row = 3 + 2 * i
        ws.cell(row, 1, lab)
        ws.cell(row, 2).border = Border(left=thin, right=thin, top=thin, bottom=thin)
    row = 3 + 2 * len(LABELS)
    ws.cell(row, 1, CHOICE[0] + ":")
    for j, opt in enumerate(CHOICE[1]):
        ws.cell(row, 2 + j, "☐ " + opt)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


MAKERS = {"pdf": pdf_form, "docx": docx_form, "xlsx": xlsx_form}


def matter_fields(form: dict) -> list[tuple[str, str, tuple[str, ...], tuple[str, ...]]]:
    """(title, type, validators, option names) of every non-section field outside the library tabs, in document order."""
    out: list[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            f = node.get("field")
            if isinstance(f, dict) and f.get("type") != "SECTION":
                out.append((f.get("title", ""), f.get("type", ""), tuple(sorted(map(str, f.get("validation", [])))),
                            tuple(o.get("name", "") for o in f.get("options", []))))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for tab in form["tabs"]:
        if tab.get("title") not in LIBRARY_TABS:
            walk(tab)
    return out


@pytest.fixture(scope="module")
def results() -> dict[str, pipeline.PipelineResult]:
    return {ext: pipeline.run(make(), f"form.{ext}", SETTINGS) for ext, make in MAKERS.items()}


def test_each_format_is_read_by_its_own_reader(results):
    readers = {ext: r.sidecar["converter"]["reader"] for ext, r in results.items()}
    assert readers == {"pdf": "pdf.native", "docx": "docx.flow", "xlsx": "xlsx"}


def test_every_printed_label_becomes_a_matter_field_in_every_format(results):
    for ext, r in results.items():
        titles = [t for t, *_ in matter_fields(r.form)]
        for lab in LABELS:
            assert lab.rstrip(" *") in titles, (ext, lab, titles)


def test_the_three_formats_give_the_same_matter_fields(results):
    got = {ext: matter_fields(r.form) for ext, r in results.items()}
    assert got["pdf"], "no matter field at all from the PDF"
    assert got["docx"] == got["pdf"], ("docx differs from pdf", got["docx"], got["pdf"])
    assert got["xlsx"] == got["pdf"], ("xlsx differs from pdf", got["xlsx"], got["pdf"])


def test_concept_validators_follow_the_label_in_every_format(results):
    for ext, r in results.items():
        by_title = {t: v for t, _, v, _ in matter_fields(r.form)}
        assert "PESEL" in by_title.get("Numer PESEL", ()), ext
        assert "EMAIL" in by_title.get("Adres e-mail", ()), ext
        types = {t: ty for t, ty, *_ in matter_fields(r.form)}
        assert types.get("Data urodzenia") == "DATEPICKER", ext


def test_the_choice_row_is_one_radio_with_the_printed_options_in_every_format(results):
    for ext, r in results.items():
        rows = [m for m in matter_fields(r.form) if m[0] == CHOICE[0]]
        assert len(rows) == 1, (ext, rows)
        assert rows[0][1] == "RADIO" and list(rows[0][3]) == CHOICE[1], (ext, rows)


def test_the_title_is_the_same_in_every_format(results):
    titles = {ext: r.form["title"] for ext, r in results.items()}
    assert len(set(titles.values())) == 1, titles

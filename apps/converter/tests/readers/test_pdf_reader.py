"""PDF reader on synthetic PDFs drawn with reportlab (design 5.1, 6.2; WP-F2a)."""
from __future__ import annotations

import pytest

from app import readers
from app.model.page import Page
from app.readers import ReaderError, read_document
from readers_builders import pdf_bytes

H = 841.89  # A4 height in points


def _form(c) -> None:  # noqa: ANN001
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, 800, "WNIOSEK TESTOWY")
    c.setFont("Helvetica", 9)
    c.drawString(56, 700, "Nazwa wnioskodawcy ..........................")
    c.drawString(56, 680, "Lewa kolumna")
    c.drawString(400, 680, "Prawa kolumna")
    c.setDash(4, 3)
    c.line(56, 650, 300, 650)
    c.setDash(1, 2)
    c.line(56, 640, 300, 640)
    c.setDash()
    c.setLineWidth(1)
    c.line(56, 630, 300, 630)
    c.rect(56, 600, 12, 12)                    # a box to tick
    c.rect(56, 580, 200, 1, stroke=0, fill=1)  # a thin filled rectangle is a line
    c.setFillColorRGB(1, 1, 1)
    c.rect(300, 560, 100, 30, stroke=0, fill=1)  # white background: not ink
    c.setFillColorRGB(0, 0, 0)
    c.acroForm.textfield(name="nip", x=100, y=500, width=140, height=14, maxlen=10, fieldFlags="comb")
    c.acroForm.checkbox(name="zgoda", x=100, y=450, size=12)
    c.acroForm.radio(name="tryb", value="a", x=100, y=420, size=12)
    c.acroForm.radio(name="tryb", value="b", x=130, y=420, size=12)
    c.acroForm.choice(name="kraj", options=["Polska", "Inny"], value="Polska", x=100, y=380, width=100, height=14)
    c.showPage()
    c.setFont("Helvetica", 9)
    c.drawString(56, 800, "1/2")  # a page with almost no text
    c.line(56, 700, 300, 700)
    c.showPage()


@pytest.fixture(scope="module")
def model():
    return read_document(pdf_bytes(_form), "pdf")


def _run(page: Page, text: str):
    hits = [r for r in page.runs if r.text == text]
    assert hits, f"no run {text!r} in {[r.text for r in page.runs]}"
    return hits[0]


def test_source_and_pages(model):
    assert model.source.format == "pdf" and model.source.reader == "pdf.native"
    assert model.source.pages == 2 and len(model.source.sha256) == 64
    p1 = model.pages[0]
    assert p1.origin == "native" and p1.width == pytest.approx(595.28, abs=0.01) and p1.height == pytest.approx(H, abs=0.01)


def test_runs_have_top_left_boxes_size_and_weight(model):
    title = _run(model.pages[0], "WNIOSEK TESTOWY")
    assert title.bold and title.size == 14 and title.conf == 1.0
    x0, y0, x1, y1 = title.box
    assert x0 == pytest.approx(200, abs=0.5)
    assert y0 < y1 and y1 == pytest.approx(H - 800 + 3.5, abs=4)  # top-left origin: near the top of the page
    assert not _run(model.pages[0], "Lewa kolumna").bold


def test_leader_is_its_own_run_and_columns_split(model):
    p1 = model.pages[0]
    label = _run(p1, "Nazwa wnioskodawcy")
    leader = _run(p1, "..........................")
    assert leader.box[0] > label.box[2] - 0.01 and leader.box[1] == pytest.approx(label.box[1], abs=0.5)
    _run(p1, "Lewa kolumna"), _run(p1, "Prawa kolumna")


def test_lines_rects_and_styles(model):
    p1 = model.pages[0]
    styles = sorted(ln.style for ln in p1.lines if ln.box[0] == pytest.approx(56, abs=0.5) and ln.box[2] == pytest.approx(300, abs=0.5))
    assert styles == ["dashed", "dotted", "solid"]
    thin = [ln for ln in p1.lines if ln.box[2] == pytest.approx(256, abs=0.5)]
    assert len(thin) == 1 and thin[0].box[1] == thin[0].box[3]
    boxes = [q.box for q in p1.rects]
    assert any(b[2] - b[0] == pytest.approx(12, abs=0.5) and b[3] - b[1] == pytest.approx(12, abs=0.5) for b in boxes)
    assert not any(b[2] - b[0] == pytest.approx(100, abs=0.5) for b in boxes), "white background read as a box"


def test_declared_fields(model):
    assert [x.name for x in model.pages[0].widgets].count("tryb") == 2
    w = {x.name: x for x in model.pages[0].widgets}
    assert w["nip"].kind == "text" and w["nip"].max_len == 10 and w["nip"].comb
    assert w["nip"].box[1] == pytest.approx(H - 514, abs=0.5)
    assert w["zgoda"].kind == "checkbox" and not w["zgoda"].comb
    assert w["tryb"].kind == "radio"
    assert w["kraj"].kind == "choice" and w["kraj"].options == ["Polska", "Inny"]


def test_page_without_text_is_kept_with_a_warning(model):
    p2 = model.pages[1]
    assert [r.text for r in p2.runs] == ["1/2"] and len(p2.lines) == 1
    warn = [x for x in model.warnings if x.page == 2]
    assert len(warn) == 1 and warn[0].code == "UNREADABLE_PART"
    assert not [x for x in model.warnings if x.page == 1]


def test_textless_page_takes_the_hook_when_one_is_registered(monkeypatch):
    calls = []

    def fake(data, index, number, ids, options):  # noqa: ANN001
        calls.append(number)
        return Page(number=number, width=595.28, height=H, origin="ocr")

    monkeypatch.setitem(readers._HOOKS, "pdf.textless_page", fake)
    m = read_document(pdf_bytes(_form), "pdf")
    assert calls == [2] and m.pages[1].origin == "ocr"
    assert [(x.code, x.page) for x in m.warnings] == [("OCR_USED", 2)]


def test_ids_unique_and_deterministic(model):
    again = read_document(pdf_bytes(_form), "pdf")
    assert again.to_json_bytes() == model.to_json_bytes()


@pytest.mark.parametrize("data", [b"", b"plain text, not a PDF", b"%PDF-1.4\n%garbage without objects",
                                  b"PK\x03\x04 a zip named pdf"])
def test_broken_pdf_is_a_reader_error(data):
    with pytest.raises(ReaderError) as e:
        read_document(data, "pdf")
    assert e.value.code in ("UNREADABLE", "ENCRYPTED") and "Traceback" not in e.value.reason


def test_truncated_pdf_is_a_reader_error_or_a_valid_model():
    data = pdf_bytes(_form)
    try:
        m = read_document(data[: len(data) // 2], "pdf")
    except ReaderError as e:
        assert e.code == "UNREADABLE"
    else:
        assert m.source.pages == len(m.pages)


def test_page_limit():
    with pytest.raises(ReaderError) as e:
        read_document(pdf_bytes(_form), "pdf", {"max_pages": 1})
    assert e.value.code == "TOO_LARGE"

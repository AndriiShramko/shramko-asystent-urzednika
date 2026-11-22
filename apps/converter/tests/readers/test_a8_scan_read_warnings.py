"""AUDIT-8 VE-2 (04-F1, 28-F7): a scan page with ink that OCR reads as nothing, or as mostly unconfident words (a rotated
or blurred scan), must carry a page warning; a PDF page without ink must not claim it was read from its pixels."""
from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw

from app import readers
from app.readers import _ocr

W = 1654
PAGE_H = round(W * 2 ** 0.5)


class Engine:
    name = "fake"

    def __init__(self, words):
        self.words = words

    def read(self, png, lang, timeout):
        return self.words


@pytest.fixture(autouse=True)
def reset_engine():
    yield
    _ocr.set_engine(None)


def _png_with_ink() -> bytes:
    page = Image.new("L", (W, PAGE_H), 255)
    ImageDraw.Draw(page).text((100, 100), "x", fill=0)
    out = io.BytesIO()
    page.save(out, format="PNG")
    return out.getvalue()


def _words(confs):
    return [_ocr.Word(f"w{i}", 100 + 20 * i, 100, 115 + 20 * i, 130, c, (1, 1, 1)) for i, c in enumerate(confs)]


def _page_warnings(model, page=1):
    return [w for w in model.warnings if w.code == "UNREADABLE_PART" and w.page == page]


def test_ink_but_no_words_is_a_page_warning():
    _ocr.set_engine(Engine([]))
    model = readers.read_document(_png_with_ink(), "png")
    warns = _page_warnings(model)
    assert warns and "not read" in warns[0].detail


def test_mostly_unconfident_words_are_a_page_warning():
    # a rotated scan measured in V0: 32 % of the words at confidence 0.6 or more
    _ocr.set_engine(Engine(_words([0.9] * 3 + [0.3] * 7)))
    model = readers.read_document(_png_with_ink(), "png")
    warns = _page_warnings(model)
    assert warns and "confiden" in warns[0].detail
    assert len(model.pages[0].runs) == 10          # the words are kept, only flagged


def test_a_well_read_page_stays_quiet():
    # the weakest partner page measured in V0 had 58 % confident words
    _ocr.set_engine(Engine(_words([0.9] * 6 + [0.3] * 4)))
    model = readers.read_document(_png_with_ink(), "png")
    assert model.warnings == []


def _blank_pdf() -> bytes:
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595.28, 841.89))
    c.showPage()
    c.save()
    return buf.getvalue()


def test_a_blank_pdf_page_does_not_claim_ocr():
    _ocr.set_engine(Engine([]))
    model = readers.read_document(_blank_pdf(), "pdf")
    assert "OCR_USED" not in [w.code for w in model.warnings]

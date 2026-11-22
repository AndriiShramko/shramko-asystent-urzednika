"""Audit 8 SL1, S1 (SCAN_PREP tokens "glyph", "leader", "thick"), all on the OCR words of the page:
- glyph: a small closed box inside a word of two or more letters is the counter of a letter, not a checkbox;
- leader: a dotted leader the OCR did not read as dots becomes a run of dots, so the finder sees a place to write;
- thick: a ruled line too thick for the finder (over 1.5 pt) is kept as a thin line through its middle.
Without OCR words, or without the tokens, the page is the page of before."""
from __future__ import annotations

import re

import pytest
from PIL import Image, ImageDraw

from app.readers import _ocr, _raster, image
from app.readers._base import Ids, ReadOptions

W, H = 1654, 2339


@pytest.fixture(autouse=True)
def no_engine():
    _ocr.set_engine(None, disabled=True)
    yield
    _ocr.set_engine(None)


class Engine:
    name = "fake"

    def __init__(self, words):
        self.words = words

    def read(self, png, lang, timeout):
        return self.words


def form() -> Image.Image:
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    d.rectangle((100, 300, 1500, 303), fill=0)               # a ruled line 1401 x 4
    d.rectangle((900, 500, 936, 536), outline=0, width=3)    # one checkbox 37 x 37
    for x in range(200, 800, 12):                             # a dotted leader, 4 px dots, pitch 12
        d.rectangle((x, 800, x + 3, 803), fill=0)
    d.rectangle((300, 1000, 317, 1017), outline=0, width=2)  # an 18 x 18 ring: the counter of a big letter
    d.rectangle((100, 1200, 1500, 1205), fill=0)             # a 6 px thick rule
    return img


WORDS = [_ocr.Word("Imie", 100, 770, 180, 806, 0.9, (1, 1, 1)),
         _ocr.Word("Odbiorca", 280, 985, 480, 1030, 0.9, (1, 2, 1))]


def read(tokens, words=WORDS):
    if words is not None:
        _ocr.set_engine(Engine(words))
    page, _ = image.read_strip(form(), 1, Ids(), ReadOptions(scan_prep=frozenset(tokens)))
    return page


def ring(page):
    return [r for r in page.rects if abs(r.box[0] - 108) < 2 and abs(r.box[1] - 360) < 2]


def checkbox(page):
    return [r for r in page.rects if abs(r.box[0] - 324) < 2 and abs(r.box[1] - 180) < 2]


def test_glyph_drops_the_counter_and_keeps_the_checkbox():
    assert ring(read(set())) and checkbox(read(set()))       # today the counter is a box
    page = read({"glyph"})
    assert not ring(page)
    assert checkbox(page)


def test_leader_becomes_a_run_of_dots():
    assert not [r for r in read(set()).runs if re.fullmatch(r"\.{8,}", r.text)]
    dots = [r for r in read({"leader"}).runs if re.fullmatch(r"\.{8,}", r.text)]
    assert len(dots) == 1
    assert abs(dots[0].box[0] - 72.0) < 1 and abs(dots[0].box[3] - 289.44) < 1


def test_leader_the_ocr_read_is_not_doubled():
    words = WORDS + [_ocr.Word("..........", 198, 795, 802, 806, 0.6, (1, 1, 1))]
    dots = [r for r in read({"leader"}, words).runs if re.fullmatch(r"\.{8,}", r.text)]
    assert [r.text for r in dots] == [".........."]


def test_thick_rule_becomes_a_thin_line():
    def rule(page):
        return [ln for ln in page.lines if abs(ln.box[1] - 432) < 2.5 and ln.box[2] - ln.box[0] > 400]
    assert all(ln.box[3] - ln.box[1] > 1.5 for ln in rule(read(set())))
    thin = rule(read({"thick"}))
    assert len(thin) == 1 and thin[0].box[3] - thin[0].box[1] <= 1.0
    thin4 = [ln for ln in read({"thick"}).lines if abs(ln.box[1] - 108) < 1 and ln.box[2] - ln.box[0] > 400]
    assert thin4 and thin4[0].box[3] - thin4[0].box[1] == pytest.approx(4 * _raster.PX_TO_PT, abs=0.02)  # 1.44 pt stays


def test_without_words_the_tokens_change_nothing():
    a = read({"glyph", "leader", "thick"}, words=None)
    b = read(set(), words=None)
    assert a.model_dump() == b.model_dump()
    assert a.runs == []


def test_without_tokens_the_page_is_the_page_of_before():
    a, b = read(set()), read(set())
    assert a.model_dump() == b.model_dump()

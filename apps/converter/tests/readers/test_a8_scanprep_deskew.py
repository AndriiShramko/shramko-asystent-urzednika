"""Audit 8 SL1, S2 (SCAN_PREP token "deskew"): a page strip tilted by up to 5 degrees is turned level before
binarisation and shape detection (projection profile of rows); below 0.3 degrees the strip is the same object."""
from __future__ import annotations

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


def draw_form() -> Image.Image:
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    d.text((100, 100), "WNIOSEK", fill=0)
    d.rectangle((100, 300, 1500, 303), fill=0)               # a ruled line 1401 x 4
    d.line((100, 400, 100, 700), fill=0, width=3)            # a vertical rule
    for i in range(11):                                       # a comb of 11 cells, 40 x 50
        x = 200 + i * 40
        d.rectangle((x, 500, x + 40, 550), outline=0, width=3)
    d.rectangle((900, 500, 936, 536), outline=0, width=3)    # one checkbox 37 x 37
    for y in range(900, 2100, 60):                            # lines of "text"
        d.rectangle((150, y, 1400, y + 12), fill=0)
    return img


@pytest.mark.parametrize("turn", [2.0, -1.2, 3.5])
def test_tilted_page_is_found_and_levelled(turn):
    tilted = draw_form().rotate(turn, Image.Resampling.BICUBIC, fillcolor=255)
    level, a = _raster.deskew(tilted)
    assert abs(a + turn) <= 0.15
    rules = [b for b in _raster.detect(_raster.binarize(level)).hlines if b[2] - b[0] >= 1350]
    assert len(rules) == 1


def test_tilted_rule_is_lost_today():
    tilted = draw_form().rotate(2.0, Image.Resampling.BICUBIC, fillcolor=255)
    assert not [b for b in _raster.detect(_raster.binarize(tilted)).hlines if b[2] - b[0] >= 1350]


def test_upright_page_is_the_same_object():
    p = draw_form()
    out, a = _raster.deskew(p)
    assert out is p and a == 0.0


def test_page_of_vertical_rules_only_is_not_turned():
    p = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(p)
    for x in range(200, 1500, 150):
        d.rectangle((x, 200, x + 3, 2100), fill=0)
    out, a = _raster.deskew(p)
    assert out is p and a == 0.0


def test_blank_page_is_the_same_object():
    p = Image.new("L", (W, H), 255)
    out, a = _raster.deskew(p)
    assert out is p and a == 0.0


def test_reader_levels_with_the_token_only():
    tilted = draw_form().rotate(2.0, Image.Resampling.BICUBIC, fillcolor=255)

    def long_rules(tokens):
        page, _ = image.read_strip(tilted, 1, Ids(), ReadOptions(scan_prep=frozenset(tokens)))
        return [ln for ln in page.lines if ln.box[2] - ln.box[0] >= 1350 * _raster.PX_TO_PT]

    assert not long_rules(set())
    assert len(long_rules({"deskew"})) == 1

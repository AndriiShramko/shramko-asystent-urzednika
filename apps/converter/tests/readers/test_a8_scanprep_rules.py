"""Audit 8 SL1, S4 (SCAN_PREP token "rules"): an open solid rule (at least 40 pt long, not the edge of a box, not
closed by verticals, not inside a table cell) with text left of it or above it is a place to write, so the page gets
a run of underscores on it, as a born-digital form has. Underlines of text and table grids stay plain lines."""
from __future__ import annotations

import re

import pytest
from PIL import Image, ImageDraw

from app.readers import _ocr, image
from app.readers._base import Ids, ReadOptions

W, H = 1654, 2339
RULES = frozenset({"rules"})


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


def word(text, x0, y0, x1, y1):
    return _ocr.Word(text, x0, y0, x1, y1, 0.9, (1, 1, 1))


def unders(draw, words, tokens=RULES):
    img = Image.new("L", (W, H), 255)
    draw(ImageDraw.Draw(img))
    _ocr.set_engine(Engine(words))
    page, _ = image.read_strip(img, 1, Ids(), ReadOptions(scan_prep=frozenset(tokens)))
    return [r for r in page.runs if re.fullmatch(r"_{8,}", r.text)]


def rule_after_label(d):
    d.rectangle((420, 600, 820, 602), fill=0)                 # a 400 px rule, 3 px thick


LABEL = [word("Nazwisko", 200, 570, 400, 602)]


def test_rule_right_of_a_label_is_a_place():
    got = unders(rule_after_label, LABEL)
    assert len(got) == 1
    assert abs(got[0].box[0] - 151.2) < 1 and abs(got[0].box[2] - 295.56) < 1


def test_without_the_token_nothing_is_added():
    assert unders(rule_after_label, LABEL, set()) == []


def test_rule_closed_by_verticals_is_not_a_place():
    def draw(d):
        rule_after_label(d)
        d.rectangle((420, 520, 422, 602), fill=0)
        d.rectangle((818, 520, 820, 602), fill=0)
    assert unders(draw, LABEL) == []


def test_table_grid_is_not_a_place():
    def draw(d):
        for i in range(4):
            d.rectangle((300, 600 + i * 120, 1300, 602 + i * 120), fill=0)
            d.rectangle((300 + i * 333, 600, 302 + i * 333, 962), fill=0)
    words = [word("Lp", 320, 640, 380, 680), word("Nazwa", 660, 640, 800, 680), word("Kwota", 990, 640, 1120, 680)]
    assert unders(draw, words) == []


def test_rule_with_no_text_near_is_not_a_place():
    assert unders(rule_after_label, [word("Uwagi", 200, 1500, 330, 1540)]) == []


def test_underline_of_a_heading_is_not_a_place():
    def draw(d):
        d.rectangle((200, 640, 900, 642), fill=0)
    words = [word("Informacja", 200, 590, 520, 632), word("dodatkowa", 540, 590, 900, 632)]
    assert unders(draw, words) == []


def test_rule_the_ocr_read_as_underscores_is_not_doubled():
    words = LABEL + [word("________________", 418, 585, 822, 604)]
    assert [r.text for r in unders(rule_after_label, words)] == ["________________"]  # the OCR's run only


def test_rule_under_a_label_line_above_is_a_place():
    def draw(d):
        d.rectangle((200, 700, 1200, 702), fill=0)
    words = [word("Adres", 200, 610, 330, 650), word("zamieszkania:", 340, 610, 600, 650)]
    assert len(unders(draw, words)) == 1

"""Wave 11 SCANQ: a piece of a dotted leader that the OCR read as letters ("eeeeeeeeee« szerokość", "eeeeeeeev. razem",
"e..e.eees eeer eee eee eee ke eee działka nr ewid": labels of set scans 06 in the verified image), alone or glued
to the word before it ("miejscowości..................eeveeeeseeeseeee": set scan 01), becomes the dots it is, told
by its ink (one low row of small marks), not by its text. Words printed with letters stay as read."""
from __future__ import annotations

import re

import pytest
from PIL import Image, ImageDraw

from app import pipeline
from app.config import Settings
from app.readers import _ocr, _raster, image
from app.readers._base import Ids, ReadOptions

W, H = 1654, 2339
SETTINGS = Settings.from_env({})


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


def letters(d: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    """Ink as tall as printed letters (28 px), in strokes: a stand-in for a word."""
    for x in range(x0, x1, 14):
        d.rectangle((x, y, x + 6, y + 28), fill=0)


def dots(d: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    for x in range(x0, x1, 12):                               # 4 px dots, pitch 12: a dotted leader
        d.rectangle((x, y, x + 3, y + 3), fill=0)


def page_06() -> Image.Image:
    """One line as on set 06: "długość ......... szerokość ......... razem ........."."""
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    letters(d, 100, 250, 400)
    dots(d, 270, 520, 424)
    letters(d, 540, 720, 400)
    dots(d, 740, 990, 424)
    letters(d, 1010, 1110, 400)
    dots(d, 1130, 1380, 424)
    d.rectangle((100, 800, 700, 802), fill=0)                 # a solid rule with a word box over it
    return img


# the texts are the ones the verified image printed for set 06 (PNG, JPG, JPEG), the boxes are of this drawing
WORDS_06 = [
    _ocr.Word("długość", 100, 398, 252, 432, 0.95, (1, 1, 1)),
    _ocr.Word("eeeeeeeeee«", 268, 420, 512, 430, 0.31, (1, 1, 1)),
    _ocr.Word("szerokość", 540, 398, 722, 432, 0.94, (1, 1, 1)),
    _ocr.Word("e-eeeeeeee", 738, 420, 982, 430, 0.28, (1, 1, 1)),
    _ocr.Word("razem", 1010, 398, 1112, 432, 0.95, (1, 1, 1)),
    _ocr.Word("eeeeeeeev.", 1128, 420, 1372, 430, 0.22, (1, 1, 1)),
]


def read(words, img=None):
    _ocr.set_engine(Engine(words))
    page, _ = image.read_strip(img or page_06(), 1, Ids(), ReadOptions())
    return page


def test_dots_read_as_letters_become_dots():
    texts = [r.text for r in read(WORDS_06).runs]
    assert texts[0] == "długość" and texts[2] == "szerokość" and texts[4] == "razem"
    for t in (texts[1], texts[3], texts[5]):
        assert re.fullmatch(r"\.{8,}", t), t
    assert not any("eee" in t for t in texts)


def test_the_number_of_dots_is_the_number_on_the_paper():
    ink = _raster.binarize(page_06())
    assert image._dot_parts(ink, WORDS_06[1]) == (0, 0, 21)   # x = 270 .. 510 step 12
    assert image._dot_parts(ink, WORDS_06[0]) == (0, 0, 0)    # letters only


# set scan 01 (PNG, JPEG) in the verified image: the word and its leader came back as ONE word, box 585 x 30, conf 0
GLUED = ["miejscowości..................eeveeeeseeeseeee", "micjscowOŚCI..................reeeeeeeeeee",
         "ulicy?.........................eesesesese", "ulicyeeeeeeeeee"]


@pytest.mark.parametrize("text", GLUED)
def test_a_leader_glued_to_its_word_keeps_the_word(text):
    words = [_ocr.Word(text, 100, 398, 512, 432, 0.0, (1, 1, 1)), WORDS_06[2]]
    got = read(words).runs[0].text
    head = re.split(r"\.{3,}|eee", text)[0]
    assert got == head + "." * 21, got


def test_a_leader_glued_before_its_word_keeps_the_word():
    words = [_ocr.Word("eeeeeeee....szerokość", 268, 398, 722, 432, 0.05, (1, 1, 1))]
    assert read(words).runs[0].text == "." * 21 + "szerokość"


def test_a_word_of_letters_is_never_touched_whatever_its_text():
    words = [_ocr.Word("eeeeeeeeee", 100, 398, 252, 432, 0.3, (1, 1, 1)),      # tall ink: letters, not dots
             _ocr.Word("Zeee", 540, 398, 722, 432, 0.3, (1, 1, 1))]
    assert [r.text for r in read(words).runs] == ["eeeeeeeeee", "Zeee"]


def test_a_word_the_engine_is_sure_of_is_never_touched():
    words = [_ocr.Word("oraz", 268, 420, 512, 430, 0.92, (1, 1, 1))]
    assert [r.text for r in read(words).runs] == ["oraz"]


def test_small_print_is_not_a_row_of_dots():
    """Set scan 01, page 2: "w", "na", "oraz", "numeru" of the small-print clause have ink 10 px tall."""
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    for x in range(270, 330, 9):
        d.rectangle((x, 420, x + 2, 429), fill=0)             # strokes 3 px wide and 10 px tall
    words = [_ocr.Word("numeru", 268, 418, 332, 432, 0.4, (1, 1, 1))]
    assert [r.text for r in read(words, img).runs] == ["numeru"]


def test_dots_read_as_dots_and_a_rule_stay_as_read():
    words = [_ocr.Word("..........", 268, 420, 512, 430, 0.2, (1, 1, 1)),      # no letter in the text: not ours
             _ocr.Word("eeeeee", 100, 796, 700, 806, 0.2, (1, 2, 1)),          # a solid rule read as letters: not dots
             _ocr.Word("ke", 740, 420, 760, 430, 0.2, (1, 1, 1))]              # two dots: ink this low is no letter
    assert [r.text for r in read(words).runs] == ["..........", "eeeeee", ".."]


def test_two_stacked_rows_of_dots_are_not_one_leader():
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    dots(d, 270, 520, 420)
    dots(d, 270, 520, 440)
    words = [_ocr.Word("eeeeee", 268, 416, 512, 446, 0.2, (1, 1, 1))]          # 24 px between the rows: not one row
    assert [r.text for r in read(words, img).runs] == ["eeeeee"]


def _titles(obj, acc=None):
    acc = [] if acc is None else acc
    if isinstance(obj, dict):
        if isinstance(obj.get("title"), str):
            acc.append(obj["title"])
        for v in obj.values():
            _titles(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _titles(v, acc)
    return acc


def test_in_the_form_the_leader_is_the_place_and_not_the_label():
    out = __import__("io").BytesIO()
    page_06().save(out, format="PNG")
    _ocr.set_engine(Engine(WORDS_06))
    res = pipeline.run(out.getvalue(), "scan.png", SETTINGS)
    titles = [t.lower() for t in _titles(res.form)]
    assert not any("eee" in t for t in titles), titles
    assert any("szerokość" in t for t in titles), titles
    assert any("razem" in t for t in titles), titles

"""Audit 8 SL1, S3 (SCAN_PREP token "scale"): every page strip of a scan is brought to A4 at 200 dpi before OCR and
shape detection, so the pixel thresholds of `_raster` and Tesseract see the size they were made for. A strip within
10 % of that size is left alone (the same object); the factor is capped at 3 and by the pixel budget."""
from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw

from app import readers
from app.readers import _ocr, _raster
from app.readers._base import ReadOptions

W = 1654


@pytest.fixture(autouse=True)
def no_engine():
    _ocr.set_engine(None, disabled=True)
    yield
    _ocr.set_engine(None)


class WidthEngine:
    name = "fake"

    def __init__(self):
        self.widths = []

    def read(self, png, lang, timeout):
        self.widths.append(Image.open(io.BytesIO(png)).size[0])
        return [_ocr.Word("Wniosek", 100, 100, 300, 140, 0.9, (1, 1, 1))]


def png_bytes(img):
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def half_size_form() -> Image.Image:
    """A form drawn at 100 dpi: 827 x 1169 pixels."""
    img = Image.new("L", (827, 1169), 255)
    d = ImageDraw.Draw(img)
    d.rectangle((50, 150, 750, 151), fill=0)
    d.rectangle((450, 250, 468, 268), outline=0, width=2)
    return img


def test_low_dpi_strip_is_scaled_to_a4_at_200_dpi():
    out, f = _raster.normalize(half_size_form(), 120_000_000)
    assert out.size[0] == W and abs(out.size[1] - 2338) <= 1
    assert abs(f - 2.0) < 0.01


@pytest.mark.parametrize("size", [(1654, 2339), (1700, 2200), (1560, 2206)])
def test_strip_near_200_dpi_is_the_same_object(size):
    img = Image.new("L", size, 255)
    out, f = _raster.normalize(img, 120_000_000)
    assert out is img and f == 1.0


def test_300_dpi_strip_is_scaled_down():
    out, f = _raster.normalize(Image.new("L", (2480, 3508), 255), 120_000_000)
    assert out.size[0] == W and f < 1


def test_landscape_page_keeps_its_long_side_at_a4():
    out, _ = _raster.normalize(Image.new("L", (1169, 827), 255), 120_000_000)
    assert abs(out.size[0] - 2339) <= 1


def test_factor_is_capped_at_3_and_by_the_pixel_budget():
    out, f = _raster.normalize(Image.new("L", (300, 424), 255), 120_000_000)
    assert f == 3.0 and out.size == (900, 1272)
    out, f = _raster.normalize(half_size_form(), 2_000_000)
    assert out.size[0] * out.size[1] <= 2_000_000 and 1.0 < f < 2.0


def test_reader_scales_with_the_token_and_warns():
    eng = WidthEngine()
    _ocr.set_engine(eng)
    m = readers.read_document(png_bytes(half_size_form()), "png", ReadOptions(scan_prep=frozenset({"scale"})))
    assert eng.widths == [W]
    assert abs(m.pages[0].width - 595.44) < 0.5
    assert any("scaled from about 100 dpi" in (w.detail or "") for w in m.warnings)
    assert any(abs(r.box[0] - 36.0) < 0.5 for r in m.pages[0].runs)  # word box at 100 px of the 1654-px page = 36 pt


def test_reader_without_the_token_is_the_reader_of_before():
    eng = WidthEngine()
    _ocr.set_engine(eng)
    m = readers.read_document(png_bytes(half_size_form()), "png", ReadOptions())
    assert eng.widths == [827]
    assert abs(m.pages[0].width - 297.72) < 0.01
    assert not any("scaled from" in (w.detail or "") for w in m.warnings)


def test_tiff_frames_are_scaled_too():
    eng = WidthEngine()
    _ocr.set_engine(eng)
    out = io.BytesIO()
    half_size_form().save(out, format="TIFF")
    m = readers.read_document(out.getvalue(), "tiff", ReadOptions(scan_prep=frozenset({"scale"})))
    assert eng.widths == [W] and abs(m.pages[0].width - 595.44) < 0.5

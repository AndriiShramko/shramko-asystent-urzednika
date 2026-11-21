"""WP-F2c: the image reader on synthetic scans drawn with Pillow (no Tesseract needed); the OCR adapter with a fake
engine and with a faked subprocess. One test needs the real program and carries the marker `tesseract`."""
from __future__ import annotations

import io
import time

import pytest
from PIL import Image, ImageDraw

from app import readers
from app.readers import _ocr, _raster
from app.readers._base import ReaderError, ReadOptions

W = 1654
PAGE_H = round(W * 2 ** 0.5)  # 2339


def blank_page() -> Image.Image:
    return Image.new("L", (W, PAGE_H), 255)


def draw_form(img: Image.Image) -> None:
    d = ImageDraw.Draw(img)
    d.text((100, 100), "WNIOSEK", fill=0)
    d.rectangle((100, 300, 1500, 303), fill=0)               # a ruled line 1401 x 4
    d.line((100, 400, 100, 700), fill=0, width=3)            # a vertical rule
    for i in range(11):                                       # a comb of 11 cells, shared borders, 40 x 50
        x = 200 + i * 40
        d.rectangle((x, 500, x + 40, 550), outline=0, width=3)
    d.rectangle((900, 500, 936, 536), outline=0, width=3)    # one checkbox 37 x 37
    for x in range(200, 800, 12):                             # a dotted leader, 4 px dots, pitch 12
        d.rectangle((x, 800, x + 3, 803), fill=0)


def png_bytes(img: Image.Image, **kw) -> bytes:
    out = io.BytesIO()
    img.save(out, format="PNG", **kw)
    return out.getvalue()


@pytest.fixture(autouse=True)
def no_engine():
    _ocr.set_engine(None, disabled=True)
    yield
    _ocr.set_engine(None)


class FakeEngine:
    name = "fake"

    def __init__(self, words=None, error=None):
        self.words, self.error, self.calls = words or [], error, 0

    def read(self, png, lang, timeout):
        self.calls += 1
        assert lang == "pol+eng" and Image.open(io.BytesIO(png)).size[0] == W
        if self.error:
            raise _ocr.OcrError(self.error)
        return self.words


# ---------------------------------------------------------------- decoding


def test_decode_drops_metadata_and_applies_orientation():
    img = Image.new("RGB", (60, 30), (255, 255, 255))
    exif = Image.Exif()
    exif[0x0112] = 6          # rotated: the pixels must come out 30 x 60
    exif[0x010E] = "description of a scan"
    jpeg = io.BytesIO()
    img.save(jpeg, format="JPEG", exif=exif)
    assert b"description of a scan" in jpeg.getvalue()
    out = _raster.decode(jpeg.getvalue(), ReadOptions())
    assert out.mode == "L" and out.size == (30, 60) and out.info == {} and not out.getexif()
    from PIL import PngImagePlugin
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Author", "somebody")
    out = _raster.decode(png_bytes(img, pnginfo=meta, dpi=(72, 72)), ReadOptions())
    assert out.info == {}


def test_decode_lays_transparency_on_white():
    rgba = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    assert _raster.decode(png_bytes(rgba), ReadOptions()).getextrema() == (255, 255)


def test_decode_refuses_other_formats_and_big_images_before_decoding():
    gif = io.BytesIO()
    Image.new("L", (5, 5)).save(gif, format="GIF")
    with pytest.raises(ReaderError) as e:  # decode() is the JPEG/PNG door; the other formats use decode_frames()
        _raster.decode(gif.getvalue(), ReadOptions())
    assert e.value.code == "UNREADABLE"
    big = png_bytes(Image.new("L", (2000, 2000), 255))
    with pytest.raises(ReaderError) as e:
        _raster.decode(big, ReadOptions(max_pixels=1_000_000))
    assert e.value.code == "TOO_LARGE"
    with pytest.raises(ReaderError):
        readers.read_document(big[: len(big) // 2], "png")  # truncated: a 422, not a trace


# ---------------------------------------------------------------- cutting


def test_tall_scan_is_cut_into_pages_at_white_bands():
    stack = Image.new("L", (W, PAGE_H * 3), 255)
    d = ImageDraw.Draw(stack)
    for k in range(3):
        for y in range(k * PAGE_H + 200, k * PAGE_H + PAGE_H - 160, 20):  # text-like stripes per page
            d.rectangle((100, y, 1500, y + 8), fill=0)
    cuts, unsnapped = _raster.cut_points(_raster.binarize(stack))
    assert len(cuts) == 4 and unsnapped == []
    for c in cuts[1:3]:
        assert any(abs(c - k * PAGE_H) <= 150 for k in (1, 2))
        row = stack.crop((0, c, W, c + 1)).getextrema()
        assert row == (255, 255), "a cut goes through a white row"


def test_cut_without_white_band_is_reported():
    stack = Image.new("L", (W, PAGE_H * 2), 0)
    cuts, unsnapped = _raster.cut_points(_raster.binarize(Image.blend(stack, Image.new("L", stack.size, 90), 0.0)))
    assert len(cuts) <= 3  # all black becomes light-on-dark and inverted to blank: no ink, snaps anywhere


@pytest.mark.parametrize("pages", [1, 2, 6])
def test_page_count_from_height(pages):
    stack = Image.new("L", (W, PAGE_H * pages), 255)
    ImageDraw.Draw(stack).text((100, 100), "x", fill=0)
    model = readers.read_document(png_bytes(stack), "png")
    assert len(model.pages) == pages and model.source.pages == pages
    assert all(p.origin == "ocr" and p.width == pytest.approx(W * 0.36, abs=0.01) for p in model.pages)


def test_a_sixteen_page_scan_of_37424_pixels_is_sixteen_pages():
    stack = Image.new("L", (W, 37424), 255)
    t0 = time.time()
    model = readers.read_document(png_bytes(stack, compress_level=1), "png")
    assert len(model.pages) == 16
    assert time.time() - t0 < 20


# ---------------------------------------------------------------- shapes


def test_shapes_lines_boxes_comb_and_leader():
    page = blank_page()
    draw_form(page)
    s = _raster.detect(_raster.binarize(page))
    assert any(abs(b[0] - 100) <= 2 and b[2] - b[0] >= 1395 and abs(b[1] - 300) <= 2 for b in s.hlines)
    assert any(abs(b[0] - 100) <= 3 and b[3] - b[1] >= 295 for b in s.vlines)
    # the comb: eleven cells with equal width and equal (here negative, shared border) gap
    assert len(s.combs) == 1 and len(s.combs[0]) == 11
    assert {b[2] - b[0] for b in s.combs[0]} <= set(range(40, 47))
    # the checkbox is a box, not part of the comb
    assert any(abs(b[0] - 900) <= 3 and abs(b[2] - 937) <= 3 and abs(b[1] - 500) <= 3 for b in s.boxes)
    assert not any(900 <= b[0] <= 937 for b in s.combs[0])
    # the leader
    assert len(s.leaders) == 1 and s.leaders[0][0] <= 205 and s.leaders[0][2] >= 790


def test_letters_and_plain_text_make_no_boxes():
    page = blank_page()
    d = ImageDraw.Draw(page)
    for y in range(100, 1500, 30):
        d.text((100, y), "EBHD TEXT Wniosek o wydanie decyzji 0123456789 IIII", fill=0)
    s = _raster.detect(_raster.binarize(page))
    assert s.boxes == [] and s.combs == [] and s.leaders == []


def test_blank_page_is_quiet_and_fast():
    t0 = time.time()
    s = _raster.detect(_raster.binarize(blank_page()))
    assert (s.hlines, s.vlines, s.boxes, s.leaders) == ([], [], [], [])
    assert time.time() - t0 < 2


def test_detection_of_a_full_page_is_fast():
    page = blank_page()
    draw_form(page)
    t0 = time.time()
    _raster.detect(_raster.binarize(page))
    assert time.time() - t0 < 5


# ---------------------------------------------------------------- the reader


def test_without_an_engine_the_page_is_not_read_and_the_form_is_valid():
    page = blank_page()
    draw_form(page)
    model = readers.read_document(png_bytes(page), "png")
    p = model.pages[0]
    assert p.runs == [] and p.ink is True and p.origin == "ocr"
    assert len(p.rects) >= 12 and len(p.lines) >= 3
    assert any(w.code == "UNREADABLE_PART" and w.page == 1 and "not read" in (w.detail or "") for w in model.warnings)
    assert model.source.format == "png" and model.source.reader == "image.raster"
    assert any(l.style == "dotted" for l in p.lines)


def test_a_blank_page_has_no_ink_and_no_warning():
    model = readers.read_document(png_bytes(blank_page()), "png")
    assert model.pages[0].ink is False and model.warnings == []


def test_fake_engine_words_become_runs_with_confidence_and_points():
    words = [_ocr.Word("Imię", 100, 100, 220, 140, 0.93, (1, 1, 1)), _ocr.Word("i", 230, 100, 245, 140, 0.4, (1, 1, 1)),
             _ocr.Word("nazwisko", 100, 200, 300, 250, 0.88, (1, 1, 2))]
    eng = FakeEngine(words)
    _ocr.set_engine(eng)
    page = blank_page()
    ImageDraw.Draw(page).text((100, 100), "x", fill=0)
    model = readers.read_document(png_bytes(page), "png")
    runs = model.pages[0].runs
    assert [r.text for r in runs] == ["Imię", "i", "nazwisko"] and eng.calls == 1
    assert runs[1].conf == pytest.approx(0.4)
    assert runs[0].box[0] == pytest.approx(36.0) and runs[0].box[3] == pytest.approx(50.4)
    assert model.source.reader == "image.ocr" and model.warnings == []
    assert len({r.id for r in runs}) == 3


def test_engine_failure_is_a_warning_per_page_not_a_crash():
    _ocr.set_engine(FakeEngine(error="the OCR program did not finish in 90 s"))
    stack = Image.new("L", (W, PAGE_H * 2), 255)
    d = ImageDraw.Draw(stack)
    d.text((100, 100), "a", fill=0)
    d.text((100, PAGE_H + 100), "b", fill=0)
    model = readers.read_document(png_bytes(stack), "png")
    notread = [w.page for w in model.warnings if "not read" in (w.detail or "")]
    assert notread == [1, 2]


def test_word_ids_are_unique_across_pages():
    _ocr.set_engine(FakeEngine([_ocr.Word("a", 10, 10, 50, 40, 0.9)]))
    stack = Image.new("L", (W, PAGE_H * 2), 255)
    d = ImageDraw.Draw(stack)
    d.text((100, 100), "a", fill=0)
    d.text((100, PAGE_H + 100), "b", fill=0)
    model = readers.read_document(png_bytes(stack), "png")
    assert [r.id for p in model.pages for r in p.runs] == ["r1", "r2"]


def test_jpeg_goes_through_the_jpeg_reader():
    page = blank_page()
    draw_form(page)
    out = io.BytesIO()
    page.save(out, format="JPEG", quality=80)
    model = readers.read_document(out.getvalue(), "jpeg")
    assert model.source.format == "jpeg" and len(model.pages[0].rects) >= 5


def _textless_pdf() -> bytes:
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595.28, 841.89))
    c.rect(100, 600, 200, 30)
    c.showPage()
    c.save()
    return buf.getvalue()


def test_a_pdf_without_text_takes_the_image_way_with_a_page_in_points():
    _ocr.set_engine(FakeEngine([_ocr.Word("Imie", 400, 400, 600, 440, 0.9)]))
    model = readers.read_document(_textless_pdf(), "pdf")
    p = model.pages[0]
    assert p.origin == "ocr" and p.width == pytest.approx(595.28, abs=0.5) and p.height == pytest.approx(841.89, abs=0.5)
    assert p.runs[0].box[0] == pytest.approx(144.0, abs=0.1)        # 400 px at 200 dpi
    # the drawn rectangle (200 x 30 pt, its top at 841.89 - 630) comes back as a box in points
    assert any(abs(q.box[0] - 100) < 3 and abs(q.box[1] - (841.89 - 630)) < 3 and abs(q.box[2] - 300) < 3 for q in p.rects)
    assert [w.code for w in model.warnings] == ["OCR_USED"]


def test_a_huge_pdf_page_is_rendered_within_the_pixel_budget():
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(200 * 72, 200 * 72))   # 200 x 200 inches: at 200 dpi this would be 1.6 gigapixels
    c.rect(1000, 1000, 2000, 300)
    c.showPage()
    c.save()
    seen = []

    class Spy:
        name = "spy"

        def read(self, png, lang, timeout):
            seen.append(Image.open(io.BytesIO(png)).size)
            return []

    _ocr.set_engine(Spy())
    budget = 4_000_000
    model = readers.read_document(buf.getvalue(), "pdf", ReadOptions(max_pixels=budget))
    assert seen and seen[0][0] * seen[0][1] <= budget
    assert model.pages[0].width == pytest.approx(14400, rel=0.01)    # mapped back to points


def test_a_pdf_without_text_and_without_ocr_stays_native_with_a_warning():
    model = readers.read_document(_textless_pdf(), "pdf")
    assert model.pages[0].origin == "native"
    assert [w.code for w in model.warnings] == ["UNREADABLE_PART"] and "not read" in model.warnings[0].detail


# ---------------------------------------------------------------- the adapter


TSV = ("level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
       "1\t1\t0\t0\t0\t0\t0\t0\t1654\t2339\t-1\t\n"
       "5\t1\t1\t1\t1\t1\t100\t100\t120\t40\t96.5\tWniosek\n"
       "5\t1\t1\t1\t1\t2\t230\t100\t60\t40\t-1\tnoise\n"
       "5\t1\t1\t1\t1\t3\t300\t100\t60\t40\t55\t \n"
       "5\t1\t1\t1\t2\t1\t100\t160\t80\t30\t88\tz\twrotem\n")


def test_tsv_parser_keeps_words_only():
    words = _ocr.parse_tsv(TSV)
    assert [w.text for w in words] == ["Wniosek", "z\twrotem"]
    assert words[0].conf == pytest.approx(0.965) and (words[0].x1, words[0].y1) == (220, 140)
    assert words[1].line == (1, 1, 2)


def test_tesseract_adapter_with_a_faked_subprocess(monkeypatch):
    seen = {}

    class Done:
        returncode, stdout = 0, TSV.encode()

    def fake_run(cmd, **kw):
        seen["cmd"], seen["timeout"] = cmd, kw["timeout"]
        return Done()

    monkeypatch.setattr(_ocr.subprocess, "run", fake_run)
    eng = _ocr.TesseractEngine("/usr/bin/tesseract")
    assert len(eng.read(b"png", "pol+eng", 30)) == 2
    assert seen["cmd"][0] == "/usr/bin/tesseract" and "pol+eng" in seen["cmd"] and seen["cmd"][-1] == "tsv"
    assert seen["timeout"] == 30

    def boom(cmd, **kw):
        raise _ocr.subprocess.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(_ocr.subprocess, "run", boom)
    with pytest.raises(_ocr.OcrError):
        eng.read(b"png", "pol+eng", 1)
    with pytest.raises(_ocr.OcrError):
        _ocr.TesseractEngine(None).__class__.__new__(_ocr.TesseractEngine).__setattr__("executable", None) or \
            _ocr.TesseractEngine.read(type("E", (), {"executable": None})(), b"", "pol", 1)


@pytest.mark.tesseract
def test_real_tesseract_reads_a_drawn_word():
    _ocr.set_engine(None)  # the program itself
    page = Image.new("L", (W, PAGE_H), 255)
    from PIL import ImageFont
    try:
        font = ImageFont.load_default(size=60)
    except TypeError:
        pytest.skip("this Pillow cannot scale its default font")
    ImageDraw.Draw(page).text((200, 300), "WNIOSEK", fill=0, font=font)
    model = readers.read_document(png_bytes(page), "png")
    assert any("WNIOSEK" in r.text.upper() for r in model.pages[0].runs)

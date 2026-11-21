"""WP-F20e: TIFF (every frame a page), BMP, GIF and WEBP through the image reader, ODT through its own reader,
HEIC/HEIF and RTF refused by the guard. Every file is built in the test; one positive and one negative control each."""
from __future__ import annotations

import io
import zipfile

import pytest
from PIL import Image, ImageDraw

from app import readers
from app.config import Settings
from app.guard import ProblemError, inspect_upload
from app.readers import _ocr
from app.readers._base import ReaderError, ReadOptions

S = Settings(auth_mode="off", max_upload_bytes=5_000_000)


@pytest.fixture(autouse=True)
def no_engine():
    _ocr.set_engine(None, disabled=True)
    yield
    _ocr.set_engine(None)


def page_image(label_y: int = 300) -> Image.Image:
    img = Image.new("L", (1240, 1754), 255)
    d = ImageDraw.Draw(img)
    d.text((100, 100), "WNIOSEK", fill=0)
    d.rectangle((100, label_y, 700, label_y + 40), outline=0, width=3)   # a box to fill in
    d.line((100, label_y + 200, 900, label_y + 200), fill=0, width=3)
    return img


def save(img: Image.Image, fmt: str, **kw) -> bytes:
    out = io.BytesIO()
    img.save(out, format=fmt, **kw)
    return out.getvalue()


def tiff_bytes(frames: int = 1) -> bytes:
    imgs = [page_image(300 + 20 * i) for i in range(frames)]
    return save(imgs[0], "TIFF", save_all=True, append_images=imgs[1:], compression="tiff_lzw")


def odt_bytes(content_body: str, mimetype: str = "application/vnd.oasis.opendocument.text") -> bytes:
    content = ('<?xml version="1.0" encoding="UTF-8"?>'
               '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
               'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
               'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.3">'
               f'<office:body><office:text>{content_body}</office:text></office:body></office:document-content>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("mimetype", mimetype, compress_type=zipfile.ZIP_STORED)
        z.writestr("content.xml", content, compress_type=zipfile.ZIP_DEFLATED)
    return buf.getvalue()


SIMPLE_ODT = ('<text:h>Wniosek o zaświadczenie</text:h><text:p>Proszę wypełnić.</text:p>'
              '<table:table><table:table-column/>'
              '<table:table-row><table:table-cell><text:p>Imię:</text:p></table:table-cell>'
              '<table:table-cell><text:p/></table:table-cell></table:table-row>'
              '<table:table-row><table:table-cell><text:p>Nazwisko:</text:p></table:table-cell>'
              '<table:table-cell table:number-columns-spanned="2"><text:p/></table:table-cell></table:table-row>'
              '</table:table>')

# format -> (bytes, extension, guard kind)
FORMATS = {
    "tiff": (lambda: tiff_bytes(1), "tiff", "tiff"),
    "tif": (lambda: tiff_bytes(1), "tif", "tiff"),
    "bmp": (lambda: save(page_image(), "BMP"), "bmp", "bmp"),
    "gif": (lambda: save(page_image(), "GIF"), "gif", "gif"),
    "webp": (lambda: save(page_image(), "WEBP", lossless=True), "webp", "webp"),
}


# ---- positive: guard accepts, reader reads --------------------------------------------------------------------

@pytest.mark.parametrize("key", sorted(FORMATS))
def test_image_format_is_accepted_and_read_with_its_shapes(key):
    make, ext, kind = FORMATS[key]
    data = make()
    info = inspect_upload(f"skan.{ext.upper()}", data, S)
    assert info.kind == kind
    model = readers.read_document(data, kind)
    assert model.source.reader == "image.raster"            # no OCR engine here: shapes only, with a warning
    assert len(model.pages) == 1 and model.pages[0].origin == "ocr"
    assert len(model.pages[0].rects) >= 1 and len(model.pages[0].lines) >= 1
    assert any(w.code == "UNREADABLE_PART" and w.page == 1 for w in model.warnings)


def test_every_tiff_frame_is_a_page():
    data = tiff_bytes(3)
    assert inspect_upload("a.tiff", data, S).kind == "tiff"
    model = readers.read_document(data, "tiff")
    assert [p.number for p in model.pages] == [1, 2, 3]
    tops = [min(r.box[1] for r in p.rects) for p in model.pages]
    assert tops[0] < tops[1] < tops[2]                       # each frame drew its box one step lower


def test_animated_gif_reads_its_first_frame_only():
    a, b = page_image(300), Image.new("L", (1240, 1754), 255)
    data = save(a, "GIF", save_all=True, append_images=[b, b])
    assert inspect_upload("a.gif", data, S).kind == "gif"
    model = readers.read_document(data, "gif")
    assert len(model.pages) == 1 and len(model.pages[0].rects) >= 1


def test_transparent_webp_is_laid_on_white():
    rgba = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    model = readers.read_document(save(rgba, "WEBP", lossless=True), "webp")
    assert model.pages[0].ink is False


# ---- the same limits --------------------------------------------------------------------------------------------

def test_tiff_with_more_frames_than_the_page_limit_is_refused_by_guard_and_reader():
    data = tiff_bytes(4)
    with pytest.raises(ProblemError) as e:
        inspect_upload("a.tiff", data, Settings(auth_mode="off", max_pages=3))
    assert e.value.code == "TOO_LARGE"
    with pytest.raises(ReaderError) as r:
        readers.read_document(data, "tiff", ReadOptions(max_pages=3))
    assert r.value.code == "TOO_LARGE"


@pytest.mark.parametrize("key", ["tiff", "bmp", "gif", "webp"])
def test_pixel_limit_is_checked_before_decoding(key):
    make, _, kind = FORMATS[key]
    data = make()
    with pytest.raises(ProblemError) as e:
        inspect_upload(f"a.{kind}", data, Settings(auth_mode="off", max_pixels=1_000_000))
    assert e.value.code == "TOO_MANY_PIXELS"
    with pytest.raises(ReaderError) as r:
        readers.read_document(data, kind, ReadOptions(max_pixels=1_000_000))
    assert r.value.code == "TOO_LARGE"


def test_truncated_tiff_is_a_reader_error_not_a_trace():
    data = tiff_bytes(2)
    with pytest.raises(ReaderError):
        readers.read_document(data[: len(data) // 2], "tiff")


# ---- negative controls: a text file with the extension never reaches a reader ---------------------------------

@pytest.mark.parametrize("ext", ["tiff", "tif", "bmp", "gif", "webp", "odt"])
def test_binary_garbage_with_the_extension_is_refused_by_the_guard(ext, monkeypatch):
    reached = []
    monkeypatch.setattr(readers, "read_document", lambda *a, **k: reached.append(a))
    with pytest.raises(ProblemError) as e:
        inspect_upload(f"a.{ext}", b"To nie jest obraz.\x00\x01" * 20, S)
    assert e.value.code == "TYPE_MISMATCH" and not reached


def test_bmp_signature_alone_is_not_enough():
    with pytest.raises(ProblemError) as e:
        inspect_upload("a.bmp", b"BM" + b"\x00binary that starts with BM" * 5, S)
    assert e.value.code == "TYPE_MISMATCH"


def test_text_with_an_image_extension_stays_refused():
    with pytest.raises(ProblemError) as e:
        inspect_upload("a.tiff", b"To jest zwykly tekst, nie obraz.\n" * 20, S)
    assert e.value.code == "TYPE_MISMATCH"


def test_image_named_with_the_wrong_extension_is_read_as_what_it_is():
    info = inspect_upload("a.png", save(page_image(), "GIF"), S)
    assert info.kind == "gif" and "obraz GIF" in info.warnings[0]


# ---- HEIC / HEIF (the reader comes with stage 1b of WP-F20f) ----------------------------------------------------

HEIC = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 64


@pytest.mark.parametrize("name", ["zdjecie.heic", "zdjecie.HEIF"])
def test_heic_is_accepted_by_the_guard_by_extension_and_content(name):
    assert inspect_upload(name, HEIC, S).kind == "heic"


def test_heic_content_under_a_jpg_name_is_routed_as_heic_with_a_warning():
    info = inspect_upload("zdjecie.jpg", HEIC, S)
    assert info.kind == "heic" and "HEIC" in info.warnings[0]


# ---- ODT ------------------------------------------------------------------------------------------------------

def test_odt_is_accepted_and_read_as_paragraphs_and_a_table():
    data = odt_bytes(SIMPLE_ODT)
    info = inspect_upload("wniosek.odt", data, S)
    assert info.kind == "odt" and info.members == 2
    model = readers.read_document(data, "odt")
    assert model.source.reader == "odt" and len(model.pages) == 1 and model.pages[0].origin == "flow"
    page = model.pages[0]
    assert [r.text for r in page.runs] == ["Wniosek o zaświadczenie", "Proszę wypełnić.", "Imię:", "Nazwisko:"]
    assert [r.anchor for r in page.runs[:2]] == ["p[0]", "p[1]"]
    table = page.tables[0]
    assert table.anchor == "tbl[0]" and [(c.r, c.c, c.cs) for c in table.cells] == [(0, 0, 1), (1, 0, 1)]
    assert table.cells[0].anchor == "tbl[0]/cell[0,0]"


def test_odt_with_a_list_and_a_section_keeps_their_paragraphs():
    body = ('<text:section><text:p>Sekcja</text:p></text:section>'
            '<text:list><text:list-item><text:p>Punkt jeden</text:p></text:list-item></text:list>')
    model = readers.read_document(odt_bytes(body), "odt")
    assert [r.text for r in model.pages[0].runs] == ["Sekcja", "Punkt jeden"]


def test_odt_repeats_are_bounded_before_they_are_expanded():
    body = ('<table:table><table:table-row table:number-rows-repeated="1000000">'
            '<table:table-cell table:number-columns-repeated="1000"><text:p>x</text:p></table:table-cell>'
            '</table:table-row></table:table>')
    with pytest.raises(ReaderError) as e:
        readers.read_document(odt_bytes(body), "odt", ReadOptions(max_cells=1000))
    assert e.value.code == "TOO_LARGE"


def test_odt_with_a_doctype_is_refused():
    bad = odt_bytes('<text:p>x</text:p>')
    buf = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(bad)) as zin, zipfile.ZipFile(buf, "w") as zout:
        zout.writestr("mimetype", zin.read("mimetype"), compress_type=zipfile.ZIP_STORED)
        zout.writestr("content.xml", b'<!DOCTYPE x [<!ENTITY e "boom">]>' + zin.read("content.xml"))
    with pytest.raises(ReaderError):
        readers.read_document(buf.getvalue(), "odt")


def test_a_spreadsheet_package_is_not_an_odt_and_vice_versa():
    ods_like = odt_bytes(SIMPLE_ODT, mimetype="application/vnd.oasis.opendocument.spreadsheet")
    assert inspect_upload("a.odt", ods_like, S).kind == "ods"   # WP-F20f: read as what it is, with a warning
    assert inspect_upload("a.ods", odt_bytes(SIMPLE_ODT), S).kind == "odt"
    with pytest.raises(ReaderError):
        readers.read_document(ods_like, "odt")


# ---- the whole pipeline ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("name,make", [("a.odt", lambda: odt_bytes(SIMPLE_ODT)), *[(f"a.{v[1]}", v[0]) for v in FORMATS.values()]])
def test_pipeline_converts_each_new_format_to_a_form_that_passes_the_gate(name, make):
    from app import pipeline

    data = make()
    inspect_upload(name, data, S)
    result = pipeline.run(data, name, S)
    assert result.form["tabs"] and result.sidecar["counts"]["source_pages"] >= 1

"""Reader of JPEG and PNG scans, and the image way of a PDF page without text (design 6.2, 6.2.2; WP-F2c).

    scan (1654 px wide, pages stacked) -> decode with limits -> cut into A4 pages -> per page: OCR words with boxes and
    confidence, raster lines, boxes, combs and leaders -> pages of origin "ocr", sizes in points (200 dpi).

Where OCR is not available, or fails on a strip, the page still carries its drawn shapes and a warning
UNREADABLE_PART "not read" with the page number: never a crash, never an invented text. The PDF hook
"pdf.textless_page" renders the page with pypdfium2 and takes the same way; it returns (page, warnings).
"""
from __future__ import annotations

import io
from typing import Any

from PIL import Image

from app.model.common import Warning
from app.model.page import Line, Page, Rect, Run

from . import register, register_hook
from . import _ocr, _raster
from ._base import Ids, ReaderError, ReadOptions, ReadResult, r2

S = _raster.PX_TO_PT
MAX_SHAPES = 4000  # per page: a page that "has" more is noise, the rest is dropped with a warning


def _pt(box: tuple[int, int, int, int], s: float = S) -> list[float]:
    return [r2(box[0] * s), r2(box[1] * s), r2(box[2] * s), r2(box[3] * s)]


def _png(img: Image.Image) -> bytes:
    out = io.BytesIO()
    img.save(out, format="PNG", compress_level=1)
    return out.getvalue()


def _runs(words: list[_ocr.Word], ids: Ids, page: int, s: float = S) -> tuple[list[Run], list[Warning]]:
    """One run per word, in the engine's order. The size is the tallest box of the word's line, in points x 0.85:
    a rough, comparable measure for headings, not a font size."""
    tallest: dict[tuple[int, int, int], int] = {}
    for w in words:
        tallest[w.line] = max(tallest.get(w.line, 0), w.y1 - w.y0)
    runs: list[Run] = []
    warns: list[Warning] = []
    for w in words:
        run, bad = Run.safe(page, id=ids.next("r"), text=w.text, box=_pt((w.x0, w.y0, w.x1, w.y1), s),
                            size=r2(tallest[w.line] * s * 0.85), conf=round(w.conf, 3))
        warns.extend(bad)
        if run is not None:
            runs.append(run)
    return runs, warns


def read_strip(grey: Image.Image, number: int, ids: Ids, options: ReadOptions, s: float = S) -> tuple[Page, list[Warning]]:
    """One page strip (mode L) -> page of origin "ocr" and its warnings."""
    w, h = grey.size
    ink = _raster.binarize(grey)
    has_ink = ink.getbbox() is not None
    warns: list[Warning] = []
    runs: list[Run] = []
    if has_ink:
        engine = _ocr.get_engine()
        if engine is None:
            warns.append(Warning(code="UNREADABLE_PART", page=number,
                                 detail="page not read: no OCR engine in this build; its lines and boxes are kept"))
        else:
            try:
                words = engine.read(_png(grey), options.ocr_lang, options.ocr_timeout)
            except _ocr.OcrError as e:
                warns.append(Warning(code="UNREADABLE_PART", page=number, detail=f"page not read: {e}"))
            else:
                runs, bad = _runs(words, ids, number, s)
                warns.extend(bad)
    shapes = _raster.detect(ink)
    lines: list[Line] = []
    rects: list[Rect] = []
    items: list[tuple[str, Any, str]] = (
        [("l", b, "solid") for b in shapes.hlines + shapes.vlines] + [("l", b, "dotted") for b in shapes.leaders])
    dropped = max(0, len(items) + len(shapes.boxes) - MAX_SHAPES)
    for _, b, style in items[:MAX_SHAPES]:
        el, bad = Line.safe(number, id=ids.next("l"), box=_pt(b, s), style=style)
        warns.extend(bad)
        if el is not None:
            lines.append(el)
    for b in shapes.boxes[:max(0, MAX_SHAPES - len(items))]:
        el, bad = Rect.safe(number, id=ids.next("q"), box=_pt(b, s))
        warns.extend(bad)
        if el is not None:
            rects.append(el)
    if dropped:
        warns.append(Warning(code="UNREADABLE_PART", page=number,
                             detail=f"{dropped} shapes beyond the limit of {MAX_SHAPES} per page were left out"))
    page = Page(number=number, width=r2(w * s), height=r2(h * s), origin="ocr", runs=runs, lines=lines, rects=rects,
                ink=has_ink)
    return page, warns


@register("jpeg")
def read_jpeg(data: bytes, options: ReadOptions) -> ReadResult:
    return _read(data, options)


@register("png")
def read_png(data: bytes, options: ReadOptions) -> ReadResult:
    return _read(data, options)


def _read(data: bytes, options: ReadOptions) -> ReadResult:
    grey = _raster.decode(data, options)
    ink_all = _raster.binarize(grey)
    cuts, unsnapped = _raster.cut_points(ink_all)
    del ink_all
    if len(cuts) - 1 > options.max_pages:
        raise ReaderError("TOO_LARGE", f"{len(cuts) - 1} pages, the limit is {options.max_pages}")
    ids = Ids()
    pages: list[Page] = []
    warnings: list[Warning] = []
    for i in range(len(cuts) - 1):
        page, warns = read_strip(grey.crop((0, cuts[i], grey.size[0], cuts[i + 1])), i + 1, ids, options)
        pages.append(page)
        warnings.extend(warns)
        if i + 1 in unsnapped:
            warnings.append(Warning(code="UNREADABLE_PART", page=i + 1,
                                    detail="the scan was cut below this page without a white band: a line of text may be split"))
    reader = "image.ocr" if _ocr.get_engine() is not None else "image.raster"
    return ReadResult(reader=reader, pages=pages, warnings=warnings)


def textless_pdf_page(data: bytes, index: int, number: int, ids: Ids, options: ReadOptions) -> tuple[Page, list[Warning]]:
    """Hook "pdf.textless_page": render the page at 200 dpi and read its pixels."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    try:
        pg = pdf[index]
        w_pt, h_pt = pg.get_size()
        scale = 200.0 / 72.0
        while w_pt * h_pt * scale * scale > options.max_pixels and scale > 0.5:
            scale *= 0.8
        grey = pg.render(scale=scale).to_pil().convert("L")
    finally:
        pdf.close()
    grey = Image.frombytes("L", grey.size, grey.tobytes())
    return read_strip(grey, number, ids, options, 1.0 / scale)


register_hook("pdf.textless_page", textless_pdf_page)

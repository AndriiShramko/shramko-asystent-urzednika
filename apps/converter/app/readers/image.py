"""Reader of JPEG, PNG, TIFF, BMP, GIF and WEBP scans (WP-F2c, WP-F20e: the last four), and the image way of a PDF page without text (design 6.2, 6.2.2; WP-F2c).

    scan (1654 px wide, pages stacked) -> decode with limits -> cut into A4 pages -> per page: OCR words with boxes and
    confidence, raster lines, boxes, combs and leaders -> pages of origin "ocr", sizes in points (200 dpi).

Where OCR is not available, or fails on a strip, the page still carries its drawn shapes and a warning
UNREADABLE_PART "not read" with the page number: never a crash, never an invented text. The PDF hook
"pdf.textless_page" renders the page with pypdfium2 and takes the same way; it returns (page, warnings).
"""
from __future__ import annotations

import io
import threading
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


CONFIDENT = 0.6      # a word the engine is fairly sure of
MIN_CONFIDENT_SHARE = 0.5  # AUDIT-8 VE-2, measured in V0: partner scans 58 % and more, rotated pages 30 to 45 %


def _quality(words: list[_ocr.Word], number: int) -> list[Warning]:
    """A page with ink that OCR read as nothing, or as mostly unconfident words (rotated, blurred, too small), is told
    to the user per page; the words are kept."""
    if not words:
        return [Warning(code="UNREADABLE_PART", page=number,
                        detail="page not read: the scan has marks but OCR found no words; its lines and boxes are kept")]
    share = sum(1 for w in words if w.conf >= CONFIDENT) / len(words)
    if share < MIN_CONFIDENT_SHARE:
        return [Warning(code="UNREADABLE_PART", page=number,
                        detail=f"page read poorly: only {round(share * 100)} % of {len(words)} OCR words are confident; "
                               "the scan may be rotated, blurred or too small, check this page against the paper")]
    return []


GLYPH_MAX_PX = 26     # S1 glyph: a closed box at most this wide and tall (200 dpi) inside a word is a letter's counter
THICK_MAX_PT = 1.5    # S1 thick: the finder takes a ruled line up to this thickness (find/_shapes.py `ruled`)
DOTS = frozenset(".…_")


def _cover(b: tuple[int, int, int, int], w: _ocr.Word) -> float:
    """Share of box b that lies inside the word's box."""
    ix = min(b[2], w.x1) - max(b[0], w.x0)
    iy = min(b[3], w.y1) - max(b[1], w.y0)
    area = max(1, (b[2] - b[0]) * (b[3] - b[1]))
    return ix * iy / area if ix > 0 and iy > 0 else 0.0


def _thin(b: tuple[int, int, int, int], across: int, k: float) -> tuple[int, int, int, int]:
    """A line box whose thickness (axis `across`: 1 = y, 0 = x) is over THICK_MAX_PT -> a line of max(1, int(k))
    pixels through its middle (k = pixels per point); a thinner line is returned as is."""
    lo, hi = b[across], b[across + 2]
    if (hi - lo) / k <= THICK_MAX_PT:
        return b
    mid = (lo + hi) // 2
    t = max(1, int(k))
    return (b[0], mid, b[2], mid + t) if across == 1 else (mid, b[1], mid + t, b[3])


def _prep_shapes(shapes: _raster.Shapes, words: list[_ocr.Word], prep: frozenset[str], s: float) -> list[dict[str, Any]]:
    """SCAN_PREP steps that need the OCR words (S1). Changes `shapes` in place; returns the runs to add."""
    k = 1.0 / s
    extra: list[dict[str, Any]] = []
    if "rules" in prep:  # first: on the shapes as detected (glyph and thick change boxes and lines)
        for b in _raster.open_rules(shapes.hlines, shapes.vlines, shapes.boxes,
                                    [(w.x0, w.y0, w.x1, w.y1) for w in words], k, [w.text for w in words]):
            x0, _, x1, y1 = _pt(b, s)
            extra.append(dict(text="_" * max(8, int((x1 - x0) / 2.2)), box=[x0, r2(max(0.0, y1 - 8)), x1, y1],
                              size=8.0, conf=0.9))
    if "glyph" in prep:
        big = [w for w in words if len(w.text) >= 2]
        shapes.boxes = [b for b in shapes.boxes
                        if not (b[2] - b[0] <= GLYPH_MAX_PX and b[3] - b[1] <= GLYPH_MAX_PX
                                and any(_cover(b, w) >= 0.8 for w in big))]
    if "thick" in prep:
        shapes.hlines = [_thin(b, 1, k) for b in shapes.hlines]
        shapes.vlines = [_thin(b, 0, k) for b in shapes.vlines]
    if "leader" in prep:
        for b in shapes.leaders:
            if any(set(w.text) <= DOTS and w.y0 - 10 <= b[3] and w.y1 + 10 >= b[1]
                   and min(b[2], w.x1) - max(b[0], w.x0) > 0.5 * (b[2] - b[0]) for w in words):
                continue  # the OCR already read these dots
            x0, _, x1, y1 = _pt(b, s)
            extra.append(dict(text="." * max(8, int((x1 - x0) / 2.2)), box=[x0, r2(max(0.0, y1 - 8)), x1, y1],
                              size=8.0, conf=0.9))
    return extra


def read_strip(grey: Image.Image, number: int, ids: Ids, options: ReadOptions, s: float = S) -> tuple[Page, list[Warning]]:
    """One page strip (mode L) -> page of origin "ocr" and its warnings."""
    warns: list[Warning] = []
    if "deskew" in options.scan_prep:
        grey, angle = _raster.deskew(grey)
        if angle:
            warns.append(Warning(code="UNREADABLE_PART", page=number, detail=f"page straightened by {angle} degrees"))
    w, h = grey.size
    ink = _raster.binarize(grey)
    has_ink = ink.getbbox() is not None
    runs: list[Run] = []
    words: list[_ocr.Word] = []
    if has_ink:
        engine = _ocr.get_engine()
        if engine is None:
            warns.append(Warning(code="UNREADABLE_PART", page=number,
                                 detail="page not read: no OCR engine in this build; its lines and boxes are kept"))
        else:
            try:
                words = engine.read(_png(grey), options.ocr_lang, options.ocr_timeout)
            except _ocr.OcrError as e:
                words = []
                warns.append(Warning(code="UNREADABLE_PART", page=number, detail=f"page not read: {e}"))
            else:
                runs, bad = _runs(words, ids, number, s)
                warns.extend(bad)
                warns.extend(_quality(words, number))
    shapes = _raster.detect(ink)
    extra = _prep_shapes(shapes, words, options.scan_prep, s) if words and options.scan_prep else []
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
    for e in extra:
        run, bad = Run.safe(number, id=ids.next("r"), **e)
        warns.extend(bad)
        if run is not None:
            runs.append(run)
    page = Page(number=number, width=r2(w * s), height=r2(h * s), origin="ocr", runs=runs, lines=lines, rects=rects,
                ink=has_ink)
    return page, warns


def _scaled(grey: Image.Image, number: int, options: ReadOptions, warnings: list[Warning]) -> Image.Image:
    """SCAN_PREP "scale": a page strip of a scan -> A4 at 200 dpi, with a warning when it was resampled."""
    if "scale" not in options.scan_prep:
        return grey
    out, f = _raster.normalize(grey, options.max_pixels)
    if out is not grey:
        warnings.append(Warning(code="UNREADABLE_PART", page=number,
                                detail=f"page scaled from about {round(_raster.a4_dpi(grey.size))} dpi to 200 dpi"))
    return out


@register("jpeg")
def read_jpeg(data: bytes, options: ReadOptions) -> ReadResult:
    return _read(data, options)


@register("png")
def read_png(data: bytes, options: ReadOptions) -> ReadResult:
    return _read(data, options)


def _read_frames(data: bytes, options: ReadOptions, kind: str) -> ReadResult:
    """TIFF, BMP, GIF, WEBP: one frame is one page (GIF and WEBP: the first frame only), no cutting."""
    ids = Ids()
    pages: list[Page] = []
    warnings: list[Warning] = []
    for i, grey in enumerate(_raster.decode_frames(data, options, kind), 1):
        grey = _scaled(grey, i, options, warnings)
        page, warns = read_strip(grey, i, ids, options)
        pages.append(page)
        warnings.extend(warns)
        del grey
    reader = "image.ocr" if _ocr.get_engine() is not None else "image.raster"
    return ReadResult(reader=reader, pages=pages, warnings=warnings)


@register("tiff")
def read_tiff(data: bytes, options: ReadOptions) -> ReadResult:
    return _read_frames(data, options, "tiff")


@register("bmp")
def read_bmp(data: bytes, options: ReadOptions) -> ReadResult:
    return _read_frames(data, options, "bmp")


@register("gif")
def read_gif(data: bytes, options: ReadOptions) -> ReadResult:
    return _read_frames(data, options, "gif")


@register("webp")
def read_webp(data: bytes, options: ReadOptions) -> ReadResult:
    return _read_frames(data, options, "webp")


def _read(data: bytes, options: ReadOptions) -> ReadResult:
    drafted: list[str] = []
    grey = _raster.decode(data, options, drafted)
    ink_all = _raster.binarize(grey)
    cuts, unsnapped = _raster.cut_points(ink_all)
    del ink_all
    if len(cuts) - 1 > options.max_pages:
        raise ReaderError("TOO_LARGE", f"{len(cuts) - 1} pages, the limit is {options.max_pages}")
    ids = Ids()
    pages: list[Page] = []
    warnings: list[Warning] = [Warning(code="UNREADABLE_PART", detail=d) for d in drafted]
    for i in range(len(cuts) - 1):
        strip = _scaled(grey.crop((0, cuts[i], grey.size[0], cuts[i + 1])), i + 1, options, warnings)
        page, warns = read_strip(strip, i + 1, ids, options)
        del strip
        pages.append(page)
        warnings.extend(warns)
        if i + 1 in unsnapped:
            warnings.append(Warning(code="UNREADABLE_PART", page=i + 1,
                                    detail="the scan was cut below this page without a white band: a line of text may be split"))
    reader = "image.ocr" if _ocr.get_engine() is not None else "image.raster"
    return ReadResult(reader=reader, pages=pages, warnings=warnings)


# PDFium is not thread-safe and pypdfium2 calls it with the GIL released: with CONCURRENCY=2 two scanned PDFs would
# render at once. One render at a time in the process; the OCR of the rendered page runs outside the lock.
_PDFIUM_LOCK = threading.Lock()


def textless_pdf_page(data: bytes, index: int, number: int, ids: Ids, options: ReadOptions) -> tuple[Page, list[Warning]]:
    """Hook "pdf.textless_page": render the page at 200 dpi and read its pixels."""
    import pypdfium2 as pdfium

    with _PDFIUM_LOCK:
        pdf = pdfium.PdfDocument(data)
        try:
            pg = pdf[index]
            w_pt, h_pt = pg.get_size()
            scale = 200.0 / 72.0
            if w_pt > 0 and h_pt > 0 and w_pt * h_pt * scale * scale > options.max_pixels:
                # the pixel budget is a hard limit: scale down exactly, never render a huge page at a fixed dpi
                scale = (options.max_pixels / (w_pt * h_pt)) ** 0.5
            grey = pg.render(scale=scale).to_pil().convert("L")
        finally:
            pdf.close()
    grey = Image.frombytes("L", grey.size, grey.tobytes())
    return read_strip(grey, number, ids, options, 1.0 / scale)


register_hook("pdf.textless_page", textless_pdf_page)

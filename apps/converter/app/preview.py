"""Read-only preview of the paper (wave 10, fill and print): a picture of every page and the place of every field
candidate, so the review page can show where a field came from and print values onto the original page.

`preview(data, settings, images, dpi)` reads the file with the SAME functions and options as `app.pipeline.run`
(`read_document` with `read_options(settings)`, then `find`), so the candidate ids are those of the ledger rows of
`/v1/forms/convert?report=1` and join with them. Nothing of the pipeline is changed or re-run here: no meaning, no
composer, no gate; the form JSON and the sidecar are untouched. No external call.

Pictures: a PDF page is rendered with pypdfium2 (under the readers' PDFium lock) as 8-bit greyscale PNG; a JPEG or
PNG scan gives the page strips exactly as the image reader decoded and cut them. Formats without page geometry
(DOCX, DOC, XLSX, ODS and the rest) answer `page_images: "NO_PAGE_IMAGE"`, `pages: []` and anchors.
The answer is deterministic: the same bytes and query give the same JSON bytes. Contract: FP-contract.md (wave 10).
"""
from __future__ import annotations

import base64
import hashlib
import io
import logging
import threading

from PIL import Image

from app import pipeline
from app.config import Settings, read_options
from app.find import find
from app.guard import ProblemError
from app.guard.checks import KIND_LABEL
from app.readers import ReaderError, formats, read_document

DPI_DEFAULT = 150
DPI_MIN, DPI_MAX = 50, 200
PDF_KINDS = frozenset({"pdf"})
SCAN_KINDS = frozenset({"jpeg", "png"})   # the reader cuts these into strips; other picture formats: no picture yet
log = logging.getLogger("converter")
_PLACE_KEYS = ("cells", "lines", "mask", "group", "section")


def _png(grey: Image.Image) -> dict:
    buf = io.BytesIO()
    grey.save(buf, "PNG", optimize=False, compress_level=6)   # Pillow writes no time or text chunk: same pixels, same bytes
    return {"media_type": "image/png", "width_px": grey.size[0], "height_px": grey.size[1],
            "data": base64.b64encode(buf.getvalue()).decode("ascii")}


def _scale(w_pt: float, h_pt: float, dpi: int, max_pixels: int) -> float:
    """Pixels per point; the pixel budget of the installation is a hard limit, as in the readers."""
    scale = dpi / 72.0
    if w_pt > 0 and h_pt > 0 and w_pt * h_pt * scale * scale > max_pixels:
        scale = (max_pixels / (w_pt * h_pt)) ** 0.5
    return scale


def _pdf_images(data: bytes, dpi: int, max_pixels: int) -> list[dict]:
    import pypdfium2 as pdfium

    from app.readers.image import _PDFIUM_LOCK

    out: list[dict] = []
    with _PDFIUM_LOCK:
        pdf = pdfium.PdfDocument(data)
        try:
            for index in range(len(pdf)):
                pg = pdf[index]
                w_pt, h_pt = pg.get_size()
                scale = _scale(w_pt, h_pt, dpi, max_pixels)
                grey = pg.render(scale=scale).to_pil().convert("L")
                img = _png(Image.frombytes("L", grey.size, grey.tobytes()))
                out.append({"media_type": img["media_type"], "dpi": round(scale * 72.0, 2),
                            "width_px": img["width_px"], "height_px": img["height_px"], "data": img["data"]})
                del grey
        finally:
            pdf.close()
    return out


def _scan_images(data: bytes, settings: Settings, pages: list, dpi: int) -> list[dict]:
    """The strips of a JPEG or PNG exactly as `app.readers.image._read` cuts them, resampled to `dpi`."""
    from app.readers import _raster

    opts = read_options(settings)
    grey = _raster.decode(data, opts, [])
    ink = _raster.binarize(grey)
    cuts, _ = _raster.cut_points(ink)
    del ink
    out: list[dict] = []
    for i in range(len(cuts) - 1):
        strip = grey.crop((0, cuts[i], grey.size[0], cuts[i + 1]))
        w_pt, h_pt = pages[i]["w"], pages[i]["h"]
        scale = min(_scale(w_pt, h_pt, dpi, opts.max_pixels), strip.size[0] / w_pt if w_pt else 1.0)
        size = (max(1, round(w_pt * scale)), max(1, round(h_pt * scale)))
        if size != strip.size:
            strip = strip.resize(size, Image.Resampling.LANCZOS)
        img = _png(strip)
        out.append({"media_type": img["media_type"], "dpi": round(scale * 72.0, 2),
                    "width_px": img["width_px"], "height_px": img["height_px"], "data": img["data"]})
    return out


def _place(c) -> dict:
    p: dict = {"page": c.page, "kind": c.kind}
    if c.box is not None:
        p["box"] = [float(v) for v in c.box]
    if c.anchor is not None:
        p["anchor"] = c.anchor
    if c.label is not None:
        p["label"] = c.label.text
    for key in _PLACE_KEYS:
        v = getattr(c, key)
        if v is not None:
            p[key] = v
    if c.options:
        p["options"] = [{"text": o.text, **({"mark": o.mark} if o.mark else {}), **({"blank": o.blank} if o.blank else {})}
                        for o in c.options]
    return p


def preview(data: bytes, settings: Settings, images: bool = True, dpi: int = DPI_DEFAULT) -> dict:
    """The preview answer of the contract. Raises ProblemError (the same codes as the pipeline) and nothing else."""
    fmt = pipeline._format_of(data, settings)
    if fmt not in formats():
        if fmt == "heic":
            raise ProblemError("UNREADABLE", "Ta instalacja nie ma dekodera HEIC.")
        raise ProblemError("UNREADABLE", f"Ta wersja usługi nie potrafi jeszcze czytać tego formatu ({KIND_LABEL.get(fmt, fmt)}).")
    try:
        model = read_document(data, fmt, read_options(settings))
    except ReaderError as exc:
        raise pipeline._problem_of(exc) from None
    finder = find(model)
    geometry = fmt in PDF_KINDS | SCAN_KINDS and all(p.width is not None and p.height is not None for p in model.pages)
    pages: list[dict] = []
    state = "NO_PAGE_IMAGE"
    if geometry:
        pages = [{"n": p.number, "w": float(p.width), "h": float(p.height), "source": p.origin} for p in model.pages]
        state = "OMITTED"
        if images:
            try:
                pics = (_pdf_images(data, dpi, settings.max_pixels) if fmt in PDF_KINDS
                        else _scan_images(data, settings, pages, dpi))
            except ProblemError:
                raise
            except MemoryError:
                raise ProblemError("TOO_LARGE", "Dokument jest większy, niż pozwala ta instalacja (strony lub pamięć).") from None
            except Exception as exc:  # noqa: BLE001 - a picture that cannot be made is told, never a stack trace
                log.warning("stage=preview result=NO_PAGE_IMAGE error=%s", type(exc).__name__)
                pics = []
            if len(pics) == len(pages):
                for page, pic in zip(pages, pics):
                    page["img"] = pic
                state = "OK"
            else:   # the pictures do not match the pages one to one: places only, honestly
                state = "NO_PAGE_IMAGE"
                pages = []
    places = {c.id: _place(c) for c in finder.candidates}
    return {
        "version": 1,
        "input_sha256": hashlib.sha256(data).hexdigest(),
        "format": fmt,
        "units": "pt",
        "origin": "top-left",
        "page_images": state,
        "pages": pages,
        "places": places,
        "counts": {"pages": model.source.pages, "places": len(places),
                   "boxed": sum(1 for p in places.values() if "box" in p),
                   "anchored": sum(1 for p in places.values() if "anchor" in p)},
    }


def preview_limited(data: bytes, settings: Settings, images: bool = True, dpi: int = DPI_DEFAULT) -> dict:
    """`preview` under `settings.job_timeout_s`, sharing the pipeline's account of abandoned jobs (504 TIMEOUT,
    429 BUSY while too many of them still run): the same rule as `pipeline.run_limited`."""
    with pipeline._abandoned_lock:
        pipeline._abandoned[:] = [t for t in pipeline._abandoned if t.is_alive()]
        if len(pipeline._abandoned) >= settings.concurrency:
            raise ProblemError("BUSY", "Poprzednie zadania przekroczyły limit czasu i jeszcze się kończą.",
                               headers={"Retry-After": "30"})
    box: dict = {}

    def work() -> None:
        try:
            box["result"] = preview(data, settings, images, dpi)
        except BaseException as exc:   # handed to the caller, which re-raises it
            box["error"] = exc

    th = threading.Thread(target=work, name="preview-job", daemon=True)
    th.start()
    th.join(settings.job_timeout_s)
    if th.is_alive():
        with pipeline._abandoned_lock:
            pipeline._abandoned.append(th)
        raise ProblemError("TIMEOUT", f"Przetwarzanie pliku trwało dłużej niż {settings.job_timeout_s} s; wynik nie zostanie zwrócony, a zadanie kończy się w tle.")
    if "error" in box:
        raise box["error"]
    return box["result"]

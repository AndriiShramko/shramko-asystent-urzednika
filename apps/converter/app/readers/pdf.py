"""PDF reader (design 6.2): text runs with boxes, lines and rectangles, declared form fields. Origin "native".

Everything comes from pdfplumber (pdfminer.six underneath), so text, vectors and fields share one coordinate
space: points, origin top left of the page box. A page with fewer than `ocr_min_chars` characters takes the
image way through the hook "pdf.textless_page" (WP-F2c); without the hook it stays empty with a warning. So does a
scan with a short text layer: one picture over SCAN_COVER of the page and fewer than SCAN_TEXT_MAX characters.

Runs: characters in file order, joined while they sit on one line, close together, in the same weight and size.
A row of three or more leader characters (dots, underscores) is its own run: it draws a place to fill.
"""
from __future__ import annotations

import io
import warnings as warnings_mod
from typing import Any

from app.model.common import Warning
from app.model.page import Line, Page, Rect, Run, Widget

from . import hook, register
from ._base import Ids, ReaderError, ReadOptions, ReadResult, is_bold_font, leader_spans, nn, r2

LINE_MAX_THICKNESS = 3.0   # a filled or stroked rectangle thinner than this is a line
DOT_MAX = 1.0              # a shape smaller than this both ways is a dot (of a dotted leader), not a line or box
GAP_SPACE = 0.2            # gap / font size above which a missing space is written between two characters
GAP_BREAK = 1.2            # gap / font size above which a run ends (a column, a tab)
SCAN_COVER = 0.7           # one picture covering this share of the page makes the page a scan ...
SCAN_TEXT_MAX = 200        # ... when its own text is shorter than this (a scanner app's footer, a digital stamp)


def _scan_cover(page: Any) -> float:
    """Share of the page that its largest picture covers (clipped to the page), 0 when it has none."""
    area = float(page.width) * float(page.height)
    best = 0.0
    for im in page.images:
        w = min(float(im["x1"]), float(page.width)) - max(float(im["x0"]), 0.0)
        h = min(float(im["bottom"]), float(page.height)) - max(float(im["top"]), 0.0)
        if w > 0 and h > 0 and area > 0:
            best = max(best, w * h / area)
    return best


# ---------------------------------------------------------------- text


def _runs(chars: list[dict[str, Any]], ids: Ids) -> list[Run]:
    groups: list[list[dict[str, Any]]] = []
    cur: list[dict[str, Any]] = []
    for ch in chars:
        if not ch.get("text"):
            continue
        if cur and not _joins(cur, ch):
            groups.append(cur)
            cur = []
        cur.append(ch)
    if cur:
        groups.append(cur)

    runs: list[Run] = []
    for g in groups:
        text, owners = _text_of(g)
        for a, b, _leader in leader_spans(text):
            piece = [owners[i] for i in range(a, b) if owners[i] is not None and not g[owners[i]]["text"].isspace()]
            seg = text[a:b].strip()
            if not seg or not piece:
                continue
            cs = [g[i] for i in sorted(set(piece))]
            runs.append(Run(**nn(
                id=ids.next("r"), text=seg,
                box=(r2(min(c["x0"] for c in cs)), r2(min(c["top"] for c in cs)),
                     r2(max(c["x1"] for c in cs)), r2(max(c["bottom"] for c in cs))),
                size=r2(cs[0]["size"]) if cs[0].get("size") else None,
                bold=is_bold_font(cs[0].get("fontname")),
            )))
    return runs


def _joins(cur: list[dict[str, Any]], ch: dict[str, Any]) -> bool:
    last = cur[-1]
    size = max(float(last.get("size") or 1.0), 1.0)
    if abs(float(ch["top"]) - float(last["top"])) > 0.35 * size and abs(float(ch["bottom"]) - float(last["bottom"])) > 0.35 * size:
        return False
    gap = float(ch["x0"]) - float(last["x1"])
    if gap < -0.5 * size or gap > GAP_BREAK * size:
        return False
    if ch["text"].isspace() or last["text"].isspace():
        return True
    first = next((c for c in cur if not c["text"].isspace()), last)
    if is_bold_font(first.get("fontname")) != is_bold_font(ch.get("fontname")):
        return False
    return abs(float(ch.get("size") or 0) - float(first.get("size") or 0)) <= 0.6


def _text_of(g: list[dict[str, Any]]) -> tuple[str, list[int | None]]:
    """Text of a group with the index of the character behind each position (None for an inserted space)."""
    out: list[str] = []
    owners: list[int | None] = []
    for i, ch in enumerate(g):
        if i:
            prev = g[i - 1]
            size = max(float(prev.get("size") or 1.0), 1.0)
            if (float(ch["x0"]) - float(prev["x1"]) > GAP_SPACE * size and not ch["text"].isspace()
                    and not prev["text"].isspace()):
                out.append(" ")
                owners.append(None)
        for c in ch["text"]:
            out.append(c)
            owners.append(i)
    return "".join(out), owners


# ---------------------------------------------------------------- vectors


def _white(color: Any) -> bool:
    if color is None:
        return False
    vals = list(color) if isinstance(color, (list, tuple)) else [color]
    try:
        nums = [float(v) for v in vals]
    except (TypeError, ValueError):
        return False
    if len(nums) == 4:  # CMYK: white is no ink
        return all(v <= 0.02 for v in nums)
    return bool(nums) and all(v >= 0.98 for v in nums)


def _style(obj: dict[str, Any]) -> str:
    dash = obj.get("dash")
    pattern = list(dash[0]) if isinstance(dash, (list, tuple)) and dash and isinstance(dash[0], (list, tuple)) else []
    if not pattern or not any(float(v) > 0 for v in pattern):
        return "solid"
    on = float(pattern[0])
    width = float(obj.get("linewidth") or 0)
    return "dotted" if on <= max(1.5 * width, 1.0) else "dashed"


def _visible(obj: dict[str, Any]) -> bool:
    stroke = bool(obj.get("stroke")) and not _white(obj.get("stroking_color"))
    fill = bool(obj.get("fill")) and not _white(obj.get("non_stroking_color"))
    return stroke or fill


def _vectors(page: Any, ids: Ids) -> tuple[list[Line], list[Rect]]:
    lines: list[Line] = []
    rects: list[Rect] = []
    for ln in page.lines:
        if not bool(ln.get("stroke", True)) or _white(ln.get("stroking_color")):
            continue
        x0, x1, top, bottom = float(ln["x0"]), float(ln["x1"]), float(ln["top"]), float(ln["bottom"])
        w, h = x1 - x0, bottom - top
        if w < DOT_MAX and h < DOT_MAX:
            continue
        if h <= w:  # horizontal (or close to it): one y
            y = (top + bottom) / 2
            box = (r2(x0), r2(y), r2(x1), r2(y))
        else:
            x = (x0 + x1) / 2
            box = (r2(x), r2(top), r2(x), r2(bottom))
        lines.append(Line(id=ids.next("l"), box=box, style=_style(ln)))
    for rc in page.rects:
        if not _visible(rc):
            continue
        x0, x1, top, bottom = float(rc["x0"]), float(rc["x1"]), float(rc["top"]), float(rc["bottom"])
        w, h = x1 - x0, bottom - top
        if w < DOT_MAX and h < DOT_MAX:
            continue
        if h <= LINE_MAX_THICKNESS and w > h:
            y = (top + bottom) / 2
            lines.append(Line(id=ids.next("l"), box=(r2(x0), r2(y), r2(x1), r2(y)), style=_style(rc)))
        elif w <= LINE_MAX_THICKNESS and h > w:
            x = (x0 + x1) / 2
            lines.append(Line(id=ids.next("l"), box=(r2(x), r2(top), r2(x), r2(bottom)), style=_style(rc)))
        else:
            rects.append(Rect(id=ids.next("q"), box=(r2(x0), r2(top), r2(x1), r2(bottom))))
    return lines, rects


# ---------------------------------------------------------------- declared fields


def _name(v: Any) -> str:
    from pdfminer.psparser import PSLiteral

    if isinstance(v, PSLiteral):
        return str(v.name)
    if isinstance(v, bytes):
        return v.decode("latin-1")
    return str(v) if v is not None else ""


def _text(v: Any) -> str:
    from pdfminer.utils import decode_text

    if isinstance(v, bytes):
        return decode_text(v)
    return str(v) if v is not None else ""


def _inherited(d: dict[str, Any], key: str) -> Any:
    from pdfminer.pdftypes import resolve1

    seen = 0
    while isinstance(d, dict) and seen < 32:
        if key in d:
            return resolve1(d[key])
        d = resolve1(d.get("Parent"))
        seen += 1
    return None


def _full_name(d: dict[str, Any]) -> str:
    from pdfminer.pdftypes import resolve1

    parts: list[str] = []
    seen = 0
    while isinstance(d, dict) and seen < 32:
        if "T" in d:
            parts.append(_text(resolve1(d["T"])))
        d = resolve1(d.get("Parent"))
        seen += 1
    return ".".join(reversed([p for p in parts if p]))


def _widgets(page: Any, ids: Ids) -> list[Widget]:
    from pdfminer.pdftypes import resolve1

    out: list[Widget] = []
    for a in page.annots or []:
        d = a.get("data") or {}
        if _name(resolve1(d.get("Subtype"))) != "Widget":
            continue
        ft = _name(_inherited(d, "FT"))
        flags = int(_inherited(d, "Ff") or 0)
        kind: str | None
        if ft == "Tx":
            kind = "text"
        elif ft == "Btn":
            if flags & (1 << 16):  # push button: not a place to fill
                kind = None
            else:
                kind = "radio" if flags & (1 << 15) else "checkbox"
        elif ft == "Ch":
            kind = "choice"
        elif ft == "Sig":
            kind = "signature"
        else:
            kind = None
        if kind is None:
            continue
        x0, top, x1, bottom = (float(a[k]) for k in ("x0", "top", "x1", "bottom"))
        if x1 < x0:
            x0, x1 = x1, x0
        if bottom < top:
            top, bottom = bottom, top
        options: list[str] = []
        if kind == "choice":
            for o in resolve1(_inherited(d, "Opt")) or []:
                o = resolve1(o)
                options.append(_text(resolve1(o[-1])) if isinstance(o, list) and o else _text(o))
        max_len = _inherited(d, "MaxLen") if kind == "text" else None
        name = _full_name(d)
        out.append(Widget(**nn(
            id=ids.next("w"), kind=kind, name=name or None,
            box=(r2(x0), r2(top), r2(x1), r2(bottom)),
            max_len=int(max_len) if isinstance(max_len, (int, float)) and max_len >= 1 else None,
            comb=bool(kind == "text" and flags & (1 << 24)),
            options=options,
        )))
    return out


# ---------------------------------------------------------------- document


@register("pdf")
def read(data: bytes, options: ReadOptions) -> ReadResult:
    import pdfplumber
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    from pdfplumber.utils.exceptions import PdfminerException

    if not data.lstrip()[:5].startswith(b"%PDF-") and b"%PDF-" not in data[:1024]:
        raise ReaderError("UNREADABLE", "no PDF header in the first kilobyte")
    ids = Ids()
    pages: list[Page] = []
    warnings: list[Warning] = []
    try:
        # An owner password only restricts printing and copying: the empty user password opens the file. A legacy 8-bit
        # annotation string (title, contents) must never sink the page: it is not used here, so a bad one is dropped.
        with warnings_mod.catch_warnings():
            warnings_mod.simplefilter("ignore")
            pdf = pdfplumber.open(io.BytesIO(data), password="", raise_unicode_errors=False)
    except PDFPasswordIncorrect:
        raise ReaderError("ENCRYPTED", "the PDF needs a user password") from None
    except PdfminerException as e:   # pdfplumber wraps what pdfminer raises; the password case is told apart here
        if e.args and isinstance(e.args[0], PDFPasswordIncorrect):
            raise ReaderError("ENCRYPTED", "the PDF needs a user password") from None
        raise
    with pdf:
        if len(pdf.pages) > options.max_pages:
            raise ReaderError("TOO_LARGE", f"{len(pdf.pages)} pages, the limit is {options.max_pages}")
        image_way = hook("pdf.textless_page")
        for index, page in enumerate(pdf.pages):
            number = index + 1
            chars = page.chars
            ink = sum(1 for c in chars if c.get("text") and not c["text"].isspace())
            no_ocr: list[Warning] = []
            scan = 0.0
            if options.ocr_min_chars <= ink < SCAN_TEXT_MAX and image_way is not None:
                scan = _scan_cover(page)   # a scan with a short text layer (04-F4) takes the image way too
            if (ink < options.ocr_min_chars or scan >= SCAN_COVER) and image_way is not None:
                got = image_way(data, index, number, ids, options)
                page_, extra = got if isinstance(got, tuple) else (got, [])
                if page_.ink is False and not extra:   # AUDIT-8 VE-2: a measured blank page was not "read from its pixels"
                    pages.append(page_)
                    continue
                if page_.runs or not extra:
                    pages.append(page_)
                    warnings.extend(extra)
                    why = (f"{ink} characters of text and a picture over {round(100 * scan)}% of the page (a scan)"
                           if scan >= SCAN_COVER else f"{ink} characters of text")
                    warnings.append(Warning(code="OCR_USED", page=number,
                                            detail=f"{why}; the page was read from its pixels"))
                    continue
                # the image way read nothing (no engine, a failure): the native few characters stay, the reason is told
                no_ocr = extra
            runs = _runs(chars, ids)
            lines, rects = _vectors(page, ids)
            if no_ocr:
                warnings.extend(no_ocr)
            elif ink < options.ocr_min_chars:
                warnings.append(Warning(
                    code="UNREADABLE_PART", page=number,
                    detail=f"{ink} characters of text, fewer than {options.ocr_min_chars}: the page needs the image "
                           "way (OCR), which this build does not have; text drawn as pixels is not read"))
            try:
                with warnings_mod.catch_warnings():
                    warnings_mod.simplefilter("ignore")
                    widgets = _widgets(page, ids)
            except Exception as e:  # noqa: BLE001 - one broken annotation never sinks a page
                widgets = []
                warnings.append(Warning(code="UNREADABLE_PART", page=number,
                                        detail=f"the form fields of the page were not read ({type(e).__name__})"))
            pages.append(Page(
                number=number, width=r2(page.width), height=r2(page.height), origin="native",
                runs=runs, lines=lines, rects=rects, widgets=widgets,
            ))
    return ReadResult(reader="pdf.native", pages=pages, warnings=warnings)

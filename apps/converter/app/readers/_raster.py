"""Pixels without OpenCV (design 6.2.2): decode with limits, drop metadata, cut a tall scan into pages, and find
lines, boxes, combs and dotted leaders in a page with Pillow and the `re` module only (no numpy).

All coordinates here are pixels of the page strip, origin top left; `image.py` converts them to points.
Rows of a bitmap are `bytes` (255 = ink), so a run of ink is one regular expression match and the work is done in C.
"""
from __future__ import annotations

import io
import math
import re
import warnings
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterator
from statistics import median

from PIL import Image, ImageOps

from ._base import ReaderError, ReadOptions

PX_TO_PT = 72.0 / 200.0  # a scan of A4 that is 1654 pixels wide was made at 200 dpi
SQRT2 = math.sqrt(2.0)
_PNG = b"\x89PNG\r\n\x1a\n"

# ---------------------------------------------------------------- decode


def decode(data: bytes, options: ReadOptions) -> Image.Image:
    """Bytes of a JPEG or PNG -> 8-bit grey image with no metadata at all (pixels only).

    Only the two formats are opened (Pillow restricted by `formats`). The size is read from the header and checked
    against `options.max_pixels` before a single pixel is decoded. Orientation from EXIF is applied, then dropped
    with everything else; transparency is laid on white; only the first frame of an animated PNG is read."""
    if data[:3] == b"\xff\xd8\xff":
        formats = ["JPEG"]
    elif data[:8] == _PNG:
        formats = ["PNG"]
    else:
        raise ReaderError("UNREADABLE", "the file has no JPEG or PNG signature")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # Pillow's own bomb warning; the limit below is ours
        try:
            im = Image.open(io.BytesIO(data), formats=formats)
        except Image.DecompressionBombError:
            raise ReaderError("TOO_LARGE", "the image declares more pixels than the decoder may open") from None
        w, h = im.size
        if w < 1 or h < 1:
            raise ReaderError("UNREADABLE", "the image has no pixels")
        if w * h > options.max_pixels:
            raise ReaderError("TOO_LARGE", f"{w} x {h} pixels, the limit is {options.max_pixels} pixels")
        try:
            im.load()
        except Image.DecompressionBombError:
            raise ReaderError("TOO_LARGE", "the image has more pixels than the decoder may open") from None
        return _to_grey(im)


_FRAME_FORMATS = {"tiff": "TIFF", "bmp": "BMP", "gif": "GIF", "webp": "WEBP"}


def _to_grey(im: Image.Image) -> Image.Image:
    """A loaded frame -> 8-bit grey with no metadata: orientation applied, transparency on white."""
    try:
        im = ImageOps.exif_transpose(im) or im
    except Exception:  # noqa: BLE001 - a broken EXIF block is metadata we drop anyway
        pass
    if im.mode in ("I;16", "I;16L", "I;16B", "I"):
        im = im.convert("I").point(lambda v: v * (1 / 256), "L")
    elif im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        rgba = im.convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        im = Image.alpha_composite(white, rgba)
    grey = im.convert("L")
    # a new image from the raw pixels carries no `info`, no EXIF, no ICC profile, no text chunks
    return Image.frombytes("L", grey.size, grey.tobytes())


def decode_frames(data: bytes, options: ReadOptions, kind: str) -> Iterator[Image.Image]:
    """TIFF (every frame), BMP, GIF and WEBP (the first frame only) -> one grey image per page, one at a time.

    The same limits as `decode`: Pillow is restricted to the one format the guard proved, the size of EVERY frame is
    read from its header and checked against `options.max_pixels` before its pixels are decoded, and the number of
    frames is checked against `options.max_pages` before the first is decoded. Only one frame is in memory at once."""
    fmt = _FRAME_FORMATS[kind]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            im = Image.open(io.BytesIO(data), formats=[fmt])
        except Image.DecompressionBombError:
            raise ReaderError("TOO_LARGE", "the image declares more pixels than the decoder may open") from None
        frames = getattr(im, "n_frames", 1) if kind == "tiff" else 1
        if frames > options.max_pages:
            raise ReaderError("TOO_LARGE", f"{frames} pages, the limit is {options.max_pages}")
        for i in range(frames):
            im.seek(i)
            w, h = im.size
            if w < 1 or h < 1:
                raise ReaderError("UNREADABLE", "the image has no pixels")
            if w * h > options.max_pixels:
                raise ReaderError("TOO_LARGE", f"{w} x {h} pixels, the limit is {options.max_pixels} pixels")
            try:
                im.load()
            except Image.DecompressionBombError:
                raise ReaderError("TOO_LARGE", "the image has more pixels than the decoder may open") from None
            yield _to_grey(im)


def otsu(grey: Image.Image) -> int:
    hist = grey.histogram()
    total = sum(hist)
    if total == 0:
        return 128
    sum_all = sum(i * c for i, c in enumerate(hist))
    best, best_t, w0, s0 = -1.0, 128, 0, 0
    for t in range(256):
        w0 += hist[t]
        if w0 == 0:
            continue
        w1 = total - w0
        if w1 == 0:
            break
        s0 += t * hist[t]
        m0, m1 = s0 / w0, (sum_all - s0) / w1
        between = w0 * w1 * (m0 - m1) ** 2
        if between > best:
            best, best_t = between, t
    return max(60, min(200, best_t))


def binarize(grey: Image.Image) -> Image.Image:
    """Mode L with 255 where there is ink. A page whose majority is dark is taken as light text on dark and inverted."""
    t = otsu(grey)
    ink = grey.point([255 if v <= t else 0 for v in range(256)])
    dark = ink.resize((1, 1), Image.BOX).getpixel((0, 0))
    if dark > 128:
        ink = ink.point([255 - v for v in range(256)])
    return ink


# ---------------------------------------------------------------- cutting a tall scan


def cut_points(ink: Image.Image) -> tuple[list[int], list[int]]:
    """Boundaries [0, c1, ..., h] of the pages of a stacked scan, and the pages (1-based) whose lower cut found no
    white band and was made at the nominal place.

    A page is A4: height = width x sqrt(2). The count is the height over that, rounded; each nominal cut k*h/n is
    moved to the centre of the nearest run of white rows within 8 % of a page (design 6.2)."""
    w, h = ink.size
    page_h = w * SQRT2
    n = max(1, round(h / page_h))
    if n == 1:
        return [0, h], []
    means = ink.resize((1, h), Image.BOX).tobytes() if w > 1 else ink.tobytes()
    white = [m <= 2 for m in means]
    window = max(4, int(page_h * 0.08))
    cuts = [0]
    unsnapped: list[int] = []
    for k in range(1, n):
        nominal = round(k * h / n)
        lo, hi = max(cuts[-1] + 1, nominal - window), min(h - 1, nominal + window)
        best: tuple[float, int] | None = None
        y = lo
        while y <= hi:
            if white[y]:
                s = y
                while y <= hi and white[y]:
                    y += 1
                centre = (s + y - 1) // 2
                d = abs(centre - nominal)
                if best is None or d < best[0]:
                    best = (d, centre)
            else:
                y += 1
        if best is None:
            unsnapped.append(k)
            cuts.append(max(cuts[-1] + 1, nominal))
        else:
            cuts.append(best[1])
    cuts.append(h)
    return cuts, unsnapped


# ---------------------------------------------------------------- shapes


@dataclass
class Edge:
    """A straight run of ink: x0..x1 along the line (exclusive end), y0..y1 across it (exclusive end)."""

    x0: int
    x1: int
    y0: int
    y1: int


Box4 = tuple[int, int, int, int]  # x0, y0, x1, y1 in pixels


@dataclass
class Shapes:
    hlines: list[Box4] = field(default_factory=list)
    vlines: list[Box4] = field(default_factory=list)
    boxes: list[Box4] = field(default_factory=list)
    combs: list[list[Box4]] = field(default_factory=list)
    leaders: list[Box4] = field(default_factory=list)


@lru_cache(maxsize=64)
def _run_pattern(min_len: int) -> re.Pattern[bytes]:
    return re.compile(rb"\xff{%d,}" % min_len)


def _rows(img: Image.Image) -> list[bytes]:
    w, h = img.size
    raw = img.tobytes()
    return [raw[y * w:(y + 1) * w] for y in range(h)]


def _close_gaps(row: bytes) -> bytes:
    """A single missing pixel inside a ruled line (a scan's noise) does not break the line."""
    if b"\xff\x00\xff" not in row:
        return row
    return row.replace(b"\xff\x00\xff", b"\xff\xff\xff").replace(b"\xff\x00\xff", b"\xff\xff\xff")


def edges_of(rows: list[bytes], min_len: int, max_thick: int, tol: int = 3) -> list[Edge]:
    """Runs of ink of at least `min_len` in a row, joined with the runs of the next rows that start and end at the
    same places (within `tol`); a stack thicker than `max_thick` rows is a filled shape, not a line, and is dropped."""
    pat = _run_pattern(min_len)
    active: list[Edge] = []
    done: list[Edge] = []
    for y, row in enumerate(rows):
        runs = [(m.start(), m.end()) for m in pat.finditer(_close_gaps(row))]
        nxt: list[Edge] = []
        taken: set[int] = set()
        for a, b in runs:
            for i, e in enumerate(active):
                if i not in taken and e.y1 == y and abs(e.x0 - a) <= tol and abs(e.x1 - b) <= tol:
                    taken.add(i)
                    e.x0, e.x1, e.y1 = min(e.x0, a), max(e.x1, b), y + 1
                    nxt.append(e)
                    break
            else:
                nxt.append(Edge(a, b, y, y + 1))
        done.extend(e for i, e in enumerate(active) if i not in taken)
        active = nxt
    done.extend(active)
    return [e for e in done if e.y1 - e.y0 <= max_thick]


def _column_clusters(profile: bytes, level: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    start = -1
    for i, v in enumerate(profile):
        if v >= level and start < 0:
            start = i
        elif v < level and start >= 0:
            out.append((start, i))
            start = -1
    if start >= 0:
        out.append((start, len(profile)))
    return out


def _boxes(ink: Image.Image, hedges: list[Edge], min_side: int, max_h: int) -> list[Box4]:
    """Closed boxes: a top edge, a bottom edge of the same extent below it, and solid sides in between. Sides inside
    the extent (a row of cells that share their borders) cut it into several boxes."""
    buckets: dict[int, list[Edge]] = {}
    for e in hedges:
        buckets.setdefault(e.x0 // 6, []).append(e)
    found: dict[Box4, None] = {}
    for t in hedges:
        cand: Edge | None = None
        for k in (t.x0 // 6 - 1, t.x0 // 6, t.x0 // 6 + 1):
            for b in buckets.get(k, ()):
                gap = b.y0 - t.y1
                if gap < min_side - 4 or gap > max_h or abs(b.x0 - t.x0) > 4 or abs(b.x1 - t.x1) > 4:
                    continue
                if cand is None or b.y0 < cand.y0:
                    cand = b
        if cand is None:
            continue
        x0, x1 = t.x0, t.x1
        profile = ink.crop((x0, t.y1, x1, cand.y0)).resize((x1 - x0, 1), Image.BOX).tobytes()
        clusters = _column_clusters(profile, 230)
        if len(clusters) < 2 or clusters[0][0] > 4 or x1 - x0 - clusters[-1][1] > 4:
            continue
        for (a0, _a1), (_b0, b1) in zip(clusters, clusters[1:]):
            if b1 - a0 >= min_side:
                found[(x0 + a0, t.y0, x0 + b1, cand.y1)] = None
    return list(found)


def _combs(boxes: list[Box4], max_side: int) -> list[list[Box4]]:
    small = sorted((b for b in boxes if b[2] - b[0] <= max_side and b[3] - b[1] <= max_side * 2),
                   key=lambda b: (round(b[1] / 4), b[0]))
    combs: list[list[Box4]] = []
    used: set[Box4] = set()
    for i, first in enumerate(small):
        if first in used:
            continue
        row = [first]
        w0, gap0 = first[2] - first[0], None
        for nxt in small[i + 1:]:
            last = row[-1]
            if abs(nxt[1] - first[1]) > 3 or abs(nxt[3] - first[3]) > 3:
                continue
            if abs((nxt[2] - nxt[0]) - w0) > 3 or nxt[0] < last[0]:
                continue
            gap = nxt[0] - last[2]
            if gap < -8 or gap > 2 * w0:
                continue
            if gap0 is None:
                gap0 = gap
            elif abs(gap - gap0) > 3:
                continue
            row.append(nxt)
        if len(row) >= 3:
            combs.append(row)
            used.update(row)
    return combs


def _leaders(ink: Image.Image, rows: list[bytes]) -> list[Box4]:
    """Dotted leaders: a text-line band of 8 or more small marks of equal size and equal pitch, with nothing around."""
    w, _h = ink.size
    mark = re.compile(rb"\xff+")
    qualifying: list[tuple[int, int, int, int]] = []  # y, x0, x1, pitch
    for y, row in enumerate(rows):
        if b"\xff" not in row:
            continue
        runs = [(m.start(), m.end()) for m in mark.finditer(row) if m.end() - m.start() <= 9]  # long ink is a rule
        if len(runs) < 8:
            continue
        pitches = [runs[i + 1][0] - runs[i][0] for i in range(len(runs) - 1)]
        p = median(pitches)
        if not 5 <= p <= 40:
            continue
        # the longest stretch of marks that keep the pitch
        best, cur = (0, 0), 0
        for i, q in enumerate(pitches):
            if abs(q - p) <= 2:
                cur += 1
                if cur > best[1] - best[0]:
                    best = (i - cur + 1, i + 1)
            else:
                cur = 0
        i0, i1 = best
        if i1 - i0 + 1 < 8:
            continue
        # a stretch where runs follow no wider than the marks themselves (a long ink run) is not a dot
        qualifying.append((y, runs[i0][0], runs[i1][1], int(p)))
    leaders: list[Box4] = []
    i = 0
    while i < len(qualifying):
        j = i
        while j + 1 < len(qualifying) and qualifying[j + 1][0] - qualifying[j][0] <= 1:
            j += 1
        band = qualifying[i:j + 1]
        i = j + 1
        y0, y1 = band[0][0], band[-1][0] + 1
        x0, x1 = min(b[1] for b in band), max(b[2] for b in band)
        if y1 - y0 > 12 or x1 - x0 < 8 * min(b[3] for b in band) * 0.9:
            continue
        pad = 6
        around = []
        for ya, yb in ((max(0, y0 - pad), y0), (y1, min(ink.size[1], y1 + pad))):
            if yb > ya:
                around.append(ink.crop((x0, ya, x1, yb)).resize((1, 1), Image.BOX).getpixel((0, 0)))
        if all(a <= 5 for a in around):
            leaders.append((x0, y0, x1, y1))
    del w
    return leaders


def detect(ink: Image.Image, *, min_line: int = 30, max_thick: int = 8) -> Shapes:
    """Lines, boxes, combs and leaders of one page strip (`ink` from `binarize`)."""
    w, h = ink.size
    shapes = Shapes()
    if w < 20 or h < 20 or ink.getbbox() is None:
        return shapes
    rows = _rows(ink)
    hedges = edges_of(rows, 14, max_thick)
    shapes.hlines = [(e.x0, e.y0, e.x1, e.y1) for e in hedges if e.x1 - e.x0 >= min_line]
    cols = _rows(ink.transpose(Image.Transpose.TRANSPOSE))
    shapes.vlines = [(e.y0, e.x0, e.y1, e.x1) for e in edges_of(cols, min_line, max_thick)]
    shapes.boxes = _boxes(ink, hedges, 12, max(60, h // 2))
    shapes.combs = _combs(shapes.boxes, 120)
    shapes.leaders = _leaders(ink, rows)
    return shapes

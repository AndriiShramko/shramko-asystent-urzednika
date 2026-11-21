"""Drawn shapes of a page: closed boxes from rectangles and from ruled lines, rows of equal boxes, reading order.

A paper draws a box either as one rectangle or as four line segments that nearly touch (the PDF of judged set 2
draws every comb cell from separate segments with gaps of half a point). Both become plain boxes here.
"""
from __future__ import annotations

from app.model.page import Page

Box = tuple[float, float, float, float]

TOL = 2.5            # points by which the ends of two segments may miss each other
MIN_SIDE = 5.0       # a box smaller than this is a dot or a corner, not a place to write
COL_GAP = 18.0       # white gutter that separates two columns
BLOCK_GAP = 14.0     # white band that separates two blocks
ROW_GAP = 0.5


def ruled(page: Page) -> tuple[list[Box], list[Box]]:
    """Horizontal and vertical ruled lines of the page (line elements and the edges of rectangles)."""
    hor: list[Box] = []
    ver: list[Box] = []
    for ln in page.lines:
        x0, y0, x1, y1 = ln.box
        if abs(y1 - y0) <= 1.5 and x1 - x0 >= 3:
            hor.append((x0, y0, x1, y1))
        elif abs(x1 - x0) <= 1.5 and y1 - y0 >= 3:
            ver.append((x0, y0, x1, y1))
    return hor, ver


def _covered(hor: list[Box], y: float, xa: float, xb: float) -> bool:
    segs = sorted((h[0], h[2]) for h in hor if abs((h[1] + h[3]) / 2 - y) <= TOL and h[2] > xa and h[0] < xb)
    reach = xa + TOL
    for s, e in segs:
        if s > reach:
            return False
        reach = max(reach, e + TOL)
    return reach >= xb


def _from_lines(hor: list[Box], ver: list[Box]) -> list[Box]:
    out: list[Box] = []
    groups: list[list[Box]] = []
    for v in sorted(ver, key=lambda v: (v[1], v[3], v[0])):
        for g in groups:
            if abs(g[0][1] - v[1]) <= 1.5 and abs(g[0][3] - v[3]) <= 1.5:
                g.append(v)
                break
        else:
            groups.append([v])
    for g in groups:
        xs: list[float] = []
        for v in sorted(g, key=lambda v: v[0]):
            if not xs or v[0] - xs[-1] > 1.5:
                xs.append(v[0])
        ya, yb = g[0][1], g[0][3]
        for xa, xb in zip(xs, xs[1:]):
            if xb - xa >= MIN_SIDE and yb - ya >= MIN_SIDE and _covered(hor, ya, xa, xb) and _covered(hor, yb, xa, xb):
                out.append((xa, ya, xb, yb))
    return out


def area(b: Box) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def inter(a: Box, b: Box) -> float:
    return area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))


def inside(inner: Box, outer: Box, tol: float = 1.5) -> bool:
    return (inner[0] >= outer[0] - tol and inner[1] >= outer[1] - tol
            and inner[2] <= outer[2] + tol and inner[3] <= outer[3] + tol)


def centre_in(b: Box, outer: Box) -> bool:
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    return outer[0] <= cx <= outer[2] and outer[1] <= cy <= outer[3]


def union(boxes: list[Box]) -> Box:
    return (round(min(b[0] for b in boxes), 2), round(min(b[1] for b in boxes), 2),
            round(max(b[2] for b in boxes), 2), round(max(b[3] for b in boxes), 2))


def boxes(page: Page, hor: list[Box], ver: list[Box]) -> list[Box]:
    """Closed boxes of the page without duplicates; a box that holds another box is kept (the caller decides)."""
    raw: list[Box] = []
    for q in page.rects:
        x0, y0, x1, y1 = q.box
        if x1 - x0 >= MIN_SIDE and y1 - y0 >= MIN_SIDE:
            raw.append((x0, y0, x1, y1))
    raw += _from_lines(hor, ver)
    out: list[Box] = []
    for b in sorted(raw, key=lambda b: (b[1], b[0], area(b))):
        if not any(inter(b, o) > 0.8 * max(area(b), area(o)) for o in out):
            out.append(b)
    return out


def combs(cells: list[Box], gap_text) -> tuple[list[list[Box]], list[Box]]:  # noqa: ANN001
    """Rows of at least three equal boxes with equal gaps -> (chains, the boxes left over).

    `gap_text(box)` returns the text printed in a gap between two boxes; more than two characters there is a
    label, and a label ends the row (two address boxes with "Nr lokalu" between them are not a comb)."""
    left: list[Box] = []
    chains: list[list[Box]] = []
    small = [b for b in cells if 6 <= b[2] - b[0] <= 32 and 8 <= b[3] - b[1] <= 32]
    left += [b for b in cells if b not in small]
    bands: list[list[Box]] = []
    for b in sorted(small, key=lambda b: (b[1], b[0])):
        for band in bands:
            if abs(band[0][1] - b[1]) <= 2 and abs(band[0][3] - b[3]) <= 2:
                band.append(b)
                break
        else:
            bands.append([b])
    for band in bands:
        band.sort(key=lambda b: b[0])
        cur = [band[0]]
        for b in band[1:] + [None]:  # type: ignore[list-item]
            p = cur[-1]
            w = cur[0][2] - cur[0][0]
            ok = False
            if b is not None:
                gap = b[0] - p[2]
                ok = abs((b[2] - b[0]) - w) <= 0.2 * w and -1.5 <= gap <= 1.6 * w
                if ok and gap > 0.4 * w and len(gap_text((p[2], p[1], b[0], p[3])).strip()) > 2:
                    ok = False
            if ok:
                cur.append(b)  # type: ignore[arg-type]
            else:
                if len(cur) >= 3:
                    chains.append(cur)
                else:
                    left += cur
                if b is not None:
                    cur = [b]
    return chains, left


def _split(items: list[tuple[Box, object]], axis: int, gap: float) -> list[list[tuple[Box, object]]]:
    its = sorted(items, key=lambda it: it[0][axis])
    groups = [[its[0]]]
    hi = its[0][0][axis + 2]
    for it in its[1:]:
        if it[0][axis] - hi >= gap:
            groups.append([it])
            hi = it[0][axis + 2]
        else:
            groups[-1].append(it)
            hi = max(hi, it[0][axis + 2])
    return groups


def reading_order(items: list[tuple[Box, object]], ygap: float = BLOCK_GAP) -> list[tuple[Box, object]]:
    """Recursive cuts along white space (design 6.3.1): columns first, then blocks, then rows left to right."""
    if len(items) <= 1:
        return list(items)
    cols = _split(items, 0, COL_GAP)
    if len(cols) > 1 and sum(len(c) >= 2 for c in cols) >= 2:
        return [x for c in cols for x in reading_order(c, BLOCK_GAP)]
    bands = _split(items, 1, ygap)
    if len(bands) > 1:
        return [x for b in bands for x in reading_order(b, ygap)]
    if ygap > ROW_GAP:
        return reading_order(items, ROW_GAP)
    rows: list[list[tuple[Box, object]]] = []
    for it in sorted(items, key=lambda it: ((it[0][1] + it[0][3]) / 2, it[0][0])):
        cy = (it[0][1] + it[0][3]) / 2
        if rows and rows[-1][0][0][1] <= cy <= rows[-1][0][0][3]:
            rows[-1].append(it)
        else:
            rows.append([it])
    return [x for row in rows for x in sorted(row, key=lambda it: it[0][0])]

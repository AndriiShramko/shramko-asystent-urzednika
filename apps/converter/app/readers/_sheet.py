"""The grid of one sheet -> one page of origin "flow" (shared by the XLSX and ODS readers; design 6.2).

A sheet is a page without geometry: every run and cell carries an anchor in the workbook's own notation,
"Arkusz1!B7"; the table of the sheet is anchored at its used range, "Arkusz1!A1:H40". Rules, one place each:

- One run per cell with text, in row-major order. Cell r and c are the sheet's own indices from 0 (row 7 is r=6),
  so they line up with `row_heights` and `col_widths`.
- A cell of the table is: a cell with text, a merged range (its top-left cell, spans rs and cs), or an empty
  cell with a drawn border (an empty bordered range beside a label is a place to fill). An empty merge without
  a border is a spacer and is left out.
- Borders: a side is drawn when the cell (any cell along that side of a merge) declares it, or when the
  neighbour across that side declares the opposite one (spreadsheets store a shared edge on either cell).
- Merges are clamped to the used range before anything is expanded, so a merge "A1:XFD1048576" costs nothing.
- Hidden rows and columns are read; their height or width is 0 (they print nothing). Sizes are given up to the
  last used row and column only.
- A data-validation list is a widget of kind "choice" anchored at its range; options that cannot be resolved
  leave the widget without options and an UNREADABLE_PART warning (never a guessed list).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.model.common import Warning
from app.model.page import Cell, Page, Run, Table, Widget

from ._base import Ids, r2

MAX_ROW, MAX_COL = 1 << 20, 1 << 14   # the largest sheet any of the formats addresses
_REF = re.compile(r"^\$?([A-Za-z]{1,3})\$?(\d{1,7})$")


def col_letters(c: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA."""
    s = ""
    c += 1
    while c:
        c, rem = divmod(c - 1, 26)
        s = chr(65 + rem) + s
    return s


def a1(r: int, c: int) -> str:
    return f"{col_letters(c)}{r + 1}"


def parse_a1(ref: str) -> tuple[int, int] | None:
    """"B7" or "$B$7" -> (6, 1); None when it is not a cell reference."""
    m = _REF.match(ref.strip())
    if not m:
        return None
    c = 0
    for ch in m.group(1).upper():
        c = c * 26 + ord(ch) - 64
    r = int(m.group(2))
    if r < 1 or c < 1 or r > MAX_ROW or c > MAX_COL:
        return None
    return r - 1, c - 1


def parse_range(ref: str) -> tuple[int, int, int, int] | None:
    """"B7:D9" or "B7" -> (r0, c0, r1, c1) inclusive; whole rows or columns are not accepted."""
    a, _, b = ref.partition(":")
    p = parse_a1(a)
    q = parse_a1(b) if b else p
    if p is None or q is None:
        return None
    return min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1])


@dataclass
class Text:
    text: str
    bold: bool = False
    size: float | None = None


@dataclass
class Validation:
    r0: int
    c0: int
    r1: int
    c1: int
    options: list[str] | None   # None: the list could not be resolved


@dataclass
class Sheet:
    name: str
    hidden: bool = False
    texts: dict[tuple[int, int], Text] = field(default_factory=dict)
    borders: dict[tuple[int, int], str] = field(default_factory=dict)     # declared sides, any of "trbl"
    merges: list[tuple[int, int, int, int]] = field(default_factory=list)  # (r0, c0, r1, c1) inclusive
    validations: list[Validation] = field(default_factory=list)
    default_row: float = 15.0          # points
    default_col: float = 48.0          # points
    rows: dict[int, float] = field(default_factory=dict)   # explicit heights, points; 0 when hidden
    cols: list[tuple[int, int, float]] = field(default_factory=list)  # (c0, c1 inclusive, width pt; 0 hidden)


def _side(sheet: Sheet, r: int, c: int, side: str) -> bool:
    if side in sheet.borders.get((r, c), ""):
        return True
    opposite = {"t": ((-1, 0), "b"), "b": ((1, 0), "t"), "l": ((0, -1), "r"), "r": ((0, 1), "l")}[side]
    (dr, dc), other = opposite
    return other in sheet.borders.get((r + dr, c + dc), "")


def _drawn(sheet: Sheet, r0: int, c0: int, r1: int, c1: int) -> str:
    out = ""
    if any(_side(sheet, r0, c, "t") for c in range(c0, c1 + 1)):
        out += "t"
    if any(_side(sheet, r, c1, "r") for r in range(r0, r1 + 1)):
        out += "r"
    if any(_side(sheet, r1, c, "b") for c in range(c0, c1 + 1)):
        out += "b"
    if any(_side(sheet, r, c0, "l") for r in range(r0, r1 + 1)):
        out += "l"
    return out


def build_page(number: int, sheet: Sheet, ids: Ids, warnings: list[Warning]) -> Page:
    # The used range: cells with text or a declared border, and the first cell of each data validation.
    keys = [*sheet.texts, *sheet.borders, *((v.r0, v.c0) for v in sheet.validations)]
    max_r = max((k[0] for k in keys), default=-1)
    max_c = max((k[1] for k in keys), default=-1)

    # Merges clamped to the used range, first one wins where two overlap. A merge outside it is empty.
    top_left: dict[tuple[int, int], tuple[int, int]] = {}
    covered: set[tuple[int, int]] = set()
    for r0, c0, r1, c1 in sheet.merges:
        if r0 > max_r or c0 > max_c or (r0, c0) in covered or (r0, c0) in top_left:
            continue
        r1, c1 = min(r1, max_r), min(c1, max_c)
        cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
        if any(p in covered or p in top_left for p in cells):
            continue
        top_left[(r0, c0)] = (r1 - r0 + 1, c1 - c0 + 1)
        covered.update(cells[1:])

    anchor = lambda r, c: f"{sheet.name}!{a1(r, c)}"  # noqa: E731
    places = sorted({p for p in (*sheet.texts, *sheet.borders, *top_left) if p not in covered})
    runs: list[Run] = []
    cells: list[Cell] = []
    for r, c in places:
        rs, cs = top_left.get((r, c), (1, 1))
        drawn = _drawn(sheet, r, c, r + rs - 1, c + cs - 1)
        t = sheet.texts.get((r, c))
        text = t.text.strip() if t else ""
        rid: list[str] = []
        if text:
            run, ws = Run.safe(number, id=ids.next("r"), text=text, anchor=anchor(r, c), bold=t.bold, size=t.size)
            warnings.extend(ws)
            if run is not None:
                runs.append(run)
                rid = [run.id]
        if not rid and not drawn:
            continue
        cells.append(Cell(r=r, c=c, rs=rs, cs=cs, anchor=anchor(r, c), runs=rid, borders=drawn))

    widgets: list[Widget] = []
    for v in sheet.validations:
        ref = a1(v.r0, v.c0) if (v.r0, v.c0) == (v.r1, v.c1) else f"{a1(v.r0, v.c0)}:{a1(v.r1, v.c1)}"
        w, ws = Widget.safe(number, id=ids.next("w"), kind="choice", anchor=f"{sheet.name}!{ref}",
                            options=v.options or [])
        warnings.extend(ws)
        if w is not None:
            widgets.append(w)
            if v.options is None:
                warnings.append(Warning(code="UNREADABLE_PART", page=number, anchor=w.anchor,
                                        detail=f"widget {w.id}: the list of a data validation could not be resolved"))

    tables: list[Table] = []
    if cells:
        tables.append(Table(id=ids.next("t"), anchor=f"{sheet.name}!A1:{a1(max_r, max_c)}", cells=cells))
    row_heights = [r2(sheet.rows.get(r, sheet.default_row)) for r in range(max_r + 1)]
    col_widths = []
    for c in range(max_c + 1):
        w = next((x for c0, c1, x in sheet.cols if c0 <= c <= c1), sheet.default_col)
        col_widths.append(r2(w))
    if sheet.hidden:
        warnings.append(Warning(code="HIDDEN_SHEET", page=number,
                                detail="the sheet is hidden in the workbook; its content is read and kept"))
    return Page(number=number, origin="flow", name=sheet.name, hidden=sheet.hidden, runs=runs, tables=tables,
                widgets=widgets, row_heights=row_heights, col_widths=col_widths)

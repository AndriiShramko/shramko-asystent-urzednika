"""Builders for the finder tests: a page model written by hand, or a PDF drawn with reportlab and read back.

Synthetic words only; the PDF texts avoid Polish diacritics because the built-in fonts of reportlab lack them.
"""
from __future__ import annotations

import io
from typing import Any, Callable

from app.model.page import Cell, Line, Page, PageModel, Rect, Run, Source, Table
from app.readers import read_document

STRICT = {"strict": True}
DOTS = "." * 40


def model(*pages: Page, fmt: str = "pdf") -> PageModel:
    return PageModel(source=Source(sha256="0" * 64, format=fmt, reader="test.built", pages=len(pages)), pages=list(pages))


class Native:
    """One page with geometry, built element by element (points, origin top left)."""

    def __init__(self, number: int = 1) -> None:
        self.number, self.n = number, 0
        self.runs: list[Run] = []
        self.lines: list[Line] = []
        self.rects: list[Rect] = []

    def text(self, x: float, y: float, text: str, w: float, bold: bool = False, size: float = 10.0, rid: str | None = None) -> str:
        self.n += 1
        rid = rid or f"p{self.number}r{self.n}"
        self.runs.append(Run(id=rid, text=text, box=(x, y, x + w, y + size), size=size, bold=bold))
        return rid

    def rect(self, x: float, y: float, w: float, h: float) -> None:
        self.n += 1
        self.rects.append(Rect(id=f"p{self.number}q{self.n}", box=(x, y, x + w, y + h)))

    def hline(self, x0: float, x1: float, y: float) -> None:
        self.n += 1
        self.lines.append(Line(id=f"p{self.number}l{self.n}", box=(x0, y, x1, y)))

    def page(self) -> Page:
        return Page(number=self.number, width=595.0, height=842.0, origin="native", runs=self.runs,
                    lines=self.lines, rects=self.rects)


def flow(*texts: str, bold: tuple[int, ...] = (), number: int = 1) -> Page:
    """A page without geometry: one run per paragraph, in the file's order."""
    runs = [Run(id=f"f{number}r{i}", text=t, anchor=f"p[{i}]", size=11.0, bold=i in bold) for i, t in enumerate(texts)]
    return Page(number=number, origin="flow", runs=runs)


def flow_table(number: int, tid: str, rows: list[list[str]], before: tuple[str, ...] = ()) -> Page:
    """A flow page with paragraphs and then one table; a cell text of "" is an empty cell."""
    runs = [Run(id=f"{tid}p{i}", text=t, anchor=f"p[{i}]", size=11.0) for i, t in enumerate(before)]
    cells: list[Cell] = []
    for r, row in enumerate(rows):
        for c, t in enumerate(row):
            ids = []
            if t:
                rid = f"{tid}r{r}c{c}"
                runs.append(Run(id=rid, text=t, anchor=f"{tid}/cell[{r},{c}]", size=11.0))
                ids = [rid]
            cells.append(Cell(r=r, c=c, anchor=f"{tid}/cell[{r},{c}]", runs=ids))
    return Page(number=number, origin="flow", runs=runs, tables=[Table(id=tid, anchor=tid, cells=cells)])


def pdf(draw: Callable[[Any], None]) -> PageModel:
    """Draw one or more A4 pages on a reportlab canvas (origin bottom left) and read the PDF with our reader."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    draw(c)
    c.save()
    return read_document(buf.getvalue(), "pdf")


def tops(out: Any) -> list[Any]:
    """Candidates that are not members of a group: what a reader would call the fields."""
    return [c for c in out.candidates if c.group is None]

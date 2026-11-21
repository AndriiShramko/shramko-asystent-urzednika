"""Page model: the output of every reader and the only thing later steps see (design 5.1, 6.2).

Coordinates in points, origin top left. A page of origin native or ocr places every run, table, cell and widget
with a box; a page of origin flow (binary Word, a DOCX of ordinary paragraphs, sheet cells without geometry)
places them with an anchor instead. Readers never invent coordinates. Ids are unique inside the document.
Reading order is not part of this model: it is the finder's (design 6.3.1); runs are listed in the file's order.
"""
from __future__ import annotations

from typing import Literal, Self

from pydantic import ConfigDict, Field, model_validator

from .common import ONE_PLACE_SCHEMA, Anchor, Box, Contract, Format, PageNo, Sha256, Unit, Warning, exactly_one_place, unique

Origin = Literal["native", "ocr", "flow"]
LineStyle = Literal["solid", "dashed", "dotted"]
# What the format itself declares (design 5.1): PDF form fields, Word content controls and legacy form fields,
# sheet data-validation lists. Add a kind here with the reader that meets it.
WidgetKind = Literal["text", "checkbox", "radio", "choice", "date", "signature"]


class Source(Contract):
    sha256: Sha256
    format: Format
    reader: str = Field(pattern=r"^[a-z0-9_]+(\.[a-z0-9_]+)*$", description='Reader that made the model, e.g. "pdf.native".')
    pages: int = Field(ge=0)


class Run(Contract):
    model_config = ConfigDict(json_schema_extra=ONE_PLACE_SCHEMA)

    id: str = Field(min_length=1)
    text: str
    box: Box | None = None
    anchor: Anchor | None = None
    size: float | None = Field(default=None, gt=0, description="Font size in points, when the format gives it.")
    bold: bool = False
    conf: Unit = Field(default=1.0, description="1 for native text; the OCR word confidence otherwise.")

    @model_validator(mode="after")
    def _one_place(self) -> Self:
        exactly_one_place(self, "run")
        return self


class Line(Contract):
    id: str = Field(min_length=1)
    box: Box
    style: LineStyle = "solid"


class Rect(Contract):
    id: str = Field(min_length=1)
    box: Box


class Cell(Contract):
    model_config = ConfigDict(json_schema_extra=ONE_PLACE_SCHEMA)

    r: int = Field(ge=0)
    c: int = Field(ge=0)
    rs: int = Field(default=1, ge=1)
    cs: int = Field(default=1, ge=1)
    box: Box | None = None
    anchor: Anchor | None = None
    runs: list[str] = []
    borders: str = Field(default="", pattern=r"^t?r?b?l?$", description="Drawn borders: any of t, r, b, l in this order.")

    @model_validator(mode="after")
    def _one_place(self) -> Self:
        exactly_one_place(self, "cell")
        return self


class Table(Contract):
    model_config = ConfigDict(json_schema_extra=ONE_PLACE_SCHEMA)

    id: str = Field(min_length=1)
    box: Box | None = None
    anchor: Anchor | None = None
    cells: list[Cell] = []

    @model_validator(mode="after")
    def _one_place(self) -> Self:
        exactly_one_place(self, "table")
        return self


class Widget(Contract):
    model_config = ConfigDict(json_schema_extra=ONE_PLACE_SCHEMA)

    id: str = Field(min_length=1)
    kind: WidgetKind
    name: str | None = None
    box: Box | None = None
    anchor: Anchor | None = None
    max_len: int | None = Field(default=None, ge=1)
    comb: bool = False
    options: list[str] = []

    @model_validator(mode="after")
    def _one_place(self) -> Self:
        exactly_one_place(self, "widget")
        return self


class Page(Contract):
    number: PageNo
    width: float | None = Field(default=None, gt=0)
    height: float | None = Field(default=None, gt=0)
    origin: Origin
    name: str | None = Field(default=None, description="Sheet name of a workbook page.")
    hidden: bool = False
    runs: list[Run] = []
    lines: list[Line] = []
    rects: list[Rect] = []
    tables: list[Table] = []
    widgets: list[Widget] = []

    @model_validator(mode="after")
    def _geometry_matches_origin(self) -> Self:
        placed = [*self.runs, *self.tables, *(c for t in self.tables for c in t.cells), *self.widgets]
        if self.origin == "flow":
            if self.width is not None or self.height is not None or self.lines or self.rects:
                raise ValueError(f"page {self.number}: a flow page has no width, height, lines or rects")
            if any(p.box is not None for p in placed):
                raise ValueError(f"page {self.number}: in a flow page every element carries an anchor, not a box")
        else:
            if self.width is None or self.height is None:
                raise ValueError(f"page {self.number}: a {self.origin} page has width and height")
            if any(p.anchor is not None for p in placed):
                raise ValueError(f"page {self.number}: in a {self.origin} page every element carries a box, not an anchor")
        run_ids = {r.id for r in self.runs}
        missing = sorted({rid for t in self.tables for c in t.cells for rid in c.runs} - run_ids)
        if missing:
            raise ValueError(f"page {self.number}: table cells name runs not on this page: {missing}")
        return self


class PageModel(Contract):
    """The whole document as read: its source, its pages, the readers' warnings."""

    model_version: Literal[1] = 1
    source: Source
    pages: list[Page]
    warnings: list[Warning] = []

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if [p.number for p in self.pages] != list(range(1, len(self.pages) + 1)):
            raise ValueError("pages are numbered 1, 2, 3 ... in order")
        if self.source.pages != len(self.pages):
            raise ValueError(f"source.pages is {self.source.pages} but {len(self.pages)} pages are listed")
        unique([e.id for p in self.pages for e in (*p.runs, *p.lines, *p.rects, *p.tables, *p.widgets)], "ids in the page model")
        return self

    def run_index(self) -> dict[str, tuple[int, Run]]:
        """Run id -> (page number, run): the lookup every later step needs."""
        return {r.id: (p.number, r) for p in self.pages for r in p.runs}

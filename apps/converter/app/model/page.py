"""Page model: the output of every reader and the only thing later steps see (design 5.1, 6.2).

Coordinates in points, origin top left. A page of origin native or ocr places every run, table, cell and widget
with a box; a page of origin flow (binary Word, a DOCX of ordinary paragraphs, sheet cells without geometry)
places them with an anchor instead. Readers never invent coordinates. Ids are unique inside the document.
Reading order is not part of this model: it is the finder's (design 6.3.1); runs are listed in the file's order.

Revision 1.1 (additive): placement is per element. An element may carry a box and an anchor together (a text box
anchored to a paragraph), so a flow page can mix flow paragraphs (anchor) and placed boxes (anchor and box); the
page's origin only says which of the two is mandatory (flow: anchor, native and ocr: box). A flow page may state
its size, and then carry lines and rects too. Reader facts the source declares are kept when given: tab leader,
region, footnote link, picture bounds or an ink flag, row heights and column widths, widget field reference,
display and export values, on-state. Readers build elements with `X.safe(...)`, which never raises on a bad
observation: it normalises or drops it and returns an UNREADABLE_PART warning with the place.
"""
from __future__ import annotations

import math
from typing import Any, ClassVar, Literal, Self

from pydantic import ConfigDict, Field, ValidationError, model_validator

from .common import (
    ONE_PLACE_SCHEMA,
    Anchor,
    Box,
    Contract,
    Format,
    PageNo,
    Sha256,
    Unit,
    Warning,
    omit_empty,
    placed,
    unique,
)

Origin = Literal["native", "ocr", "flow"]
LineStyle = Literal["solid", "dashed", "dotted"]
# What the format itself declares (design 5.1): PDF form fields, Word content controls and legacy form fields,
# sheet data-validation lists. Add a kind here with the reader that meets it.
WidgetKind = Literal["text", "checkbox", "radio", "choice", "date", "signature"]
# Revision 1.1, reader facts (verification plan 5 #5): the leader of a tab stop the source declares ("none": the
# source declares a tab without a leader), and the part of the page a run or table belongs to.
Leader = Literal["dots", "underscores", "none"]
Region = Literal["body", "header", "footer", "footnote"]


class Source(Contract):
    sha256: Sha256
    format: Format
    reader: str = Field(pattern=r"^[a-z0-9_]+(\.[a-z0-9_]+)*$", description='Reader that made the model, e.g. "pdf.native".')
    pages: int = Field(ge=0)


class _Safe:
    """Reader-boundary builder (revision 1.1, verification plan 5 #9): `X.safe(page, **fields)` returns
    (element or None, warnings) and never raises. A raw box is normalised by Box.from_raw; an optional metric that
    is not usable (a font size of zero, a length of zero) is dropped with a warning; an element that still does not
    validate, or that has no usable place, is skipped with a warning. Warnings are UNREADABLE_PART with the page,
    the box or anchor when known, and the element id in `detail`."""

    _METRICS: ClassVar[dict[str, str]] = {}  # optional numeric key -> "positive" | "unit"

    @classmethod
    def safe(cls, page: int, **fields: Any) -> tuple[Any, list[Warning]]:
        kw = {k: v for k, v in fields.items() if v is not None}
        what = f"{cls.__name__.lower()} {kw.get('id', '')}".strip()
        warns: list[Warning] = []
        where: dict[str, Any] = {"page": page} if isinstance(page, int) and page >= 1 else {}

        def warn(detail: str) -> None:
            loc = dict(where)
            if "box" in kw:
                loc["box"] = kw["box"]
            if "anchor" in kw:
                loc["anchor"] = kw["anchor"]
            warns.append(Warning(code="UNREADABLE_PART", detail=f"{what}: {detail}", **loc))

        if "box" in kw:
            raw = kw.pop("box")
            box = Box.from_raw(*raw) if isinstance(raw, (list, tuple)) and len(raw) == 4 else None
            if box is None:
                warn(f"box {list(raw) if isinstance(raw, (list, tuple)) else raw!r} is not usable, left out")
            else:
                kw["box"] = box
        for key, rule in cls._METRICS.items():
            if key not in kw:
                continue
            v = kw[key]
            ok = isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
            ok = ok and (v > 0 if rule == "positive" else 0 <= v <= 1)
            if not ok:
                del kw[key]
                warn(f"{key} {v!r} is not usable, left out")
        try:
            return cls(**kw), warns  # type: ignore[call-arg]
        except ValidationError as e:
            first = e.errors()[0]
            warn(f"skipped, not readable: {first.get('msg', '')}")
            return None, warns


class Run(_Safe, Contract):
    model_config = ConfigDict(json_schema_extra=ONE_PLACE_SCHEMA)
    _METRICS: ClassVar[dict[str, str]] = {"size": "positive", "conf": "unit"}

    id: str = Field(min_length=1)
    text: str
    box: Box | None = None
    anchor: Anchor | None = None
    size: float | None = Field(default=None, gt=0, description="Font size in points, when the format gives it.")
    bold: bool = False
    conf: Unit = Field(default=1.0, description="1 for native text; the OCR word confidence otherwise.")
    leader: Leader | None = Field(default=None, description="1.1: tab leader the source declares for this run's tab.")
    region: Region | None = Field(default=None, description="1.1: part of the page the source declares; absent: not declared.")
    footnote: str | None = Field(default=None, min_length=1, description="1.1: id of the footnote, on its reference mark and on the runs of its text.")

    @model_validator(mode="after")
    def _one_place(self) -> Self:
        placed(self, "run")
        return self


class Line(_Safe, Contract):
    id: str = Field(min_length=1)
    box: Box
    style: LineStyle = "solid"


class Rect(_Safe, Contract):
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
        placed(self, "cell")
        return self


class Table(Contract):
    model_config = ConfigDict(json_schema_extra=ONE_PLACE_SCHEMA)

    id: str = Field(min_length=1)
    box: Box | None = None
    anchor: Anchor | None = None
    cells: list[Cell] = []
    region: Region | None = Field(default=None, description="1.1: part of the page the source declares.")

    @model_validator(mode="after")
    def _one_place(self) -> Self:
        placed(self, "table")
        return self


class WidgetValue(Contract):
    """1.1: one option of a widget as the file declares it: the text shown and the value exported."""

    display: str
    export: str


class Widget(_Safe, Contract):
    model_config = ConfigDict(json_schema_extra=ONE_PLACE_SCHEMA)
    _METRICS: ClassVar[dict[str, str]] = {"max_len": "positive"}

    id: str = Field(min_length=1)
    kind: WidgetKind
    name: str | None = None
    box: Box | None = None
    anchor: Anchor | None = None
    max_len: int | None = Field(default=None, ge=1)
    comb: bool = False
    options: list[str] = []
    field: str | None = Field(default=None, min_length=1, description="1.1: reference of the field this widget is one of (the radio group's shared field).")
    values: list[WidgetValue] = omit_empty(description="1.1: display and export value of each option, when they differ or are declared.")
    on_state: str | None = Field(default=None, min_length=1, description="1.1: the value a checkbox or radio button takes when on.")

    @model_validator(mode="after")
    def _one_place(self) -> Self:
        placed(self, "widget")
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
    pictures: list[Box] = omit_empty(description="1.1: bounds of placed pictures (stamps, logos, scans) the source declares.")
    ink: bool | None = Field(default=None, description="1.1: whether the page shows anything at all; absent: not measured.")
    row_heights: list[float] = omit_empty(description="1.1: sheet row heights in points, by row index from 0.")
    col_widths: list[float] = omit_empty(description="1.1: sheet column widths in points, by column index from 0.")

    @model_validator(mode="after")
    def _geometry_matches_origin(self) -> Self:
        placed_ = [*self.runs, *self.tables, *(c for t in self.tables for c in t.cells), *self.widgets]
        if (self.width is None) != (self.height is None):
            raise ValueError(f"page {self.number}: width and height are given together")
        if any(v < 0 for v in (*self.row_heights, *self.col_widths)):
            raise ValueError(f"page {self.number}: row heights and column widths are not negative")
        if self.origin == "flow":
            if self.width is None and (self.lines or self.rects or self.pictures):
                raise ValueError(f"page {self.number}: a flow page has no width, height, lines or rects unless it states its size")
            if any(p.anchor is None for p in placed_):
                raise ValueError(f"page {self.number}: in a flow page every element carries an anchor, not a box alone")
        else:
            if self.width is None or self.height is None:
                raise ValueError(f"page {self.number}: a {self.origin} page has width and height")
            if any(p.box is None for p in placed_):
                raise ValueError(f"page {self.number}: in a {self.origin} page every element carries a box, not an anchor alone")
        run_ids = {r.id for r in self.runs}
        missing = sorted({rid for t in self.tables for c in t.cells for rid in c.runs} - run_ids)
        if missing:
            raise ValueError(f"page {self.number}: table cells name runs not on this page: {missing}")
        return self


class PageModel(Contract):
    """The whole document as read: its source, its pages, the readers' warnings."""

    model_version: Literal[1, 1.1] = Field(default=1.1, description="Revision of this contract; 1 (1.0) still validates.")
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
